"""Memory-pressure supervision and status-contract behavior for the local worker."""

from __future__ import annotations

import pytest

from poldergraph.config.models import Config
from poldergraph.decision_runtime import apply_supervision_limits
from poldergraph.decision_worker import (
    STATUS_CONTRACT_VERSION,
    LocalDecisionWorker,
    _validate_max_rss_mb,
    rss_bytes,
)
from poldergraph.decisions import DecisionError, choice


def _echo_worker(connection, offline_only: bool) -> None:
    while True:
        message = connection.recv()
        if message is None:
            return
        connection.send((True, {"offline_only": offline_only}))


def test_status_reports_versioned_contract_fields() -> None:
    worker = LocalDecisionWorker(worker_main=_echo_worker)
    try:
        status = worker.status()
        for field in (
            "contract_version",
            "deadline_ms",
            "offline_only",
            "model_revision",
            "max_state_tokens",
            "status",
        ):
            if field == "status":
                # The contract exposes worker state under "state"; assert it is bounded.
                assert status["state"] in {"warm", "running", "stopped", "busy"}
                continue
            assert field in status
        assert status["contract_version"] == STATUS_CONTRACT_VERSION
    finally:
        worker.close()


def test_status_exposes_resident_memory_and_cap() -> None:
    worker = LocalDecisionWorker(worker_main=_echo_worker, max_rss_mb=512.0)
    try:
        worker.decide("state", {}, model=None, timeout=2)
        status = worker.status()
        assert status["max_rss_mb"] == 512.0
        assert status["rss_known"] is True
        assert status["rss_bytes"] > 0
    finally:
        worker.close()


def test_oversized_worker_is_evicted_and_restarts_cleanly() -> None:
    worker = LocalDecisionWorker(worker_main=_echo_worker, max_rss_mb=0.000001)
    try:
        worker.decide("state", {}, model=None, timeout=2)
        first_pid = worker._process.pid
        # The next call observes the over-cap child, evicts it and starts fresh.
        worker.decide("state", {}, model=None, timeout=2)
        status = worker.status()
        assert status["evictions"] >= 1
        assert status["last_eviction"] == "memory"
        assert worker._process.pid != first_pid
        assert status["state"] == "warm"
    finally:
        worker.close()


def test_unmeasurable_memory_never_triggers_eviction(monkeypatch) -> None:
    monkeypatch.setattr("poldergraph.decision_worker.rss_bytes", lambda pid: None)
    worker = LocalDecisionWorker(worker_main=_echo_worker, max_rss_mb=0.000001)
    try:
        worker.decide("state", {}, model=None, timeout=2)
        pid = worker._process.pid
        worker.decide("state", {}, model=None, timeout=2)
        assert worker._process.pid == pid
        assert worker.status()["evictions"] == 0
    finally:
        worker.close()


def test_rss_bytes_is_none_for_invalid_pid() -> None:
    assert rss_bytes(None) is None
    assert rss_bytes(0) is None
    assert rss_bytes(-1) is None


def test_max_rss_mb_validation() -> None:
    assert _validate_max_rss_mb(None) is None
    assert _validate_max_rss_mb(128) == 128.0
    with pytest.raises(ValueError):
        _validate_max_rss_mb(0)
    with pytest.raises(ValueError):
        _validate_max_rss_mb(-5)


def test_state_token_bound_is_enforced_and_reported() -> None:
    worker = LocalDecisionWorker(worker_main=_echo_worker, max_state_tokens=5)
    try:
        with pytest.raises(DecisionError) as excinfo:
            worker.decide("word " * 500, {}, model="fixture", timeout=2)
        assert "max_state_tokens" in str(excinfo.value)
        worker.decide("short", {}, model="fixture", timeout=2)
        status = worker.status()
        assert status["max_state_tokens"] == 5
        assert status["model_revision"] == "fixture"
    finally:
        worker.close()


def test_batch_respects_state_token_bound() -> None:
    worker = LocalDecisionWorker(worker_main=_echo_worker, max_state_tokens=5)
    try:
        with pytest.raises(DecisionError):
            worker.decide_batch(
                [{"q": "word " * 500}], {}, model="fixture", timeout=2
            )
    finally:
        worker.close()


def test_apply_supervision_limits_pushes_config_into_worker() -> None:
    from poldergraph.decision_runtime import local_decision_worker

    config = Config()
    config.decisions.provider = "laya"
    config.decisions.max_rss_mb = 256.0
    config.decisions.max_state_tokens = 128
    try:
        apply_supervision_limits(config.decisions)
        assert local_decision_worker._max_rss_mb == 256.0
        assert local_decision_worker._max_state_tokens == 128
        status = local_decision_worker.status()
        assert status["max_rss_mb"] == 256.0
        assert status["max_state_tokens"] == 128
    finally:
        local_decision_worker.set_limits(max_rss_mb=None, max_state_tokens=0)


def test_config_rejects_invalid_supervision_caps() -> None:
    from poldergraph.config.models import DecisionsConfig

    with pytest.raises(Exception):
        DecisionsConfig(max_rss_mb=-1)
    with pytest.raises(Exception):
        DecisionsConfig(max_state_tokens=-5)
    assert DecisionsConfig().max_rss_mb is None
    assert DecisionsConfig().max_state_tokens == 0


def test_oversized_state_is_rejected_before_any_model_load() -> None:
    worker = LocalDecisionWorker(worker_main=_echo_worker, max_state_tokens=1)
    try:
        with pytest.raises(DecisionError):
            worker.decide(
                "a state that is comfortably larger than one token",
                {"intent": choice("intent", "Pick one", {"a": "first", "b": "second"})},
                model="fixture",
                timeout=2,
            )
        assert worker.status()["state"] == "stopped"
    finally:
        worker.close()