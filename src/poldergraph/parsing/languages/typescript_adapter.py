"""TypeScript / TSX language adapter (strong).

Extends the JavaScript traversal with type-level declarations that have no
JavaScript equivalent: interfaces, type aliases, enums, type parameters,
parameter and return types, `implements` clauses and overload signatures.
"""

from __future__ import annotations

from tree_sitter import Node

from ...models.edge import EdgeType, Provenance, SourceLocation
from ..engine import first_child_of_type, get_parser, node_text, walk
from ..types import (
    ExportRecord,
    ImportRecord,
    ParseResult,
    ParsedSymbol,
    Reference,
)

_TYPE_DECLARATIONS: dict[str, str] = {
    "interface_declaration": "interface",
    "type_alias_declaration": "type_alias",
    "enum_declaration": "enum",
}

_FUNCTION_TYPES = frozenset(
    {
        "function_declaration",
        "generator_function_declaration",
        "function_signature",
        "method_signature",
        "method_definition",
        "function_expression",
        "generator_function",
    }
)

_PRIMITIVES = frozenset(
    {"string", "number", "boolean", "void", "any", "unknown", "never", "object", "symbol", "bigint", "null", "undefined"}
)


class TypeScriptAdapter:
    """Strong adapter for TypeScript and TSX."""

    resolves_imports = True

    def __init__(self, language: str = "typescript") -> None:
        self.language = language
        self.grammar = "tsx" if language == "tsx" else "typescript"

    def supports(self) -> bool:
        return True

    def parse(self, source: bytes, path: str) -> ParseResult:
        parser = get_parser(self.grammar)
        tree = parser.parse(source)
        result = ParseResult(adapter=f"{self.language}-table")
        result.metadata["path"] = path
        self._visit(source, tree.root_node, result, parent=None, scope=[])
        return result

    def _loc(self, node: Node, path: str) -> SourceLocation:
        return SourceLocation(path=path, line=node.start_point[0], col=node.start_point[1])

    def _name_of(self, source: bytes, node: Node) -> str | None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return None
        return node_text(source, name_node).strip() or None

    def _visit(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str]
    ) -> None:
        for child in node.named_children:
            self._visit_node(source, child, result, parent, scope)

    def _visit_node(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str]
    ) -> None:
        from .javascript_adapter import JavaScriptAdapter

        path = result.metadata.get("path", "")
        node_type = node.type

        if node_type in _TYPE_DECLARATIONS:
            self._add_type_declaration(source, node, result, parent, scope, path)
            return

        if node_type == "abstract_class_declaration" or node_type == "class_declaration":
            self._add_class(source, node, result, parent, scope, path)
            return

        if node_type in {"import_statement", "import_alias"}:
            # Import grammar is identical to JS; reuse that extraction.
            self._delegate_declaration(source, node, result, parent, path)
            return

        if node_type == "export_statement":
            # An export wraps a declaration. Record the export, then keep
            # walking so the wrapped declaration still produces symbols.
            self._delegate_declaration(source, node, result, parent, path)
            self._visit(source, node, result, parent, scope)
            return

        if node_type in {"lexical_declaration", "variable_declaration"}:
            self._record_variable(source, node, result, parent, scope, path)
            self._visit(source, node, result, parent, scope)
            return

        if node_type in _FUNCTION_TYPES:
            self._add_function(source, node, result, parent, scope, path)
            return

        if node_type in {"public_field_definition", "property_signature"}:
            self._add_property(source, node, result, parent, scope, path)
            return

        if node_type == "call_expression":
            self._record_call(source, node, result, parent, path)
            self._visit(source, node, result, parent, scope)
            return

        if node_type in {"type_annotation", "generic_type"}:
            self._record_type_refs(source, node, result, parent, path)
            return

        self._visit(source, node, result, parent, scope)

    def _delegate_declaration(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, path: str
    ) -> None:
        """Reuse the JS import/export extraction against the TS grammar."""
        from .javascript_adapter import JavaScriptAdapter

        helper = JavaScriptAdapter(self.language)
        helper.grammar = self.grammar
        if node.type in {"import_statement", "import_alias"}:
            helper._record_import(source, node, result, parent, path)
        else:
            helper._record_export(source, node, result, parent, path)

    # ------------------------------------------------------------- symbols

    def _add_type_declaration(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str], path: str
    ) -> None:
        name = self._name_of(source, node)
        if not name:
            return
        kind = _TYPE_DECLARATIONS[node.type]
        index = len(result.symbols)
        result.symbols.append(
            ParsedSymbol(
                kind=kind,
                name=name,
                qualified_name=".".join([*scope, name]),
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                start_line=node.start_point[0],
                end_line=node.end_point[0],
                parent_index=parent,
                signature=_first_line(source, node),
                docstring=_leading_comment(source, node),
                visibility="public",
            )
        )
        result.exports.append(
            ExportRecord(name=name, local_name=name, source_symbol_index=index, location=self._loc(node, path))
        )

        body = node.child_by_field_name("body")
        if body is not None:
            for member in body.named_children:
                if member.type in {"method_signature", "property_signature", "public_field_definition"}:
                    self._add_property_or_signature(source, member, result, index, [*scope, name], path)
                else:
                    self._visit_node(source, member, result, index, [*scope, name])
        else:
            value = node.child_by_field_name("value")
            if value is not None:
                self._record_type_refs(source, value, result, index, path)

    def _add_property_or_signature(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str], path: str
    ) -> None:
        name = self._name_of(source, node)
        if not name:
            return
        kind = "method" if "signature" in node.type or "method" in node.type else "property"
        index = len(result.symbols)
        result.symbols.append(
            ParsedSymbol(
                kind=kind,
                name=name,
                qualified_name=".".join([*scope, name]),
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                start_line=node.start_point[0],
                end_line=node.end_point[0],
                parent_index=parent,
                signature=_first_line(source, node),
                docstring=_leading_comment(source, node),
                visibility="public",
                metadata={"is_test": name.startswith(("test", "should"))},
            )
        )
        type_node = node.child_by_field_name("type")
        if type_node is not None:
            self._record_type_refs(source, type_node, result, index, path)
        parameters = node.child_by_field_name("parameters")
        if parameters is not None:
            self._record_parameter_types(source, parameters, result, index, path)

    def _add_class(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str], path: str
    ) -> None:
        name = self._name_of(source, node)
        index = len(result.symbols)
        qualified = ".".join([*scope, name]) if name else ".".join(scope)
        if name:
            result.symbols.append(
                ParsedSymbol(
                    kind="class",
                    name=name,
                    qualified_name=qualified,
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    start_line=node.start_point[0],
                    end_line=node.end_point[0],
                    parent_index=parent,
                    signature=_first_line(source, node),
                    docstring=_leading_comment(source, node),
                    visibility="public",
                )
            )
            result.exports.append(
                ExportRecord(
                    name=name, local_name=name, source_symbol_index=index, location=self._loc(node, path)
                )
            )

        heritage = node.child_by_field_name("superclass")
        if heritage is not None:
            superclass = first_child_of_type(heritage, "identifier", "member_expression", "generic_type")
            if superclass is not None:
                text = node_text(source, superclass)
                result.references.append(
                    Reference(
                        name=text.rsplit(".", 1)[-1].strip(),
                        edge_type=EdgeType.INHERITS,
                        source_symbol_index=index,
                        location=self._loc(superclass, path),
                        provenance=Provenance.EXTRACTED,
                        qualifier=".".join(text.split(".")[:-1]) or None,
                    )
                )
        for child in node.named_children:
            if child.type == "class_heritage":
                implements = child.child_by_field_name("implements") or first_child_of_type(
                    child, "implements_clause", "extends_clause"
                )
                target = implements if implements is not None else child
                for current in walk(target):
                    if current.type in {"type_identifier", "generic_type", "nested_type_identifier"}:
                        text = node_text(source, current).strip()
                        if not text:
                            continue
                        result.references.append(
                            Reference(
                                name=text.rsplit(".", 1)[-1],
                                edge_type=EdgeType.IMPLEMENTS,
                                source_symbol_index=index,
                                location=self._loc(current, path),
                                provenance=Provenance.EXTRACTED,
                                qualifier=".".join(text.split(".")[:-1]) or None,
                            )
                        )

        body = node.child_by_field_name("body")
        if body is not None:
            for member in body.named_children:
                if member.type in {"method_definition", "public_field_definition", "abstract_method_signature"}:
                    self._add_property_or_signature(source, member, result, index, [*scope, name], path)
                    value = member.child_by_field_name("value")
                    if value is not None:
                        self._visit_node(source, value, result, index, [*scope, name])
                else:
                    self._visit_node(source, member, result, index, [*scope, name])

    def _add_property(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str], path: str
    ) -> None:
        self._add_property_or_signature(source, node, result, parent, scope, path)

    def _add_function(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str], path: str
    ) -> None:
        name = self._name_of(source, node)
        if not name:
            identifier = first_child_of_type(node, "identifier")
            if identifier is not None:
                name = node_text(source, identifier)
        if not name:
            self._visit(source, node, result, parent, scope)
            return
        index = len(result.symbols)
        result.symbols.append(
            ParsedSymbol(
                kind="method" if node.type in {"method_definition", "method_signature"} else "function",
                name=name,
                qualified_name=".".join([*scope, name]),
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                start_line=node.start_point[0],
                end_line=node.end_point[0],
                parent_index=parent,
                signature=_signature(source, node),
                docstring=_leading_comment(source, node),
                visibility="public",
                metadata={"is_test": name.startswith(("test", "should"))},
            )
        )
        result.exports.append(
            ExportRecord(name=name, local_name=name, source_symbol_index=index, location=self._loc(node, path))
        )

        parameters = node.child_by_field_name("parameters")
        if parameters is not None:
            self._record_parameter_types(source, parameters, result, index, path)
        returns = node.child_by_field_name("return_type")
        if returns is not None:
            self._record_type_refs(source, returns, result, index, path)
        body = node.child_by_field_name("body")
        if body is not None:
            self._visit(source, body, result, index, [*scope, name])

    def _record_variable(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str], path: str
    ) -> None:
        from .javascript_adapter import JavaScriptAdapter
        from ..engine import descendants_of_type

        helper = JavaScriptAdapter(self.language)
        helper.grammar = self.grammar
        helper._record_variable(source, node, result, parent, scope, path)

    # ---------------------------------------------------------- references

    def _record_parameter_types(
        self, source: bytes, parameters: Node, result: ParseResult, index: int, path: str
    ) -> None:
        for current in walk(parameters):
            if current.type not in {"required_parameter", "optional_parameter", "identifier"}:
                continue
            type_node = current.child_by_field_name("type")
            if type_node is not None:
                self._record_type_refs(source, type_node, result, index, path)

    def _record_type_refs(
        self, source: bytes, node: Node, result: ParseResult, index: int | None, path: str
    ) -> None:
        for current in walk(node):
            if current.type not in {"type_identifier", "nested_type_identifier", "generic_type", "array_type", "union_type"}:
                continue
            text = node_text(source, current).strip()
            if not text or not text.isprintable():
                continue
            if text in _PRIMITIVES:
                continue
            # Skip the bare identifiers that duplicate a parent generic node.
            if current.parent is not None and current.parent.type in {"generic_type", "array_type"} and current.parent.named_child_count == 1:
                continue
            result.references.append(
                Reference(
                    name=text.rsplit(".", 1)[-1].strip("<>[]{} ,"),
                    edge_type=EdgeType.ACCEPTS_TYPE,
                    source_symbol_index=index,
                    location=self._loc(current, path),
                    provenance=Provenance.EXTRACTED,
                    qualifier=".".join(text.split(".")[:-1]) or None,
                )
            )

    def _record_call(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, path: str
    ) -> None:
        from .javascript_adapter import JavaScriptAdapter

        helper = JavaScriptAdapter(self.language)
        helper.grammar = self.grammar
        helper._record_call(source, node, result, parent, path)


def _first_line(source: bytes, node: Node) -> str | None:
    if node.end_point[0] != node.start_point[0]:
        return None
    text = node_text(source, node).strip()
    return text[:300] if text else None


def _signature(source: bytes, node: Node) -> str | None:
    body = node.child_by_field_name("body")
    end = body.start_byte if body is not None else min(node.end_byte, node.start_byte + 300)
    text = source[node.start_byte:end].decode("utf-8", errors="replace").strip()
    return " ".join(text.split())[:300] or None


def _leading_comment(source: bytes, node: Node) -> str | None:
    previous = node.prev_named_sibling
    while previous is not None and previous.type in {"comment", "line_comment", "block_comment"}:
        text = node_text(source, previous).strip()
        if text:
            for marker in ("/**", "*/", "//", "*"):
                text = text.replace(marker, " ")
            return " ".join(text.split()) or None
        previous = previous.prev_named_sibling
    return None