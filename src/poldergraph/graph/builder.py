"""Semantic edge materialization.

Vector search exists independently of semantic graph edges. Materializing every
nearest neighbour would produce a hairball, so edges are capped, filtered,
mutual-preference weighted and thresholded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..config.models import Config
from ..embedding.protocol import DOCUMENT_TASK, QUERY_TASK, EmbeddingBackend
from ..models.edge import Edge, Provenance
from ..storage.repository import Repository
from ..storage.vectors import VectorRecord, create_vector_store

#: Thresholds derived when configuration says "auto". These are calibrated by
#: the benchmark harness, not asserted as universal constants.
DEFAULT_THRESHOLD = 0.72
LOW_THRESHOLD = 0.65

#: Multiplier applied to the observed median best-neighbour similarity.
THRESHOLD_MARGIN = 0.85


@dataclass
class SemanticEdgeStats:
    considered: int = 0
    created: int = 0
    filtered_by_similarity: int = 0
    filtered_by_degree: int = 0
    mutual: int = 0
    threshold: float = DEFAULT_THRESHOLD
    degraded: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "considered": self.considered,
            "created": self.created,
            "filtered_by_similarity": self.filtered_by_similarity,
            "filtered_by_degree": self.filtered_by_degree,
            "mutual": self.mutual,
            "threshold": round(self.threshold, 4),
            "degraded": self.degraded,
        }


def derive_threshold(best_similarities: list[float], config: Config) -> float:
    """Derive a similarity threshold from the observed distribution.

    Uses each entity's *best* neighbour similarity and takes their median: that
    reflects the typical strength of a meaningful relationship in this corpus.
    A high quantile over every pair would instead track near-duplicates and
    reject everything useful.
    """
    if not best_similarities:
        return config.semantic_edges.resolved_threshold(None)
    ordered = sorted(best_similarities)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        median = ordered[middle]
    else:
        median = (ordered[middle - 1] + ordered[middle]) / 2
    # A margin below the median keeps genuinely related pairs while dropping
    # the long tail of weak similarity.
    return config.semantic_edges.resolved_threshold(median * THRESHOLD_MARGIN)


def compute_semantic_edges(
    repo: Repository,
    config: Config,
    backend: EmbeddingBackend | None,
    *,
    root_id: str | None = None,
    limit: int | None = None,
) -> SemanticEdgeStats:
    """Materialize bounded, high-confidence semantic edges."""
    stats = SemanticEdgeStats()
    policy = config.semantic_edges
    if not policy.enabled or backend is None:
        return stats

    info = backend.model_info()
    store = create_vector_store(repo.con, dimensions=info.dimensions, model_id=info.model_id)
    if info.dimensions == 0:
        stats.degraded.append("semantic backend unavailable")
        return stats

    entities = [
        e
        for e in repo.iter_entities(root_id=root_id)
        if e.kind not in {"directory", "workspace", "repository", "unknown_symbol"}
    ]
    if not entities:
        return stats
    if limit:
        entities = entities[:limit]
    entity_ids = [e.id for e in entities]

    # Retrieve neighbours for every eligible entity.
    neighbours: dict[str, list[tuple[str, float]]] = {}
    best_similarities: list[float] = []
    for entity_id in entity_ids:
        embedding = _embedding_for(repo, store, entity_id)
        if embedding is None:
            continue
        hits = store.search(embedding, top_k=policy.top_k + 4)
        rows = []
        for hit in hits:
            if not hit.entity_id or hit.entity_id == entity_id:
                continue
            rows.append((hit.entity_id, hit.similarity))
        if rows:
            neighbours[entity_id] = rows
            best_similarities.append(max(similarity for _, similarity in rows))

    threshold = derive_threshold(best_similarities, config)
    stats.threshold = threshold

    # Mutual-neighbour preference: a link is stronger when both sides select it.
    inverse = {target: source for source, rows in neighbours.items() for target, _ in rows}

    degree: dict[str, int] = {}
    created = 0
    for source_id, rows in neighbours.items():
        stats.considered += 1
        ranked = sorted(rows, key=lambda pair: pair[1], reverse=True)
        for target_id, similarity in ranked:
            if similarity < threshold:
                stats.filtered_by_similarity += 1
                break
            if degree.get(source_id, 0) >= policy.max_degree:
                stats.filtered_by_degree += 1
                break
            if degree.get(target_id, 0) >= policy.max_degree:
                continue
            is_mutual = policy.mutual_preferred and inverse.get(target_id) == source_id
            if is_mutual:
                stats.mutual += 1
            elif policy.mutual_preferred and similarity < min(1.0, threshold + 0.05):
                # Not mutual and barely above threshold: skip to avoid noise.
                stats.filtered_by_similarity += 1
                continue
            repo.upsert_edges(
                [
                    Edge(
                        source_id=source_id,
                        target_id=target_id,
                        type="semantically_related",
                        provenance=Provenance.SEMANTIC,
                        confidence=similarity,
                        resolver="vector_knn",
                        metadata={
                            "model_id": info.model_id,
                            "revision": info.revision,
                            "dimensions": info.dimensions,
                            "mutual": is_mutual,
                        },
                    )
                ]
            )
            degree[source_id] = degree.get(source_id, 0) + 1
            degree[target_id] = degree.get(target_id, 0) + 1
            created += 1
            if degree[source_id] >= policy.max_degree:
                break

    stats.created = created
    return stats


def _embedding_for(repo: Repository, store: Any, entity_id: str) -> list[float] | None:
    """Read the stored vector for an entity, normalized for cosine search."""
    import math

    from ..storage.vectors import get_entity_vector

    vector = get_entity_vector(store, entity_id)
    if vector is None:
        return None
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def clear_semantic_edges(repo: Repository) -> int:
    """Remove all materialized semantic edges before recomputing them."""
    from ..models.edge import SEMANTIC_EDGE_TYPES

    types = list(SEMANTIC_EDGE_TYPES)
    placeholders = ",".join("?" * len(types))
    cur = repo.con.execute(f"DELETE FROM edges WHERE type IN ({placeholders})", types)
    return cur.rowcount or 0