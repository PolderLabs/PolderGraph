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
