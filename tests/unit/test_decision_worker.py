"""Process supervision behavior for the optional local decision model."""

from __future__ import annotations

import time

import pytest

from poldergraph.decision_worker import LocalDecisionWorker
from poldergraph.decisions import DecisionError


def _echo_worker(connection, offline_only: bool) -> None:
    while True:
        message = connection.recv()
        if message is None:
            return
        connection.send((True, {"offline_only": offline_only}))


def _hung_worker(connection, _offline_only: bool) -> None:
    connection.recv()
    time.sleep(10)


def test_worker_reuses_child_and_respects_offline_mode() -> None:
    worker = LocalDecisionWorker(worker_main=_echo_worker)
    try:
        first = worker.decide("state", {}, model=None, timeout=2)
        first_pid = worker._process.pid
        second = worker.decide("state", {}, model=None, timeout=2)
        assert first == second == {"offline_only": False}
        assert worker._process.pid == first_pid
        offline = worker.decide("state", {}, model=None, timeout=2, offline_only=True)
        assert offline == {"offline_only": True}
        assert worker._process.pid != first_pid
    finally:
        worker.close()


def test_hung_worker_is_killed_at_deadline() -> None:
    worker = LocalDecisionWorker(worker_main=_hung_worker)
    with pytest.raises(DecisionError, match="deadline exceeded"):
        worker.decide("state", {}, model=None, timeout=0.2)
    assert worker._process is None
    worker.close()
