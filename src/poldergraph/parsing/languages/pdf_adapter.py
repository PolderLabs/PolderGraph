"""PDF text extraction with page metadata.

A PDF search hit must preserve its page number so the reader can jump to it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..types import ParseResult, ParsedSymbol


@dataclass
class PdfPage:
    number: int
    text: str
    image_count: int = 0


@dataclass
class PdfDocument:
    pages: list[PdfPage] = field(default_factory=list)
    error: str | None = None

    @property
    def text(self) -> str:
        return "\n\n".join(page.text for page in self.pages if page.text)


def extract_pdf(path: Path, *, max_pages: int = 2000) -> PdfDocument:
    """Extract per-page text using pypdf.

    Extraction failure returns an error rather than raising: a PDF that cannot
    be parsed is still recorded as a file with no sections.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return PdfDocument(error="pypdf not installed")

    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        return PdfDocument(error=f"cannot open PDF: {exc}")

    document = PdfDocument()
    try:
        for index, page in enumerate(reader.pages[:max_pages]):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            image_count = 0
            try:
                image_count = len(page.images)
            except Exception:
                image_count = 0
            document.pages.append(
                PdfPage(number=index + 1, text=text.strip(), image_count=image_count)
            )
    except Exception as exc:
        document.error = f"page extraction failed: {exc}"
    return document


class PdfAdapter:
    """Turn extracted PDF pages into document/section entities."""

    language = "pdf"
    resolves_imports = False

    def supports(self) -> bool:
        return True

    def parse_file(self, path: Path, rel_path: str) -> ParseResult:
        result = ParseResult(adapter="pdf")
        result.metadata["path"] = rel_path
        document = extract_pdf(path)
        if document.error:
            result.metadata["error"] = document.error
            return result
        result.metadata["page_count"] = len(document.pages)
        for page in document.pages:
            if not page.text:
                continue
            title = _first_heading(page.text) or f"Page {page.number}"
            result.symbols.append(
                ParsedSymbol(
                    kind="section",
                    name=title[:200],
                    qualified_name=f"page:{page.number}",
                    start_line=None,
                    end_line=None,
                    signature=f"Page {page.number}",
                    docstring=page.text[:600],
                    metadata={"page": page.number, "image_count": page.image_count},
                )
            )
        return result


def _first_heading(text: str) -> str | None:
    """Best-effort section title from the first short line of a page."""
    for line in text.splitlines()[:6]:
        stripped = line.strip()
        if 2 <= len(stripped) <= 90 and not stripped.endswith("."):
            return stripped
    return None