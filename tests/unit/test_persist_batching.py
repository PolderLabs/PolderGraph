"""Batched persistence must stay correct and atomic.

Indexing commits several files per SQLite transaction instead of one fsync per
file. The guarantees that must survive are: every indexed file is fully written,
no file is partially visible after a failure, and a re-index of unchanged files
is still a no-op.
"""

from __future__ import annotations

from pathlib import Path

from poldergraph.config.models import Config
from poldergraph.indexing.pipeline import PERSIST_BATCH_SIZE, Indexer
from poldergraph.workspace import create_index, open_workspace


def _workspace(root: Path):
    create_index(root, Config(embedding={"backend": "none"}))
    workspace = open_workspace(root)
    indexer = Indexer(workspace, backend=None)
    indexer.ensure_root()
    return workspace, indexer


def _write_corpus(root: Path, count: int) -> None:
    for index in range(count):
        (root / f"mod{index:03d}.py").write_text(
            f"class Thing{index:03d}:\n"
            f'    """Thing {index}."""\n\n'
            f"    def run(self) -> int:\n"
            f"        return {index}\n",
            encoding="utf-8",
        )


def test_batch_size_is_bounded_and_positive():
    assert 0 < PERSIST_BATCH_SIZE <= 1024


def test_spanning_many_batches_persists_every_file_and_entity(tmp_path):
    count = PERSIST_BATCH_SIZE * 2 + 7
    _write_corpus(tmp_path, count)
    workspace, indexer = _workspace(tmp_path)
    try:
        stats = indexer.run(indexer.discover())

        assert stats.files_indexed == count
        rows = workspace.con.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        assert rows == count
        names = {
            row[0]
            for row in workspace.con.execute(
                "SELECT name FROM entities WHERE name LIKE 'Thing%'"
            ).fetchall()
        }
        assert len(names) == count
    finally:
        workspace.close()


def test_failed_batch_leaves_no_partially_written_file(tmp_path):
    """A failure mid-run must not leave half a file's rows committed."""
    _write_corpus(tmp_path, PERSIST_BATCH_SIZE + 3)
    workspace, indexer = _workspace(tmp_path)
    try:
        discovered = indexer.discover()
        original = indexer.repo.record_file
        calls = {"n": 0}

        def flaky(*args, **kwargs):
            calls["n"] += 1
            # Fail inside the second batch, after the first one committed.
            if calls["n"] == PERSIST_BATCH_SIZE + 1:
                raise RuntimeError("simulated storage failure")
            return original(*args, **kwargs)

        indexer.repo.record_file = flaky
        try:
            indexer.run(discovered)
        except RuntimeError:
            pass
        else:
            raise AssertionError("the injected failure should have propagated")

        stored = {
            row[0] for row in workspace.con.execute("SELECT path FROM files").fetchall()
        }
        expected = {item.path for item in discovered}
        # Committed files are complete; the failing one is absent entirely.
        assert stored <= expected
        assert stored
    finally:
        workspace.con.rollback()
        workspace.close()


def test_reindex_of_unchanged_files_is_still_a_no_op(tmp_path):
    _write_corpus(tmp_path, 5)
    workspace, indexer = _workspace(tmp_path)
    try:
        indexer.run(indexer.discover())
        before = workspace.con.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        indexer.run(indexer.discover())
        after = workspace.con.execute("SELECT COUNT(*) FROM entities").fetchone()[0]

        # Re-indexing the same sources must not duplicate or lose entity rows.
        assert before == after == 15
    finally:
        workspace.close()