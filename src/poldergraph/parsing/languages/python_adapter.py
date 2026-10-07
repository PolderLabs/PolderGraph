"""Python language adapter (strong).

Extracts declarations, ownership, imports, calls, inheritance, decorators and
type references from the syntax tree. No regex over source.
"""

from __future__ import annotations

from typing import Any

from tree_sitter import Node

from ...models.edge import EdgeType, Provenance, SourceLocation
from ..engine import children_of_type, node_text, walk
from ..types import (
    ExportRecord,
    ImportRecord,
    ParseResult,
    ParsedSymbol,
    Reference,
)

#: Statement nodes that introduce a class.
_CLASS_NODES = {"class_definition"}
#: Statement nodes that introduce a function.
_FUNCTION_NODES = {"function_definition"}
_DECORATORS = {"decorator"}


class PythonAdapter:
    """Strong adapter for Python."""

    language = "python"
    resolves_imports = True

    def supports(self) -> bool:
        return True

    def parse(self, source: bytes, path: str) -> ParseResult:
        from ..engine import get_parser

        parser = get_parser("python")
        tree = parser.parse(source)
        root = tree.root_node
        result = ParseResult(adapter="python")
        result.metadata["path"] = path
        self._visit_module(source, root, result, parent=None, scope=[])
        return result

    # -------------------------------------------------------------- helpers

    def _line(self, node: Node) -> int:
        return node.start_point[0]

    def _loc(self, node: Node, path: str) -> SourceLocation:
        return SourceLocation(path=path, line=node.start_point[0], col=node.start_point[1])

    def _add_symbol(
        self,
        result: ParseResult,
        *,
        kind: str,
        name_node: Node | None,
        node: Node,
        parent_index: int | None,
        scope: list[str],
        source: bytes,
        path: str,
        decorators: list[Node] | None = None,
    ) -> int | None:
        if name_node is None:
            return None
        name = node_text(source, name_node)
        qualified = ".".join([*scope, name])
        body_node = node.child_by_field_name("body")
        signature = self._signature(source, node)
        docstring = self._docstring(source, body_node)
        visibility = "private" if name.startswith("_") and not name.startswith("__") else "public"
        index = len(result.symbols)
        result.symbols.append(
            ParsedSymbol(
                kind=kind,
                name=name,
                qualified_name=qualified,
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                start_line=node.start_point[0],
                end_line=node.end_point[0],
                parent_index=parent_index,
                signature=signature,
                docstring=docstring,
                visibility=visibility,
                body_text=node_text(source, node) if body_node is None else node_text(source, body_node),
                metadata={"decorators": len(decorators or [])},
            )
        )
        if decorators:
            for decorator in decorators:
                text = node_text(source, decorator).lstrip("@")
                result.references.append(
                    Reference(
                        name=_last_segment(text),
                        edge_type=EdgeType.DECORATES,
                        source_symbol_index=parent_index if parent_index is not None else index,
                        location=self._loc(decorator, path),
                        provenance=Provenance.EXTRACTED,
                        qualifier=_qualifier_of(text),
                        metadata={"raw": text[:120]},
                    )
                )
        return index

    def _signature(self, source: bytes, node: Node) -> str | None:
        """Build a compact signature without the function body."""
        params = node.child_by_field_name("parameters")
        returns = node.child_by_field_name("return_type")
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return None
        parts = [node_text(source, name_node)]
        if params is not None:
            parts.append(node_text(source, params).replace("\n", " "))
        if returns is not None:
            parts.append(f"-> {node_text(source, returns)}")
        return " ".join(" ".join(parts).split())

    def _docstring(self, source: bytes, body: Node | None) -> str | None:
        """Extract a leading string literal from a function/class body.

        Tree-sitter exposes a bare docstring directly as a ``string`` node in
        the block; older grammars wrap it in an ``expression_statement``.
        """
        if body is None or not body.named_children:
            return None
        first = body.named_children[0]
        if first.type == "expression_statement":
            first = first.named_children[0] if first.named_children else None
        if first is None or first.type != "string":
            return None
        raw = node_text(source, first)
        for quote in ('"""', "'''"):
            if raw.startswith(quote) and raw.endswith(quote) and len(raw) >= 6:
                return raw[3:-3].strip()
        return raw.strip("\"'").strip() or None

    # ----------------------------------------------------------- traversal

    def _visit_module(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str]
    ) -> None:
        for child in node.named_children:
            self._visit_statement(source, child, result, parent, scope)

    def _visit_statement(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str]
    ) -> None:
        node_type = node.type

        if node_type in _FUNCTION_NODES:
            decorators = [d for d in node.named_children if d.type in _DECORATORS]
            name_node = node.child_by_field_name("name")
            index = self._add_symbol(
                result,
                kind="method" if parent is not None else "function",
                name_node=name_node,
                node=node,
                parent_index=parent,
                scope=scope,
                source=source,
                path=self._path(node, result),
                decorators=decorators,
            )
            if index is None:
                return
            name = node_text(source, name_node)
            qualified = ".".join([*scope, name])
            new_scope = [*scope, name]
            params = node.child_by_field_name("parameters")
            returns = node.child_by_field_name("return_type")
            if params is not None:
                for param in _parameter_names(params):
                    result.references.append(
                        Reference(
                            name=param.name,
                            edge_type=EdgeType.ACCEPTS_TYPE,
                            source_symbol_index=index,
                            location=self._loc(param.node, self._path(node, result)),
                            provenance=Provenance.INFERRED,
                            metadata={"annotation": param.annotation},
                        )
                    )
            if returns is not None:
                self._record_type_refs(
                    source, returns, result, index, EdgeType.RETURNS_TYPE, self._path(node, result)
                )
            self._visit_body(source, node.child_by_field_name("body"), result, index, new_scope)
            self._record_test_link(result, index, decorators)
            return

        if node_type in _CLASS_NODES:
            decorators = [d for d in node.named_children if d.type in _DECORATORS]
            name_node = node.child_by_field_name("name")
            index = self._add_symbol(
                result,
                kind="class",
                name_node=name_node,
                node=node,
                parent_index=parent,
                scope=scope,
                source=source,
                path=self._path(node, result),
                decorators=decorators,
            )
            if index is None:
                return
            name = node_text(source, name_node)
            superscripts = node.child_by_field_name("superclasses")
            if superscripts is not None:
                for base in superscripts.named_children:
                    base_name = _last_segment(node_text(source, base))
                    result.references.append(
                        Reference(
                            name=base_name,
                            edge_type=EdgeType.INHERITS,
                            source_symbol_index=index,
                            location=self._loc(base, self._path(node, result)),
                            provenance=Provenance.EXTRACTED,
                            qualifier=_qualifier_of(node_text(source, base)),
                        )
                    )
            body = node.child_by_field_name("body")
            if body is not None:
                for member in body.named_children:
                    self._visit_statement(source, member, result, index, [*scope, name])
            self._record_test_link(result, index, decorators)
            return

        if node_type == "import_statement":
            for child in node.named_children:
                if child.type == "dotted_name":
                    module = node_text(source, child)
                    result.imports.append(
                        ImportRecord(
                            module=module,
                            source_symbol_index=parent,
                            location=self._loc(child, self._path(node, result)),
                            aliases={module.split(".")[-1]: module},
                        )
                    )
                elif child.type == "aliased_import":
                    fields = child.named_children
                    if len(fields) == 2:
                        target = node_text(source, fields[0])
                        alias = node_text(source, fields[1])
                        result.imports.append(
                            ImportRecord(
                                module=target,
                                source_symbol_index=parent,
                                location=self._loc(child, self._path(node, result)),
                                aliases={alias: target},
                            )
                        )
            return

        if node_type == "import_from_statement":
            module_node = node.child_by_field_name("module_name")
            module = node_text(source, module_node) if module_node else ""
            # `child_by_field_name` returns a fresh wrapper on every call, so
            # identity comparison is unreliable; match the byte span instead.
            module_span = (
                (module_node.start_byte, module_node.end_byte) if module_node is not None else None
            )
            wildcards = [c for c in node.named_children if c.type == "wildcard_import"]
            for child in node.named_children:
                if module_span is not None and (child.start_byte, child.end_byte) == module_span:
                    continue
                if child.type == "dotted_name" and not wildcards:
                    alias = node_text(source, child)
                    # `from a.b import c` imports the *module* `a.b`; `c` is the
                    # name bound locally. Keeping them separate is what lets the
                    # resolver reach `a/b.py` and then find `c` inside it.
                    imported = module if module else alias
                    result.imports.append(
                        ImportRecord(
                            module=imported,
                            source_symbol_index=parent,
                            location=self._loc(child, self._path(node, result)),
                            aliases={alias: imported},
                        )
                    )
                elif child.type == "aliased_import":
                    fields = child.named_children
                    if len(fields) == 2:
                        target, alias = node_text(source, fields[0]), node_text(source, fields[1])
                        result.imports.append(
                            ImportRecord(
                                module=module if module else target,
                                source_symbol_index=parent,
                                location=self._loc(child, self._path(node, result)),
                                aliases={alias: target},
                            )
                        )
                elif child.type == "wildcard_import":
                    result.imports.append(
                        ImportRecord(
                            module=module,
                            source_symbol_index=parent,
                            location=self._loc(child, self._path(node, result)),
                            aliases={},
                            metadata={"star": True},
                        )
                    )
            return

        if node_type == "decorated_definition":
            definition = next(
                (c for c in node.named_children if c.type in (_FUNCTION_NODES | _CLASS_NODES)), None
            )
            if definition is not None:
                for decorator in [c for c in node.named_children if c.type == "decorator"]:
                    text = node_text(source, decorator).lstrip("@")
                    result.references.append(
                        Reference(
                            name=_last_segment(text),
                            edge_type=EdgeType.DECORATES,
                            source_symbol_index=parent,
                            location=self._loc(decorator, self._path(node, result)),
                            provenance=Provenance.EXTRACTED,
                            qualifier=_qualifier_of(text),
                        )
                    )
                self._visit_statement(source, definition, result, parent, scope)
            return

        self._record_expressions(source, node, result, parent)
        for child in node.named_children:
            self._visit_statement(source, child, result, parent, scope)

    def _visit_body(
        self, source: bytes, body: Node | None, result: ParseResult, owner: int, scope: list[str]
    ) -> None:
        if body is None:
            return
        for child in body.named_children:
            self._visit_statement(source, child, result, owner, scope)

    def _record_test_link(self, result: ParseResult, index: int, decorators: list[Node]) -> None:
        result.symbols[index].metadata["is_test"] = _looks_like_test(result.symbols[index].qualified_name)

    def _path(self, node: Node, result: ParseResult) -> str:
        return result.metadata.get("path", "")

    def _record_type_refs(
        self, source: bytes, node: Node, result: ParseResult, index: int, edge_type: str, path: str
    ) -> None:
        for current in walk(node):
            if current.type == "identifier":
                text = node_text(source, current)
                if text and text not in {"str", "int", "float", "bool", "bytes", "None", "Any"}:
                    result.references.append(
                        Reference(
                            name=text,
                            edge_type=edge_type,
                            source_symbol_index=index,
                            location=self._loc(current, path),
                            provenance=Provenance.EXTRACTED,
                        )
                    )

    def _record_expressions(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None
    ) -> None:
        """Record calls appearing directly under ``node``.

        Nested calls inside arguments are recorded too, attributed to the same
        enclosing entity, so an inner callee is never lost.
        """
        path = result.metadata.get("path", "")
        for child in node.named_children:
            if child.type != "call":
                continue
            self._record_call_node(source, child, result, parent, path)

    def _record_call_node(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, path: str
    ) -> None:
        function = node.child_by_field_name("function")
        if function is not None:
            text = node_text(source, function).strip()
            qualifier, _, name = text.rpartition(".")
            result.references.append(
                Reference(
                    name=name or text,
                    edge_type=EdgeType.CONSTRUCTS
                    if _looks_like_constructor(text)
                    else EdgeType.CALLS,
                    source_symbol_index=parent,
                    location=SourceLocation(
                        path=path, line=node.start_point[0], col=node.start_point[1]
                    ),
                    provenance=Provenance.EXTRACTED,
                    qualifier=qualifier or None,
                )
            )
        arguments = node.child_by_field_name("arguments")
        if arguments is None:
            return
        for argument in arguments.named_children:
            # Keyword arguments still contain the call's real callee.
            if argument.type == "keyword_argument":
                argument = argument.child_by_field_name("value") or argument
            for current in walk(argument):
                if current.type == "call":
                    self._record_call_node(source, current, result, parent, path)


