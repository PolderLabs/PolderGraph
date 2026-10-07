"""Structural retrieval: bounded graph expansion, paths and impact.

Expansion policy follows edge value: calls/imports/inheritance carry strong
structural meaning, references fan out widely, and semantic edges are excluded
from structural expansion because their candidates were already retrieved from
the vector index.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models.edge import (
    HIGH_VALUE_EDGES,
    OWNERSHIP_EDGES,
    SEMANTIC_EDGE_TYPES,
    STRUCTURAL_EDGE_TYPES,
    Edge,
    EdgeType,
    Provenance,
)
from ..storage.repository import Repository

#: Default edge classes that structural expansion will traverse.
DEFAULT_EXPANSION_EDGES: frozenset[str] = (
    HIGH_VALUE_EDGES | OWNERSHIP_EDGES | frozenset({EdgeType.REFERENCES.value})
)

#: Edge classes used for reverse-dependency impact analysis.
DEFAULT_IMPACT_EDGES: frozenset[str] = frozenset(
    {
        EdgeType.CALLS.value,
        EdgeType.CONSTRUCTS.value,
        EdgeType.IMPORTS.value,
        EdgeType.REFERENCES.value,
        EdgeType.INHERITS.value,
        EdgeType.IMPLEMENTS.value,
        EdgeType.OVERRIDES.value,
        EdgeType.ROUTES_TO.value,
        EdgeType.ACCEPTS_TYPE.value,
        EdgeType.RETURNS_TYPE.value,
    }
)


@dataclass
class ExpansionResult:
    """Entities discovered by bounded structural expansion."""

    entity_ids: list[str] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    truncated: bool = False


def expand(
    repo: Repository,
    seeds: list[str],
    *,
    hops: int = 2,
    fanout_cap: int = 25,
    total_cap: int = 150,
    edge_types: set[str] | None = None,
    include_semantic: bool = False,
    provenances: set[str] | None = None,
) -> ExpansionResult:
    """Expand a bounded neighborhood around seed entities."""
    allowed = edge_types if edge_types is not None else set(DEFAULT_EXPANSION_EDGES)
    if include_semantic:
        allowed = allowed | set(SEMANTIC_EDGE_TYPES)

    result = ExpansionResult()
    seen = set(seeds)
    frontier = list(seeds)

    for _ in range(max(0, hops)):
        if not frontier or len(result.entity_ids) >= total_cap:
            break
        next_frontier: list[str] = []
        for node in frontier:
            edges = repo.get_edges(node, direction="both", limit=fanout_cap * 2)
            per_node = 0
            for edge in edges:
                if edge.type not in allowed:
                    continue
                if provenances and str(edge.provenance) not in provenances:
                    continue
                other = edge.target_id if edge.source_id == node else edge.source_id
                if not other or other in seen:
                    if edge not in result.edges:
                        result.edges.append(edge)
                    continue
                if per_node >= fanout_cap or len(result.entity_ids) >= total_cap:
                    result.truncated = True
                    continue
                seen.add(other)
                result.entity_ids.append(other)
                result.edges.append(edge)
                next_frontier.append(other)
                per_node += 1
                if len(result.entity_ids) >= total_cap:
                    result.truncated = True
                    break
        frontier = next_frontier
        if len(result.entity_ids) >= total_cap:
            result.truncated = True
            break

    return result


@dataclass
class PathResult:
    """A path between two entities with per-edge provenance."""

    found: bool
    nodes: list[str] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    hops: int = 0
    reason: str | None = None


def find_path(
    repo: Repository,
    source_id: str,
    target_id: str,
    *,
    structural_only: bool = True,
    include_semantic: bool = False,
    max_hops: int = 12,
    edge_types: set[str] | None = None,
) -> PathResult:
    """Compute a shortest path between two entities.

    Extracted/resolved structural edges cost less than inferred or semantic
    ones, so a weighted search prefers deterministic evidence.
    """
    import heapq

    if source_id == target_id:
        return PathResult(found=True, nodes=[source_id], hops=0)

    allowed = edge_types if edge_types is not None else set(STRUCTURAL_EDGE_TYPES)
    if include_semantic:
        allowed = allowed | set(SEMANTIC_EDGE_TYPES)
    if structural_only:
        allowed = allowed - set(SEMANTIC_EDGE_TYPES)

    def edge_cost(edge: Edge) -> float:
        if edge.type in SEMANTIC_EDGE_TYPES:
            return 3.0
        if edge.provenance == Provenance.EXTRACTED:
            return 1.0
        if edge.provenance == Provenance.RESOLVED:
            return 1.2
        if edge.provenance == Provenance.INFERRED:
            return 1.8
        if edge.provenance == Provenance.AMBIGUOUS:
            return 2.5
        return 1.5

    # Bidirectional BFS keeps the search bounded on large graphs.
    adjacency = _adjacency(repo, source_id, allowed, max_hops * 8)
    if source_id not in adjacency:
        return PathResult(found=False, reason="source has no traversable edges")

    frontier = {source_id: 0.0}
    came_from: dict[str, tuple[str, Edge]] = {}
    queue: list[tuple[float, str]] = [(0.0, source_id)]
    visited_depth: dict[str, int] = {source_id: 0}

    while queue:
        cost, node = heapq.heappop(queue)
        if cost > frontier.get(node, float("inf")):
            continue
        if node == target_id:
            return _reconstruct(came_from, source_id, target_id)
        depth = visited_depth.get(node, 0)
        if depth >= max_hops:
            continue
        for other, edge in adjacency.get(node, []):
            new_cost = cost + edge_cost(edge)
            if new_cost < frontier.get(other, float("inf")):
                frontier[other] = new_cost
                came_from[other] = (node, edge)
                visited_depth[other] = depth + 1
                heapq.heappush(queue, (new_cost, other))

    return PathResult(found=False, reason=f"no path within {max_hops} hops")


def _adjacency(
    repo: Repository, start: str, allowed: set[str], limit: int
) -> dict[str, list[tuple[str, Edge]]]:
    """Build a bounded adjacency map reachable from ``start``."""
    adjacency: dict[str, list[tuple[str, Edge]]] = {}
    seen = {start}
    frontier = [start]
    for _ in range(4):
        next_frontier: list[str] = []
        for node in frontier:
            edges = repo.get_edges(node, direction="both", limit=limit)
            bucket: list[tuple[str, Edge]] = []
            for edge in edges:
                if edge.type not in allowed:
                    continue
                other = edge.target_id if edge.source_id == node else edge.source_id
                if other and other != node:
                    bucket.append((other, edge))
                    if other not in seen:
                        seen.add(other)
                        next_frontier.append(other)
            adjacency[node] = bucket
        frontier = next_frontier
        if not frontier:
            break
    return adjacency


def _reconstruct(
    came_from: dict[str, tuple[str, Edge]], source_id: str, target_id: str
) -> PathResult:
    nodes = [target_id]
    edges: list[Edge] = []
    current = target_id
    guard = 0
    while current != source_id and guard < 1000:
        previous, edge = came_from[current]
        edges.append(edge)
        nodes.append(previous)
        current = previous
        guard += 1
    nodes.reverse()
    edges.reverse()
    return PathResult(found=True, nodes=nodes, edges=edges, hops=len(edges))


@dataclass
class ImpactResult:
    """Reverse-dependency impact classification."""

    direct: list[str] = field(default_factory=list)
    transitive: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    docs: list[str] = field(default_factory=list)
    semantic_only: list[str] = field(default_factory=list)
    truncated: bool = False

    def to_dict(self, repo: Repository) -> dict[str, Any]:
        def describe(ids: list[str]) -> list[dict[str, Any]]:
            entities = repo.get_entities(ids)
            return [
                {
                    "id": entity.id,
                    "name": entity.qualified_name or entity.name,
                    "kind": entity.kind,
                    "path": entity.path,
                    "start_line": entity.start_line,
                }
                for entity in entities.values()
            ]

        return {
            "direct": describe(self.direct),
            "transitive": describe(self.transitive),
            "tests": describe(self.tests),
            "docs": describe(self.docs),
            "semantic_only": describe(self.semantic_only),
            "truncated": self.truncated,
        }


def impact(
    repo: Repository,
    entity_id: str,
    *,
    max_depth: int = 3,
    edge_types: set[str] | None = None,
    test_kinds: set[str] | None = None,
) -> ImpactResult:
    """Traverse reverse dependency edges to answer "what may be affected?"."""
    allowed = edge_types if edge_types is not None else set(DEFAULT_IMPACT_EDGES)
    result = ImpactResult()
    seen = {entity_id}
    frontier = [entity_id]

    for depth in range(max_depth):
        next_frontier: list[str] = []
        for node in frontier:
            edges = repo.get_edges(node, direction="inbound", limit=200)
            for edge in edges:
                if edge.type not in allowed:
                    continue
                dependent = edge.source_id
                if not dependent or dependent in seen:
                    continue
                seen.add(dependent)
                entity = repo.get_entity(dependent)
                if entity is None:
                    continue
                if entity.kind == "test":
                    result.tests.append(dependent)
                elif entity.kind in {"document", "section"}:
                    result.docs.append(dependent)
                elif depth == 0:
                    result.direct.append(dependent)
                else:
                    result.transitive.append(dependent)
                next_frontier.append(dependent)
                if len(result.direct) + len(result.transitive) > 2000:
                    result.truncated = True
                    return result
        frontier = next_frontier
        if not frontier:
            break

    return result


def find_tests(repo: Repository, entity_ids: list[str], *, limit: int = 50) -> list[str]:
    """Find tests structurally linked to the given entities."""
    tests: list[str] = []
    for edge in repo.con.execute(
        "SELECT DISTINCT source_id, target_id FROM edges WHERE type='tests'"
    ).fetchall():
        source, target = edge[0], edge[1]
        if source in entity_ids or target in entity_ids:
            other = target if source in entity_ids else source
            if other not in tests:
                tests.append(other)
        if len(tests) >= limit:
            break

    if not tests:
        # Fall back to lexical linkage between test files and the target path.
        for entity_id in entity_ids:
            entity = repo.get_entity(entity_id)
            if entity is None or not entity.path:
                continue
            stem = entity.path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            for candidate in repo.con.execute(
                "SELECT id FROM entities WHERE kind='test' AND path LIKE ? LIMIT 20",
                (f"%{stem}%",),
            ).fetchall():
                if candidate[0] not in tests:
                    tests.append(candidate[0])
            if len(tests) >= limit:
                break
    return tests[:limit]