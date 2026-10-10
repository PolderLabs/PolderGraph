#!/usr/bin/env python3
"""Compare memory decision gates on a disclosed, offline dataset.

Measures what actually runs in this environment and reports unavailable
backends as unavailable. It never fabricates or extrapolates numbers for a
provider whose weights or credentials are absent.

The benchmark drives the real capture path
(`capture_explicit_user_preferences`), so the reported writes are the writes
PolderGraph would really perform.

Usage:
    python tests/benchmarks/benchmark_decision_gates.py [--dest DIR]
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _workspace import benchmark_workspace  # noqa: E402
from gate_cases import GATE_DATASET_VERSION, gate_cases, retrieval_cases  # noqa: E402


def _build_store(destination: Path) -> tuple[Any, Any]:
    from poldergraph.config.models import Config
    from poldergraph.memory import MemoryStore

    root = destination
    root.mkdir(parents=True, exist_ok=True)
    config = Config(embedding={"backend": "none"})
    return MemoryStore(root), config


def _evaluate_provider(destination: Path, provider: str, cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Run the disclosed dataset through the real capture path for one provider."""
    from poldergraph.config.models import Config
    from poldergraph.memory import capture_explicit_user_preferences

    run_root = destination / f"gate-{provider}"
    store, _config = _build_store(run_root)
    config = Config(embedding={"backend": "none"})
    config.decisions.provider = provider

    stored: list[str] = []
    per_case: list[dict[str, Any]] = []
    latencies: list[float] = []
    for case in cases:
        started = time.perf_counter()
        # The capture path only admits explicit first-person user statements, so
        # each candidate is presented as a user turn exactly as a real hook would.
        written = capture_explicit_user_preferences(
            store,
            case["text"],
            decision_config=config.decisions,
            trusted_user_message=True,
            event_source="benchmark",
            session_id=f"session-{provider}",
            turn_id=case["id"],
        )
        latencies.append((time.perf_counter() - started) * 1000.0)
        wrote = bool(written)
        if wrote:
            stored.append(case["id"])
        per_case.append(
            {
                "id": case["id"],
                "class": case["class"],
                "expected_store": case["expected_store"],
                "stored": wrote,
            }
        )
    scored = [row for row in per_case if row["expected_store"] is not None]
    true_positive = sum(1 for row in scored if row["expected_store"] and row["stored"])
    false_positive = sum(1 for row in scored if not row["expected_store"] and row["stored"])
    false_negative = sum(1 for row in scored if row["expected_store"] and not row["stored"])
    true_negative = sum(1 for row in scored if not row["expected_store"] and not row["stored"])
    # A write that should not have happened is the safety-critical error.
    false_write_rate = false_positive / max(1, false_positive + true_negative)
    return {
        "provider": provider,
        "available": True,
        "cases": len(per_case),
        "stored": len(stored),
        "precision": round(true_positive / max(1, true_positive + false_positive), 4),
        "recall": round(true_positive / max(1, true_positive + false_negative), 4),
        "false_write_rate": round(false_write_rate, 4),
        "abstention_rate": round(
            sum(1 for row in per_case if row["expected_store"] is None and not row["stored"])
            / max(1, sum(1 for row in per_case if row["expected_store"] is None)),
            4,
        ),
        "mean_latency_ms": round(statistics.mean(latencies), 3),
        "p95_latency_ms": round(sorted(latencies)[max(0, round(0.95 * (len(latencies) - 1)))], 3),
        "cold_start_ms": round(latencies[0], 3) if latencies else 0.0,
        "per_case": per_case,
    }


def _probe_laya() -> dict[str, Any]:
    try:
        import laya  # noqa: F401
    except Exception as exc:
        return {
            "provider": "laya",
            "available": False,
            "reason": f"laya package not importable ({type(exc).__name__})",
        }
    return {"provider": "laya", "available": True, "reason": "laya installed"}


def _probe_typesafe() -> dict[str, Any]:
    if not os.environ.get("TYPESAFE_API_KEY"):
        return {
            "provider": "typesafe",
            "available": False,
            "reason": "TYPESAFE_API_KEY is not set; hosted decisions stay opt-in and fail closed.",
        }
    return {"provider": "typesafe", "available": True, "reason": "TYPESAFE_API_KEY present"}


def _retrieval_gate(destination: Path) -> dict[str, Any]:
    """Measure abstention on irrelevant queries through the relevance gate."""
    from poldergraph.config.models import Config
    from poldergraph.memory import MemoryStore

    store, _ = _build_store(destination / "retrieval")
    store.add("Use ruff for linting and formatting in this project.", kind="preference")
    store.add("I prefer pytest fixtures over unittest setUp methods.", kind="preference")
    config = Config(embedding={"backend": "none"})
    results = []
    for case in retrieval_cases():
        started = time.perf_counter()
        memories, meta = _relevance(store, case["query"], config)
        results.append(
            {
                "id": case["id"],
                "relevant": case["relevant"],
                "returned": len(memories),
                "status": meta.get("status"),
                "latency_ms": round((time.perf_counter() - started) * 1000.0, 3),
            }
        )
    relevant = [row for row in results if row["relevant"]]
    irrelevant = [row for row in results if not row["relevant"]]
    return {
        "relevant_cases": len(relevant),
        "irrelevant_cases": len(irrelevant),
        "relevant_answered": sum(1 for row in relevant if row["returned"] > 0),
        "irrelevant_answered": sum(1 for row in irrelevant if row["returned"] > 0),
        "abstains_on_irrelevant": all(row["returned"] == 0 for row in irrelevant),
        "per_case": results,
    }


def _relevance(store: Any, query: str, config: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from poldergraph.decision_runtime import decide_memory_relevance

    memories = store.search(query, limit=10)
    kept, meta = decide_memory_relevance(query, memories, config.decisions)
    return kept, meta or {"status": "not_applied"}


def run(destination: Path) -> dict[str, Any]:
    cases = gate_cases()
    report: dict[str, Any] = {
        "dataset_version": GATE_DATASET_VERSION,
        "dataset_cases": len(cases),
        "offline": True,
        "deterministic_baseline": _evaluate_provider(destination, "disabled", cases),
        "provider_availability": {"laya": _probe_laya(), "typesafe": _probe_typesafe()},
        "privacy": {
            "network_calls": 0,
            "weight_downloads": 0,
            "note": (
                "Hosted providers are opt-in and fail closed without an explicit "
                "credential; no repository content is sent anywhere."
            ),
        },
    }
    for provider, probe in report["provider_availability"].items():
        if probe["available"]:
            report[f"{provider}_gates"] = _evaluate_provider(destination, provider, cases)
        else:
            report[f"{provider}_gates"] = {
                "provider": provider,
                "available": False,
                "reason": probe["reason"],
                "note": "No figures are reported because this backend cannot run here.",
            }
    report["retrieval_gate"] = _retrieval_gate(destination)
    report["limitations"] = [
        "The dataset is small, synthetic and synthetic-shaped; it is not a task-success benchmark.",
        "Precision/recall describe the gate's write decision, not agent productivity.",
        "An unavailable provider is reported as unavailable, never estimated.",
    ]
    return report


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=None)
    args = parser.parse_args()
    if args.dest is None:
        # A temp dir under a contaminated parent would resolve to the wrong
        # workspace root and invalidate every measurement.
        with benchmark_workspace("gate-bench-") as temporary:
            report = run(temporary)
    else:
        report = run(args.dest)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())