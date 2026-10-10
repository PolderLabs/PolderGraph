"""Guard the offline benchmark entry points.

Benchmarks are evidence, so they must keep running end to end without weights,
credentials or network access, and must never report figures for a backend that
could not actually run.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
VENV_PYTHON = REPO / ".venv" / "bin" / "python"


def _run(script: str) -> dict:
    python = VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable)
    completed = subprocess.run(
        [str(python), str(REPO / "tests" / "benchmarks" / script)],
        capture_output=True,
        text=True,
        cwd=REPO / "tests" / "benchmarks",
        timeout=900,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    return json.loads(completed.stdout)


@pytest.mark.slow
def test_decision_gate_benchmark_reports_honest_availability():
    report = _run("benchmark_decision_gates.py")

    baseline = report["deterministic_baseline"]
    assert baseline["available"] is True
    assert baseline["cases"] == report["dataset_cases"]
    # A gate that stores nothing it should not is the safety-critical property.
    assert baseline["false_write_rate"] == 0.0

    for provider in ("laya_gates", "typesafe_gates"):
        entry = report[provider]
        if entry["available"] is False:
            # An unavailable backend must carry a reason and no invented metrics.
            assert entry["reason"]
            assert "precision" not in entry
            assert "recall" not in entry

    assert report["privacy"]["network_calls"] == 0
    assert report["privacy"]["weight_downloads"] == 0


@pytest.mark.slow
def test_memory_task_suite_shows_memory_beats_no_memory_baseline():
    report = _run("benchmark_memory_tasks.py")

    enabled = report["memory_enabled"]
    baseline = report["no_memory_baseline"]
    assert enabled["scenarios_fully_passed"] == enabled["scenarios"]
    # Cross-session carry-over is exactly what persistence buys.
    assert enabled["task_success_rate"] > baseline["task_success_rate"]
    assert report["delta_task_success"] > 0


def test_gate_dataset_is_versioned_and_disclosed():
    sys.path.insert(0, str(REPO / "tests" / "benchmarks"))
    from gate_cases import GATE_DATASET_VERSION, gate_cases

    cases = gate_cases()
    assert GATE_DATASET_VERSION
    assert len(cases) == 15
    assert any(case["expected_store"] is True for case in cases)
    assert any(case["expected_store"] is False for case in cases)
    assert any(case["expected_store"] is None for case in cases)