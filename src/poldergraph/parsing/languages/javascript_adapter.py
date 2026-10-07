"""JavaScript / JSX language adapter (strong)."""

from __future__ import annotations

from tree_sitter import Node

from ...models.edge import EdgeType, Provenance, SourceLocation
from ..engine import first_child_of_type, get_parser, node_text
from ..types import (
    ExportRecord,
    ImportRecord,
    ParseResult,
    ParsedSymbol,
    Reference,
)

_FUNCTION_TYPES = frozenset(
    {
        "function_declaration",
        "generator_function_declaration",
        "function_expression",
        "generator_function",
        "arrow_function",
        "method_definition",
    }
)
_CLASS_TYPES = frozenset({"class_declaration", "class"})
_METHOD_MEMBER_TYPES = frozenset(
    {"method_definition", "field_definition", "public_field_definition"}
)


class JavaScriptAdapter:
    """Strong adapter for JavaScript and JSX."""

    resolves_imports = True

    def __init__(self, language: str = "javascript") -> None:
        self.language = language
        self.grammar = "javascript"

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

    def _visit(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str]
    ) -> None:
        for child in node.named_children:
            self._visit_node(source, child, result, parent, scope)

    def _visit_node(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str]
    ) -> None:
        path = result.metadata.get("path", "")
        node_type = node.type

        if node_type == "import_statement":
            self._record_import(source, node, result, parent, path)
            return

        if node_type == "export_statement":
            self._record_export(source, node, result, parent, path)
            # An export wraps a declaration; keep walking into it.
            self._visit(source, node, result, parent, scope)
            return

        if node_type in _CLASS_TYPES:
            self._add_class(source, node, result, parent, scope, path)
            return

        if node_type in {"lexical_declaration", "variable_declaration"}:
            self._record_variable(source, node, result, parent, scope, path)
            self._visit(source, node, result, parent, scope)
            return

        if node_type in _FUNCTION_TYPES:
            self._add_function(source, node, result, parent, scope, path)
            return

        if node_type == "call_expression":
            self._record_call(source, node, result, parent, path)

        self._visit(source, node, result, parent, scope)

    # ------------------------------------------------------------- symbols

    def _name_of(self, source: bytes, node: Node) -> str | None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return None
        text = node_text(source, name_node).strip()
        return text or None

    def _add_class(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str], path: str
    ) -> None:
        name = self._name_of(source, node)
        qualified = ".".join([*scope, name]) if name else ".".join(scope)
        index = len(result.symbols)
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
                    signature=node_text(source, node).splitlines()[0][:200],
                )
            )
        heritage = node.child_by_field_name("superclass")
        if heritage is not None:
            superclass = first_child_of_type(heritage, "identifier", "member_expression")
            if superclass is not None:
                text = node_text(source, superclass)
                result.references.append(
                    Reference(
                        name=text.rsplit(".", 1)[-1],
                        edge_type=EdgeType.INHERITS,
                        source_symbol_index=index,
                        location=self._loc(superclass, path),
                        provenance=Provenance.EXTRACTED,
                        qualifier=".".join(text.split(".")[:-1]) or None,
                    )
                )

        body = node.child_by_field_name("body")
        if body is not None:
            for member in body.named_children:
                if member.type in _METHOD_MEMBER_TYPES:
                    self._add_member(source, member, result, index, [*scope, name] if name else scope, path)
                else:
                    self._visit_node(source, member, result, index, [*scope, name] if name else scope)

    def _add_member(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str], path: str
    ) -> None:
        name = self._name_of(source, node)
        if not name:
            self._visit(source, node, result, parent, scope)
            return
        is_field = "field" in node.type
        index = len(result.symbols)
        result.symbols.append(
            ParsedSymbol(
                kind="property" if is_field else "method",
                name=name,
                qualified_name=".".join([*scope, name]),
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                start_line=node.start_point[0],
                end_line=node.end_point[0],
                parent_index=parent,
                signature=node_text(source, node).splitlines()[0][:200],
                metadata={"is_test": name.startswith("test") or name.startswith("should")},
            )
        )
        if node.type in {"public_field_definition"}:
            type_node = node.child_by_field_name("type")
            if type_node is not None:
                self._record_type_refs(source, type_node, result, index, EdgeType.RETURNS_TYPE, path)
        value = node.child_by_field_name("value")
        if value is not None:
            self._visit_node(source, value, result, index, scope)

    def _add_function(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str], path: str
    ) -> None:
        name = self._name_of(source, node)
        variable = first_child_of_type(node, "identifier")
        if not name and variable is not None:
            name = node_text(source, variable)
        if not name:
            self._visit(source, node, result, parent, scope)
            return

        kind = "method" if node.type == "method_definition" else (
            "function" if parent is None else "function"
        )
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
                signature=_signature(source, node),
                docstring=_leading_comment(source, node),
                metadata={"is_test": name.startswith(("test", "should"))},
            )
        )
        result.exports.append(
            ExportRecord(name=name, local_name=name, source_symbol_index=index, location=self._loc(node, path))
        )
        self._visit(source, node, result, index, [*scope, name])

    def _record_variable(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str], path: str
    ) -> None:
        from ..engine import descendants_of_type

        for declarator in descendants_of_type(node, "variable_declarator"):
            name_node = declarator.child_by_field_name("name")
            if name_node is None or name_node.type != "identifier":
                continue
            name = node_text(source, name_node)
            value = declarator.child_by_field_name("value")
            # A variable initialized with an arrow/function is that function.
            if value is not None and value.type in _FUNCTION_TYPES:
                self._add_function_from_value(source, value, declarator, name, result, parent, scope, path)
                continue
            index = len(result.symbols)
            result.symbols.append(
                ParsedSymbol(
                    kind="constant" if node.type == "lexical_declaration" else "variable",
                    name=name,
                    qualified_name=".".join([*scope, name]),
                    start_byte=declarator.start_byte,
                    end_byte=declarator.end_byte,
                    start_line=declarator.start_point[0],
                    end_line=declarator.end_point[0],
                    parent_index=parent,
                    signature=node_text(source, declarator).splitlines()[0][:200],
                )
            )
            result.exports.append(
                ExportRecord(
                    name=name, local_name=name, source_symbol_index=index, location=self._loc(declarator, path)
                )
            )
            type_node = declarator.child_by_field_name("type")
            if type_node is not None:
                self._record_type_refs(source, type_node, result, index, EdgeType.RETURNS_TYPE, path)

    def _add_function_from_value(
        self,
        source: bytes,
        value: Node,
        declarator: Node,
        name: str,
        result: ParseResult,
        parent: int | None,
        scope: list[str],
        path: str,
    ) -> None:
        index = len(result.symbols)
        result.symbols.append(
            ParsedSymbol(
                kind="function",
                name=name,
                qualified_name=".".join([*scope, name]),
                start_byte=declarator.start_byte,
                end_byte=declarator.end_byte,
                start_line=declarator.start_point[0],
                end_line=declarator.end_point[0],
                parent_index=parent,
                signature=_signature(source, value),
                docstring=_leading_comment(source, declarator),
                metadata={"is_test": name.startswith(("test", "should"))},
            )
        )
        result.exports.append(
            ExportRecord(
                name=name, local_name=name, source_symbol_index=index, location=self._loc(declarator, path)
            )
        )
        self._visit(source, value, result, index, [*scope, name])

    # ---------------------------------------------------------- references

    def _record_import(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, path: str
    ) -> None:
        module_node = node.child_by_field_name("source")
        module = node_text(source, module_node).strip("\"'`") if module_node else ""
        if not module:
            return
        aliases: dict[str, str] = {}
        clause = first_child_of_type(node, "import_clause")
        if clause is not None:
            from ..engine import walk

            default = clause.child_by_field_name("name")
            if default is not None:
                aliases[node_text(source, default)] = "default"
            namespace = clause.child_by_field_name("namespace_identifier")
            if namespace is not None:
                text = node_text(source, namespace)
                if text:
                    aliases[text] = "*"
            for current in walk(clause):
                if current.type == "named_imports":
                    for specifier in current.named_children:
                        if specifier.type != "import_specifier":
                            continue
                        local = specifier.child_by_field_name("name")
                        original = specifier.child_by_field_name("alias") or local
                        if original is not None:
                            aliases[node_text(source, original)] = node_text(source, local or original)

        result.imports.append(
            ImportRecord(
                module=module,
                source_symbol_index=parent,
                location=self._loc(node, path),
                aliases=aliases,
            )
        )
        for alias, original in aliases.items():
            result.references.append(
                Reference(
                    name=alias,
                    edge_type=EdgeType.IMPORTS,
                    source_symbol_index=parent,
                    location=self._loc(node, path),
                    provenance=Provenance.EXTRACTED,
                    qualifier=module,
                    metadata={"original": original},
                )
            )

    def _record_export(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, path: str
    ) -> None:
        declaration = first_child_of_type(
            node, "lexical_declaration", "variable_declaration", "function_declaration", "class_declaration"
        )
        if declaration is not None:
            return
        source_node = node.child_by_field_name("source")
        if source_node is not None:
            module = node_text(source, source_node).strip("\"'`")
            result.imports.append(
                ImportRecord(
                    module=module,
                    source_symbol_index=parent,
                    location=self._loc(node, path),
                    aliases={},
                    is_reexport=True,
                )
            )
            result.exports.append(
                ExportRecord(
                    name="*",
                    local_name=None,
                    source_symbol_index=parent,
                    location=self._loc(node, path),
                    metadata={"module": module},
                )
            )
            return
        clause = first_child_of_type(node, "export_clause")
        if clause is not None:
            from ..engine import walk

            for current in walk(clause):
                if current.type in {"export_specifier"}:
                    original = current.child_by_field_name("name")
                    alias = current.child_by_field_name("alias")
                    name = node_text(source, original) if original is not None else ""
                    if name:
                        result.exports.append(
                            ExportRecord(
                                name=name,
                                local_name=node_text(source, alias) if alias is not None else name,
                                source_symbol_index=parent,
                                location=self._loc(current, path),
                            )
                        )

    def _record_call(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, path: str
    ) -> None:
        from ..engine import walk

        function = node.child_by_field_name("function")
        if function is None:
            function = first_child_of_type(node, "identifier", "member_expression")
        if function is not None:
            text = node_text(source, function)
            if text:
                is_construct = _is_constructor(text)
                result.references.append(
                    Reference(
                        name=text.rsplit(".", 1)[-1],
                        edge_type=EdgeType.CONSTRUCTS if is_construct else EdgeType.CALLS,
                        source_symbol_index=parent,
                        location=self._loc(function, path),
                        provenance=Provenance.EXTRACTED,
                        qualifier=".".join(text.split(".")[:-1]) or None,
                    )
                )
        arguments = node.child_by_field_name("arguments")
        if arguments is None:
            return
        for current in walk(arguments):
            if current.type != "call_expression":
                continue
            nested = current.child_by_field_name("function")
            if nested is None:
                continue
            text = node_text(source, nested)
            if text:
                result.references.append(
                    Reference(
                        name=text.rsplit(".", 1)[-1],
                        edge_type=EdgeType.CONSTRUCTS if _is_constructor(text) else EdgeType.CALLS,
                        source_symbol_index=parent,
                        location=self._loc(current, path),
                        provenance=Provenance.EXTRACTED,
                        qualifier=".".join(text.split(".")[:-1]) or None,
                    )
                )

    def _record_type_refs(
        self, source: bytes, node: Node, result: ParseResult, index: int, edge_type: str, path: str
    ) -> None:
        from ..engine import walk

        for current in walk(node):
            if current.type not in {"type_identifier", "nested_type_identifier", "generic_type"}:
                continue
            text = node_text(source, current)
            if not text or not text.isprintable():
                continue
            result.references.append(
                Reference(
                    name=text.rsplit(".", 1)[-1],
                    edge_type=edge_type,
                    source_symbol_index=index,
                    location=self._loc(current, path),
                    provenance=Provenance.EXTRACTED,
                    qualifier=".".join(text.split(".")[:-1]) or None,
                )
            )


def _signature(source: bytes, node: Node) -> str | None:
    """Text from the name up to the body, so the signature excludes the body."""
    start = node.start_byte
    body = node.child_by_field_name("body")
    end = body.start_byte if body is not None else min(node.end_byte, start + 300)
    text = source[start:end].decode("utf-8", errors="replace").strip()
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


def _is_constructor(text: str) -> bool:
    tail = text.rsplit(".", 1)[-1]
    return bool(tail) and tail[0].isupper()