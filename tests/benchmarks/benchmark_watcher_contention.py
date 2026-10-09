"""Measure watcher CPU and concurrent read latency during a 100-save burst.

This is a machine-specific harness for the #27 contention acceptance criterion.
It uses the offline structural index and does not load embedding weights.
"""

from __future__ import annotations

import json
import statistics
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


def percentile(samples: list[float], fraction: float) -> float:
    ordered = sorted(samples)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def run(root: Path) -> dict[str, Any]:
    from poldergraph.config.models import Config
    from poldergraph.indexing.pipeline import Indexer
    from poldergraph.query_daemon import Daemon
    from poldergraph.workspace import create_index, open_workspace

    root.mkdir(parents=True, exist_ok=True)
    source = root / "module.py"
    baseline = "class AuthService:\n    def validate(self):\n        return True\n"
    source.write_text(baseline, encoding="utf-8")
    create_index(root, Config(embedding={"backend": "none"}))
    workspace = open_workspace(root)
    indexer = Indexer(workspace, backend=None)
    indexer.ensure_root()
    indexer.run(indexer.discover())
    workspace.close()

    daemon = Daemon(root, idle_timeout=0)
    service = daemon._ensure_loaded()
    latencies_ms: list[float] = []
    read_errors: list[str] = []
    cpu_started = time.process_time()
    wall_started = time.perf_counter()

    def reader() -> None:
        for _ in range(40):
            started = time.perf_counter()
            result = daemon.handle(
                "search",
                {"query": "AuthService validate", "limit": 5, "include_semantic": False},
            )
            latencies_ms.append((time.perf_counter() - started) * 1000)
            if not result.get("ok", True):
                read_errors.append(str(result.get("error", "unknown read error")))

    try:
        with ThreadPoolExecutor(max_workers=3) as clients:
            readers = [clients.submit(reader) for _ in range(3)]
            for revision in range(100):
                content = baseline + f"\nREVISION = {revision}\n"
                if revision == 99:
                    content += "\ndef watcher_burst_final_probe():\n    return True\n"
                source.write_text(content, encoding="utf-8")
                time.sleep(0.003)
            for future in readers:
                future.result(timeout=30)

        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if service.resolve_entity("watcher_burst_final_probe") is not None:
                break
            time.sleep(0.05)
        final_indexed = service.resolve_entity("watcher_burst_final_probe") is not None
        cpu_seconds = time.process_time() - cpu_started
        wall_seconds = time.perf_counter() - wall_started
        idle_cpu_started = time.process_time()
        idle_wall_started = time.perf_counter()
        time.sleep(2.0)
        idle_cpu_seconds = time.process_time() - idle_cpu_started
        idle_wall_seconds = time.perf_counter() - idle_wall_started
        return {
            "files_written": 100,
            "concurrent_readers": 3,
            "reads": len(latencies_ms),
            "read_errors": len(read_errors),
            "maximum_read_latency_ms": round(max(latencies_ms, default=0.0), 3),
            "p50_read_latency_ms": round(statistics.median(latencies_ms), 3),
            "p95_read_latency_ms": round(percentile(latencies_ms, 0.95), 3),
            "wall_seconds": round(wall_seconds, 3),
            "process_cpu_seconds": round(cpu_seconds, 3),
            "cpu_cores_used_average": round(cpu_seconds / max(wall_seconds, 1e-9), 4),
            "idle_observation_seconds": round(idle_wall_seconds, 3),
            "idle_process_cpu_seconds": round(idle_cpu_seconds, 4),
            "idle_cpu_cores_used_average": round(
                idle_cpu_seconds / max(idle_wall_seconds, 1e-9), 4
            ),
            "final_revision_visible": final_indexed,
            "supervisor_state": daemon._supervisor.status()["state"],
            "embedding_backend": "none",
        }
    finally:
        if daemon._supervisor is not None:
            daemon._supervisor.stop()
        daemon.close()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be at least one")
    with tempfile.TemporaryDirectory(prefix="poldergraph-watcher-bench-") as temporary:
        runs = [run(Path(temporary) / f"repo-{index}") for index in range(args.repeats)]
    summary = {
        "runs": len(runs),
        "successful_runs": sum(
            item["final_revision_visible"] and item["read_errors"] == 0 for item in runs
        ),
        "median_wall_seconds": round(statistics.median(item["wall_seconds"] for item in runs), 3),
        "median_process_cpu_seconds": round(
            statistics.median(item["process_cpu_seconds"] for item in runs), 3
        ),
        "median_cpu_cores_used_average": round(
            statistics.median(item["cpu_cores_used_average"] for item in runs), 4
        ),
        "median_idle_process_cpu_seconds": round(
            statistics.median(item["idle_process_cpu_seconds"] for item in runs), 4
        ),
        "median_idle_cpu_cores_used_average": round(
            statistics.median(item["idle_cpu_cores_used_average"] for item in runs), 4
        ),
        "median_p50_read_latency_ms": round(
            statistics.median(item["p50_read_latency_ms"] for item in runs), 3
        ),
        "median_p95_read_latency_ms": round(
            statistics.median(item["p95_read_latency_ms"] for item in runs), 3
        ),
        "worst_maximum_read_latency_ms": round(
            max(item["maximum_read_latency_ms"] for item in runs), 3
        ),
    }
    print(json.dumps({"summary": summary, "runs": runs}, indent=2, sort_keys=True))
    return 0 if summary["successful_runs"] == len(runs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
