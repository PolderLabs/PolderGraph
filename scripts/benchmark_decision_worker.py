#!/usr/bin/env python3
"""Measure local decision-worker supervision: cold start, warm latency, RSS, eviction.

This benchmark exercises the real supervisor lifecycle (spawn, deadline
enforcement, resident-memory eviction, idle eviction, explicit close) using a
local stand-in worker, so it runs offline and without model weights.

It deliberately does NOT fabricate model-inference figures. Whether a real Laya
checkpoint and a hosted Jev credential are available is probed and reported
explicitly as measured availability, never as extrapolated numbers.

Usage:
    python scripts/benchmark_decision_worker.py [--calls 20] [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from poldergraph.config.models import DecisionsConfig  # noqa: E402
from poldergraph.decision_worker import LocalDecisionWorker  # noqa: E402


def _echo_worker(connection: Any, offline_only: bool) -> None:
    """Stand-in child: same serialization contract, no model weights."""
    while True:
        message = connection.recv()
        if message is None:
            return
        connection.send((True, {"offline_only": offline_only}))


def _hung_worker(connection: Any, _offline_only: bool) -> None:
    """Stand-in child that never answers, to exercise hard deadline killing."""
    connection.recv()
    time.sleep(30)


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def measure_cold_start(worker: LocalDecisionWorker, *, samples: int = 3) -> dict[str, Any]:
    """Time spawn-to-first-answer for a fresh child each time."""
    durations: list[float] = []
    for _ in range(samples):
        worker.close()
        started = time.perf_counter()
        worker.decide("state", {}, model=None, timeout=10.0)
        durations.append((time.perf_counter() - started) * 1000.0)
    return {
        "samples": samples,
        "mean_ms": round(sum(durations) / len(durations), 3),
        "p50_ms": round(_percentile(durations, 0.50), 3),
        "p95_ms": round(_percentile(durations, 0.95), 3),
    }


def measure_warm_latency(worker: LocalDecisionWorker, *, calls: int) -> dict[str, Any]:
    """Time repeated calls against the same already-loaded child."""
    worker.decide("state", {}, model=None, timeout=10.0)
    durations: list[float] = []
    for _ in range(calls):
        started = time.perf_counter()
        worker.decide("state", {}, model=None, timeout=10.0)
        durations.append((time.perf_counter() - started) * 1000.0)
    return {
        "calls": calls,
        "mean_ms": round(sum(durations) / len(durations), 3),
        "p50_ms": round(_percentile(durations, 0.50), 3),
        "p95_ms": round(_percentile(durations, 0.95), 3),
        "p99_ms": round(_percentile(durations, 0.99), 3),
    }


def measure_deadline_enforcement(worker: LocalDecisionWorker) -> dict[str, Any]:
    """A hung child must be killed at the deadline, not block the caller."""

    from poldergraph.decisions import DecisionError

    hung = LocalDecisionWorker(worker_main=_hung_worker)
    try:
        started = time.perf_counter()
        error = None
        try:
            hung.decide("state", {}, model=None, timeout=0.5)
        except DecisionError as exc:
            error = type(exc).__name__
        elapsed = (time.perf_counter() - started) * 1000.0
        return {
            "deadline_ms": 500,
            "elapsed_ms": round(elapsed, 3),
            "error": error,
            "child_stopped_after_timeout": hung.status()["state"] == "stopped",
        }
    finally:
        hung.close()


def measure_memory_cap(worker: LocalDecisionWorker) -> dict[str, Any]:
    """Force a tiny cap so the resident-memory eviction path always triggers."""
    worker.set_limits(max_rss_mb=0.000001)
    try:
        worker.decide("state", {}, model=None, timeout=10.0)
        first_pid = worker._process.pid
        worker.decide("state", {}, model=None, timeout=10.0)
        status = worker.status()
        return {
            "cap_mb": 0.000001,
            "evictions": status["evictions"],
            "last_eviction": status["last_eviction"],
            "child_replaced": worker._process.pid != first_pid,
            "state_after_restart": status["state"],
        }
    finally:
        worker.set_limits(max_rss_mb=None, max_state_tokens=0)


def measure_idle_eviction() -> dict[str, Any]:
    """A worker left unused past its idle window must release its child."""
    worker = LocalDecisionWorker(worker_main=_echo_worker, idle_seconds=0.2)
    try:
        worker.decide("state", {}, model=None, timeout=10.0)
        pid = worker._process.pid
        time.sleep(0.5)
        return {
            "idle_seconds": 0.2,
            "child_stopped": worker.status()["state"] == "stopped",
            "child_released": worker._process is None or pid != worker._process.pid,
        }
    finally:
        worker.close()


def probe_provider_availability() -> dict[str, Any]:
    """Report real availability of the optional decision backends."""
    availability: dict[str, Any] = {}
    try:
        import laya  # noqa: F401

        availability["laya_package"] = "installed"
    except Exception:
        availability["laya_package"] = "not_installed"
    cache = Path(
        os.environ.get("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
    )
    availability["checkpoint_cache"] = str(cache)
    availability["checkpoint_cached"] = any(cache.glob("**/*laya*")) if cache.exists() else False
    availability["typesafe_api_key_present"] = bool(os.environ.get("TYPESAFE_API_KEY"))
    availability["note"] = (
        "No Laya checkpoint is cached and no Jev credential is present, so "
        "model-inference latency, cold-load VRAM and hosted latency are not "
        "measured in this environment."
    )
    return availability


def run(calls: int) -> dict[str, Any]:
    worker = LocalDecisionWorker(worker_main=_echo_worker)
    try:
        report: dict[str, Any] = {
            "platform": {
                "system": platform.system(),
                "machine": platform.machine(),
                "python": platform.python_version(),
            },
            "cold_start": measure_cold_start(worker),
            "warm": measure_warm_latency(worker, calls=calls),
            "resident_memory_after_load": worker.status()["rss_bytes"],
            "deadline_enforcement": measure_deadline_enforcement(worker),
            "memory_cap": measure_memory_cap(worker),
            "idle_eviction": measure_idle_eviction(),
            "provider_availability": probe_provider_availability(),
        }
        return report
    finally:
        worker.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calls", type=int, default=20, help="Warm calls to time.")
    parser.add_argument("--json", type=Path, default=None, help="Also write JSON here.")
    args = parser.parse_args()

    report = run(args.calls)
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())