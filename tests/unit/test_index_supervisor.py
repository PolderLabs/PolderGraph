from __future__ import annotations

from pathlib import Path

from poldergraph.indexing import watcher
from poldergraph.indexing.supervisor import IndexSupervisor


def test_watch_filter_uses_watchfiles_change_and_path_signature() -> None:
    assert watcher._should_watch("added", "src/module.py") is True
    assert watcher._should_watch("added", ".git/HEAD") is False


def test_poll_backoff_is_bounded_and_resets_on_change() -> None:
    interval = 1.0
    observed = []
    for _ in range(8):
        interval = watcher._next_poll_interval(
            interval, minimum=1.0, maximum=8.0, changed=False
        )
        observed.append(interval)
    assert observed == [1.5, 2.25, 3.375, 5.0625, 7.59375, 8.0, 8.0, 8.0]
    assert watcher._next_poll_interval(
        interval, minimum=1.0, maximum=8.0, changed=True
    ) == 1.0


def test_watch_intervals_are_configurable_and_validated() -> None:
    import pytest
    from pydantic import ValidationError

    from poldergraph.config.models import IndexConfig

    config = IndexConfig(watch_poll_interval_seconds=2, watch_poll_max_interval_seconds=12)
    assert config.watch_poll_interval_seconds == 2
    assert config.watch_poll_max_interval_seconds == 12
    with pytest.raises(ValidationError):
        IndexConfig(watch_poll_interval_seconds=5, watch_poll_max_interval_seconds=2)


def test_supervisor_starts_and_stops_background_watcher(tmp_path: Path, monkeypatch) -> None:
    def fake_watch(root, *, stop_event, on_started, **_kwargs):
        assert root == tmp_path.resolve()
        on_started()
        stop_event.wait()
        return {"updates": 0, "files_indexed": 0, "errors": 0}

    monkeypatch.setattr(watcher, "run_watch", fake_watch)
    supervisor = IndexSupervisor(tmp_path)

    assert supervisor.start(wait_seconds=1)["state"] == "running"
    assert supervisor.stop(timeout=1)["state"] == "stopped"


def test_supervisor_reports_another_process_as_owner(tmp_path: Path, monkeypatch) -> None:
    from poldergraph.errors import IndexLockedError

    def already_running(*_args, **_kwargs):
        raise IndexLockedError("already supervised")

    monkeypatch.setattr(watcher, "run_watch", already_running)
    supervisor = IndexSupervisor(tmp_path)
    assert supervisor.start(wait_seconds=1)["state"] == "supervised_elsewhere"


def test_supervisor_can_be_disabled_without_starting_thread(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("POLDERGRAPH_NO_WATCHER", "1")
    supervisor = IndexSupervisor(tmp_path)
    assert supervisor.start()["state"] == "disabled"
    assert supervisor._thread is None


def test_watcher_ready_callback_fires_after_watch_registration(tmp_path: Path, monkeypatch) -> None:
    import sys
    import threading
    from types import SimpleNamespace

    from poldergraph.config.models import Config
    from poldergraph.indexing.watcher import run_watch
    from poldergraph.workspace import create_index

    create_index(tmp_path, Config(embedding={"backend": "none"}))
    registered = threading.Event()
    ready = threading.Event()

    def fake_watch(*_roots, **_kwargs):
        registered.set()
        yield set()

    monkeypatch.setitem(sys.modules, "watchfiles", SimpleNamespace(watch=fake_watch))

    def on_started():
        assert registered.is_set()
        ready.set()

    run_watch(tmp_path, on_started=on_started)
    assert ready.is_set()


def test_watcher_loads_backend_before_acquiring_writer_lock(indexed_workspace, monkeypatch):
    import sys
    from types import SimpleNamespace

    active_locks: set[str] = set()
    backend_loaded_under_writer: list[bool] = []

    class FakeIndexLock:
        def __init__(self, _path, *, lock_name="writer", **_kwargs):
            self.name = lock_name

        def acquire(self):
            active_locks.add(self.name)

        def release(self):
            active_locks.discard(self.name)

        def __enter__(self):
            active_locks.add(self.name)
            return self

        def __exit__(self, *_args):
            active_locks.discard(self.name)

    def fake_watch(*_roots, **_kwargs):
        yield {("added", "pkg/auth.py")}

    def fake_apply(_workspace, *, backend):
        assert backend == "loaded-backend"
        assert "writer" in active_locks
        return SimpleNamespace(files_indexed=0)

    monkeypatch.setattr(watcher, "IndexLock", FakeIndexLock)
    monkeypatch.setattr(watcher, "apply_changes", fake_apply)
    monkeypatch.setitem(sys.modules, "watchfiles", SimpleNamespace(watch=fake_watch))

    def backend_provider():
        backend_loaded_under_writer.append("writer" in active_locks)
        return "loaded-backend"

    stats = watcher.run_watch(
        indexed_workspace.root,
        debounce=0,
        max_iterations=1,
        backend_provider=backend_provider,
    )

    assert stats["updates"] == 1
    assert backend_loaded_under_writer == [False]


def test_supervisor_indexes_a_live_edit_without_model_download(tmp_path: Path) -> None:
    import time

    from poldergraph.config.models import Config
    from poldergraph.indexing.pipeline import Indexer
    from poldergraph.workspace import create_index, open_workspace

    source = tmp_path / "module.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    create_index(tmp_path, Config(embedding={"backend": "none"}))
    workspace = open_workspace(tmp_path)
    indexer = Indexer(workspace, backend=None)
    indexer.ensure_root()
    indexer.run(indexer.discover())
    workspace.close()

    # Exercise bounded reconciliation as a fallback for missed native events;
    # keep the interval short so the cross-platform smoke test is practical.
    supervisor = IndexSupervisor(tmp_path, reconcile_interval=1.0)
    assert supervisor.start(wait_seconds=3)["state"] in {"running", "supervised_elsewhere"}
    source.write_text("def live_supervisor_probe():\n    return True\n", encoding="utf-8")
    deadline = time.monotonic() + 15
    try:
        while time.monotonic() < deadline:
            workspace = open_workspace(tmp_path)
            try:
                if indexer_entity_exists(workspace, "live_supervisor_probe"):
                    break
            finally:
                workspace.close()
            time.sleep(0.1)
    finally:
        supervisor.stop()

    workspace = open_workspace(tmp_path)
    try:
        assert indexer_entity_exists(workspace, "live_supervisor_probe")
    finally:
        workspace.close()


def indexer_entity_exists(workspace, name: str) -> bool:
    return (
        workspace.con.execute(
            "SELECT 1 FROM entities WHERE name=? LIMIT 1", (name,)
        ).fetchone()
        is not None
    )
