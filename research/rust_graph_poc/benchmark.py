"""Compare Python and Rust structural breadth-first traversal on same graphs."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SIZES = ((100, 32), (10_000, 64), (100_000, 128))


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def parse_output(stdout: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field in stdout.strip().split():
        key, value = field.split("=", 1)
        result[key] = None if value == "null" else int(value)
    return result


def sample(command: list[str]) -> tuple[dict[str, Any], float]:
    started = time.perf_counter_ns()
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    wall_ns = time.perf_counter_ns() - started
    return parse_output(result.stdout), wall_ns / 1_000_000


def summarize(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    traversal_ms = [row["elapsed_ns"] / 1_000_000 for row in rows]
    wall_ms = [row["wall_ms"] for row in rows]
    rss = [row["peak_rss_kb"] for row in rows if row["peak_rss_kb"] is not None]
    return {
        "implementation": name,
        "traversal_p50_ms": round(statistics.median(traversal_ms), 3),
        "traversal_p95_ms": round(percentile(traversal_ms, 0.95), 3),
        "process_wall_p50_ms": round(statistics.median(wall_ms), 3),
        "process_wall_p95_ms": round(percentile(wall_ms, 0.95), 3),
        "peak_rss_p50_kb": round(statistics.median(rss)) if rss else None,
    }


def run(repeats: int) -> dict[str, Any]:
    rust_version = subprocess.run(
        ["rustc", "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    started = time.perf_counter()
    subprocess.run(
        ["cargo", "build", "--offline", "--release", "--manifest-path", str(ROOT / "Cargo.toml")],
        check=True,
        capture_output=True,
        text=True,
    )
    rust_build_seconds = time.perf_counter() - started
    binary = ROOT / "target" / "release" / "graph-traversal-poc"
    py_impl = ROOT / "python_baseline.py"
    reports = []

    for nodes, queries in SIZES:
        rust_rows: list[dict[str, Any]] = []
        python_rows: list[dict[str, Any]] = []
        for _ in range(repeats):
            rust, rust_wall = sample([str(binary), str(nodes), str(queries), "4"])
            python, python_wall = sample(
                [sys.executable, str(py_impl), str(nodes), str(queries), "4"]
            )
            if rust["checksum"] != python["checksum"]:
                raise RuntimeError(
                    f"Traversal mismatch for {nodes} nodes: "
                    f"Rust={rust['checksum']} Python={python['checksum']}"
                )
            rust["wall_ms"] = rust_wall
            python["wall_ms"] = python_wall
            rust_rows.append(rust)
            python_rows.append(python)
        reports.append(
            {
                "nodes": nodes,
                "edges": nodes * 8,
                "queries_per_process": queries,
                "depth_limit": 4,
                "checksum": rust_rows[0]["checksum"],
                "same_answers": True,
                "rust": summarize(rust_rows, "rust_csr"),
                "python": summarize(python_rows, "python_list_of_lists"),
            }
        )
    return {
        "method": {
            "repeats": repeats,
            "environment": {
                "platform": platform.platform(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "cpu_count": os.cpu_count(),
                "python": platform.python_version(),
                "rustc": rust_version,
            },
            "rust_build_seconds_excluded_from_runtime": round(rust_build_seconds, 3),
            "operation": "depth-limited outgoing BFS from deterministic seed nodes",
            "graph_generation": "same 8-edge deterministic formula in both implementations",
            "timing": "internal timer covers traversal only; process wall includes startup and graph construction",
            "rss": "peak resident set from /proc/self/status VmHWM on Linux",
            "limitations": [
                "This isolates one structural graph traversal primitive; it does not index files, parse source, use SQLite, or embed vectors.",
                "Synthetic regular graphs are not representative of every repository topology.",
                "The Rust result is a disposable POC, not drop-in PolderGraph feature parity.",
                "Linux RSS and wall-time measurements are local to this machine.",
            ],
        },
        "sizes": reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=7)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be at least one")
    print(json.dumps(run(args.repeats), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
