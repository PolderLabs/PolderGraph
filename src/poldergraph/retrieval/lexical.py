"""Exact symbol/path lookup and lexical retrieval.

Exact matches use dedicated B-tree indexes rather than FTS scoring, so an exact
identifier is never buried by relevance ranking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models.entity import Entity
from ..storage.repository import Repository


@dataclass
class Candidate:
    """One retrieval candidate with its per-channel evidence."""

    entity_id: str
    features: dict[str, float] = field(default_factory=dict)
    entity: Entity | None = None
    channels: set[str] = field(default_factory=set)
    graph_provenance: dict[str, Any] | None = None

    @property
    def score(self) -> float:
        return float(self.features.get("score", 0.0))


def exact_matches(
    repo: Repository,
    query: str,
    *,
    root_id: str | None = None,
    limit: int = 50,
) -> list[Candidate]:
    """Resolve an exact identifier or path to entities."""
    out: list[Candidate] = []
    seen: set[str] = set()

    def add(entity: Entity, feature: float, channel: str) -> None:
        if entity.id in seen:
            for candidate in out:
                if candidate.entity_id == entity.id:
                    candidate.features[channel] = max(candidate.features.get(channel, 0.0), feature)
                    candidate.channels.add(channel)
            return
        seen.add(entity.id)
        candidate = Candidate(entity_id=entity.id, entity=entity)
        candidate.features[channel] = feature
        candidate.channels.add(channel)
        out.append(candidate)

    normalized = query.strip()

    # Exact path.
    if "/" in normalized or normalized.endswith((".py", ".ts", ".js", ".rs", ".go", ".java")):
        entities = repo.find_by_path(normalized.lstrip("./"), root_id=root_id)
        for entity in entities:
            add(entity, 1.0, "exact_path")
        if not entities:
            # Path suffix match, e.g. "auth/service.py".
            for entity in repo.find_by_name(normalized.rsplit("/", 1)[-1], limit=limit):
                if entity.path and entity.path.endswith(normalized.lstrip("./")):
                    add(entity, 0.8, "exact_path")

    # Exact qualified name.
    for entity in repo.find_by_qualified_name(normalized, root_id=root_id):
        add(entity, 1.0, "exact_name")

    # Exact bare name.
    for entity in repo.find_by_name(normalized.rsplit(".", 1)[-1], limit=limit):
        add(entity, 0.9, "exact_name")

    return out[:limit]


def lexical_candidates(
    repo: Repository,
    query: str,
    *,
    limit: int = 40,
    kinds: list[str] | None = None,
    languages: list[str] | None = None,
    root_id: str | None = None,
    path_prefixes: list[str] | None = None,
) -> list[Candidate]:
    """Run FTS5 and return scored candidates."""
    rows = repo.fts.search(
        query,
        limit=limit,
        kinds=kinds,
        languages=languages,
        root_ids=[root_id] if root_id else None,
        path_prefixes=path_prefixes,
    )
    if not rows:
        return []
    max_score = max(row["score"] for row in rows) or 1.0
    return [
        Candidate(
            entity_id=row["entity_id"],
            features={"lexical": row["score"] / max_score},
            channels={"lexical"},
        )
        for row in rows
    ]
