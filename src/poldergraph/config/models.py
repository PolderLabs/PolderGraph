"""Configuration models.

Precedence, lowest to highest:
1. built-in defaults
2. user config
3. workspace .poldergraph/config.toml
4. environment variables (POLDERGRAPH_ prefix, __ nesting)
5. CLI flags
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

CONFIG_VERSION = 1
ENV_PREFIX = "POLDERGRAPH_"

SUPPORTED_DIMENSIONS: tuple[int, ...] = (128, 256, 512, 768)
MAX_API_DIMENSIONS = 3072
EMBEDDING_MODEL = "google/embeddinggemma-2"


class IndexConfig(BaseModel):
    dimensions: int = 256
    include_media: bool = True
    include_generated: bool = False
    follow_symlinks: bool = False
    max_file_bytes: int = 5_000_000
    max_roots: int = 64

    @field_validator("dimensions")
    @classmethod
    def _check_dimensions(cls, value: int) -> int:
        if not 1 <= value <= MAX_API_DIMENSIONS:
            raise ValueError(f"dimensions must be between 1 and {MAX_API_DIMENSIONS}, got {value}")
        return value


class EmbeddingConfig(BaseModel):
    backend: Literal["native", "ollama", "api", "none"] = "native"
    model: str = EMBEDDING_MODEL
    batch_size: int = 0  # 0 == auto
    device: str = "auto"
    normalize: bool = True
    revision: str | None = None
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "embeddinggemma"
    api_provider: Literal["openai", "voyage"] = "openai"
    api_endpoint: str | None = None
    api_model: str | None = None
    api_timeout: float = 30.0
    # Runtime-only consent: workspace config must not authorize repository text egress.
    remote_authorized: bool = Field(default=False, exclude=True, repr=False)
    endpoint_authorized: bool = Field(default=False, exclude=True, repr=False)
    max_tokens: int = 2048

    @field_validator("api_timeout")
    @classmethod
    def _check_api_timeout(cls, value: float) -> float:
        if not 0.1 <= value <= 120:
            raise ValueError("api_timeout must be between 0.1 and 120 seconds")
        return value


class SemanticEdgeConfig(BaseModel):
    enabled: bool = True
    top_k: int = 12
    mutual_preferred: bool = True
    max_degree: int = 8
    #: "auto" derives a threshold from the observed similarity distribution.
    minimum_similarity: float | str = "auto"
    #: Floor applied when the derived threshold cannot be computed.
    auto_floor: float = 0.55

    def resolved_threshold(self, derived: float | None = None) -> float:
        if isinstance(self.minimum_similarity, float):
            return self.minimum_similarity
        if derived is None:
            return self.auto_floor
        return max(self.auto_floor, derived)


class GraphConfig(BaseModel):
    community_algorithm: Literal["leiden", "louvain", "label_propagation"] = "leiden"
    compute_structural_communities: bool = True
    compute_hybrid_communities: bool = True
    community_resolution: float = 1.0
    compute_betweenness: bool = False
    betweenness_sample: int = 5000
    pagerank_damping: float = 0.85


class RetrievalConfig(BaseModel):
    semantic_candidates: int = 40
    lexical_candidates: int = 40
    graph_hops: int = 2
    max_graph_candidates: int = 150
    default_context_tokens: int = 6000
    max_expansion_fanout: int = 25
    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "semantic": 1.0,
            "lexical": 0.8,
            "exact_name": 1.6,
            "exact_path": 1.4,
            "graph_proximity": 0.35,
            "graph_expansion": 0.6,
            "centrality": 0.2,
            "kind_prior": 0.15,
            "community_affinity": 0.1,
            "recency": 0.05,
        }
    )
    kind_priors: dict[str, float] = Field(
        default_factory=lambda: {
            "function": 1.0,
            "method": 1.0,
            "class": 0.95,
            "interface": 0.95,
            "file": 0.8,
            "module": 0.75,
            "test": 0.6,
            "section": 0.6,
            "document": 0.55,
            "variable": 0.35,
            "field": 0.3,
            "directory": 0.3,
        }
    )


class UIConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 7432
    open_browser: bool = True
    global_graph_node_cap: int = 3000
    global_graph_edge_cap: int = 12000
    neighborhood_fanout: int = 60


class PrivacyConfig(BaseModel):
    allow_model_downloads: bool = True
    allow_remote_embedding: bool = False
    allow_remote_decisions: bool = False
    telemetry: bool = False


class DecisionsConfig(BaseModel):
    """Optional typed-decision routing; disabled keeps all inference local."""

    provider: Literal["disabled", "typesafe", "openai", "laya"] = "disabled"
    model: str | None = None
    endpoint: str | None = None
    timeout: float = 3.0
    confidence_threshold: float = 0.9
    remote_providers: list[Literal["typesafe", "openai"]] = Field(default_factory=list)
    # Runtime-only authorization metadata populated by the config loader.
    remote_authorized: bool = Field(default=False, exclude=True, repr=False)
    endpoint_authorized: bool = Field(default=False, exclude=True, repr=False)
    authorized_remote_providers: list[str] = Field(default_factory=list, exclude=True, repr=False)

    @field_validator("timeout")
    @classmethod
    def _check_timeout(cls, value: float) -> float:
        if not 0.1 <= value <= 120:
            raise ValueError("timeout must be between 0.1 and 120 seconds")
        return value

    @field_validator("confidence_threshold")
    @classmethod
    def _check_confidence_threshold(cls, value: float) -> float:
        if not 0.5 < value <= 1:
            raise ValueError("confidence_threshold must be greater than 0.5 and at most 1")
        return value


class Config(BaseModel):
    version: int = CONFIG_VERSION
    index: IndexConfig = Field(default_factory=IndexConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    semantic_edges: SemanticEdgeConfig = Field(default_factory=SemanticEdgeConfig)
    graph: GraphConfig = Field(default_factory=GraphConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    decisions: DecisionsConfig = Field(default_factory=DecisionsConfig)
    exclude: list[str] = Field(default_factory=list)
    include: list[str] = Field(default_factory=list)

    def to_toml_dict(self) -> dict[str, Any]:
        """Serialize to the documented TOML shape, dropping default-only noise."""
        return {
            "version": self.version,
            "index": self.index.model_dump(),
            "embedding": self.embedding.model_dump(),
            "semantic_edges": self.semantic_edges.model_dump(),
            "graph": self.graph.model_dump(),
            "retrieval": {
                **self.retrieval.model_dump(),
                "weights": {k: round(v, 4) for k, v in self.retrieval.weights.items()},
            },
            "ui": self.ui.model_dump(),
            "privacy": self.privacy.model_dump(),
            "decisions": self.decisions.model_dump(),
            "exclude": self.exclude,
            "include": self.include,
        }


def default_config_path(index_dir: Path) -> Path:
    return index_dir / "config.toml"
