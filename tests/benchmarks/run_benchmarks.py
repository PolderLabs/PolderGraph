"""Retrieval benchmark harness.

Compares lexical-only, embedding-only, structural-only and hybrid retrieval so
the default hybrid configuration is justified by measurement rather than
assumption.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from corpus_repo import build_corpus, cases


@dataclass
class RetrievalMetrics:
    """Standard retrieval metrics for one configuration."""

    configuration: str
    recall_at_k: float = 0.0
    mrr: float = 0.0
    precision_at_k: float = 0.0
    context_precision: float = 0.0
    structural_path_correctness: float = 0.0
    freshness_correct: float = 0.0
    mean_latency_ms: float = 0.0
    cases: int = 0
    per_case: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "configuration": self.configuration,
            "cases": self.cases,
            "recall_at_k": round(self.recall_at_k, 4),
            "mrr": round(self.mrr, 4),
            "precision_at_k": round(self.precision_at_k, 4),
            "context_precision": round(self.context_precision, 4),
            "structural_path_correctness": round(self.structural_path_correctness, 4),
            "freshness_correct": round(self.freshness_correct, 4),
            "mean_latency_ms": round(self.mean_latency_ms, 3),
        }


def _names(results: list[Any]) -> list[str]:
    out: list[str] = []
    for result in results:
        entity = getattr(result, "entity", None)
        if entity is None:
            continue
        out.append(entity.qualified_name or entity.name)
    return out


def evaluate(service: Any, *, configuration: str, k: int = 5) -> RetrievalMetrics:
    """Score one retrieval configuration against the benchmark corpus."""
    metrics = RetrievalMetrics(configuration=configuration)
    manifest_cases = cases()
    latencies: list[float] = []
    recall_total = 0.0
    mrr_total = 0.0
    precision_total = 0.0

    for case in manifest_cases:
        expected = set(case["expect"])
        started = time.perf_counter()
        response = service.search(case["question"], limit=k)
        latencies.append((time.perf_counter() - started) * 1000)

        names = _names(response.results)
        hits = [name for name in names if name in expected]
        recall_total += len(hits) / len(expected) if expected else 0.0
        precision_total += len(hits) / len(names) if names else 0.0
        reciprocal = 0.0
        for rank, name in enumerate(names, start=1):
            if name in expected:
                reciprocal = 1.0 / rank
                break
        mrr_total += reciprocal

        metrics.per_case.append(
            {
                "id": case["id"],
                "class": case["class"],
                "question": case["question"],
                "expected": sorted(expected),
                "returned": names,
                "hits": hits,
            }
        )

    total = max(1, len(manifest_cases))
    metrics.cases = len(manifest_cases)
    metrics.recall_at_k = recall_total / total
    metrics.mrr = mrr_total / total
    metrics.precision_at_k = precision_total / total
    metrics.context_precision = metrics.precision_at_k
    metrics.mean_latency_ms = sum(latencies) / max(1, len(latencies))

    # Structural path correctness: every dependency_path case must have a path.
    path_cases = [c for c in metrics.per_case if c["class"] == "dependency_path"]
    if path_cases:
        correct = 0
        for case in path_cases:
            names = set(case["returned"])
            if set(case["expected"]) & names:
                correct += 1
        metrics.structural_path_correctness = correct / len(path_cases)

    metrics.freshness_correct = 1.0 if service.freshness()["fresh"] else 0.0
    return metrics


def make_backend(config: Any) -> Any:
    """Construct a real embedding backend, or None when unavailable."""
    from poldergraph.embedding.gemma import create_backend

    try:
        backend = create_backend(config)
        backend.model_info()
    except Exception:
        return None
    return backend if backend.capabilities() else None


def run_benchmark(destination: Path, *, backend: Any = None) -> dict[str, Any]:
    """Index the corpus and compare retrieval configurations.

    A semantic backend is required for the semantic and hybrid rows. Without
    one those configurations are reported as *skipped* rather than silently
    measured as lexical, which would make every row indistinguishable.
    """
    from poldergraph.config.models import Config
    from poldergraph.graph import run_graph_stage
    from poldergraph.indexing.pipeline import Indexer
    from poldergraph.retrieval.service import QueryService
    from poldergraph.storage.repository import Repository
    from poldergraph.workspace import create_index, open_workspace

    root = build_corpus(destination)
    config = Config()
    create_index(root, config)
    workspace = open_workspace(root)
    repo = Repository(workspace.con)

    if backend is None:
        backend = make_backend(config)
    semantic_available = backend is not None

    indexer = Indexer(workspace, backend=backend)
    indexer.ensure_root()
    indexer.run(indexer.discover())
    run_graph_stage(workspace, config, repo, backend)

    service = QueryService(repo, config, backend, root_id=workspace.root_id())
    results: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    # Evaluate with the semantic channel disabled by withholding the backend,
    # rather than wrapping `search` (which would recurse).
    lexical_service = QueryService(repo, config, None, root_id=workspace.root_id())
    results.append(evaluate(lexical_service, configuration="lexical_only").to_dict())

    if semantic_available:
        hybrid = evaluate(service, configuration="hybrid")
        results.append(hybrid.to_dict())
        semantic = evaluate_semantic_only(service)
        results.append(semantic.to_dict())
    else:
        for name in ("hybrid", "semantic_only"):
            skipped.append(
                {
                    "configuration": name,
                    "reason": "no embedding backend available; cannot measure the semantic channel",
                }
            )

    results.append(_structural_only_metrics(service).to_dict())

    payload = {
        "corpus": str(root),
        "entities": repo.count_entities(root_id=workspace.root_id()),
        "semantic_available": semantic_available,
        "results": results,
        "skipped": skipped,
    }
    workspace.close()
    return payload


def evaluate_semantic_only(service: Any, *, k: int = 5) -> RetrievalMetrics:
    """Score the semantic channel alone, excluding exact and lexical hits."""
    from poldergraph.retrieval.service import SearchFilters

    metrics = RetrievalMetrics(configuration="semantic_only")
    manifest_cases = cases()
    recall = mrr = precision = 0.0
    latencies: list[float] = []

    for case in manifest_cases:
        expected = set(case["expect"])
        started = time.perf_counter()
        response = service.search(
            case["question"],
            limit=k * 4,
            filters=SearchFilters(),
            include_semantic=True,
            include_structural_context=False,
        )
        latencies.append((time.perf_counter() - started) * 1000)
        # Keep only results whose evidence is the semantic channel.
        names = [
            result.entity.qualified_name or result.entity.name
            for result in response.results
            if result.entity is not None and result.features.get("semantic")
        ][:k]
        hits = [name for name in names if name in expected]
        recall += len(hits) / len(expected) if expected else 0.0
        precision += len(hits) / len(names) if names else 0.0
        reciprocal = 0.0
        for rank, name in enumerate(names, start=1):
            if name in expected:
                reciprocal = 1.0 / rank
                break
        mrr += reciprocal
        metrics.per_case.append(
            {"id": case["id"], "class": case["class"], "returned": names, "hits": hits}
        )

    total = max(1, len(manifest_cases))
    metrics.cases = len(manifest_cases)
    metrics.recall_at_k = recall / total
    metrics.mrr = mrr / total
    metrics.precision_at_k = precision / total
    metrics.context_precision = metrics.precision_at_k
    metrics.mean_latency_ms = sum(latencies) / max(1, len(latencies))
    return metrics


def _structural_only_metrics(service: Any) -> RetrievalMetrics:
    metrics = RetrievalMetrics(configuration="structural_only")
    manifest_cases = [c for c in cases() if c["class"] in {"dependency_path", "exact_implementation"}]
    correct = 0
    latencies: list[float] = []
    for case in manifest_cases:
        started = time.perf_counter()
        response = service.search(case["question"], limit=5, include_semantic=False)
        latencies.append((time.perf_counter() - started) * 1000)
        names = set(_names(response.results))
        if set(case["expect"]) & names:
            correct += 1
        metrics.per_case.append(
            {"id": case["id"], "class": case["class"], "returned": sorted(names)}
        )
    metrics.cases = len(manifest_cases)
    metrics.structural_path_correctness = correct / max(1, len(manifest_cases))
    metrics.mean_latency_ms = sum(latencies) / max(1, len(latencies))
    return metrics


def dimension_benchmark(
    destination: Path, dimensions: list[int], *, backend_factory: Any = None
) -> dict[str, Any]:
    """Run the same retrieval set at several embedding dimensions.

    Requires a real embedding backend: without one every dimension would index
    lexically and the comparison would be meaningless, so it reports skipped.
    """
    from poldergraph.config.models import Config
    from poldergraph.indexing.pipeline import Indexer
    from poldergraph.retrieval.service import QueryService
    from poldergraph.storage.repository import Repository
    from poldergraph.storage.sqlite import database_size_bytes
    from poldergraph.workspace import create_index, open_workspace

    probe = Config()
    if backend_factory is not None:
        probe_backend = backend_factory(probe)
    else:
        probe_backend = make_backend(probe)
    if probe_backend is None:
        return {
            "dimensions": [],
            "skipped": "no embedding backend available; dimension comparison requires vectors",
        }

    rows: list[dict[str, Any]] = []
    for dimension in dimensions:
        root = build_corpus(destination / f"dim{dimension}")
        config = Config()
        config.index.dimensions = dimension
        create_index(root, config)
        workspace = open_workspace(root)
        repo = Repository(workspace.con)
        backend = backend_factory(config) if backend_factory is not None else make_backend(config)
        if backend is None:
            workspace.close()
            continue
        indexer = Indexer(workspace, backend=backend)
        indexer.ensure_root()
        started = time.perf_counter()
        indexer.run(indexer.discover())
        index_seconds = time.perf_counter() - started

        service = QueryService(repo, config, backend, root_id=workspace.root_id())
        metrics = evaluate(service, configuration=f"hybrid_{dimension}d")
        rows.append(
            {
                "dimensions": dimension,
                "recall_at_k": round(metrics.recall_at_k, 4),
                "mrr": round(metrics.mrr, 4),
                "index_seconds": round(index_seconds, 3),
                "mean_latency_ms": round(metrics.mean_latency_ms, 3),
                "db_bytes": database_size_bytes(workspace.index_dir),
            }
        )
        workspace.close()
    return {"dimensions": rows}


def semantic_edge_calibration(service: Any, *, repo: Any) -> dict[str, Any]:
    """Report the degree distribution of materialized semantic edges."""
    from poldergraph.config.models import Config
    from poldergraph.graph.builder import compute_semantic_edges

    config = service.config
    stats = compute_semantic_edges(repo, config, service.backend, root_id=service.root_id)
    degrees: dict[str, int] = {}
    for edge in repo.iter_edges(root_id=service.root_id):
        if edge.is_semantic:
            degrees[edge.source_id] = degrees.get(edge.source_id, 0) + 1
    values = sorted(degrees.values())
    mean_degree = sum(values) / len(values) if values else 0.0
    hubs = sum(1 for value in values if value >= config.semantic_edges.max_degree)
    return {
        "edges_created": stats.created,
        "threshold": round(stats.threshold, 4),
        "mutual": stats.mutual,
        "mean_degree": round(mean_degree, 4),
        "max_degree": max(values) if values else 0,
        "noisy_hubs": hubs,
        "degree_histogram": {str(value): values.count(value) for value in set(values)},
    }