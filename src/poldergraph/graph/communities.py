"""Community detection for structural and hybrid graph views.

Structural communities use deterministic relationships only. Hybrid communities
add semantic edges, but only those that pass the configured high-confidence
policy — never every nearest neighbour, which would produce a hairball.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..config.models import Config
from ..models.edge import Edge, Provenance
from ..storage.repository import Repository

#: Provenance classes that count as structural topology.
STRUCTURAL_PROVENANCES = frozenset(
    {Provenance.EXTRACTED.value, Provenance.RESOLVED.value, Provenance.INFERRED.value}
)


@dataclass
class CommunityResult:
    mode: str
    algorithm: str
    #: community_id -> member entity ids
    memberships: dict[str, list[str]] = field(default_factory=dict)
    #: community_id -> human label generated without an LLM
    labels: dict[str, str] = field(default_factory=dict)
    resolution: float = 1.0

    def summary(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "algorithm": self.algorithm,
            "count": len(self.memberships),
            "sizes": sorted((len(v) for v in self.memberships.values()), reverse=True)[:20],
        }


def build_graph(
    repo: Repository,
    *,
    include_semantic: bool = False,
    semantic_threshold: float | None = None,
    root_id: str | None = None,
) -> tuple[list[str], list[tuple[int, int, float]]]:
    """Build a NetworkX graph from persisted edges.

    Returns (nodes, edges-with-weight). Semantic edges are opt-in so structural
    clustering never silently absorbs similarity.
    """
    import networkx as nx

    graph = nx.Graph()
    for entity in repo.iter_entities(root_id=root_id):
        graph.add_node(entity.id)

    for edge in repo.iter_edges(root_id=root_id):
        if edge.source_id not in graph or edge.target_id not in graph:
            continue
        if edge.is_semantic:
            if not include_semantic:
                continue
            if semantic_threshold is not None and edge.confidence < semantic_threshold:
                continue
            weight = edge.confidence
        else:
            if str(edge.provenance) not in STRUCTURAL_PROVENANCES:
                continue
            # Extracted relationships are stronger than inferred ones.
            weight = edge.confidence
        if graph.has_edge(edge.source_id, edge.target_id):
            if graph[edge.source_id][edge.target_id].get("weight", 0) < weight:
                graph[edge.source_id][edge.target_id]["weight"] = weight
        else:
            graph.add_edge(edge.source_id, edge.target_id, weight=weight, type=edge.type)

    return list(graph.nodes), list(graph.edges(data=True))


def detect_communities(
    repo: Repository,
    config: Config,
    *,
    mode: str = "structural",
    root_id: str | None = None,
    semantic_threshold: float = 0.75,
) -> CommunityResult:
    """Detect communities for one mode."""
    include_semantic = mode == "hybrid"
    nodes, edges = build_graph(
        repo, include_semantic=include_semantic, semantic_threshold=semantic_threshold, root_id=root_id
    )
    result = CommunityResult(
        mode=mode,
        algorithm=config.graph.community_algorithm,
        resolution=config.graph.community_resolution,
    )
    if not nodes:
        return result

    partitions = _partition(nodes, edges, config)
    for index, community_nodes in enumerate(partitions):
        community_id = f"{mode}-{index:05d}"
        result.memberships[community_id] = community_nodes
        result.labels[community_id] = _label(community_id, community_nodes, repo)

    # A single community for the whole graph carries no information.
    if len(result.memberships) <= 1 and len(nodes) > 1:
        result.memberships = {}
        result.labels = {}
    return result


def _partition(
    nodes: list[str], edges: list[tuple[str, str, dict[str, Any]]], config: Config
) -> list[list[str]]:
    """Partition nodes, preferring Leiden and degrading deterministically."""
    algorithm = config.graph.community_algorithm
    if algorithm == "leiden":
        partitions = _leiden(nodes, edges, config.graph.community_resolution)
        if partitions is not None:
            return partitions
    if algorithm in {"leiden", "louvain"}:
        partitions = _louvain(nodes, edges, config.graph.community_resolution)
        if partitions is not None:
            return partitions
    return _connected_components(nodes, edges)


def _leiden(
    nodes: list[str], edges: list[tuple[str, str, dict[str, Any]]], resolution: float
) -> list[list[str]] | None:
    """Cluster with igraph/leidenalg; return None when unavailable."""
    try:
        import igraph
        import leidenalg
    except ImportError:
        return None
    if not edges:
        return [[node] for node in nodes]

    name_to_index = {node: index for index, node in enumerate(nodes)}
    graph = igraph.Graph(n=len(nodes), edges=[(name_to_index[a], name_to_index[b]) for a, b, _ in edges])
    graph.es["weight"] = [max(0.001, data.get("weight", 1.0)) for _, _, data in edges]
    try:
        partition = leidenalg.find_partition(
            graph, leidenalg.RBConfigurationVertexPartition, resolution_parameter=resolution
        )
    except Exception:
        return None
    # igraph addresses vertices by integer index, so every member must be mapped
    # back to its entity ID before the partition leaves this module.
    index_to_name = {index: node for index, node in enumerate(nodes)}
    return [[index_to_name[index] for index in members if index in index_to_name] for members in partition]


def _louvain(
    nodes: list[str], edges: list[tuple[str, str, dict[str, Any]]], resolution: float
) -> list[list[str]] | None:
    """Cluster with NetworkX Louvain as the portable default."""
    try:
        import networkx as nx
    except ImportError:
        return None
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    for a, b, data in edges:
        graph.add_edge(a, b, weight=max(0.001, data.get("weight", 1.0)))
    if graph.number_of_edges() == 0:
        return [[node] for node in nodes]
    try:
        communities = nx.community.louvain_communities(graph, resolution=resolution, seed=17)
    except Exception:
        return None
    return [sorted(community) for community in communities if community]


def _connected_components(
    nodes: list[str], edges: list[tuple[str, str, dict[str, Any]]]
) -> list[list[str]]:
    import networkx as nx

    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    for a, b, _ in edges:
        graph.add_edge(a, b)
    return [sorted(component) for component in nx.connected_components(graph)]


def _label(community_id: str, members: list[str], repo: Repository) -> str:
    """Generate a community label without an LLM.

    Uses representative symbols, paths and lexical terms drawn from the members.
    """
    entities = repo.get_entities(members[:80])
    if not entities:
        return community_id

    paths: list[str] = []
    for entity in entities.values():
        if entity.path:
            parts = entity.path.split("/")
            if len(parts) > 1:
                paths.append(parts[-2] if parts[-1].endswith(tuple(f".{ext}" for ext in ("py", "ts", "js"))) else parts[-1])
    path_term = max(set(paths), key=paths.count) if paths else ""

    names = [e.name for e in entities.values() if e.name]
    name_term = max(set(names), key=names.count) if names else ""

    terms = f"{path_term} {name_term}".strip()
    return terms or community_id


def compute_all(
    repo: Repository, config: Config, *, root_id: str | None = None, semantic_threshold: float = 0.75
) -> list[CommunityResult]:
    """Compute every configured community view and persist it."""
    results: list[CommunityResult] = []
    if config.graph.compute_structural_communities:
        results.append(detect_communities(repo, config, mode="structural", root_id=root_id))
    if config.graph.compute_hybrid_communities:
        results.append(
            detect_communities(
                repo, config, mode="hybrid", root_id=root_id, semantic_threshold=semantic_threshold
            )
        )
    return results