"""Hybrid fusion, reranking and query intent detection.

Weights are configurable and every feature contribution stays inspectable so
`--explain-score` can show why an item ranked where it did.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ..config.models import Config
from ..models.edge import Provenance
from ..storage.repository import Repository
from .lexical import Candidate


class QueryIntent(StrEnum):
    """Deterministic intent classes; never requires an LLM."""

    EXACT_SYMBOL = "exact_symbol"
    WHERE = "where"
    HOW_REACHES = "how_reaches"
    ARCHITECTURE = "architecture"
    CHANGE_IMPACT = "change_impact"
    TESTS = "tests"
    SEMANTIC = "semantic"


_WHERE_RE = re.compile(r"\bwhere\b.*\b(is|are|does|do|check|handle|validat|enforc)", re.I)
_HOW_REACHES_RE = re.compile(r"\bhow\s+does\b.*\b(reach|get to|call|flow|end up)", re.I)
_IMPACT_RE = re.compile(r"\b(impact|affect|break|change|modify|refactor|safe to)\b", re.I)
_TESTS_RE = re.compile(r"\b(test|tests|spec|coverage|covered)\b", re.I)
_ARCH_RE = re.compile(r"\b(architecture|structure|overview|design|pattern|module|subsystem|layout)\b", re.I)
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")


def detect_intent(query: str) -> QueryIntent:
    """Classify a query deterministically."""
    text = query.strip()
    if _IMPACT_RE.search(text):
        return QueryIntent.CHANGE_IMPACT
    if _TESTS_RE.search(text):
        return QueryIntent.TESTS
    if _HOW_REACHES_RE.search(text):
        return QueryIntent.HOW_REACHES
    if _WHERE_RE.search(text):
        return QueryIntent.WHERE
    if _ARCH_RE.search(text):
        return QueryIntent.ARCHITECTURE
    if _IDENTIFIER_RE.match(text):
        return QueryIntent.EXACT_SYMBOL
    return QueryIntent.SEMANTIC


@dataclass
class RankedResult:
    """A scored candidate with a full, inspectable feature breakdown."""

    entity_id: str
    score: float
    features: dict[str, float] = field(default_factory=dict)
    contributions: dict[str, float] = field(default_factory=dict)
    channels: list[str] = field(default_factory=list)
    entity: Any = None

    def explain(self) -> dict[str, Any]:
        """Return why this result ranked where it did."""
        ordered = sorted(self.contributions.items(), key=lambda pair: abs(pair[1]), reverse=True)
        return {
            "id": self.entity_id,
            "score": round(self.score, 6),
            "channels": self.channels,
            "features": {key: round(value, 6) for key, value in self.features.items()},
            "contributions": {key: round(value, 6) for key, value in ordered},
        }


def fuse(
    candidates: list[Candidate],
    repo: Repository,
    config: Config,
    *,
    query: str,
    structural_expansion_ids: set[str] | None = None,
    communities: dict[str, str] | None = None,
    metrics: dict[str, dict[str, float]] | None = None,
    seed_ids: set[str] | None = None,
) -> list[RankedResult]:
    """Fuse channel candidates into a single ranked list.

    Uses a configurable weighted ranker rather than hard-coded universal weights;
    every contribution is retained for inspection.
    """
    weights = config.retrieval.weights
    kind_priors = config.retrieval.kind_priors
    structural_expansion_ids = structural_expansion_ids or set()
    communities = communities or {}
    metrics = metrics or {}

    # Graph proximity: distance from other high-confidence candidates.
    strong = [c.entity_id for c in candidates if c.score >= 0.7][:10]
    proximity = _graph_proximity(repo, strong)

    max_centrality = max(
        (values.get("pagerank", 0.0) for values in metrics.values()), default=0.0
    ) or 1.0

    community_counts: dict[str, int] = {}
    for community_id in communities.values():
        community_counts[community_id] = community_counts.get(community_id, 0) + 1
    dominant_community = (
        max(community_counts, key=community_counts.get) if community_counts else None
    )

    results: list[RankedResult] = []
    for candidate in candidates:
        entity = candidate.entity or repo.get_entity(candidate.entity_id)
        if entity is None:
            continue

        features: dict[str, float] = dict(candidate.features)
        if candidate.entity_id in structural_expansion_ids:
            features["graph_expanded"] = 1.0
        features["centrality"] = metrics.get(candidate.entity_id, {}).get("pagerank", 0.0) / max_centrality
        features["kind_prior"] = kind_priors.get(entity.kind, 0.4)
        features["community_affinity"] = (
            1.0
            if dominant_community and communities.get(candidate.entity_id) == dominant_community
            else 0.0
        )
        proximity_value = proximity.get(candidate.entity_id)
        if proximity_value is not None:
            features["graph_proximity"] = proximity_value

        contributions: dict[str, float] = {}
        total = 0.0
        for name, value in features.items():
            weight = weights.get(name, 0.0)
            contributions[name] = value * weight
            total += value * weight

        # Provenance bonus: structurally verified facts outrank guesses.
        provenance_bonus = _provenance_bonus(repo, candidate.entity_id)
        if provenance_bonus:
            contributions["provenance"] = provenance_bonus
            total += provenance_bonus

        results.append(
            RankedResult(
                entity_id=candidate.entity_id,
                score=total,
                features=features,
                contributions=contributions,
                channels=sorted(candidate.channels),
                entity=entity,
            )
        )

    results.sort(key=lambda item: item.score, reverse=True)
    return results


def _provenance_bonus(repo: Repository, entity_id: str) -> float:
    """Small bonus for entities reachable through strong structural evidence."""
    edges = repo.get_edges(entity_id, direction="outbound", limit=20)
    best = 0.0
    for edge in edges:
        if edge.provenance == Provenance.EXTRACTED:
            best = max(best, 0.05)
        elif edge.provenance == Provenance.RESOLVED:
            best = max(best, 0.03)
    return best


def _graph_proximity(repo: Repository, seeds: list[str]) -> dict[str, float]:
    """Score nodes by structural closeness to the strongest candidates."""
    if not seeds:
        return {}
    import networkx as nx

    graph = nx.Graph()
    graph.add_nodes_from(seeds)
    for seed in seeds:
        for edge in repo.get_edges(seed, direction="both", limit=60):
            graph.add_edge(edge.source_id, edge.target_id)
    try:
        lengths = nx.single_source_shortest_path_length(graph, seeds[0], cutoff=2)
    except Exception:
        return {}
    return {
        node_id: max(0.0, 1.0 - (distance / 3.0))
        for node_id, distance in lengths.items()
        if distance > 0
    }


def dedupe_results(results: list[RankedResult]) -> list[RankedResult]:
    """Drop duplicate entities that can arise from parent/child overlap."""
    seen: set[str] = set()
    out: list[RankedResult] = []
    for result in results:
        if result.entity_id in seen:
            continue
        seen.add(result.entity_id)
        out.append(result)
    return out