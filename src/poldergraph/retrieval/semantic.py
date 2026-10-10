"""Semantic retrieval against the local vector index."""

from __future__ import annotations

from typing import Any

from ..embedding.protocol import QUERY_TASK, EmbeddingBackend
from ..storage.repository import Repository
from ..storage.vectors import create_vector_store
from .lexical import Candidate


def _reason(exc: Exception) -> str:
    """Human-readable cause for a degraded semantic channel.

    Uses the error message when available, otherwise the class name, so the
    degraded note stays actionable without leaking a traceback.
    """
    message = getattr(exc, "message", None) or str(exc)
    return message.strip() or type(exc).__name__


def semantic_candidates(
    repo: Repository,
    query: str,
    backend: EmbeddingBackend | None,
    *,
    limit: int = 40,
    root_id: str | None = None,
    kinds: list[str] | None = None,
) -> tuple[list[Candidate], str | None]:
    """Embed the query with the query role and search the vector index.

    Returns (candidates, degraded_reason). A failure degrades to lexical-only
    rather than silently returning nothing.
    """
    if backend is None:
        return [], "semantic backend unavailable"
    try:
        if not backend.capabilities():
            return [], "semantic backend unavailable"
        info = backend.model_info()
    except Exception as exc:
        # A missing or unloadable backend must degrade to lexical and structural
        # evidence, never fail the whole query.
        return [], f"semantic backend unavailable: {_reason(exc)}"
    if info.dimensions == 0:
        return [], "semantic backend unavailable"

    try:
        vector = backend.embed_texts([query], task=QUERY_TASK, dimensions=info.dimensions)[0]
    except Exception as exc:
        return [], f"query embedding failed: {exc}"

    store = create_vector_store(repo.con, dimensions=info.dimensions, model_id=info.model_id)
    try:
        hits = store.search(vector, top_k=limit * 2)
    except Exception as exc:
        return [], f"vector search failed: {exc}"

    out: list[Candidate] = []
    allowed: set[str] | None = None
    if kinds:
        rows = repo.con.execute(
            f"SELECT id FROM entities WHERE kind IN ({','.join('?' * len(kinds))})",
            kinds,
        ).fetchall()
        allowed = {row[0] for row in rows}

    for hit in hits:
        if not hit.entity_id:
            continue
        if allowed is not None and hit.entity_id not in allowed:
            continue
        out.append(
            Candidate(
                entity_id=hit.entity_id,
                features={"semantic": max(0.0, hit.similarity)},
                channels={"semantic"},
            )
        )
        if len(out) >= limit:
            break
    return out, None


def neighbors_of(
    repo: Repository,
    entity_id: str,
    backend: EmbeddingBackend | None,
    *,
    limit: int = 10,
    root_id: str | None = None,
) -> list[dict[str, Any]]:
    """Semantic neighbours of one entity, using its stored vector."""
    if backend is None or not backend.capabilities():
        return []
    info = backend.model_info()
    if info.dimensions == 0:
        return []
    store = create_vector_store(repo.con, dimensions=info.dimensions, model_id=info.model_id)

    import math

    from ..storage.vectors import get_entity_vector

    stored = get_entity_vector(store, entity_id)
    if stored is None:
        return []
    norm = math.sqrt(sum(v * v for v in stored)) or 1.0
    query = [v / norm for v in stored]

    try:
        hits = store.search(query, top_k=limit + 1)
    except Exception:
        return []
    entities = repo.get_entities([hit.entity_id for hit in hits if hit.entity_id])
    out = []
    for hit in hits:
        if not hit.entity_id or hit.entity_id == entity_id:
            continue
        entity = entities.get(hit.entity_id)
        if entity is None:
            continue
        out.append({"entity": entity, "similarity": hit.similarity, "modality": hit.modality})
    return out[:limit]