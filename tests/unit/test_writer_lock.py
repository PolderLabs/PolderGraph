from __future__ import annotations

from pathlib import Path

import pytest

from poldergraph.errors import IndexLockedError
from poldergraph.storage.sqlite import IndexLock


def test_index_lock_serializes_writers_but_not_supervisor_lock(tmp_path: Path) -> None:
    writer = IndexLock(tmp_path)
    concurrent_writer = IndexLock(tmp_path)
    supervisor = IndexLock(tmp_path, lock_name="watcher.lock")

    writer.acquire()
    try:
        with pytest.raises(IndexLockedError):
            concurrent_writer.acquire()
        supervisor.acquire()
        supervisor.release()
    finally:
        writer.release()

    concurrent_writer.acquire()
    concurrent_writer.release()
