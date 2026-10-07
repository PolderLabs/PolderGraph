"""Markdown and plain-text documentation adapter.

Documentation is structured into document + heading-ancestry sections so a
search hit can name the exact section it came from.
"""

from __future__ import annotations

from ..engine import get_parser, node_text
from ..types import ParseResult, ParsedSymbol


class MarkdownAdapter:
    """Extract documents and heading-ancestry sections from Markdown."""

    language = "markdown"
    resolves_imports = False

    def supports(self) -> bool:
        return True

    def parse(self, source: bytes, path: str) -> ParseResult:
        result = ParseResult(adapter="markdown")
        result.metadata["path"] = path
        parser = get_parser("markdown")
        tree = parser.parse(source)
        root = tree.root_node

        for node in _walk(root):
            if node.type != "section":
                continue
            heading = _first_heading(node)
            if heading is None:
                continue
            title = node_text(source, heading).lstrip("#").strip()
            if not title:
                continue
            body = _section_body(source, node)
            # The nested sections of a parent carry their own heading text; the
            # parent's own text is everything before its first child section.
            index = len(result.symbols)
            result.symbols.append(
                ParsedSymbol(
                    kind="section",
                    name=title[:200],
                    qualified_name=title[:200],
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    start_line=node.start_point[0],
                    end_line=node.end_point[0],
                    signature=f"# {title[:160]}",
                    docstring=body[:600] if body else None,
                )
            )
            result.metadata.setdefault("sections", {})[str(index)] = {
                "body": body,
                "heading_line": heading.start_point[0],
            }
        return result


def _walk(node):
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.named_children))


def _first_heading(section):
    for child in section.named_children:
        if child.type == "atx_heading":
            return child
        if child.type == "setext_heading":
            return child
        if child.type == "section":
            break
    return None


def _section_body(source: bytes, section) -> str:
    """Text owned by this section, excluding nested subsections."""
    parts: list[str] = []
    for child in section.named_children:
        if child.type == "section":
            break
        parts.append(node_text(source, child))
    return "\n".join(p for p in parts if p).strip()