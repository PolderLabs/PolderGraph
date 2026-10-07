"""Graph stage: semantic edges, communities and metrics after indexing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..config.models import Config
from ..embedding.protocol import EmbeddingBackend
from ..storage.repository import Repository
from ..storage.sqlite import record_change_event, set_meta, writer_transaction
from ..workspace import Workspace
from .builder import SemanticEdgeStats, clear_semantic_edges, compute_semantic_edges
from .communities import CommunityResult, compute_all
from .metrics import MetricSummary, compute_metrics


@dataclass
class GraphStageResult:
    semantic_edges: SemanticEdgeStats
    communities: list[CommunityResult] = field(default_factory=list)
    metrics: MetricSummary | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_edges": self.semantic_edges.to_dict(),
            "communities": [c.summary() for c in self.communities],
            "metrics": self.metrics.to_dict() if self.metrics else None,
        }


def run_graph_stage(
    workspace: Workspace,
    config: Config,
    repo: Repository,
    backend: EmbeddingBackend | None,
    *,
    semantic_threshold: float = 0.75,
) -> GraphStageResult:
    """Recompute semantic edges, communities and metrics.

    Semantic edges are replaced wholesale rather than merged, so a threshold
    change cannot leave stale similarity edges behind.
    """
    with writer_transaction(workspace.con):
        clear_semantic_edges(repo)

    edge_stats = compute_semantic_edges(repo, config, backend, root_id=workspace.root_id())

    communities = compute_all(
        repo, config, root_id=workspace.root_id(), semantic_threshold=semantic_threshold
    )
    with writer_transaction(workspace.con):
        for result in communities:
            repo.replace_communities(
                result.mode, result.algorithm, result.resolution, result.memberships, result.labels
            )

    metrics = compute_metrics(repo, config, root_id=workspace.root_id(), force=True)

    with writer_transaction(workspace.con):
        set_meta(workspace.con, "graph_computed_at", int(__import__("time").time()))
        record_change_event(workspace.con, "graph", [])

    return GraphStageResult(semantic_edges=edge_stats, communities=communities, metrics=metrics)