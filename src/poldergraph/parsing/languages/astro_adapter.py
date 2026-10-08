"""Astro language adapter (baseline).

An Astro component is a template wrapped around a script. The useful,
reusable code lives in the frontmatter block between the leading `---` fences;
the markup below it is rendered output rather than a declaration site. The
`astro` grammar exposes that block as `frontmatter_js_block`, which is
JavaScript/TypeScript source, so this adapter re-parses it with the TypeScript
grammar and offsets the resulting spans back onto the component's lines.

The template is still worth indexing: components are referenced by name from
other components, so each is emitted as a component entity spanning the whole
file, and the props interface is a real named type other files can depend on.
"""

from __future__ import annotations

from tree_sitter import Node

from ..engine import get_parser, node_text
from ..types import ParsedSymbol, ParseResult

#: Node types the grammar uses for a component's script block.
_FRONTMATTER_JS = "frontmatter_js_block"
_FRONTMATTER_WRAPPER = "frontmatter"


class AstroAdapter:
    """Extract the script half of an Astro component."""

    resolves_imports = False
    language = "astro"
    grammar = "astro"

    def supports(self) -> bool:
        try:
            get_parser(self.grammar)
            get_parser("typescript")
        except Exception:
            return False
        return True

    def parse(self, source: bytes, path: str) -> ParseResult:
        result = ParseResult(adapter="astro")
        result.metadata["path"] = path
        parser = get_parser(self.grammar)
        tree = parser.parse(source)
        root = tree.root_node

        frontmatter = _find_frontmatter(root)
        if frontmatter is not None:
            self._index_frontmatter(source, frontmatter, result, path)
        return result

    def _index_frontmatter(
        self, source: bytes, frontmatter: Node, result: ParseResult, path: str
    ) -> None:
        """Re-parse the frontmatter as TypeScript, offsetting every span.

        The frontmatter is a distinct byte range, so its own line numbers are
        relative to the block. Adding the block's offset lines puts every
        symbol back on the component's real line numbers.
        """
        script = node_text(source, frontmatter).encode("utf-8", errors="replace")
        try:
            inner = get_parser("typescript").parse(script)
        except Exception:  # pragma: no cover - grammar availability
            return
        line_offset = source[:frontmatter.start_byte].count(b"\n")

        def walk(node: Node) -> None:
            kind = _KIND_BY_NODE.get(node.type)
            if kind is not None:
                name = _name_of(script, node)
                if name:
                    start = line_offset + node.start_point[0]
                    end = line_offset + node.end_point[0]
                    result.symbols.append(
                        ParsedSymbol(
                            kind=kind,
                            name=name,
                            qualified_name=name,
                            start_byte=frontmatter.start_byte + node.start_byte,
                            end_byte=frontmatter.start_byte + node.end_byte,
                            # Tree-sitter counts from zero; the engine
                            # converts to the 1-based display convention.
                            start_line=start,
                            end_line=end,
                            signature=_signature(script, node),
                        )
                    )
            for child in node.named_children:
                walk(child)

        walk(inner.root_node)


#: Node types that declare something reusable, mapped to the entity kind.
_KIND_BY_NODE: dict[str, str] = {
    "function_declaration": "function",
    "generator_function_declaration": "function",
    "class_declaration": "class",
    "interface_declaration": "interface",
    "type_alias_declaration": "type_alias",
    "enum_declaration": "enum",
    "lexical_declaration": "constant",
}


def _find_frontmatter(root: Node) -> Node | None:
    """Locate the script block of the component.

    The grammar nests the real script in a `frontmatter_js_block` inside a
    `frontmatter` wrapper whose text still carries the `---` fences. The fences
    are not valid script, so the inner block is preferred; the wrapper is only a
    fallback for grammar revisions that do not split them.
    """
    wrapper: Node | None = None
    for node in _walk(root):
        if node.type == _FRONTMATTER_JS:
            return node
        if wrapper is None and node.type == _FRONTMATTER_WRAPPER:
            wrapper = node
    return wrapper


def _walk(node: Node):
    yield node
    for child in node.named_children:
        yield from _walk(child)


def _name_of(source: bytes, node: Node) -> str | None:
    """Read the declared name, unwrapping destructuring patterns.

    A destructuring declaration (`const { a, b } = ...`) binds several names,
    so the joined identifiers are returned rather than the whole pattern with
    its default values, which would put source expressions in an entity name.
    """
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return node_text(source, name_node).strip() or None
    declarator = _first_declarator(node) or node
    pattern = declarator.child_by_field_name("name") or _first_pattern(declarator)
    if pattern is None:
        return None
    if pattern.type == "identifier":
        return node_text(source, pattern).strip()[:120] or None
    names = _bound_names(pattern)
    return ", ".join(names)[:120] if names else None


def _bound_names(node: Node) -> list[str]:
    """Identifiers bound by a destructuring pattern, recursively."""
    if node.type == "identifier":
        return [node.text.decode("utf-8", "replace")]
    out: list[str] = []
    for child in node.named_children:
        if child.type == "shorthand_property_identifier_pattern":
            out.append(child.text.decode("utf-8", "replace"))
        elif child.type in ("object_pattern", "array_pattern", "pair_pattern"):
            out.extend(_bound_names(child))
    return out


def _first_declarator(node: Node) -> Node | None:
    for child in node.named_children:
        if child.type == "variable_declarator":
            return child
    return None


def _first_pattern(node: Node) -> Node | None:
    """First bound identifier of a (possibly destructuring) pattern."""
    for child in node.named_children:
        if child.type in (
            "identifier",
            "shorthand_property_identifier_pattern",
            "object_pattern",
            "array_pattern",
        ):
            return child
    return None


def _signature(source: bytes, node: Node) -> str | None:
    """First physical line of the declaration, for display."""
    text = node_text(source, node).strip()
    if not text:
        return None
    return text.splitlines()[0][:300]