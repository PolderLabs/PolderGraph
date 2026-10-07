"""Relationship model with explicit provenance.

The central design rule: a parsed call edge is a fact extracted from source; a
cosine similarity is evidence of conceptual relatedness. The two never share a
type, and a semantic edge is never translated into a structural one.
"""

from __future__ import annotations

import hashlib
from enum import StrEnum
from typing import Any


class EdgeType(StrEnum):
    """Common structural edge taxonomy.

    Language adapters may add namespaced types for adapter-specific detail, but
    generic consumers rely on this set.
    """

    CONTAINS = "contains"
    DEFINES = "defines"
    IMPORTS = "imports"
    EXPORTS = "exports"
    CALLS = "calls"
    CONSTRUCTS = "constructs"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    OVERRIDES = "overrides"
    REFERENCES = "references"
    READS = "reads"
    WRITES = "writes"
    RETURNS_TYPE = "returns_type"
    ACCEPTS_TYPE = "accepts_type"
    DECORATES = "decorates"
    ROUTES_TO = "routes_to"
    TESTS = "tests"
    DOCUMENTS = "documents"
    # Ownership relations for documentation and media.
    CONTAINED_BY = "contained_by"
    DESCRIBES = "describes"


class SemanticEdgeType(StrEnum):
    """Semantic edges live in their own namespace, never mixed with structure."""

    SEMANTICALLY_RELATED = "semantically_related"


#: Every structural edge type for filtering and expansion defaults.
STRUCTURAL_EDGE_TYPES: frozenset[str] = frozenset(e.value for e in EdgeType)

#: Semantic edge types, kept separate so callers must opt in explicitly.
SEMANTIC_EDGE_TYPES: frozenset[str] = frozenset(e.value for e in SemanticEdgeType)

#: Edges that carry strong structural meaning during expansion and path search.
HIGH_VALUE_EDGES: frozenset[str] = frozenset(
    {
        EdgeType.CALLS,
        EdgeType.IMPORTS,
        EdgeType.INHERITS,
        EdgeType.IMPLEMENTS,
        EdgeType.OVERRIDES,
        EdgeType.ROUTES_TO,
        EdgeType.CONSTRUCTS,
    }
)

#: Edges that establish ownership/containment context.
OWNERSHIP_EDGES: frozenset[str] = frozenset(
    {EdgeType.CONTAINS, EdgeType.DEFINES, EdgeType.CONTAINED_BY}
)


class Provenance(StrEnum):
    """How a relationship became known. Confidence is meaningful only within class."""

    EXTRACTED = "extracted"
    """Syntax directly establishes the relationship."""
    RESOLVED = "resolved"
    """Source contains a reference and the resolver mapped it confidently."""
    INFERRED = "inferred"
    """Derived by a deterministic rule over incomplete direct syntax."""
    AMBIGUOUS = "ambiguous"
    """Several plausible structural targets exist."""
    SEMANTIC = "semantic"
    """Established by embedding similarity, never by source structure."""
    MANUAL = "manual"
    """User-defined extension."""

    @property
    def default_confidence(self) -> float:
        return {
            Provenance.EXTRACTED: 1.0,
            Provenance.RESOLVED: 0.9,
            Provenance.INFERRED: 0.6,
            Provenance.AMBIGUOUS: 0.4,
            Provenance.SEMANTIC: 0.5,
            Provenance.MANUAL: 1.0,
        }[self]


class SourceLocation:
    """Where in source a relationship was observed."""

    __slots__ = ("col", "line", "path")

    def __init__(self, path: str | None = None, line: int | None = None, col: int | None = None) -> None:
        self.path = path
        self.line = line
        self.col = col

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "line": self.line, "col": self.col}


class Edge:
    """A single relationship between two entities."""

    __slots__ = (
        "confidence",
        "created_at",
        "id",
        "metadata",
        "provenance",
        "resolver",
        "source_id",
        "source_location",
        "target_id",
        "type",
        "updated_at",
    )

    def __init__(
        self,
        *,
        source_id: str,
        target_id: str,
        type: str,
        provenance: str = Provenance.EXTRACTED,
        confidence: float | None = None,
        resolver: str | None = None,
        source_location: SourceLocation | dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        id: str | None = None,
        created_at: int | None = None,
        updated_at: int | None = None,
    ) -> None:
        from .entity import utcnow

        prov = Provenance(provenance)
        self.source_id = source_id
        self.target_id = target_id
        self.type = type
        self.provenance = prov
        self.confidence = float(confidence) if confidence is not None else prov.default_confidence
        self.resolver = resolver
        if isinstance(source_location, SourceLocation):
            self.source_location = source_location
        elif isinstance(source_location, dict):
            self.source_location = SourceLocation(**source_location)
        else:
            self.source_location = SourceLocation()
        self.metadata = metadata or {}
        self.id = id or self.compute_id()
        now = utcnow()
        self.created_at = created_at if created_at is not None else now
        self.updated_at = updated_at if updated_at is not None else now

    def compute_id(self) -> str:
        """Derive a deterministic edge identity.

        Endpoints are direction-sensitive (an import edge is not the same fact as
        its reverse), while the observing line is not part of identity so a
        moved call site keeps its edge row.
        """
        payload = "\x1f".join(
            [
                self.source_id,
                self.type,
                self.target_id,
                str(self.provenance),
                str(self.resolver or ""),
            ]
        )
        return "edge:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]

    @property
    def is_semantic(self) -> bool:
        return self.type in SEMANTIC_EDGE_TYPES

    @property
    def is_structural(self) -> bool:
        return self.type in STRUCTURAL_EDGE_TYPES

    def to_row(self) -> tuple[Any, ...]:
        import json

        loc = self.source_location
        return (
            self.id,
            self.source_id,
            self.target_id,
            self.type,
            str(self.provenance),
            self.confidence,
            self.resolver,
            loc.path,
            loc.line,
            loc.col,
            json.dumps(self.metadata, separators=(",", ":"), sort_keys=True),
            self.created_at,
            self.updated_at,
        )

    @classmethod
    def from_row(cls, row: tuple[Any, ...]) -> Edge:
        import json

        return cls(
            id=row[0],
            source_id=row[1],
            target_id=row[2],
            type=row[3],
            provenance=row[4],
            confidence=row[5],
            resolver=row[6],
            source_location=SourceLocation(path=row[7], line=row[8], col=row[9]),
            metadata=json.loads(row[10]) if row[10] else {},
            created_at=row[11],
            updated_at=row[12],
        )

    def to_dict(self) -> dict[str, Any]:
        # `source`/`target` are the canonical wire names used by the dashboard
        # and MCP clients; `source_id`/`target_id` are kept for the internal
        # database column names.
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type,
            "provenance": str(self.provenance),
            "confidence": self.confidence,
            "resolver": self.resolver,
            "source_location": self.source_location.to_dict(),
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return f"<Edge {self.source_id} -{self.type}-> {self.target_id} [{self.provenance}]>"