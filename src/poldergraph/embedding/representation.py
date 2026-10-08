"""Semantic representation construction.

Code entities are embedded as a structured textual representation rather than a
raw body, so the embedding model sees what the symbol *is*, not just its text.
The `semantic_hash` covers exactly the text handed to the model, so a
formatting-only change that leaves this unchanged avoids re-embedding.
"""

from __future__ import annotations

from typing import Any

from ..models.entity import Entity, semantic_hash

#: Bumped when this construction changes, forcing targeted re-embedding.
REPRESENTATION_VERSION = 1

#: Cap on body text included in a representation, per language.
#:
#: This bounds GPU/CPU inference memory as much as it bounds index size. The
#: attention cost of a batch scales with (batch x sequence length)^2, so a
#: 4000-char body roughly quadruples peak memory versus 1000 chars. Measured on
#: a 6 GB GPU, 4000-char bodies pushed a batch of 16 past the device limit,
#: while 1200-char bodies stay comfortably inside it.
MAX_BODY_CHARS = 1200


def build_code_representation(
    entity: Entity,
    *,
    body: str | None = None,
    parent_qualified_name: str | None = None,
) -> str:
    """Build the structured representation for a code entity."""
    lines: list[str] = [
        f"kind: {entity.kind}",
        f"language: {entity.language or 'unknown'}",
        f"symbol: {entity.qualified_name or entity.name}",
    ]
    if entity.path:
        lines.append(f"path: {entity.path}")
    if parent_qualified_name:
        lines.append(f"module: {parent_qualified_name}")
    if entity.signature:
        lines.extend(["", "signature:", entity.signature])
    if entity.docstring:
        lines.extend(["", "documentation:", entity.docstring[:1000]])
    if body:
        trimmed = body[:MAX_BODY_CHARS]
        lines.extend(["", "code:", trimmed])
    return "\n".join(lines)


def build_file_representation(
    entity: Entity,
    *,
    exports: list[tuple[str, str]],
    module_doc: str | None = None,
    body: str | None = None,
) -> str:
    """Build a file representation from exported symbols, without an LLM.

    The summary is composed deterministically from exported names and
    signatures so reindexing the same file yields the same hash.
    """
    lines: list[str] = [
        f"kind: {entity.kind}",
        f"language: {entity.language or 'unknown'}",
        f"path: {entity.path or entity.name}",
    ]
    if module_doc:
        lines.extend(["", "documentation:", module_doc[:1500]])
    if exports:
        lines.extend(["", "exports:"])
        for name, signature in exports[:200]:
            lines.append(f"- {signature or name}")
    if body:
        lines.extend(["", "content:", body[:MAX_BODY_CHARS]])
    return "\n".join(lines)


def build_section_representation(entity: Entity, *, ancestry: list[str] | None = None) -> str:
    """Build a documentation-section representation including heading ancestry."""
    lines: list[str] = [
        f"kind: {entity.kind}",
        "language: text",
        f"document: {entity.path or ''}",
    ]
    if ancestry:
        lines.append(f"section: {' > '.join(ancestry)}")
    else:
        lines.append(f"section: {entity.name}")
    if entity.docstring:
        lines.extend(["", "content:", entity.docstring[:MAX_BODY_CHARS]])
    return "\n".join(lines)


def build_image_representation(entity: Entity, *, context: str | None = None) -> str:
    lines = [
        f"kind: image",
        f"path: {entity.path or entity.name}",
    ]
    if context:
        lines.append(f"context: {context[:800]}")
    return "\n".join(lines)


def build_media_representation(
    entity: Entity, *, start: float | None = None, end: float | None = None, context: str | None = None
) -> str:
    lines = [f"kind: {entity.kind}", f"path: {entity.path or entity.name}"]
    if start is not None and end is not None:
        lines.append(f"time_range: {start:.1f}-{end:.1f}")
    if context:
        lines.append(f"context: {context[:600]}")
    return "\n".join(lines)


def representation_for(
    entity: Entity,
    *,
    body: str | None = None,
    exports: list[tuple[str, str]] | None = None,
    module_doc: str | None = None,
    ancestry: list[str] | None = None,
) -> str:
    """Dispatch to the correct representation builder for an entity kind."""
    from ..models.entity import EntityKind

    kind = entity.kind
    if kind in {EntityKind.IMAGE}:
        return build_image_representation(entity)
    if kind in {EntityKind.AUDIO_SEGMENT, EntityKind.VIDEO_SEGMENT}:
        start = entity.metadata.get("start_time")
        end = entity.metadata.get("end_time")
        return build_media_representation(entity, start=start, end=end, context=ancestry[0] if ancestry else None)
    if kind == EntityKind.FILE:
        return build_file_representation(entity, exports=exports or [], module_doc=module_doc, body=body)
    if kind == EntityKind.SECTION or kind == EntityKind.DOCUMENT:
        return build_section_representation(entity, ancestry=ancestry)
    return build_code_representation(entity, body=body)


def compute_semantic_hash(text: str) -> str:
    """Hash the exact normalized text sent to the model."""
    return semantic_hash(text)


def normalize_representation(text: str) -> str:
    """Normalize whitespace so reformatting does not change the hash."""
    lines = [line.rstrip() for line in text.splitlines()]
    normalized: list[str] = []
    blank = False
    for line in lines:
        if not line.strip():
            if not blank:
                normalized.append("")
            blank = True
            continue
        blank = False
        normalized.append(line)
    return "\n".join(normalized).strip()