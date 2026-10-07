"""Canonical entity model and stable identity.

Stable IDs are derived from root identity + language + kind + normalized path +
qualified name + semantic discriminator. Line numbers are deliberately excluded
so that moving code within a file does not change its identity.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class EntityKind(StrEnum):
    """Canonical node kinds.

    Language adapters may emit namespaced kinds for adapter-specific detail, but
    generic consumers (retrieval, graph, dashboard) work on this common set.
    """

    WORKSPACE = "workspace"
    REPOSITORY = "repository"
    DIRECTORY = "directory"
    FILE = "file"
    MODULE = "module"
    NAMESPACE = "namespace"
    PACKAGE = "package"
    CLASS = "class"
    INTERFACE = "interface"
    TRAIT = "trait"
    ENUM = "enum"
    TYPE_ALIAS = "type_alias"
    FUNCTION = "function"
    METHOD = "method"
    CONSTRUCTOR = "constructor"
    PROPERTY = "property"
    FIELD = "field"
    CONSTANT = "constant"
    VARIABLE = "variable"
    ENDPOINT = "endpoint"
    TEST = "test"
    DOCUMENT = "document"
    SECTION = "section"
    IMAGE = "image"
    AUDIO_SEGMENT = "audio_segment"
    VIDEO_SEGMENT = "video_segment"
    UNKNOWN_SYMBOL = "unknown_symbol"


#: Kinds that represent ownership containers rather than code symbols.
CONTAINER_KINDS: frozenset[EntityKind] = frozenset(
    {
        EntityKind.WORKSPACE,
        EntityKind.REPOSITORY,
        EntityKind.DIRECTORY,
        EntityKind.FILE,
        EntityKind.MODULE,
        EntityKind.NAMESPACE,
        EntityKind.PACKAGE,
    }
)

#: Kinds that carry executable source bodies worth embedding as code.
CODE_KINDS: frozenset[EntityKind] = frozenset(
    {
        EntityKind.CLASS,
        EntityKind.INTERFACE,
        EntityKind.TRAIT,
        EntityKind.ENUM,
        EntityKind.TYPE_ALIAS,
        EntityKind.FUNCTION,
        EntityKind.METHOD,
        EntityKind.CONSTRUCTOR,
        EntityKind.PROPERTY,
        EntityKind.CONSTANT,
        EntityKind.ENDPOINT,
        EntityKind.TEST,
    }
)


def normalize_path(path: str) -> str:
    """Normalize a repository-relative path for identity comparison.

    Uses forward slashes and strips redundant leading/trailing separators so the
    same logical path written differently yields the same stable ID.
    """
    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.strip("/")


def stable_id(
    *,
    root_id: str,
    kind: str,
    language: str | None,
    path: str | None,
    qualified_name: str | None,
    discriminator: str = "",
) -> str:
    """Compute the canonical stable ID for an entity.

    The digest covers every field that expresses *semantic identity*. Line and
    byte positions are excluded on purpose: reformatting or moving a definition
    inside its file must not invalidate its identity.
    """
    parts = [
        root_id,
        kind,
        language or "",
        normalize_path(path) if path else "",
        qualified_name or "",
        discriminator,
    ]
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return f"{kind}:{digest[:32]}"


def content_hash(data: bytes | str) -> str:
    """Hash raw file content used for change detection."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def semantic_hash(text: str) -> str:
    """Hash the exact normalized text sent to the embedding model.

    A formatting-only source change that leaves the semantic representation
    untouched produces an identical hash and therefore avoids re-embedding.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utcnow() -> int:
    """Current UTC time as whole seconds since the epoch."""
    return int(datetime.now(UTC).timestamp())


class Entity:
    """A single canonical node in the PolderGraph graph."""

    __slots__ = (
        "content_hash",
        "created_at",
        "docstring",
        "end_byte",
        "end_line",
        "id",
        "is_external",
        "is_generated",
        "kind",
        "language",
        "metadata",
        "name",
        "parent_id",
        "path",
        "qualified_name",
        "root_id",
        "semantic_hash",
        "signature",
        "start_byte",
        "start_line",
        "updated_at",
        "visibility",
    )

    def __init__(
        self,
        *,
        id: str,
        root_id: str,
        kind: str,
        name: str,
        path: str | None = None,
        language: str | None = None,
        qualified_name: str | None = None,
        parent_id: str | None = None,
        start_byte: int | None = None,
        end_byte: int | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        visibility: str | None = None,
        signature: str | None = None,
        docstring: str | None = None,
        content_hash: str | None = None,
        semantic_hash: str | None = None,
        is_generated: bool = False,
        is_external: bool = False,
        metadata: dict[str, Any] | None = None,
        created_at: int | None = None,
        updated_at: int | None = None,
    ) -> None:
        now = utcnow()
        self.id = id
        self.root_id = root_id
        self.kind = kind
        self.name = name
        self.path = path
        self.language = language
        self.qualified_name = qualified_name
        self.parent_id = parent_id
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.start_line = start_line
        self.end_line = end_line
        self.visibility = visibility
        self.signature = signature
        self.docstring = docstring
        self.content_hash = content_hash
        self.semantic_hash = semantic_hash
        self.is_generated = is_generated
        self.is_external = is_external
        self.metadata = metadata or {}
        self.created_at = created_at if created_at is not None else now
        self.updated_at = updated_at if updated_at is not None else now

    @property
    def is_container(self) -> bool:
        try:
            return EntityKind(self.kind) in CONTAINER_KINDS
        except ValueError:
            return False

    @property
    def end_line_exclusive(self) -> int | None:
        """Zero-based inclusive end converted to an exclusive bound for slicing."""
        return None if self.end_line is None else self.end_line + 1

    def to_row(self) -> tuple[Any, ...]:
        import json

        return (
            self.id,
            self.root_id,
            self.kind,
            self.language,
            self.name,
            self.qualified_name,
            self.path,
            self.parent_id,
            self.start_byte,
            self.end_byte,
            self.start_line,
            self.end_line,
            self.visibility,
            self.signature,
            self.docstring,
            self.content_hash,
            self.semantic_hash,
            int(self.is_generated),
            int(self.is_external),
            json.dumps(self.metadata, separators=(",", ":"), sort_keys=True),
            self.created_at,
            self.updated_at,
        )

    @classmethod
    def from_row(cls, row: tuple[Any, ...]) -> Entity:
        import json

        return cls(
            id=row[0],
            root_id=row[1],
            kind=row[2],
            language=row[3],
            name=row[4],
            qualified_name=row[5],
            path=row[6],
            parent_id=row[7],
            start_byte=row[8],
            end_byte=row[9],
            start_line=row[10],
            end_line=row[11],
            visibility=row[12],
            signature=row[13],
            docstring=row[14],
            content_hash=row[15],
            semantic_hash=row[16],
            is_generated=bool(row[17]),
            is_external=bool(row[18]),
            metadata=json.loads(row[19]) if row[19] else {},
            created_at=row[20],
            updated_at=row[21],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "root_id": self.root_id,
            "kind": self.kind,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "path": self.path,
            "language": self.language,
            "parent_id": self.parent_id,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "visibility": self.visibility,
            "signature": self.signature,
            "docstring": self.docstring,
            "content_hash": self.content_hash,
            "semantic_hash": self.semantic_hash,
            "is_generated": self.is_generated,
            "is_external": self.is_external,
        }

    def __repr__(self) -> str:
        return f"<Entity {self.kind} {self.qualified_name or self.name} {self.id}>"