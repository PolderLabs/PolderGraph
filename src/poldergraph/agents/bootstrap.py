"""Shared zero-configuration bootstrap for coding-agent entry points."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def workspace_root(start: Path | None = None) -> Path:
    """Resolve the nearest existing PolderGraph workspace or project root."""
    from ..discovery.scanner import detect_root
    from ..workspace import find_index_dir

    current = (start or Path.cwd()).resolve()
    existing = find_index_dir(current)
    return existing.parent if existing else detect_root(current)


def ensure_workspace_ready(start: Path | None = None, *, lock_timeout: float = 30.0) -> dict[str, Any]:
    """Create or structurally refresh an index without loading a model or using the network.

    Safe for automatic invocation by agent hooks. The canonical index writer lock
    serializes concurrent hooks and command line clients.
    """
    from ..indexing.incremental import plan_update
    from ..indexing.pipeline import Indexer
    from ..storage.repository import Repository
    from ..storage.sqlite import IndexLock
    from ..workspace import create_index, open_workspace

    root = workspace_root(start)
    index_path = root / ".poldergraph" / "index.sqlite3"
    opt_out = root / ".poldergraph-disable"
    if os.environ.get("POLDERGRAPH_AUTO_INDEX", "").strip().lower() in {"0", "false", "off", "no"}:
        return {
            "ok": True,
            "root": str(root),
            "created": False,
            "state": "unavailable",
            "reason": "Automatic repository indexing is disabled by POLDERGRAPH_AUTO_INDEX.",
            "recovery": "Unset POLDERGRAPH_AUTO_INDEX or set it to 1 to enable automatic indexing.",
        }
    if opt_out.exists():
        return {
            "ok": True,
            "root": str(root),
            "created": False,
            "state": "unavailable",
            "reason": "Automatic repository indexing is disabled by .poldergraph-disable.",
            "recovery": "Remove .poldergraph-disable to enable automatic indexing for this project.",
        }
    # Serialize first-time database creation separately from index updates.
    # The lock lives in the index directory, whose mkdir is itself idempotent.
    with IndexLock(root / ".poldergraph", timeout=lock_timeout, lock_name="bootstrap.lock"):
        created = not index_path.is_file()
        if created:
            # Config() defaults to the local backend, but no backend is constructed
            # here; first contact remains fast and strictly offline.
            create_index(root)

    workspace = open_workspace(root)
    try:
        with IndexLock(workspace.index_dir, timeout=lock_timeout):
            repo = Repository(workspace.con)
            indexer = Indexer(workspace, backend=None)
            indexer.ensure_root()
            discovered = indexer.discover()
            plan = plan_update(repo, discovered, root_id=workspace.root_id())
            stats = None
            if plan.has_work:
                stats = indexer.run(
                    discovered,
                    changed=plan.to_index,
                    removed_paths=plan.removed,
                )
            return {
                "ok": True,
                "root": str(root),
                "created": created,
                "state": "ready_structural",
                "plan": plan.summary(),
                "index": stats.to_dict() if stats else {"changed": 0},
                "graph": {},
            }
    finally:
        workspace.close()
