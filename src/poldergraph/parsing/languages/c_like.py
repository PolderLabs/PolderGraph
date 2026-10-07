"""Table-driven adapters for the C-family, Rust, Go, Java, Swift and Kotlin grammars.

These grammars share a structural shape: named declarations with a `name`
field, type definitions with base/inheritance lists, import statements and call
expressions. Expressing that as a per-language node table keeps one traversal
implementation instead of nine near-duplicates, which is how tree-sitter's own
query language is meant to be used.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from tree_sitter import Node

from ...models.edge import EdgeType, Provenance, SourceLocation
from ..types import (
    ExportRecord,
    ImportRecord,
    ParseResult,
    ParsedSymbol,
    Reference,
)

#: Node types that declare a callable function, per language.
FUNCTION_NODES: dict[str, frozenset[str]] = {
    "c": frozenset({"function_definition"}),
    "cpp": frozenset({"function_definition"}),
    "java": frozenset(
        {"method_declaration", "constructor_declaration", "compact_constructor_declaration"}
    ),
    "csharp": frozenset(
        {
            "method_declaration",
            "constructor_declaration",
            "local_function_statement",
            "destructor_declaration",
        }
    ),
    "kotlin": frozenset(
        {"function_declaration", "anonymous_initializer", "secondary_constructor"}
    ),
    "swift": frozenset(
        {
            "function_declaration",
            "init_declaration",
            "deinit_declaration",
            "subscript_declaration",
        }
    ),
    "rust": frozenset({"function_item", "function_signature_item"}),
    "go": frozenset({"function_declaration", "method_declaration"}),
    "objective_c": frozenset({"function_definition", "method_definition"}),
}

#: Node types that declare a type, mapped to the entity kind they produce.
TYPE_NODES: dict[str, dict[str, str]] = {
    "c": {
        "struct_specifier": "class",
        "union_specifier": "class",
        "enum_specifier": "enum",
        "type_definition": "type_alias",
    },
    "cpp": {
        "class_specifier": "class",
        "struct_specifier": "class",
        "union_specifier": "class",
        "enum_specifier": "enum",
        "type_definition": "type_alias",
        "alias_declaration": "type_alias",
    },
    "java": {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
        "record_declaration": "class",
        "annotation_type_declaration": "interface",
    },
    "csharp": {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "struct_declaration": "class",
        "enum_declaration": "enum",
        "record_declaration": "class",
        "record_struct_declaration": "class",
        "delegate_declaration": "type_alias",
    },
    "kotlin": {"class_declaration": "class", "object_declaration": "class"},
    "swift": {
        "class_declaration": "class",
        "protocol_declaration": "interface",
        "enum_declaration": "enum",
        "struct_declaration": "class",
        "typealias_declaration": "type_alias",
    },
    "rust": {
        "struct_item": "class",
        "enum_item": "enum",
        "trait_item": "interface",
        "impl_item": "trait",
        "union_item": "class",
        "type_item": "type_alias",
        "mod_item": "module",
    },
    "go": {"type_spec": "type_alias", "type_alias": "type_alias"},
    "objective_c": {"class_interface": "class", "protocol_declaration": "interface"},
}

#: Node types that declare a property/variable/field-like entity.
PROPERTY_NODES: dict[str, frozenset[str]] = {
    "c": frozenset({"declaration", "field_declaration"}),
    "cpp": frozenset({"declaration", "field_declaration"}),
    "java": frozenset({"field_declaration"}),
    "csharp": frozenset(
        {"field_declaration", "property_declaration", "event_field_declaration"}
    ),
    "kotlin": frozenset({"property_declaration"}),
    "swift": frozenset({"property_declaration"}),
    "rust": frozenset({"const_item", "static_item"}),
    "go": frozenset({"const_declaration", "var_declaration"}),
    "objective_c": frozenset({"property_declaration"}),
}

#: Inheritance clause nodes per language.
INHERIT_NODES: dict[str, frozenset[str]] = {
    "java": frozenset({"superclass", "super_interfaces", "extends_interfaces"}),
    "csharp": frozenset({"base_list"}),
    "swift": frozenset({"inheritance_specifier"}),
    "kotlin": frozenset({"delegation_specifier"}),
    "cpp": frozenset({"base_class_clause"}),
    "rust": frozenset({"trait_bounds", "trait"}),
}

#: Import/require node types and which field holds the module path.
IMPORT_NODES: dict[str, frozenset[str]] = {
    "c": frozenset({"preproc_include"}),
    "cpp": frozenset({"preproc_include"}),
    "java": frozenset({"import_declaration"}),
    "csharp": frozenset({"using_directive"}),
    "kotlin": frozenset({"import_header"}),
    "swift": frozenset({"import_declaration"}),
    "rust": frozenset({"use_declaration"}),
    "go": frozenset({"import_spec"}),
    "objective_c": frozenset({"import_declaration"}),
}

#: Node types that imply `constructs` rather than `calls`.
CONSTRUCT_NODES: frozenset[str] = frozenset(
    {"object_creation_expression", "new_expression", "struct_expression"}
)

#: Call-expression node types shared across these grammars.
CALL_NODES: frozenset[str] = frozenset(
    {
        "call_expression",
        "method_invocation",
        "invocation_expression",
        "object_creation_expression",
        "new_expression",
        "macro_invocation",
    }
)

_PRIMITIVES = frozenset(
    {
        "int", "long", "short", "char", "bool", "float", "double", "void", "unsigned",
        "signed", "size_t", "auto", "string", "String", "str", "uint8_t", "uint16_t",
        "uint32_t", "uint64_t", "int8_t", "int16_t", "int32_t", "int64_t", "byte",
        "number", "boolean", "any", "object", "var", "let", "const", "static",
        "usize", "isize", "u8", "u16", "u32", "u64", "i8", "i16", "i32", "i64", "f32", "f64",
    }
)


@dataclass
class LanguageSpec:
    """Per-language node tables used by the shared traversal."""

    language: str
    grammar: str
    function_nodes: frozenset[str] = field(default_factory=frozenset)
    type_nodes: dict[str, str] = field(default_factory=dict)
    property_nodes: frozenset[str] = field(default_factory=frozenset)
    inherit_nodes: frozenset[str] = field(default_factory=frozenset)
    import_nodes: frozenset[str] = field(default_factory=frozenset)
    default_visibility: str | None = None
    test_name_markers: tuple[str, ...] = ("test", "tests", "spec")


def build_spec(language: str) -> LanguageSpec:
    return LanguageSpec(
        language=language,
        grammar={
            "c": "c",
            "cpp": "cpp",
            "java": "java",
            "csharp": "csharp",
            "kotlin": "kotlin",
            "swift": "swift",
            "rust": "rust",
            "go": "go",
            "objective_c": "objc",
        }.get(language, language),
        function_nodes=FUNCTION_NODES.get(language, frozenset()),
        type_nodes=TYPE_NODES.get(language, {}),
        property_nodes=PROPERTY_NODES.get(language, frozenset()),
        inherit_nodes=INHERIT_NODES.get(language, frozenset()),
        import_nodes=IMPORT_NODES.get(language, frozenset()),
        default_visibility="public" if language in {"java", "csharp", "kotlin", "swift"} else None,
        test_name_markers=("test",) if language in {"rust", "go"} else ("test", "tests", "spec"),
    )


def _text(source: bytes, node: Node | None) -> str:
    if node is None:
        return ""
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _text_before(source: bytes, node: Node, window: int = 400) -> str:
    start = max(0, node.start_byte - window)
    return source[start : node.start_byte].decode("utf-8", errors="replace")


def _is_declarator_blob(text: str) -> bool:
    """True when text is a C/C++ declarator rather than a bare identifier."""
    return bool(text) and ("(" in text or "::" in text or "[" in text)


def _last_segment(text: str) -> str:
    cleaned = text.strip().strip("()[]{}<>;,")
    for separator in ("::", "->", "."):
        if separator in cleaned:
            cleaned = cleaned.split(separator)[-1]
    return cleaned.strip()


def _qualifier(text: str) -> str | None:
    cleaned = text.strip().strip("()[]{}<>")
    for separator in ("::", "."):
        if separator in cleaned:
            head, _, tail = cleaned.rpartition(separator)
            if head and tail:
                return head
    return None


def _strip_comment_markers(text: str) -> str:
    for marker in ("/**", "*/", "//!", "//", "///", "#'", "*"):
        text = text.replace(marker, " ")
    return " ".join(text.split())


def _signature_line(source: bytes, node: Node) -> str | None:
    """First physical line of a declaration, trimmed to a readable signature."""
    if node.end_point[0] != node.start_point[0]:
        return None
    text = _text(source, node).strip()
    return text[:300] if text else None


class CLikeAdapter:
    """Shared traversal driven by a per-language :class:`LanguageSpec`."""

    resolves_imports = True

    def __init__(self, language: str) -> None:
        self.language = language
        self.spec = build_spec(language)

    def supports(self) -> bool:
        return True

    # ------------------------------------------------------------- parsing

    def parse(self, source: bytes, path: str) -> ParseResult:
        from ..engine import first_child_of_type, get_parser

        parser = get_parser(self.spec.grammar)
        tree = parser.parse(source)
        result = ParseResult(adapter=f"{self.language}-table")
        result.metadata["path"] = path
        self._visit(source, tree.root_node, result, parent=None, scope=[])
        self._classify_tests(result)
        return result

    def _loc(self, node: Node, path: str) -> SourceLocation:
        return SourceLocation(path=path, line=node.start_point[0], col=node.start_point[1])

    def _name_of(self, source: bytes, node: Node) -> str | None:
        from ..engine import first_child_of_type

        for field_name in ("name", "declarator", "alias", "pattern", "path"):
            child = node.child_by_field_name(field_name)
            if child is None:
                continue
            inner = first_child_of_type(
                child,
                "identifier",
                "field_identifier",
                "type_identifier",
                "constant",
                "property_identifier",
                "package_identifier",
                "simple_identifier",
                "type_identifier",
            )
            text = _text(source, inner or child)
            if text and text.isprintable() and len(text) < 200:
                if not _is_declarator_blob(text):
                    return text.strip()
        # Some grammars (Kotlin) expose the declared name only as a direct
        # child node rather than through a `name` field.
        for child in node.named_children:
            if child.type in {"simple_identifier", "identifier", "type_identifier"}:
                text = _text(source, child).strip()
                if text and text.isprintable() and len(text) < 200:
                    return text
        # C++ declarators wrap the name: `Widget::area() const` is a
        # qualified_identifier containing the real identifier `area`.
        from ..engine import descendants_of_type

        for descendant in descendants_of_type(node, "identifier", "field_identifier", "type_identifier"):
            text = _text(source, descendant).strip()
            if text and text.isprintable() and "::" not in text and "(" not in text:
                return text
        return None

    def _visit(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str]
    ) -> None:
        for child in node.named_children:
            self._visit_node(source, child, result, parent, scope)

    def _visit_node(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, scope: list[str]
    ) -> None:
        spec = self.spec
        path = result.metadata.get("path", "")
        node_type = node.type

        if node_type in spec.function_nodes:
            self._add_function(source, node, result, parent, scope, path)
            return

        if node_type in spec.type_nodes:
            self._add_type(source, node, result, parent, scope, path)
            return

        if node_type in spec.property_nodes:
            self._add_property(source, node, result, parent, scope, path)

        if node_type in spec.inherit_nodes and parent is not None:
            self._record_bases(source, node, result, parent, path)

        if node_type in spec.import_nodes:
            self._record_import(source, node, result, parent, path)
            return

        if node_type in CALL_NODES:
            self._record_call(source, node, result, parent, path)

        self._visit(source, node, result, parent, scope)

    # ------------------------------------------------------------- symbols

    def _doc_before(self, source: bytes, node: Node) -> str | None:
        previous = node.prev_named_sibling
        while previous is not None and previous.type in {
            "comment",
            "line_comment",
            "block_comment",
            "doc_comment",
        }:
            text = _text(source, previous).strip()
            if text:
                return _strip_comment_markers(text)
            previous = previous.prev_named_sibling
        return None

    def _visibility(self, source: bytes, node: Node) -> str | None:
        if self.spec.default_visibility is None:
            return None
        header = _text_before(source, node)
        for keyword in ("private", "protected", "internal", "open", "public"):
            if re.search(rf"\b{keyword}\b", header):
                return keyword if keyword in {"private", "protected", "public"} else "public"
        return self.spec.default_visibility

    def _add_function(
        self,
        source: bytes,
        node: Node,
        result: ParseResult,
        parent: int | None,
        scope: list[str],
        path: str,
    ) -> None:
        name = self._name_of(source, node)
        if not name:
            self._visit(source, node, result, parent, scope)
            return
        kind = "constructor" if "constructor" in node.type else ("method" if parent is not None else "function")
        qualified = ".".join([*scope, name])
        # Rust `impl Trait for Type` and a `trait` declaration can produce the
        # same qualified name; the first definition wins so one entity is not
        # indexed twice under two indices.
        if qualified in result.metadata.setdefault("seen", {}):
            return
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
                parent_index=parent,
                signature=_signature_line(source, node),
                docstring=self._doc_before(source, node),
                visibility=self._visibility(source, node),
            )
        )
        result.metadata["seen"][qualified] = index
        result.exports.append(
            ExportRecord(
                name=name, local_name=name, source_symbol_index=index, location=self._loc(node, path)
            )
        )
        self._visit(source, node, result, index, [*scope, name])

    def _add_type(
        self,
        source: bytes,
        node: Node,
        result: ParseResult,
        parent: int | None,
        scope: list[str],
        path: str,
    ) -> None:
        name = self._name_of(source, node)
        kind = self.spec.type_nodes.get(node.type, "class")
        if not name:
            self._visit(source, node, result, parent, scope)
            return
        qualified = ".".join([*scope, name])
        if qualified in result.metadata.setdefault("seen", {}):
            return
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
                parent_index=parent,
                signature=_signature_line(source, node),
                docstring=self._doc_before(source, node),
                visibility=self._visibility(source, node),
            )
        )
        result.metadata["seen"][qualified] = index
        result.exports.append(
            ExportRecord(
                name=name, local_name=name, source_symbol_index=index, location=self._loc(node, path)
            )
        )
        self._visit(source, node, result, index, [*scope, name])

    def _add_property(
        self,
        source: bytes,
        node: Node,
        result: ParseResult,
        parent: int | None,
        scope: list[str],
        path: str,
    ) -> None:
        from ..engine import descendants_of_type, first_child_of_type

        if self.language == "rust":
            name = self._name_of(source, node)
            if name:
                index = len(result.symbols)
                result.symbols.append(
                    ParsedSymbol(
                        kind="constant",
                        name=name,
                        qualified_name=".".join([*scope, name]),
                        start_byte=node.start_byte,
                        end_byte=node.end_byte,
                        start_line=node.start_point[0],
                        end_line=node.end_point[0],
                        parent_index=parent,
                        signature=_signature_line(source, node),
                    )
                )
                result.exports.append(
                    ExportRecord(
                        name=name,
                        local_name=name,
                        source_symbol_index=index,
                        location=self._loc(node, path),
                    )
                )
            return

        for declarator in descendants_of_type(node, "variable_declarator"):
            identifier = first_child_of_type(declarator, "identifier", "field_identifier")
            if identifier is None:
                continue
            name = _text(source, identifier)
            if not name:
                continue
            index = len(result.symbols)
            result.symbols.append(
                ParsedSymbol(
                    kind="field" if parent is not None else "variable",
                    name=name,
                    qualified_name=".".join([*scope, name]),
                    start_byte=declarator.start_byte,
                    end_byte=declarator.end_byte,
                    start_line=declarator.start_point[0],
                    end_line=declarator.end_point[0],
                    parent_index=parent,
                    signature=_signature_line(source, node),
                    visibility=self._visibility(source, node),
                )
            )
            result.exports.append(
                ExportRecord(
                    name=name, local_name=name, source_symbol_index=index, location=self._loc(node, path)
                )
            )
            type_node = declarator.child_by_field_name("type")
            if type_node is not None:
                self._record_type_use(source, type_node, result, index, path)

    # --------------------------------------------------------- references

    def _record_bases(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, path: str
    ) -> None:
        from ..engine import descendants_of_type

        for current in descendants_of_type(
            node,
            "type_identifier",
            "identifier",
            "user_type",
            "generic_type",
            "scoped_type_identifier",
            "name",
        ):
            text = _text(source, current)
            if not text or not text.isprintable():
                continue
            edge = EdgeType.IMPLEMENTS if self.language in {"swift", "kotlin"} else EdgeType.INHERITS
            result.references.append(
                Reference(
                    name=_last_segment(text),
                    edge_type=edge,
                    source_symbol_index=parent,
                    location=self._loc(current, path),
                    provenance=Provenance.EXTRACTED,
                    qualifier=_qualifier(text),
                )
            )

    def _record_type_use(
        self, source: bytes, node: Node, result: ParseResult, index: int, path: str
    ) -> None:
        from ..engine import descendants_of_type

        for current in descendants_of_type(
            node, "type_identifier", "user_type", "generic_type", "predefined_type"
        ):
            text = _text(source, current)
            if not text or text in _PRIMITIVES or not text.isprintable():
                continue
            result.references.append(
                Reference(
                    name=_last_segment(text),
                    edge_type=EdgeType.ACCEPTS_TYPE,
                    source_symbol_index=index,
                    location=self._loc(current, path),
                    provenance=Provenance.EXTRACTED,
                    qualifier=_qualifier(text),
                )
            )

    def _record_import(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, path: str
    ) -> None:
        from ..engine import descendants_of_type

        module = self._module_of(source, node)
        if not module:
            return
        aliases = self._aliases(source, node)
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
                    name=_last_segment(original),
                    edge_type=EdgeType.IMPORTS,
                    source_symbol_index=parent,
                    location=self._loc(node, path),
                    provenance=Provenance.EXTRACTED,
                    qualifier=module,
                    metadata={"alias": alias},
                )
            )

    def _module_of(self, source: bytes, node: Node) -> str:
        from ..engine import descendants_of_type

        if node.type in {"preproc_include"}:
            target = node.child_by_field_name("path")
            text = _text(source, target).strip().strip('"<>')
            return text

        if node.type == "use_declaration":
            argument = node.child_by_field_name("argument")
            text = _text(source, argument).strip() if argument is not None else _text(source, node)
            text = re.sub(r"^use\s+", "", text.strip().rstrip(";"))
            return _first_use_segment(text)

        if node.type == "import_spec":
            path_node = node.child_by_field_name("path")
            text = _text(source, path_node).strip().strip('"') if path_node is not None else ""
            return text

        # Java/Kotlin/C#/Swift/ObjC import declarations.
        text = _text(source, node).strip()
        text = re.sub(
            r"^(import|using|package|#?import)\s+", "", text.strip().rstrip(";")
        )
        text = text.split(" as ")[0].strip().rstrip(";").strip()
        text = text.strip('"')
        if text and (" " not in text or "." in text):
            return text.split()[0]
        for current in descendants_of_type(
            node, "scoped_identifier", "identifier", "dotted_name", "string_literal"
        ):
            candidate = _text(source, current).strip()
            if candidate:
                return candidate
        return ""

    def _aliases(self, source: bytes, node: Node) -> dict[str, str]:
        from ..engine import descendants_of_type

        aliases: dict[str, str] = {}
        for current in descendants_of_type(
            node, "use_as_clause", "alias_declaration", "import_alias", "import_spec"
        ):
            if current.type == "import_spec":
                name_node = current.child_by_field_name("name")
                alias_node = current.child_by_field_name("alias")
                if name_node is not None and alias_node is not None:
                    original = _text(source, name_node)
                    alias = _text(source, alias_node)
                    if alias:
                        aliases[alias] = original
                continue
            children = current.named_children
            if len(children) >= 2:
                original = _text(source, children[0]).strip()
                alias = _text(source, children[1]).strip()
                if alias:
                    aliases[alias] = original
        return aliases

    def _record_call(
        self, source: bytes, node: Node, result: ParseResult, parent: int | None, path: str
    ) -> None:
        from ..engine import first_child_of_type, walk

        function = node.child_by_field_name("function") or node.child_by_field_name("name")
        if function is None:
            function = first_child_of_type(
                node,
                "identifier",
                "field_identifier",
                "scoped_identifier",
                "user_type",
                "member_expression",
                "selector_expression",
            )
        if function is None:
            return
        text = _text(source, function).strip()
        if not text or not text.isprintable():
            return
        edge = EdgeType.CONSTRUCTS if node.type in CONSTRUCT_NODES else EdgeType.CALLS
        result.references.append(
            Reference(
                name=_last_segment(text),
                edge_type=edge,
                source_symbol_index=parent,
                location=self._loc(node, path),
                provenance=Provenance.EXTRACTED,
                qualifier=_qualifier(text),
            )
        )
        arguments = node.child_by_field_name("arguments")
        if arguments is None:
            return
        for current in walk(arguments):
            if current.type not in CALL_NODES:
                continue
            nested = current.child_by_field_name("function") or current.child_by_field_name("name")
            if nested is None:
                continue
            nested_text = _text(source, nested).strip()
            if not nested_text:
                continue
            result.references.append(
                Reference(
                    name=_last_segment(nested_text),
                    edge_type=EdgeType.CONSTRUCTS
                    if current.type in CONSTRUCT_NODES
                    else EdgeType.CALLS,
                    source_symbol_index=parent,
                    location=self._loc(current, path),
                    provenance=Provenance.EXTRACTED,
                    qualifier=_qualifier(nested_text),
                )
            )

    def _classify_tests(self, result: ParseResult) -> None:
        for symbol in result.symbols:
            tail = symbol.qualified_name.rsplit(".", 1)[-1]
            lowered = tail.lower()
            if (
                lowered.startswith("test")
                or lowered.endswith("test")
                or lowered.endswith("tests")
                or "_test" in lowered
                or lowered.startswith("it_")
            ):
                symbol.metadata["is_test"] = True


def _first_use_segment(text: str) -> str:
    """Take the first segment of a Rust use path, ignoring braces/asterisks."""
    cleaned = text.strip().strip("{}").strip()
    if cleaned.startswith("*"):
        cleaned = cleaned[1:].lstrip()
    cleaned = cleaned.split("::")[0]
    return cleaned.strip()


#: Languages that get a table-driven adapter. Each ships a strong adapter in
#: the documented first-implementation target.
TABLE_ADAPTER_LANGUAGES: tuple[str, ...] = (
    "c",
    "cpp",
    "csharp",
    "go",
    "java",
    "kotlin",
    "rust",
    "swift",
)


def load_c_like_adapters() -> dict[str, CLikeAdapter]:
    """Instantiate the table-driven adapter for every supported language."""
    return {language: CLikeAdapter(language) for language in TABLE_ADAPTER_LANGUAGES}