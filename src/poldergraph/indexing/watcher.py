"""Watch mode: coalesced incremental updates.

Editor save patterns (write, rename, delete, create) are debounced into a single
transactional batch so rapid saves do not thrash the index.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..errors import PolderGraphError
from ..storage.repository import Repository
from ..storage.sqlite import IndexLock
from ..workspace import open_workspace

#: Events arriving within this window are coalesced into one update.
DEBOUNCE_SECONDS = 0.4
RECONCILE_SECONDS = 30.0


def _changed_paths(raw: set[Any]) -> set[str]:
    """Normalize watchfile events into a set of path strings."""
    return {str(item) for item in raw}


def run_watch(
    path: Path | None = None,
    *,
    debounce: float = DEBOUNCE_SECONDS,
    on_update: Callable[[Any], None] | None = None,
    max_iterations: int | None = None,
    reconcile_interval: float = RECONCILE_SECONDS,
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
    # This lock prevents duplicate supervisors for this workspace. The writer
    # lock below is held only while applying a batch, so readers and idle
    # command-line clients are not blocked for the lifetime of watch mode.
    supervisor_lock = IndexLock(workspace.index_dir, timeout=0.0, lock_name="watcher.lock")
    try:
        supervisor_lock.acquire()
    except Exception:
        workspace.close()
        raise

    stats = {"updates": 0, "files_indexed": 0, "errors": 0}
    pending: set[str] = set()
    last_event = time.monotonic()
    next_reconcile = last_event + reconcile_interval
    backend = _watch_backend(workspace)

    try:
        roots = [str(workspace.root)]
        for raw in watch(
            *roots,
            stop_event=threading.Event(),
            watch_filter=_should_watch,
            debounce=int(debounce * 1000),
            step=int(debounce * 1000),
            rust_timeout=1000,
            yield_on_timeout=True,
        ):
            changes = _changed_paths(raw)
            pending |= changes
            now = time.monotonic()
            if changes:
                last_event = now

            # Apply after the writer goes quiet.
            if pending and now - last_event < debounce:
                continue
            reconcile_due = now >= next_reconcile
            if not pending and not reconcile_due:
                continue

            if max_iterations is not None and stats["updates"] >= max_iterations:
                break

            try:
                with IndexLock(workspace.index_dir, timeout=0.0):
                    result = apply_changes(workspace, backend=backend)
                stats["updates"] += 1
                stats["files_indexed"] += result.files_indexed
                if on_update:
                    on_update(result)
            except PolderGraphError as exc:
                stats["errors"] += 1
                print(f"watch: {exc.message}")
            else:
                pending.clear()
            next_reconcile = time.monotonic() + reconcile_interval

            if max_iterations is not None and stats["updates"] >= max_iterations:
                break
    except KeyboardInterrupt:
        pass
    finally:
        supervisor_lock.release()
        workspace.close()
    return stats


def _should_watch(path: str) -> bool:
    """Ignore index-internal and VCS paths."""
    parts = Path(path).parts
    return not (".git" in parts or ".poldergraph" in parts or "node_modules" in parts)


def _watch_backend(workspace: Any) -> Any:
    """Load one optional embedding backend for the lifetime of the supervisor."""
    if workspace.config.embedding.backend == "none":
        return None
    try:
        from ..embedding.gemma import create_backend

        return create_backend(workspace.config, cache_dir=None, offline=True)
    except Exception:
        # Structural and lexical updates still work when an optional local
        # model is unavailable or has not been downloaded yet.
        return None


def apply_changes(workspace: Any, *, backend: Any = None) -> Any:
    """Run one incremental update pass for the workspace."""
    from ..graph import run_graph_stage
    from .incremental import plan_update
    from .pipeline import Indexer

    repo = Repository(workspace.con)
    indexer = Indexer(workspace, backend=backend)

    discovered = indexer.discover()
    plan = plan_update(repo, discovered, root_id=workspace.root_id())
    stats = indexer.run(discovered, changed=plan.to_index, removed_paths=plan.removed)
    run_graph_stage(workspace, workspace.config, repo, indexer.backend)
    return stats


def run_once(path: Path | None = None) -> Any:
    """Apply pending changes once; used by tests and hooks."""
    workspace = open_workspace(path)
    try:
        with IndexLock(workspace.index_dir, timeout=0.0):
            return apply_changes(workspace, backend=_watch_backend(workspace))
    finally:
        workspace.close()
