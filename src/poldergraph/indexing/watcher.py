"""Watch mode: coalesced incremental updates.

Editor save patterns (write, rename, delete, create) are debounced into a single
transactional batch so rapid saves do not thrash the index.
"""

from __future__ import annotations

import os
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
POLL_SECONDS = 5.0


def _changed_paths(raw: set[Any]) -> set[str]:
    """Normalize watchfile events into a set of path strings."""
    return {
        str(item[1] if isinstance(item, tuple) and len(item) > 1 else item)
        for item in raw
    }


def run_watch(
    path: Path | None = None,
    *,
    debounce: float = DEBOUNCE_SECONDS,
    on_update: Callable[[Any], None] | None = None,
    max_iterations: int | None = None,
    reconcile_interval: float = RECONCILE_SECONDS,
    stop_event: threading.Event | None = None,
    backend_provider: Callable[[], Any] | None = None,
    on_started: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Watch a workspace and apply incremental updates until interrupted."""
    try:
        from watchfiles import watch
    except ImportError:
        watch = None

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
    stop = stop_event or threading.Event()
    backend = None

    def get_backend() -> Any:
        nonlocal backend
        if backend is None:
            backend = backend_provider() if backend_provider else _watch_backend(workspace)
        return backend

    def apply_pending() -> None:
        nonlocal pending, next_reconcile
        with IndexLock(workspace.index_dir, timeout=0.0):
            result = apply_changes(workspace, backend=get_backend())
        stats["updates"] += 1
        stats["files_indexed"] += result.files_indexed
        if on_update:
            on_update(result)
        pending.clear()
        next_reconcile = time.monotonic() + reconcile_interval

    try:
        if on_started:
            on_started()
        if watch is None:
            _poll_changes(
                workspace,
                stop,
                debounce=debounce,
                reconcile_interval=reconcile_interval,
                pending=pending,
                apply=apply_pending,
                on_error=lambda exc: _record_watch_error(stats, exc),
                max_iterations=max_iterations,
                stats=stats,
            )
        else:
            roots = [str(workspace.root)]
            for raw in watch(
                *roots,
                stop_event=stop,
                watch_filter=_should_watch,
                debounce=int(debounce * 1000),
                step=int(debounce * 1000),
                rust_timeout=1000,
                yield_on_timeout=True,
                # Windows editor/antivirus combinations can silently lose
                # native notifications. The polling backend preserves the
                # same debounced queue while making change delivery reliable.
                force_polling=os.name == "nt",
            ):
                changes = _changed_paths(raw)
                pending |= changes
                now = time.monotonic()
                if changes:
                    last_event = now
                if pending and now - last_event < debounce:
                    continue
                if not pending and now < next_reconcile:
                    continue
                if max_iterations is not None and stats["updates"] >= max_iterations:
                    break
                try:
                    apply_pending()
                except Exception as exc:
                    _record_watch_error(stats, exc)
                if max_iterations is not None and stats["updates"] >= max_iterations:
                    break
    except KeyboardInterrupt:
        pass
    finally:
        supervisor_lock.release()
        workspace.close()
    return stats


def _record_watch_error(stats: dict[str, int], exc: Exception) -> None:
    stats["errors"] += 1
    message = exc.message if isinstance(exc, PolderGraphError) else str(exc)
    print(f"watch: {message}")


def _poll_changes(
    workspace: Any,
    stop: threading.Event,
    *,
    debounce: float,
    reconcile_interval: float,
    pending: set[str],
    apply: Callable[[], None],
    on_error: Callable[[Exception], None],
    max_iterations: int | None,
    stats: dict[str, int],
) -> None:
    """Polling fallback when the native watchfiles backend is unavailable."""
    from .pipeline import Indexer

    def fingerprint() -> dict[str, tuple[int, int]]:
        return {
            item.path: (item.size, item.mtime_ns)
            for item in Indexer(workspace, backend=None).discover().files
        }

    previous = fingerprint()
    next_reconcile = time.monotonic() + reconcile_interval
    last_change = 0.0
    while not stop.wait(POLL_SECONDS):
        now = time.monotonic()
        current = fingerprint()
        if current != previous:
            pending.add("poll-detected-change")
            previous = current
            last_change = now
        if pending and now - last_change < debounce:
            continue
        if not pending and now < next_reconcile:
            continue
        if max_iterations is not None and stats["updates"] >= max_iterations:
            break
        try:
            apply()
            pending.clear()
        except Exception as exc:
            on_error(exc)
        next_reconcile = time.monotonic() + reconcile_interval
        if max_iterations is not None and stats["updates"] >= max_iterations:
            break


def _should_watch(change_or_path: Any, path: str | None = None) -> bool:
    """Ignore index-internal and VCS paths."""
    # watchfiles filters receive (change, path); accept one-argument calls as
    # well so callers can validate a path without synthesizing an event.
    path = path if path is not None else str(change_or_path)
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
