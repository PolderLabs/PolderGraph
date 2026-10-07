"""Parse engine: tree-sitter loading, adapter dispatch and error resilience.

A parse error must never abort indexing: the tree still contains whatever the
grammar could parse, so we index it and record the error count.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from tree_sitter import Node, Parser

from ..discovery.languages import (
    BASELINE_LANGUAGES,
    STRONG_LANGUAGES,
    grammar_for,
)
from .types import AdapterInfo, ParseError, ParseResult


class TreeSitterUnavailable(Exception):
    """Raised when the tree-sitter distribution is not installed."""


@lru_cache(maxsize=64)
def get_parser(grammar: str) -> Parser:
    """Load and cache a tree-sitter parser for a grammar name."""
    try:
        from tree_sitter_language_pack import get_parser as load_parser
    except ImportError as exc:  # pragma: no cover - depends on install extras
        raise TreeSitterUnavailable(
            "tree-sitter-language-pack is not installed. "
            "Install it with: uv pip install tree-sitter-language-pack"
        ) from exc
    try:
        return load_parser(grammar)
    except Exception as exc:
        raise TreeSitterUnavailable(f"No tree-sitter grammar available for '{grammar}': {exc}") from exc


@lru_cache(maxsize=2048)
def _error_free_node_types(grammar: str) -> frozenset[str]:
    """Collect node types produced anywhere in a small sample corpus.

    Used by the baseline adapter to decide which node names carry meaning in a
    grammar it has no explicit adapter for.
    """
    return frozenset()


def count_errors(node: Node) -> int:
    """Count ERROR and missing nodes in a tree."""
    total = 0
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type == "ERROR" or current.is_missing:
            total += 1
        stack.extend(current.children)
    return total


def parse_source(source: bytes, grammar: str) -> tuple[Parser, Node]:
    """Parse source bytes, returning the parser and root node."""
    parser = get_parser(grammar)
    tree = parser.parse(source)
    return parser, tree.root_node


def node_text(source: bytes, node: Node | None) -> str:
    """Extract UTF-8 text for a node."""
    if node is None:
        return ""
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def field_text(source: bytes, node: Node, field: str) -> str | None:
    """Read a named field as text, if present."""
    child = node.child_by_field_name(field)
    if child is None:
        return None
    return node_text(source, child)


def walk(node: Node):
    """Depth-first iteration over a node and all descendants."""
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.children))


def children_of_type(node: Node, *types: str):
    """Direct children matching any of the given node types."""
    for child in node.named_children:
        if child.type in types:
            yield child


def first_child_of_type(node: Node, *types: str) -> Node | None:
    for child in node.named_children:
        if child.type in types:
            return child
    return None


def descendants_of_type(node: Node, *types: str):
    """All descendants (excluding ``node`` itself) matching the given types."""
    for current in walk(node):
        if current is node:
            continue
        if current.type in types:
            yield current


def grammar_available(grammar: str) -> bool:
    try:
        get_parser(grammar)
    except TreeSitterUnavailable:
        return False
    return True


def baseline_languages() -> list[str]:
    """Languages with a grammar but no strong adapter."""
    available = []
    for language in sorted(BASELINE_LANGUAGES):
        grammar = grammar_for(language)
        if grammar and grammar_available(grammar):
            available.append(language)
    return available


class ParseEngine:
    """Dispatch parses to the strongest available adapter for each language."""

    def __init__(self) -> None:
        self._adapters: dict[str, Any] = {}
        self._load_adapters()

    def _load_adapters(self) -> None:
        from .languages import load_adapters

        for language, adapter in load_adapters().items():
            self._adapters[language] = adapter

    def adapter_for(self, language: str | None) -> Any | None:
        if not language:
            return None
        return self._adapters.get(language)

    def capabilities(self) -> list[AdapterInfo]:
        """Report language capability for `poldergraph status`."""
        infos: list[AdapterInfo] = []
        for language in sorted(set(STRONG_LANGUAGES) | set(self._adapters)):
            adapter = self._adapters.get(language)
            grammar = grammar_for(language)
            available = grammar is not None and grammar_available(grammar)
            infos.append(
                AdapterInfo(
                    language=language,
                    available=available,
                    strong=adapter is not None,
                    resolves_imports=bool(adapter and getattr(adapter, "resolves_imports", False)),
                    detail="" if available else "grammar unavailable",
                )
            )
        for language in baseline_languages():
            if language not in self._adapters:
                infos.append(
                    AdapterInfo(
                        language=language,
                        available=True,
                        strong=False,
                        resolves_imports=False,
                        detail="baseline indexing only",
                    )
                )
        return infos

    def parse(self, source: bytes, language: str | None, path: str) -> ParseResult:
        """Parse a file, degrading to metadata-only on unsupported input."""
        adapter = self.adapter_for(language)
        grammar = grammar_for(language)
        if grammar is None or not grammar_available(grammar):
            return ParseResult(adapter="none", metadata={"reason": "unsupported_language"})
        if adapter is not None and adapter.supports():
            try:
                result = adapter.parse(source, path)
            except Exception as exc:  # adapters must never break indexing
                try:
                    _, root = parse_source(source, grammar)
                    return ParseResult(
                        adapter=adapter.__class__.__name__,
                        has_errors=True,
                        error_count=1,
                        metadata={"adapter_error": str(exc)[:200]},
                    )
                except TreeSitterUnavailable:
                    raise
                except ParseError:
                    return ParseResult(
                        adapter="none", metadata={"reason": "adapter_error", "detail": str(exc)[:200]}
                    )
            if not result.has_errors:
                try:
                    _, root = parse_source(source, grammar)
                    errors = count_errors(root)
                    if errors:
                        result.has_errors = True
                        result.error_count = errors
                except TreeSitterUnavailable:
                    pass
            return result

        from .languages.generic import GenericAdapter

        return GenericAdapter(language).parse(source, path)