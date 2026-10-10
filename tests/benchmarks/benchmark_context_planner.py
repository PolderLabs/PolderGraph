"""Compare adaptive context planning with a fixed 3k-token context baseline.

This is an offline evidence-coverage proxy, not an agent task-success benchmark.
The synthetic corpus supplies expected entities so the report can measure
grounding, context size, request latency and search-call count reproducibly.
"""

from __future__ import annotations

import json
import statistics
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from corpus_repo import build_corpus, cases  # noqa: E402


def _evidence_names(result: Any) -> set[str]:
    entities = result.entities if hasattr(result, "entities") else result.get("entities", [])
    snippets = result.snippets if hasattr(result, "snippets") else result.get("snippets", [])
    names = {item.get("name", "") for item in entities}
    names.update(item.get("name", "") for item in snippets)
    return {name for name in names if name}


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def _summarize(rows: list[dict[str, Any]], *, configuration: str) -> dict[str, Any]:
    active = [row for row in rows if row["expected"]]
    hits = [row for row in active if row["matched"]]
    relevant = sum(row["matched"] for row in rows)
    evidence = sum(row["evidence_count"] for row in rows)
    latencies = [row["latency_ms"] for row in rows]
    return {
        "configuration": configuration,
        "cases": len(rows),
        "grounded_case_recall": round(len(hits) / max(1, len(active)), 4),
        "grounded_evidence_precision": round(relevant / max(1, evidence), 4),
        "unnecessary_context_rate": round(1 - relevant / max(1, evidence), 4),
        "mean_token_estimate": round(statistics.mean(row["tokens"] for row in rows), 1),
        "p50_token_estimate": round(_percentile([row["tokens"] for row in rows], 0.50), 1),
        "p95_token_estimate": round(_percentile([row["tokens"] for row in rows], 0.95), 1),
        "mean_latency_ms": round(statistics.mean(latencies), 3),
        "p50_latency_ms": round(statistics.median(latencies), 3),
        "p95_latency_ms": round(_percentile(latencies, 0.95), 3),
        "mean_search_calls": round(statistics.mean(row["search_calls"] for row in rows), 2),
        "context_requests": len(rows),
    }


def run(destination: Path, *, repeats: int = 3) -> dict[str, Any]:
    from poldergraph.config.models import Config
    from poldergraph.graph import run_graph_stage
    from poldergraph.indexing.pipeline import Indexer
    from poldergraph.retrieval.context import pack_context
    from poldergraph.retrieval.service import QueryService
    from poldergraph.storage.repository import Repository
    from poldergraph.workspace import create_index, open_workspace

    root = build_corpus(destination)
    config = Config(embedding={"backend": "none"})
    create_index(root, config)
    workspace = open_workspace(root)
    repository = Repository(workspace.con)
    indexer = Indexer(workspace, backend=None)
    indexer.ensure_root()
    indexer.run(indexer.discover())
    run_graph_stage(workspace, config, repository, None)
    service = QueryService(repository, config, None, root_id=workspace.root_id(), workspace=workspace)
    original_search = service.search
    call_count = 0

    def counted_search(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        return original_search(*args, **kwargs)

    service.search = counted_search
    adaptive_rows: list[dict[str, Any]] = []
    adaptive_wide_rows: list[dict[str, Any]] = []
    fixed_rows: list[dict[str, Any]] = []
    try:
        benchmark_cases = [
            *cases(),
            {"id": "social_greeting", "question": "Hello!", "expect": []},
            {"id": "unrelated_weather", "question": "What is the weather?", "expect": []},
        ]
        for case in benchmark_cases:
            for _ in range(repeats):
                expected = set(case["expect"])
                # Primary comparison is budget-matched: adaptive planning and the
                # fixed baseline both run at 3,000 tokens so planner strategy is
                # the only variable. The wider budget is reported separately and
                # labelled, never as the headline comparison.
                for rows, budget in ((adaptive_rows, 3000), (adaptive_wide_rows, 6000)):
                    before = call_count
                    started = time.perf_counter()
                    adaptive = service.context(case["question"], token_budget=budget)
                    adaptive_ms = (time.perf_counter() - started) * 1000
                    adaptive_names = _evidence_names(adaptive)
                    adaptive_hits = len(expected & adaptive_names)
                    rows.append(
                        {
                            "id": case["id"],
                            "expected": bool(expected),
                            "matched": adaptive_hits,
                            "evidence_count": len(adaptive_names),
                            "tokens": adaptive.token_estimate,
                            "latency_ms": adaptive_ms,
                            "search_calls": call_count - before,
                            "intent": adaptive.plan.intent if adaptive.plan else "none",
                            "skipped": bool(adaptive.plan and adaptive.plan.skipped),
                            "budget": budget,
                        }
                    )

                before = call_count
                started = time.perf_counter()
                response = service.search(
                    case["question"],
                    limit=30,
                    include_semantic=False,
                    include_structural_context=True,
                )
                freshness = service.freshness(verify_content=False)
                fixed = pack_context(
                    service,
                    case["question"],
                    response,
                    token_budget=3000,
                    root=str(root),
                    freshness=freshness,
                )
                fixed_ms = (time.perf_counter() - started) * 1000
                fixed_names = _evidence_names(fixed)
                fixed_rows.append(
                    {
                        "id": case["id"],
                        "expected": bool(expected),
                        "matched": len(expected & fixed_names),
                        "evidence_count": len(fixed_names),
                        "tokens": fixed.token_estimate,
                        "latency_ms": fixed_ms,
                        "search_calls": call_count - before,
                    }
                )
    finally:
        workspace.close()

    return {
        "method": {
            "corpus": "tests/benchmarks/corpus_manifest.json",
            "repeats_per_case": repeats,
            "embedding_backend": "none (offline structural/lexical retrieval)",
            "baseline": "One search plus context packing with a fixed 3,000-token budget.",
            "token_budget": 3000,
            "budget_matched": True,
            "comparison_note": (
                "adaptive_planner_3000 and fixed_3000_baseline share the same "
                "3,000-token budget, so the difference is planner strategy and "
                "not budget. adaptive_planner_6000 is reported separately as a "
                "budget variant."
            ),
            "limitations": [
                "Grounding is expected-entity coverage, not model-judged answer accuracy.",
                "Synthetic corpus results do not establish coding task success or productivity.",
                "The semantic channel is disabled; this isolates planner and structural/lexical behavior.",
                "Latency is measured on the current machine and is not a cross-machine claim.",
            ],
        },
        "adaptive_planner_3000": _summarize(
            adaptive_rows, configuration="adaptive_planner_3000"
        ),
        "fixed_3000_baseline": _summarize(fixed_rows, configuration="fixed_3000_baseline"),
        "adaptive_planner_6000": _summarize(
            adaptive_wide_rows, configuration="adaptive_planner_6000"
        ),
        "cases": {
            "adaptive_planner_3000": adaptive_rows,
            "fixed_3000_baseline": fixed_rows,
            "adaptive_planner_6000": adaptive_wide_rows,
        },
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=None)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be at least one")
    if args.dest is None:
        with tempfile.TemporaryDirectory(prefix="poldergraph-context-bench-") as temporary:
            report = run(Path(temporary), repeats=args.repeats)
    else:
        args.dest.mkdir(parents=True, exist_ok=True)
        report = run(args.dest, repeats=args.repeats)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
