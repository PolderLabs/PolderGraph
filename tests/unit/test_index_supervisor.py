from __future__ import annotations

from pathlib import Path

from poldergraph.indexing import watcher
from poldergraph.indexing.supervisor import IndexSupervisor


def test_watch_filter_uses_watchfiles_change_and_path_signature() -> None:
    assert watcher._should_watch("added", "src/module.py") is True
    assert watcher._should_watch("added", ".git/HEAD") is False


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
