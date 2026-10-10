#!/usr/bin/env python3
"""Offline cross-session memory task suite with a no-memory baseline.

Each scenario is a sequence of real Codex `UserPromptSubmit` hook invocations
against a shared memory database, so the measured behavior is the behavior an
agent actually gets. Every scenario runs twice:

- **memory_enabled**: the shipped default.
- **memory_disabled**: the same tasks with memory writes suppressed, which is
  the honest baseline that shows what persistent memory actually contributes.

Scenarios cover durable-preference recall, correction with temporal history,
conflicting corrections across sessions, irrelevant-query abstention, and the
privacy boundary. Nothing here needs a model, weights, or network.

Usage:
    python tests/benchmarks/benchmark_memory_tasks.py [--dest DIR]
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _workspace import benchmark_workspace  # noqa: E402

# Retrieval here is lexical/structural (the semantic channel is disabled), so
# recall prompts deliberately overlap the stored preference wording.
SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "durable_recall",
        "description": "A preference stated in one session is recalled in a later one.",
        "turns": [
            {"session": "s1", "prompt": "I prefer concise explanations.", "event": "UserPromptSubmit", "expect": []},
            {"session": "s2", "prompt": "Do I prefer concise or detailed explanations?", "event": "UserPromptSubmit", "expect_in_output": ["I prefer concise explanations."]},
        ],
    },
    {
        "id": "correction_supersedes",
        "description": "A corrected preference is recalled and the original is superseded.",
        "turns": [
            {"session": "s1", "prompt": "I prefer concise explanations.", "event": "UserPromptSubmit", "expect": []},
            {"session": "s2", "prompt": "I prefer detailed explanations.", "event": "UserPromptSubmit", "expect": []},
            {"session": "s3", "prompt": "Do I prefer concise or detailed explanations?", "event": "UserPromptSubmit", "expect_in_output": ["I prefer detailed explanations."], "expect_absent": ["I prefer concise explanations."]},
        ],
    },
    {
        "id": "irrelevant_abstention",
        "description": "An unrelated question injects no stale preference.",
        "turns": [
            {"session": "s1", "prompt": "I prefer concise explanations.", "event": "UserPromptSubmit", "expect": []},
            {"session": "s2", "prompt": "What is the weather today?", "event": "UserPromptSubmit", "expect_absent": ["I prefer concise explanations."]},
        ],
    },
    {
        "id": "not_persisted_without_user_origin",
        "description": "Agent-authored text is never stored as a user preference.",
        "turns": [
            {"session": "s1", "prompt": "I prefer concise explanations.", "event": "AfterAgentTurn", "expect": []},
            {"session": "s2", "prompt": "Do I prefer concise or detailed explanations?", "event": "UserPromptSubmit", "expect_absent": ["I prefer concise explanations."]},
        ],
    },
]


def _run_scenario(scenario: dict[str, Any], destination: Path, *, memory_enabled: bool) -> dict[str, Any]:
    """Execute one scenario through the real hook and score its expectations.

    With ``memory_enabled=False`` the capture step is disabled, which is the
    honest no-memory baseline: retrieval still runs, nothing is ever written.
    """
    from poldergraph.agents import codex_hook

    root = destination / scenario["id"] / ("on" if memory_enabled else "off")
    root.mkdir(parents=True, exist_ok=True)
    (root / "app.py").write_text("def explain():\n    return 'evidence'\n", encoding="utf-8")

    database = destination / f"{scenario['id']}-{'on' if memory_enabled else 'off'}.sqlite3"
    if database.exists():
        database.unlink()
    os.environ["POLDERGRAPH_MEMORY_DB"] = str(database)
    os.environ["POLDERGRAPH_AUTO_INDEX"] = "1"
    os.environ["POLDERGRAPH_NO_DAEMON"] = "1"

    original_capture = codex_hook._capture_trusted_preferences
    if not memory_enabled:
        codex_hook._capture_trusted_preferences = lambda event: None
    results: list[dict[str, Any]] = []
    try:
        for index, turn in enumerate(scenario["turns"]):
            event = {
                "hook_event_name": turn["event"],
                "prompt": turn["prompt"],
                "cwd": str(root),
                "session_id": turn["session"],
                "turn_id": f"turn-{index}",
            }
            output = io.StringIO()
            started = time.perf_counter()
            codex_hook.run_hook(io.StringIO(json.dumps(event)), output)
            elapsed = (time.perf_counter() - started) * 1000.0
            rendered = output.getvalue()
            for expected in turn.get("expect_in_output", []):
                results.append(
                    {
                        "turn": index,
                        "expectation": expected,
                        "passed": expected.lower() in rendered.lower(),
                        "latency_ms": round(elapsed, 3),
                    }
                )
            for absent in turn.get("expect_absent", []):
                results.append(
                    {
                        "turn": index,
                        "expectation": f"absent: {absent}",
                        "passed": absent.lower() not in rendered.lower(),
                        "latency_ms": round(elapsed, 3),
                    }
                )
    finally:
        codex_hook._capture_trusted_preferences = original_capture

    passed = sum(1 for row in results if row["passed"])
    return {
        "scenario": scenario["id"],
        "memory_enabled": memory_enabled,
        "expectations": len(results),
        "passed": passed,
        "success": passed == len(results),
        "detail": results,
    }


def run(destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=True)
    arms: dict[str, list[dict[str, Any]]] = {"memory_enabled": [], "memory_disabled": []}
    for scenario in SCENARIOS:
        for enabled in (True, False):
            key = "memory_enabled" if enabled else "memory_disabled"
            arms[key].append(_run_scenario(scenario, destination, memory_enabled=enabled))

    def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
        total = sum(row["expectations"] for row in rows)
        passed = sum(row["passed"] for row in rows)
        return {
            "scenarios": len(rows),
            "scenarios_fully_passed": sum(1 for row in rows if row["success"]),
            "expectations": total,
            "expectations_passed": passed,
            "task_success_rate": round(passed / max(1, total), 4),
        }

    enabled_summary = summarize(arms["memory_enabled"])
    baseline_summary = summarize(arms["memory_disabled"])
    return {
        "scenarios": [scenario["id"] for scenario in SCENARIOS],
        "memory_enabled": enabled_summary,
        "no_memory_baseline": baseline_summary,
        "delta_task_success": round(
            enabled_summary["task_success_rate"] - baseline_summary["task_success_rate"], 4
        ),
        "arms": arms,
        "limitations": [
            "Synthetic scenarios with scripted expectations, not real coding tasks.",
            "No agent model is involved, so this measures memory plumbing, not productivity.",
            "Structural retrieval runs offline; the semantic channel is disabled.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=None)
    args = parser.parse_args()
    if args.dest is None:
        # A temp dir under a contaminated parent would resolve to the wrong
        # workspace root and invalidate every measurement.
        with benchmark_workspace("memory-tasks-") as temporary:
            report = run(temporary)
    else:
        report = run(args.dest)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())