def _looks_like_constructor(name: str) -> bool:
    tail = name.rsplit(".", 1)[-1]
    return bool(tail) and tail[0].isupper()


def _looks_like_test(qualified_name: str) -> bool:
    tail = qualified_name.rsplit(".", 1)[-1]
    return tail.startswith("test_") or tail.endswith("_test") or "Test" in tail


def _last_segment(text: str) -> str:
    cleaned = text.strip().strip("()[]{}<>")
    return cleaned.rsplit(".", 1)[-1]


def _qualifier_of(text: str) -> str | None:
    cleaned = text.strip().strip("()[]{}<>")
    if "." in cleaned:
        return cleaned.rsplit(".", 1)[0]
    return None


def _parameter_names(params: Node) -> list[Any]:
    from tree_sitter import Node as TNode

    out: list[Any] = []

    class _Param:
        def __init__(self, name: str, node: TNode, annotation: str | None) -> None:
            self.name = name
            self.node = node
            self.annotation = annotation

    for child in params.named_children:
        if child.type in {"typed_parameter", "default_parameter", "typed_default_parameter"}:
            name_node = child.child_by_field_name("name")
            type_node = child.child_by_field_name("type")
            if name_node is None:
                continue
            identifier = next((c for c in name_node.named_children if c.type == "identifier"), name_node)
            if child.type == "typed_default_parameter":
                identifier = next(
                    (c for c in name_node.named_children if c.type == "identifier"), name_node
                )
            out.append(_Param(identifier.text.decode(), name_node, None))
            if type_node is not None:
                out[-1].annotation = type_node.text.decode()
    return out