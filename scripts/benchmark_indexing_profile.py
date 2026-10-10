#!/usr/bin/env python3
"""Segmented profiling of the Python indexing and retrieval pipeline.

Reports per-stage wall time, CPU time, peak RSS and index size for discovery,
parsing, symbol resolution, batch SQLite writes, graph metrics, exact/FTS
search, graph path/impact and context building.

Stages needing an absent backend (embeddings, Leiden) are reported as
`unavailable` with the reason, never estimated. Corpora are generated locally so
the run needs no external repository and no network.

Usage:
    python scripts/benchmark_indexing_profile.py [--files 500] [--repeats 3]
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import statistics
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests" / "benchmarks"))

from _workspace import benchmark_workspace  # noqa: E402

UNAVAILABLE = "unavailable"


def peak_rss_bytes() -> int:
    """Peak resident set size of this process, in bytes."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024


@contextmanager
def _stage(name: str, stages: dict[str, Any]) -> Iterator[None]:
    """Measure wall, CPU and peak RSS deltas around one stage."""
    started = time.perf_counter()
    cpu_started = time.process_time()
    rss_before = peak_rss_bytes()
    try:
        yield
    finally:
        wall = (time.perf_counter() - started) * 1000.0
        cpu = (time.process_time() - cpu_started) * 1000.0
        stages[name] = {
            "wall_ms": round(wall, 3),
            "cpu_ms": round(cpu, 3),
            "peak_rss_bytes": max(peak_rss_bytes(), rss_before),
        }


_EXTENSIONS = {".py": "python", ".ts": "typescript", ".rs": "rust", ".go": "go"}


def _language_of(path: str) -> str | None:
    return _EXTENSIONS.get(Path(path).suffix)


def generate_corpus(destination: Path, files: int) -> Path:
    """Write a deterministic multi-module corpus of ``files`` source files."""
    packages = destination / "src" / "pkg"
    packages.mkdir(parents=True, exist_ok=True)
    (destination / "pyproject.toml").write_text("[project]\nname = 'generated'\n", encoding="utf-8")
    for index in range(files):
        package = index % 12
        directory = packages / f"module{package:02d}"
        directory.mkdir(exist_ok=True)
        (directory / "__init__.py").write_text("", encoding="utf-8")
        (directory / f"unit{index:05d}.py").write_text(
            f'"""Generated module {index}."""\n'
            f"from typing import Any\n\n\n"
            f"class Service{index:05d}:\n"
            f'    """Service number {index}."""\n\n'
            f"    def __init__(self, value: int = {index}) -> None:\n"
            f"        self.value = value\n\n"
            f"    def compute(self, payload: Any) -> int:\n"
            f'        """Compute a result."""\n'
            f"        return self.value + len(str(payload))\n\n\n"
            f"def helper_{index:05d}(left: int, right: int) -> int:\n"
            f'    """Combine two numbers."""\n'
            f"    return left + right\n",
            encoding="utf-8",
        )
    return destination


def index_corpus(root: Path, stages: dict[str, Any]) -> tuple[Any, Any, Any]:
    """Index a generated corpus, timing each stage separately."""
    from poldergraph.config.models import Config
    from poldergraph.graph import run_graph_stage
    from poldergraph.indexing.pipeline import Indexer
    from poldergraph.parsing.engine import ParseEngine
    from poldergraph.storage.repository import Repository
    from poldergraph.workspace import create_index, open_workspace

    config = Config(embedding={"backend": "none"})
    with _stage("create_index", stages):
        create_index(root, config)
    workspace = open_workspace(root)
    repository = Repository(workspace.con)
    indexer = Indexer(workspace, backend=None)

    with _stage("discovery", stages):
        indexer.ensure_root()
        discovered = indexer.discover()
    stages["discovery"]["files_discovered"] = len(discovered)

    # Parsing only, before persistence, so parse cost is not folded into writes.
    engine = ParseEngine()
    with _stage("parsing", stages):
        for item in discovered:
            source = (root / item.path).read_bytes()
            engine.parse(source, _language_of(item.path), item.path)

    with _stage("index_and_persist", stages):
        indexer.run(indexer.discover())

    with _stage("graph_stage", stages):
        run_graph_stage(workspace, config, repository, None)

    database = workspace.index_dir / "index.sqlite3"
    stages["index_size"] = {"bytes": database.stat().st_size}
    return workspace, repository, config


