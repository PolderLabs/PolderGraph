"""Safe complete rebuild.

The replacement index is built in a separate directory and swapped into place
only after it succeeds, so a failed rebuild never destroys a working index.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any

from .config.models import Config
from .errors import PolderGraphError
from .workspace import create_index, index_dir_for, open_workspace


def rebuild_index(
    root: Path, *, keep_backup: bool = True, use_backend: bool = True
) -> dict[str, Any]:
    """Rebuild the index atomically and return a summary.

    The replacement index is built in a separate directory that is swapped in
    only after it passes integrity checks, so a failed rebuild never destroys a
    working index. Set ``use_backend=False`` for a structural-only rebuild that
    skips the embedding model entirely.
    """
    root = root.resolve()
    index_dir = index_dir_for(root)
    staging = root / ".poldergraph.rebuild"

    if staging.exists():
        shutil.rmtree(staging)

    config = Config()
    config_path = index_dir / "config.toml"
    if config_path.is_file():
        # Preserve the operator's configuration across a rebuild.
        from .config.loader import load_config

        try:
            config = load_config(index_dir).config
        except PolderGraphError:
            pass

    started = time.monotonic()
    backup: Path | None = None
    swapped = False
    staging_src: Path | None = None

    import tempfile as _tempfile

    try:
        from .embedding.gemma import create_backend
        from .graph import run_graph_stage
        from .indexing.pipeline import Indexer
        from .storage.repository import Repository

        # Build into a temporary directory outside the root so the live index
        # is never touched during the build.
        staging_src = Path(_tempfile.mkdtemp(prefix="pg_rebuild_", dir=root.parent))
        staging_idx = staging_src / ".poldergraph"
        staging_idx.mkdir(parents=True, exist_ok=True)
        (staging_idx / "logs").mkdir(exist_ok=True)
        (staging_idx / "cache").mkdir(exist_ok=True)
        (staging_idx / "cache" / "model").mkdir(exist_ok=True)
        (staging_idx / "cache" / "media").mkdir(exist_ok=True)
        from .workspace import write_config, initialize as _init, write_state as _write_state
        from .storage.schema import SCHEMA_VERSION as _SV
        write_config(config, staging_idx)
        con = _init(staging_idx / "index.sqlite3")
        con.close()
        _write_state(staging_idx, created_at=time.time(), schema_version=_SV)

        workspace = open_workspace(staging_src, require_index=False)
        repo = Repository(workspace.con)
        backend = None
        degraded: list[str] = []
        if use_backend and workspace.config.embedding.backend != "none":
            try:
                model_cache = index_dir / "cache" / "model"
                backend = create_backend(workspace.config, cache_dir=model_cache)
                backend.model_info()
            except PolderGraphError as exc:
                degraded.append(exc.message)
                backend = None

        indexer = Indexer(workspace, backend=backend)
        # Point discovery at the real repository, not the staging directory.
        indexer.workspace.root = root
        indexer.ensure_root()
        stats = indexer.run(indexer.discover())
        graph = run_graph_stage(workspace, workspace.config, repo, backend)

        from .storage.integrity import run_doctor

        report = run_doctor(repo, dimensions=workspace.config.index.dimensions)
        if not report.ok:
            raise PolderGraphError(
                "Rebuild produced an index that fails integrity checks: "
                + ", ".join(check.name for check in report.failures),
                code="REBUILD_FAILED",
                remediation="The existing index was left untouched.",
            )

        workspace.close()

        # Atomic swap: keep the old index until the new one is in place.
        if index_dir.exists():
            backup = root / ".poldergraph.backup"
            if backup.exists():
                shutil.rmtree(backup)
            index_dir.rename(backup)
        staging_idx.rename(index_dir)
        swapped = True

        if backup is not None and not keep_backup:
            shutil.rmtree(backup)
            backup = None

        shutil.rmtree(staging_src, ignore_errors=True)

        return {
            "root": str(root),
            "files_indexed": stats.files_indexed,
            "entities_written": stats.entities_written,
            "edges_written": stats.edges_written,
            "embeddings_written": stats.embeddings_written,
            "communities": sum(len(c.memberships) for c in graph.communities),
            "duration_seconds": round(time.monotonic() - started, 3),
            "backup": str(backup) if backup else None,
            "degraded": degraded + stats.degraded,
        }
    except Exception:
        if not swapped:
            if staging_src.exists():
                shutil.rmtree(staging_src, ignore_errors=True)
            if not index_dir.exists() and backup is not None and backup.exists():
                backup.rename(index_dir)
        raise