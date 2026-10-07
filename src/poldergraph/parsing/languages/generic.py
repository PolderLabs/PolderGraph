"""Baseline adapter for grammars without an explicit language adapter.

Produces file/module level facts and definition symbols when the grammar's node
names are recognizable. It never invents relationships it cannot see.
"""

from __future__ import annotations

from ..engine import first_child_of_type, get_parser, node_text, walk
from ..types import ParseResult, ParsedSymbol

#: Node type names that conventionally declare a named symbol across grammars.
GENERIC_DEFINITION_NODES: frozenset[str] = frozenset(
    {
        "function_item",
        "function_definition",
        "function_declaration",
        "method_declaration",
        "method_definition",
        "class_declaration",
        "class_definition",
        "struct_item",
        "enum_item",
        "type_declaration",
        "interface_declaration",
        "trait_item",
        "impl_item",
        "protocol_declaration",
        "object_declaration",
        "module_declaration",
        "package_declaration",
    }
)

_NAME_FIELDS: tuple[str, ...] = ("name", "declarator", "identifier")


class GenericAdapter:
    """Grammar-agnostic baseline extraction."""

    resolves_imports = False

    def __init__(self, language: str) -> None:
        self.language = language

    def supports(self) -> bool:
        return True

    def parse(self, source: bytes, path: str) -> ParseResult:
        from ...discovery.languages import grammar_for

        grammar = grammar_for(self.language)
        result = ParseResult(adapter="generic")
        if grammar is None:
            result.metadata["reason"] = "unsupported_language"
            return result
        try:
            parser = get_parser(grammar)
        except Exception as exc:
            result.metadata["reason"] = "grammar_unavailable"
            result.metadata["detail"] = str(exc)[:160]
            return result

        tree = parser.parse(source)
        for node in walk(tree.root_node):
            if node.type not in GENERIC_DEFINITION_NODES:
                continue
            name = self._name_of(source, node)
            if not name:
                continue
            result.symbols.append(
                ParsedSymbol(
                    kind=_kind_for(node.type, self.language),
                    name=name,
                    qualified_name=name,
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    start_line=node.start_point[0],
                    end_line=node.end_point[0],
                    signature=node_text(source, node).splitlines()[0][:200]
                    if node.end_point[0] >= node.start_point[0]
                    else None,
                )
            )
        result.metadata["path"] = path
        return result

    def _name_of(self, source: bytes, node) -> str | None:
        for field_name in _NAME_FIELDS:
            child = node.child_by_field_name(field_name)
            if child is None:
                continue
            # C/C++ declarators wrap the name; descend to the innermost identifier.
            inner = first_child_of_type(child, "identifier", "field_identifier", "type_identifier")
            text = node_text(source, inner or child)
            if text and len(text) < 200 and text.isprintable():
                return text.strip()
        return None


def _kind_for(node_type: str, language: str) -> str:
    if "class" in node_type or "object" in node_type:
        return "class"
    if "interface" in node_type or "protocol" in node_type:
        return "interface"
    if "trait" in node_type or "impl" in node_type:
        return "trait"
    if "struct" in node_type:
        return "class"
    if "enum" in node_type:
        return "enum"
    if "method" in node_type:
        return "method"
    if "type" in node_type:
        return "type_alias"
    if "module" in node_type or "package" in node_type:
        return "module"
    return "function"