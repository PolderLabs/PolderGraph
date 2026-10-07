"""Turn parsed files into canonical entities and structural relationships.

This is where syntax-tree facts become graph nodes with stable IDs, and where
resolution decides between a confident edge and an honest ambiguity.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..discovery.scanner import DiscoveredFile
from ..models.edge import Edge, EdgeType, Provenance, SourceLocation
from ..models.entity import Entity, EntityKind, content_hash, normalize_path, stable_id
from ..parsing.engine import ParseEngine
from ..parsing.resolver import FileIndex, Resolver
from ..parsing.types import ParseResult


@dataclass
class FileEntities:
    """Everything produced by indexing one file."""

    path: str
    root_id: str
    entities: list[Entity] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    file_index: FileIndex | None = None
    parse_status: str = "ok"
    error_count: int = 0
    source_bytes: bytes | None = None
    module_doc: str | None = None

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.source_bytes or b"").hexdigest()


class EntityBuilder:
    """Build entities and edges for a workspace, file by file."""

    def __init__(self, *, root_id: str, engine: ParseEngine | None = None) -> None:
        self.root_id = root_id
        self.engine = engine or ParseEngine()
        self.resolver = Resolver()
        self._file_ids: dict[str, str] = {}

    # ------------------------------------------------------------- building

    def build_file(
        self,
        discovered: DiscoveredFile,
        *,
        source: bytes | None = None,
        include_generated: bool = False,
    ) -> FileEntities:
        """Parse one discovered file into entities and unresolved references."""
        rel = normalize_path(discovered.path)
        result = FileEntities(path=rel, root_id=self.root_id)

        if source is None:
            try:
                source = discovered.abs_path.read_bytes()
            except OSError:
                result.parse_status = "unreadable"
                return result
        result.source_bytes = source

        language = discovered.language
        if language == "pdf":
            return self._build_pdf(discovered, result)

        if language == "text" or (language is None and not discovered.is_media):
            result = self._build_text(discovered, result, source)
        elif discovered.is_media:
            result = self._build_media(discovered, result)
        else:
            parsed = self.engine.parse(source, language, rel)
            result.parse_status = "parse_error" if parsed.has_errors else "ok"
            result.error_count = parsed.error_count
            self._entities_from_parse(discovered, result, parsed, language)

        return result

    # ------------------------------------------------------ entity creation

    def _file_entity(self, discovered: DiscoveredFile, result: FileEntities, kind: str, name: str) -> Entity:
        rel = normalize_path(discovered.path)
        entity_id = stable_id(
            root_id=self.root_id,
            kind=kind,
            language=discovered.language,
            path=rel,
            qualified_name=name,
        )
        entity = Entity(
            id=entity_id,
            root_id=self.root_id,
            kind=kind,
            name=name,
            qualified_name=name,
            path=rel,
            language=discovered.language,
            content_hash=result.content_hash,
            is_generated=discovered.is_generated,
            metadata={"size": discovered.size},
        )
        result.entities.append(entity)
        self._file_ids[rel] = entity_id
        return entity

    def _entities_from_parse(
        self,
        discovered: DiscoveredFile,
        result: FileEntities,
        parsed: ParseResult,
        language: str | None,
    ) -> None:
        rel = normalize_path(discovered.path)
        name = _base_name(rel)
        if language == "markdown":
            file_kind = EntityKind.DOCUMENT.value
        else:
            file_kind = EntityKind.FILE.value

        file_entity = self._file_entity(discovered, result, file_kind, name)
        result.module_doc = _extract_module_doc(parsed, result.source_bytes or b"")
        if result.module_doc:
            file_entity.docstring = result.module_doc[:1000]

        symbol_to_entity: dict[int, str] = {}
        # Adapters address declarations by their position in `parsed.symbols`,
        # so the entity map must be keyed the same way. Keying by byte offset
        # would silently misattach every reference to the file entity.
        for symbol_index, symbol in enumerate(parsed.symbols):
            kind = symbol.kind
            if kind == "section":
                continue
            if symbol.metadata.get("is_test") and kind in {"function", "method"}:
                kind = EntityKind.TEST.value

            qualified = symbol.qualified_name
            entity_id = stable_id(
                root_id=self.root_id,
                kind=kind,
                language=language,
                path=rel,
                qualified_name=qualified,
                # Overloads in one file share a name; the byte offset separates them.
                discriminator=str(symbol.start_byte),
            )
            entity = Entity(
                id=entity_id,
                root_id=self.root_id,
                kind=kind,
                name=symbol.name,
                qualified_name=qualified,
                path=rel,
                language=language,
                start_byte=symbol.start_byte,
                end_byte=symbol.end_byte,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
                signature=symbol.signature,
                docstring=symbol.docstring,
                visibility=symbol.visibility,
                content_hash=result.content_hash,
                is_generated=discovered.is_generated,
                metadata={"is_test": bool(symbol.metadata.get("is_test"))},
            )
            result.entities.append(entity)
            symbol_to_entity[symbol_index] = entity_id

            # Ownership edges link a symbol to its parent declaration.
            if symbol.parent_index is not None:
                parent_id = symbol_to_entity.get(symbol.parent_index)
                if parent_id and parent_id != entity_id:
                    entity.parent_id = parent_id
                    result.edges.append(
                        Edge(
                            source_id=parent_id,
                            target_id=entity_id,
                            type=EdgeType.CONTAINS,
                            provenance=Provenance.EXTRACTED,
                            source_location=SourceLocation(path=rel, line=symbol.start_line),
                        )
                    )

            # `defines` records that the file declares this symbol.
            if entity_id != file_entity.id:
                result.edges.append(
                    Edge(
                        source_id=file_entity.id,
                        target_id=entity_id,
                        type=EdgeType.DEFINES,
                        provenance=Provenance.EXTRACTED,
                        source_location=SourceLocation(path=rel, line=symbol.start_line),
                    )
                )

        # Markdown sections become their own entities under the document.
        for symbol in parsed.symbols:
            if symbol.kind != "section":
                continue
            entity_id = stable_id(
                root_id=self.root_id,
                kind=EntityKind.SECTION.value,
                language="text",
                path=rel,
                qualified_name=symbol.qualified_name,
                discriminator=str(symbol.start_byte),
            )
            entity = Entity(
                id=entity_id,
                root_id=self.root_id,
                kind=EntityKind.SECTION.value,
                name=symbol.name,
                qualified_name=symbol.qualified_name,
                path=rel,
                language="text",
                start_line=symbol.start_line,
                end_line=symbol.end_line,
                signature=symbol.signature,
                docstring=symbol.docstring,
                parent_id=file_entity.id,
                content_hash=result.content_hash,
                metadata={"page": symbol.metadata.get("page")} if symbol.metadata.get("page") else {},
            )
            result.entities.append(entity)
            result.edges.append(
                Edge(
                    source_id=file_entity.id,
                    target_id=entity_id,
                    type=EdgeType.CONTAINS,
                    provenance=Provenance.EXTRACTED,
                    source_location=SourceLocation(path=rel, line=symbol.start_line),
                )
            )

        result.file_index = FileIndex(
            root_id=self.root_id,
            path=rel,
            language=language,
            symbol_ids={
                index: symbol_to_entity.get(index, file_entity.id)
                for index in range(len(parsed.symbols))
            },
            import_aliases=_import_bindings(parsed.imports),
        )
        for symbol_index, symbol in enumerate(parsed.symbols):
            entity_id = symbol_to_entity.get(symbol_index)
            if entity_id:
                result.file_index.symbols[symbol.qualified_name] = entity_id
                leaf = symbol.qualified_name.rsplit(".", 1)[-1]
                result.file_index.by_name.setdefault(leaf, []).append(entity_id)

        result.file_index.module_paths = {record.module: rel for record in parsed.imports}
        # References are resolved after every file is registered.
        result.metadata_references = parsed.references  # type: ignore[attr-defined]
        result.metadata_exports = [e.name for e in parsed.exports]  # type: ignore[attr-defined]
        result.symbol_to_entity = symbol_to_entity  # type: ignore[attr-defined]
        result.file_entity_id = file_entity.id  # type: ignore[attr-defined]

    def _build_text(
        self, discovered: DiscoveredFile, result: FileEntities, source: bytes
    ) -> FileEntities:
        rel = normalize_path(discovered.path)
        file_entity = self._file_entity(discovered, result, EntityKind.DOCUMENT.value, _base_name(rel))
        text = source.decode("utf-8", errors="replace")
        file_entity.docstring = text[:1000]
        result.module_doc = text[:1000]
        return result

    def _build_media(self, discovered: DiscoveredFile, result: FileEntities) -> FileEntities:
        from ..discovery.languages import is_audio_path, is_image_path, is_video_path

        rel = normalize_path(discovered.path)
        if is_image_path(rel):
            kind = EntityKind.IMAGE.value
        elif is_audio_path(rel):
            kind = EntityKind.AUDIO_SEGMENT.value
        elif is_video_path(rel):
            kind = EntityKind.VIDEO_SEGMENT.value
        else:
            kind = EntityKind.FILE.value

        entity = self._file_entity(discovered, result, kind, _base_name(rel))
        if is_image_path(rel):
            from ..embedding.multimodal import image_dimensions

            dimensions = image_dimensions(discovered.abs_path)
            if dimensions:
                entity.metadata["width"], entity.metadata["height"] = dimensions
        else:
            from ..embedding.multimodal import probe_media, sample_video_times, segment_media

            info = probe_media(discovered.abs_path)
            if info is not None:
                entity.metadata["duration"] = info.duration
                segments = (
                    sample_video_times(info.duration)
                    if info.kind == "video"
                    else segment_media(info.duration)
                )
                for segment in segments:
                    seg_id = stable_id(
                        root_id=self.root_id,
                        kind=kind,
                        language=None,
                        path=rel,
                        qualified_name=f"{_base_name(rel)}#{segment.ordinal}",
                    )
                    seg = Entity(
                        id=seg_id,
                        root_id=self.root_id,
                        kind=kind,
                        name=f"{_base_name(rel)}#{segment.ordinal}",
                        qualified_name=f"{_base_name(rel)}#{segment.ordinal}",
                        path=rel,
                        parent_id=entity.id,
                        metadata={
                            "ordinal": segment.ordinal,
                            "start_time": segment.start,
                            "end_time": segment.end,
                        },
                    )
                    result.entities.append(seg)
                    result.edges.append(
                        Edge(
                            source_id=entity.id,
                            target_id=seg_id,
                            type=EdgeType.CONTAINS,
                            provenance=Provenance.EXTRACTED,
                        )
                    )
        return result

    def _build_pdf(self, discovered: DiscoveredFile, result: FileEntities) -> FileEntities:
        from ..parsing.languages.pdf_adapter import PdfAdapter

        rel = normalize_path(discovered.path)
        adapter = PdfAdapter()
        parsed = adapter.parse_file(discovered.abs_path, rel)
        result.error_count = parsed.error_count
        result.parse_status = "ok" if not parsed.metadata.get("error") else "partial"
        self._entities_from_parse(discovered, result, parsed, "text")
        return result

    # ---------------------------------------------------------- resolution

    def register(self, built: FileEntities) -> None:
        """Register a built file so later files can resolve against it."""
        if built.file_index is not None:
            self.resolver.register_file(built.file_index)
            for module in built.file_index.module_paths:
                self.resolver.index_module_path(module, built.path)
            # Map this file's own dotted module name onto itself so imports of
            # `pkg.models` reach `pkg/models.py`.
            for module in _declared_modules(built.path):
                self.resolver.index_module_path(module, built.path)

    def register_all(self, built_files: list[FileEntities]) -> None:
        """Register every built file before any resolution runs."""
        for built in built_files:
            self.register(built)

    def resolve_all(self, built_files: list[FileEntities]) -> None:
        """Resolve references for every built file once all are registered."""
        for built in built_files:
            references = getattr(built, "metadata_references", [])
            index = built.file_index
            if index is None:
                continue
            for reference in references:
                resolved = self.resolver.resolve(index, reference)
                if resolved is None:
                    continue
                edge = resolved.edge
                if edge.metadata.get("unresolved"):
                    self._record_unresolved(built, reference, resolved.candidates)
                    continue
                if edge.provenance == Provenance.AMBIGUOUS:
                    self._record_unresolved(built, reference, resolved.candidates)
                    continue
                built.edges.append(edge)

    def _record_unresolved(self, built: FileEntities, reference: Any, candidates: list[str]) -> None:
        ref_id = "unres:" + hashlib.sha256(
            f"{built.path}:{reference.location.line}:{reference.name}:{reference.edge_type}".encode()
        ).hexdigest()[:24]
        symbol_index = reference.source_symbol_index
        source_id = (built.file_index.symbol_ids if built.file_index else {}).get(
            symbol_index, getattr(built, "file_entity_id", "")
        )
        if not source_id:
            return
        built.unresolved_refs = getattr(built, "unresolved_refs", [])  # type: ignore[attr-defined]
        built.unresolved_refs.append(  # type: ignore[attr-defined]
            {
                "id": ref_id,
                "source_id": source_id,
                "name": reference.name,
                "path": built.path,
                "line": reference.location.line,
                "edge_type": reference.edge_type,
                "resolver": "cross_file",
                "candidates": candidates,
                "root_id": self.root_id,
            }
        )


def _import_bindings(imports: list[Any]) -> dict[str, str]:
    """Build local-name -> module-path bindings for every import.

    An adapter may only report the module; the local names it introduces are
    still resolvable, so derive them from the trailing segment.
    """
    bindings: dict[str, str] = {}
    for record in imports:
        module = record.module
        if not module:
            continue
        for alias in record.aliases or {}:
            bindings[alias] = module
        leaf = module.rsplit(".", 1)[-1].rsplit("/", 1)[-1]
        if leaf and leaf not in {"*", "default"}:
            bindings.setdefault(leaf, module)
    return bindings


def _declared_modules(path: str) -> list[str]:
    """Dotted module names a file can be imported as.

    A file is reachable both by its own stem (`models`) and by its full dotted
    path (`pkg.models`), because either spelling appears in real imports.
    """
    if path.endswith("/__init__.py") or path.endswith("\\__init__.py"):
        prefix = path.rsplit("/", 1)[0].replace("/", ".")
        return [prefix] if prefix else []
    stem_path = path.rsplit(".", 1)[0] if "." in path else path
    dotted = stem_path.replace("/", ".")
    out = [dotted]
    leaf = dotted.rsplit(".", 1)[-1]
    if leaf != dotted:
        out.append(leaf)
    return out


def _base_name(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    return name.rsplit(".", 1)[0] if "." in name else name


def _extract_module_doc(parsed: ParseResult, source: bytes) -> str | None:
    """Pull a leading module-level comment/docstring for file-level context."""
    if parsed.adapter in {"python", "markdown"}:
        for symbol in parsed.symbols:
            if symbol.kind in {"class", "function"} and symbol.parent_index is None:
                break
    # Cheap textual scan is acceptable here: this is documentation, not structure.
    head = source[:2000].decode("utf-8", errors="replace")
    lines = [line.strip() for line in head.splitlines()]
    if not lines:
        return None
    first = lines[0]
    for quote in ('"""', "'''"):
        if first.startswith(quote):
            return first.strip(quote).strip() or None
    if first.startswith("//") or first.startswith("#") or first.startswith("/*"):
        collected = [first.lstrip("/*# ").strip()]
        for line in lines[1:6]:
            if line.startswith("//") or line.startswith("#") or line.startswith("*") or line.startswith("/*"):
                collected.append(line.lstrip("/*#* ").strip())
            else:
                break
        text = " ".join(part for part in collected if part).strip()
        return text or None
    return None