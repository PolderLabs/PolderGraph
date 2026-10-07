"""Graph metrics with caching.

Metrics are computed once and invalidated when the entity set changes, so a
query never pays for PageRank over a large graph on every call.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from ..config.models import Config
from ..models.edge import STRUCTURAL_EDGE_TYPES
from ..storage.repository import Repository

#: Metric names persisted in the `metrics` table.
DEGREE = "degree"
IN_DEGREE = "in_degree"
OUT_DEGREE = "out_degree"
PAGERANK = "pagerank"
BETWEENNESS = "betweenness"

CACHE_KEY = "metrics_cache_key"


def graph_cache_key(repo: Repository) -> str:
    """Cheap fingerprint of the graph shape, used to invalidate cached metrics."""
    row = repo.con.execute("SELECT COUNT(*), COALESCE(MAX(updated_at),0) FROM edges").fetchone()
    nodes = repo.con.execute("SELECT COUNT(*), COALESCE(MAX(updated_at),0) FROM entities").fetchone()
    return f"{nodes[0]}:{nodes[1]}:{row[0]}:{row[1]}"


@dataclass
class MetricSummary:
    computed: int
    duration_seconds: float
    skipped_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "computed": self.computed,
            "duration_seconds": round(self.duration_seconds, 3),
            "skipped_reason": self.skipped_reason,
        }


def compute_metrics(
    repo: Repository,
    config: Config,
    *,
    root_id: str | None = None,
    force: bool = False,
) -> MetricSummary:
    """Compute and cache degree, PageRank and optional betweenness."""
    started = time.monotonic()
    key = graph_cache_key(repo)
    cached = _get_meta(repo, CACHE_KEY)
    if cached == key and not force:
        count = int(_get_meta(repo, "metrics_count", "0") or 0)
        return MetricSummary(computed=count, duration_seconds=0.0, skipped_reason="cache_hit")

    try:
        import networkx as nx
    except ImportError:
        return MetricSummary(0, 0.0, skipped_reason="networkx unavailable")

    graph = nx.DiGraph()
    for entity in repo.iter_entities(root_id=root_id):
        graph.add_node(entity.id)
    for edge in repo.iter_edges(root_id=root_id):
        if edge.type not in STRUCTURAL_EDGE_TYPES:
            # Semantic edges are not structural importance signals.
            continue
        if edge.source_id in graph and edge.target_id in graph:
            graph.add_edge(edge.source_id, edge.target_id, weight=max(0.001, edge.confidence))

    if graph.number_of_nodes() == 0:
        return MetricSummary(0, 0.0, skipped_reason="empty graph")

    metrics: dict[str, dict[str, float]] = {node: {} for node in graph.nodes}

    degrees = graph.degree()
    for node, degree in degrees:
        metrics[node][DEGREE] = float(degree)
        metrics[node][IN_DEGREE] = float(graph.in_degree(node))
        metrics[node][OUT_DEGREE] = float(graph.out_degree(node))

    try:
        pagerank = nx.pagerank(graph, alpha=config.graph.pagerank_damping, weight="weight")
        for node, value in pagerank.items():
            metrics[node][PAGERANK] = float(value)
    except Exception:
        pass

    # Betweenness is quadratic; only compute it when scale permits.
    if config.graph.compute_betweenness and graph.number_of_nodes() <= config.graph.betweenness_sample:
        try:
            betweenness = nx.betweenness_centrality(graph, weight="weight")
            for node, value in betweenness.items():
                metrics[node][BETWEENNESS] = float(value)
        except Exception:
            pass
    elif config.graph.compute_betweenness:
        pass  # documented: skipped above the sample threshold

    repo.store_metrics(metrics)
    _set_meta(repo, CACHE_KEY, key)
    _set_meta(repo, "metrics_count", str(len(metrics)))
    return MetricSummary(computed=len(metrics), duration_seconds=time.monotonic() - started)


def importance_map(repo: Repository) -> dict[str, float]:
    """Combined importance used for node sizing and ranking."""
    pagerank = {
        entity_id: values.get(PAGERANK, 0.0)
        for entity_id, values in repo.metrics_map().items()
    }
    if pagerank:
        return pagerank
    # Fall back to degree when no ranking has been computed yet.
    return {
        entity_id: values.get(DEGREE, 0.0)
        for entity_id, values in repo.metrics_map().items()
    }


def _get_meta(repo: Repository, key: str, default: str | None = None) -> str | None:
    from ..storage.sqlite import get_meta

    return get_meta(repo.con, key, default)


def _set_meta(repo: Repository, key: str, value: str) -> None:
    from ..storage.sqlite import set_meta

    set_meta(repo.con, key, value)