"""The resident daemon must survive its index file being replaced underneath it.

The daemon keeps long-lived SQLite connections for process lifetime. When the
index is replaced (copied repository, forced reindex, WAL recovery) those
handles go stale and every query would silently return nothing until someone
restarted the daemon.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from poldergraph.config.models import Config
from poldergraph.graph import run_graph_stage
from poldergraph.indexing.pipeline import Indexer
from poldergraph.query_daemon import _is_database_failure
from poldergraph.storage.repository import Repository
from poldergraph.storage.sqlite import connect
from poldergraph.workspace import create_index, open_workspace


def _index(root: Path) -> None:
    (root / "app.py").write_text(
        "def validate_session(token: str) -> bool:\n"
        '    """Check a token is valid."""\n'
        "    return bool(token)\n",
        encoding="utf-8",
    )
    config = Config(embedding={"backend": "none"})
    create_index(root, config)
    workspace = open_workspace(root)
    indexer = Indexer(workspace, backend=None)
    indexer.ensure_root()
    indexer.run(indexer.discover())
    run_graph_stage(workspace, config, Repository(workspace.con), None)
    workspace.close()


def test_database_failures_are_distinguished_from_request_errors():
    assert _is_database_failure(sqlite3.OperationalError("attempt to write a readonly database"))
    assert _is_database_failure(sqlite3.DatabaseError("database is locked"))
    assert _is_database_failure(RuntimeError("Database is locked"))
    # A bad query or missing entity must still surface its own error.
    assert not _is_database_failure(ValueError("unknown symbol: nope"))
    assert not _is_database_failure(FileNotFoundError("no such file"))


def test_opening_an_index_checkpoints_a_carried_over_wal(tmp_path):
    """A copy taken mid-write must not fail later with a readonly database."""
    source = tmp_path / "source"
    source.mkdir()
    _index(source)
    index = source / ".poldergraph" / "index.sqlite3"
    con = connect(index)
    con.execute("INSERT INTO meta(key, value) VALUES('probe', 'x')")
    con.close()
    # Simulate a copy taken while a write-ahead log still holds content.
    (index.parent / "index.sqlite3-wal").write_bytes(b"\x00" * 4096)

    reopened = connect(index)
    try:
        assert reopened.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        reopened.execute("CREATE TABLE IF NOT EXISTS _probe(x)")
        reopened.close()
    finally:
        if reopened:
            with __import__("contextlib").suppress(Exception):
                reopened.close()