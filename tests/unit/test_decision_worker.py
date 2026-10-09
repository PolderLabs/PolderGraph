"""Process supervision behavior for the optional local decision model."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

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


def test_queued_call_deadline_includes_waiting_for_worker_lock() -> None:
    worker = LocalDecisionWorker(worker_main=_hung_worker)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(worker.decide, "first", {}, model=None, timeout=0.8)
        deadline = time.monotonic() + 1
        while worker._process is None and time.monotonic() < deadline:
            time.sleep(0.01)
        time.sleep(0.05)

        started = time.monotonic()
        with pytest.raises(DecisionError, match="waiting for the worker"):
            worker.decide("second", {}, model=None, timeout=0.1)
        assert time.monotonic() - started < 0.3
        with pytest.raises(DecisionError, match="deadline exceeded"):
            first.result(timeout=2)
    assert worker._process is None
    worker.close()