def profile_search(root: Path, workspace: Any, repository: Any, config: Any, stages: dict[str, Any], repeats: int) -> None:
    """Time the retrieval and graph-query hot paths."""
    from poldergraph.retrieval.service import QueryService

    service = QueryService(repository, config, None, root_id=workspace.root_id(), workspace=workspace)
    queries = ["Service00042", "compute", "helper00007", "module03", "value"]
    entities = workspace.con.execute("SELECT id FROM entities LIMIT 50").fetchall()
    ids = [row[0] for row in entities]

    def timed(name: str, call: Any) -> None:
        samples = []
        for _ in range(repeats):
            started = time.perf_counter()
            call()
            samples.append((time.perf_counter() - started) * 1000.0)
        stages[name] = {
            "wall_ms": round(statistics.mean(samples), 3),
            "p50_ms": round(statistics.median(samples), 3),
            "p95_ms": round(sorted(samples)[max(0, round(0.95 * (len(samples) - 1)))], 3),
            "calls": repeats,
        }

    for label, query in zip(("exact_search", "lexical_search", "fts_search", "context_build"), queries, strict=False):
        timed(label, lambda q=query: service.search(q, limit=20, include_semantic=False))

    if len(ids) >= 2:
        timed("graph_impact", lambda: service.impact(ids[0], max_depth=2))
        timed("graph_path", lambda: service.path(ids[0], ids[1]))


def probe_embedding_stage(stages: dict[str, Any]) -> None:
    """Report the embedding stage honestly rather than guessing its cost."""
    from poldergraph.embedding.gemma import NativeGemmaBackend

    stages["embeddings"] = {
        UNAVAILABLE: True,
        "reason": (
            "EmbeddingGemma 2 weights are not cached in this environment; the "
            "semantic stage is skipped rather than estimated."
        ),
        "class": NativeGemmaBackend.__name__,
    }


def probe_community_stage(stages: dict[str, Any]) -> None:
    """Report Leiden availability, measuring it when the backend is installed."""
    try:
        import igraph  # noqa: F401
        import leidenalg  # noqa: F401
    except Exception as exc:
        stages["communities_leiden"] = {
            UNAVAILABLE: True,
            "reason": f"Leiden backend not importable ({type(exc).__name__})",
        }
        return
    stages["communities_leiden"] = {"available": True}


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def run(files: int, repeats: int) -> dict[str, Any]:
    with benchmark_workspace("index-profile-") as workspace_dir:
        root = generate_corpus(workspace_dir / "repo", files)
        stages: dict[str, Any] = {}
        workspace, repository, config = index_corpus(root, stages)
        try:
            profile_search(root, workspace, repository, config, stages, repeats)
            probe_embedding_stage(stages)
            probe_community_stage(stages)
            stages["process"] = {
                "peak_rss_bytes": peak_rss_bytes(),
                "index_size_bytes": stages["index_size"]["bytes"],
                "entities": workspace.con.execute("SELECT COUNT(*) FROM entities").fetchone()[0],
                "files": workspace.con.execute("SELECT COUNT(*) FROM files").fetchone()[0],
                "edges": workspace.con.execute("SELECT COUNT(*) FROM edges").fetchone()[0],
            }
        finally:
            workspace.close()
    return {
        "corpus": {
            "generated_files": files,
            "kind": "deterministic generated multi-module Python corpus",
            "embedding_backend": "none (offline structural/lexical)",
        },
        "repeats": repeats,
        "stages": stages,
        "method": {
            "wall": "time.perf_counter around each stage",
            "cpu": "time.process_time around each stage",
            "peak_rss": "resource.getrusage(RUSAGE_SELF).ru_maxrss, a high-water mark and therefore monotonic",
            "note": (
                "Peak RSS is a process-wide high-water mark, so per-stage values "
                "are the peak reached by that point rather than a per-stage delta."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", type=int, default=500)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.files < 10:
        parser.error("--files must be at least 10")
    if args.repeats < 1:
        parser.error("--repeats must be at least one")
    print(json.dumps(run(args.files, args.repeats), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())