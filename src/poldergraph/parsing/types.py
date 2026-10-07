"""Shared parsing contracts.

Adapters produce facts from syntax trees only. Resolution into entity IDs
happens afterwards in the resolver, so an adapter never guesses a target.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from ..models.edge import Provenance, SourceLocation


@dataclass
class ParsedSymbol:
    """A declaration found in a syntax tree."""

    kind: str
    name: str
    qualified_name: str
    start_byte: int
    end_byte: int
    start_line: int
    end_line: int
    parent_index: int | None = None
    """Index into the ParseResult.symbols list of the owning declaration."""
    signature: str | None = None
    docstring: str | None = None
    visibility: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    #: Bodies are captured separately so an adapter can skip heavy text for
    #: huge containers while still indexing the declaration itself.
    body_text: str | None = None


@dataclass
class Reference:
    """A name referenced from a specific source location."""

    name: str
    #: Canonical edge type this reference implies once resolved.
    edge_type: str
    source_symbol_index: int | None
    """Index into ParseResult.symbols for the entity holding the reference."""
    location: SourceLocation
    provenance: Provenance = Provenance.EXTRACTED
    qualifier: str | None = None
    """Optional namespace/module qualifier, e.g. ``os.path`` or ``self``."""
    metadata: dict[str, Any] = field(default_factory=dict)

    def candidate_name(self) -> str:
        """Name to match during resolution."""
        if self.qualifier and self.qualifier not in {"self", "this"}:
            return f"{self.qualifier}.{self.name}"
        return self.name


@dataclass
class ImportRecord:
    """A module import, used for cross-file resolution."""

    module: str
    source_symbol_index: int | None
    location: SourceLocation
    #: Local alias -> original name, when the language supports aliasing.
    aliases: dict[str, str] = field(default_factory=dict)
    is_type_only: bool = False
    is_reexport: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportRecord:
    """An exported name, including star/namespace re-exports."""

    name: str
    local_name: str | None
    source_symbol_index: int | None
    location: SourceLocation
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseResult:
    """Everything one adapter extracted from one file."""

    symbols: list[ParsedSymbol] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)
    imports: list[ImportRecord] = field(default_factory=list)
    exports: list[ExportRecord] = field(default_factory=list)
    #: Adapters report parse quality; a tree with ERROR nodes is still indexed.
    has_errors: bool = False
    error_count: int = 0
    adapter: str = "generic"
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Parser(Protocol):
    """The contract every language adapter implements."""

    language: str

    def supports(self) -> bool: ...
    def parse(self, source: bytes, path: str) -> ParseResult: ...


class ParseError(Exception):
    """Raised when an adapter cannot produce a result at all."""


@dataclass
class AdapterInfo:
    """Language capability summary surfaced by `poldergraph status`."""

    language: str
    available: bool
    strong: bool
    resolves_imports: bool
    detail: str = ""


def base_result(adapter: str) -> ParseResult:
    return ParseResult(adapter=adapter)