"""Measure warm query freshness-barrier latency against full-scan fallback."""

from __future__ import annotations

import argparse
import json
import math
import platform
import statistics
import time
from pathlib import Path

from poldergraph.cli_support import build_service


def _percentile(samples: list[float], percentile: float) -> float:
    ordered = sorted(samples)
    index = max(0, math.ceil(len(ordered) * percentile) - 1)
    return ordered[index]


def _measure(service, query: str, samples: int, *, force_scan: bool) -> dict[str, float]:
    timings = []
    for _ in range(samples):
        if force_scan:
            service._freshness_directories = None
            service._freshness_directory_generation = None
        started = time.perf_counter()
        response = service.search(query, limit=10, include_semantic=False)
        if response.consistency_report.get("status") != "fresh":
            raise RuntimeError("Benchmark requires a fresh, unchanged index.")
        timings.append((time.perf_counter() - started) * 1000)
    return {
        "p50_ms": round(statistics.median(timings), 2),
        "p95_ms": round(_percentile(timings, 0.95), 2),
        "min_ms": round(min(timings), 2),
        "max_ms": round(max(timings), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--query", default="authentication session")
    parser.add_argument("--samples", type=int, default=30)
    args = parser.parse_args()
    if args.samples < 2:
        parser.error("--samples must be at least 2")

    workspace, _, service = build_service(args.root, need_backend=False)
    try:
        service.freshness()  # warm the directory snapshot
        result = {
            "root": str(workspace.root),
            "indexed_files": service.repo.counts().get("files"),
            "samples": args.samples,
            "query": args.query,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "directory_snapshot": _measure(service, args.query, args.samples, force_scan=False),
            "full_discovery_each_query": _measure(
                service, args.query, args.samples, force_scan=True
            ),
        }
        print(json.dumps(result, indent=2))
    finally:
        workspace.close()


if __name__ == "__main__":
    main()
