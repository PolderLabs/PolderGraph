"""Watch mode: coalesced incremental updates.

Editor save patterns (write, rename, delete, create) are debounced into a single
transactional batch so rapid saves do not thrash the index.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Callable

from ..config.loader import load_config
from ..errors import PolderGraphError
from ..storage.repository import Repository
from ..storage.sqlite import IndexLock
from ..workspace import open_workspace

#: Events arriving within this window are coalesced into one update.
DEBOUNCE_SECONDS = 0.4


def _changed_paths(raw: set[Any]) -> set[str]:
    """Normalize watchfile events into a set of path strings."""
    return {str(item) for item in raw}


def run_watch(
    path: Path | None = None,
    *,
    debounce: float = DEBOUNCE_SECONDS,
    on_update: Callable[[Any], None] | None = None,
    max_iterations: int | None = None,
) -> dict[str, Any]:
    """Watch a workspace and apply incremental updates until interrupted."""
    try:
        from watchfiles import watch
    except ImportError as exc:
        raise PolderGraphError(
            "watchfiles is not installed.",
            code="BACKEND_UNAVAILABLE",
            remediation="Install it with: uv pip install watchfiles",
        ) from exc

    workspace = open_workspace(path)
    lock = IndexLock(workspace.index_dir, timeout=0.0)
    lock.acquire()

    stats = {"updates": 0, "files_indexed": 0, "errors": 0}
    pending: set[str] = set()
    last_event = time.monotonic()

    try:
        roots = [str(workspace.root)]
        for raw in watch(
            *roots,
            stop_event=threading.Event(),
            watch_filter=_should_watch,
            debounce=int(debounce * 1000),
            step=int(debounce * 1000),
        ):
            changes = _changed_paths(raw)
            if not changes:
                continue
            pending |= changes
            last_event = time.monotonic()

            # Apply after the writer goes quiet.
            while time.monotonic() - last_event < debounce:
                time.sleep(min(0.05, debounce))

            if max_iterations is not None and stats["updates"] >= max_iterations:
                break

            try:
                result = apply_changes(workspace)
                stats["updates"] += 1
                stats["files_indexed"] += result.files_indexed
                if on_update:
                    on_update(result)
            except PolderGraphError as exc:
                stats["errors"] += 1
                print(f"watch: {exc.message}")
            pending.clear()

            if max_iterations is not None and stats["updates"] >= max_iterations:
                break
    except KeyboardInterrupt:
        pass
    finally:
        lock.release()
        workspace.close()
    return stats


def _should_watch(path: str) -> bool:
    """Ignore index-internal and VCS paths."""
    parts = Path(path).parts
    return not (".git" in parts or ".poldergraph" in parts or "node_modules" in parts)


def apply_changes(workspace: Any) -> Any:
    """Run one incremental update pass for the workspace."""
    from ..embedding.gemma import create_backend
    from ..graph import run_graph_stage
    from .incremental import plan_update
    from .pipeline import Indexer

    repo = Repository(workspace.con)
    indexer = Indexer(workspace, backend=None)
    if workspace.config.embedding.backend != "none":
        indexer.backend = create_backend(
            workspace.config, cache_dir=workspace.index_dir / "cache" / "model", offline=True
        )

    discovered = indexer.discover()
    plan = plan_update(repo, discovered, root_id=workspace.root_id())
    stats = indexer.run(discovered, changed=plan.to_index, removed_paths=plan.removed)
    run_graph_stage(workspace, workspace.config, repo, indexer.backend)
    return stats


def run_once(path: Path | None = None) -> Any:
    """Apply pending changes once; used by tests and hooks."""
    workspace = open_workspace(path)
    try:
        return apply_changes(workspace)
    finally:
        workspace.close()