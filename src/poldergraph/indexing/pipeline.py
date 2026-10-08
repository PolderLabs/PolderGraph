"""Indexing pipeline: persist entities, edges, FTS rows and embeddings.

Restart safety: each file batch is committed in one transaction, so an
interrupted run leaves the graph consistent rather than half-written.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config.models import Config
from ..discovery.scanner import DiscoveredFile, Discovery
from ..embedding.protocol import DOCUMENT_TASK, EmbeddingBackend
from ..embedding.representation import (
    REPRESENTATION_VERSION,
    normalize_representation,
    representation_for,
)
from ..models.entity import Entity, semantic_hash
from ..storage.repository import Repository
from ..storage.schema import INDEX_FORMAT_VERSION
from ..storage.sqlite import record_change_event, set_meta, writer_transaction
from ..storage.vectors import VectorRecord, create_vector_store, embedding_id_for
from ..workspace import Workspace
from .builder import EntityBuilder, FileEntities

ProgressFn = Callable[[str, int, int], None]


@dataclass
class IndexStats:
    """Counters reported by `init` and `update`."""

    files_seen: int = 0
    files_indexed: int = 0
    files_skipped: int = 0
    files_removed: int = 0
    entities_written: int = 0
    edges_written: int = 0
    entities_removed: int = 0
    embeddings_written: int = 0
    embeddings_reused: int = 0
    parse_errors: int = 0
    unresolved: int = 0
    degraded: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    semantic: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "files_seen": self.files_seen,
            "files_indexed": self.files_indexed,
            "files_skipped": self.files_skipped,
            "files_removed": self.files_removed,
            "entities_written": self.entities_written,
            "edges_written": self.edges_written,
            "entities_removed": self.entities_removed,
            "embeddings_written": self.embeddings_written,
            "embeddings_reused": self.embeddings_reused,
            "parse_errors": self.parse_errors,
            "unresolved": self.unresolved,
            "degraded": self.degraded,
            "duration_seconds": round(self.duration_seconds, 3),
            "semantic": self.semantic,
        }


class Indexer:
    """Runs discovery, parsing, resolution, persistence and embedding."""

    def __init__(
        self,
        workspace: Workspace,
        *,
        backend: EmbeddingBackend | None = None,
        progress: ProgressFn | None = None,
    ) -> None:
        self.workspace = workspace
        self.config: Config = workspace.config
        self.repo = Repository(workspace.con)
        self.backend = backend
        self.progress = progress
        self.builder = EntityBuilder(root_id=workspace.root_id())

    # ------------------------------------------------------------- discovery

    def ensure_root(self) -> None:
        """Register the workspace root and refresh its Git state."""
        from ..storage.sqlite import writer_transaction

        branch, head = git_state(self.workspace.root)
        with writer_transaction(self.workspace.con):
            self.repo.upsert_root(
                root_id=self.workspace.root_id(),
                path=str(self.workspace.root),
                name=self.workspace.root.name,
                is_primary=True,
                vcs_branch=branch,
                vcs_head=head,
            )

    def discover(self) -> list[DiscoveredFile]:
        index_cfg = self.config.index
        discovery = Discovery(
            self.workspace.root,
            include=self.config.include,
            exclude=self.config.exclude,
            follow_symlinks=index_cfg.follow_symlinks,
            include_generated=index_cfg.include_generated,
            include_media=index_cfg.include_media,
            max_file_bytes=index_cfg.max_file_bytes,
            max_roots=index_cfg.max_roots,
        )
        return discovery.scan().files

    # ------------------------------------------------------------- indexing

    def run(
        self,
        files: list[DiscoveredFile],
        *,
        changed: list[DiscoveredFile] | None = None,
        removed_paths: list[str] | None = None,
        full: bool = True,
    ) -> IndexStats:
        """Index the given files and persist the results."""
        started = time.monotonic()
        stats = IndexStats(files_seen=len(files))
        if self.backend is None or not self.backend.capabilities():
            stats.semantic = False
            if self.backend is not None:
                stats.degraded.append(
                    f"semantic backend unavailable: {getattr(self.backend, 'reason', 'unknown')}"
                )

        target = files if changed is None else changed
        if self.progress:
            self.progress("parsing", 0, len(target))

        built: list[FileEntities] = []
        for index, discovered in enumerate(target):
            result = self.builder.build_file(discovered)
            built.append(result)
            if result.error_count:
                stats.parse_errors += 1
            # Report often enough that a long parse never looks frozen.
            if self.progress and (index % 5 == 0 or index == len(target) - 1):
                self.progress(
                    "parsing", index + 1, len(target),
                    detail=f"{discovered.path} ({len(result.entities)} entities)",
                )

        if self.progress:
            # Resolve is part of parsing work; report it so a long resolution
            # shows movement, but it shares the parsing stage's clock.
            self.progress("resolving", 0, len(built), detail="cross-file resolution")

        # Register every file before resolving so cross-file references can be
        # matched regardless of discovery order.
        self.builder.register_all(built)
        self.builder.resolve_all(built)

        # Resolution can invalidate a previously stored target, so entities for
        # the whole workspace must be registered before persisting edges.
        self._register_existing_files({r.path for r in built})

        if removed_paths:
            stats.entities_removed += self._remove_paths(removed_paths)

        if self.progress:
            self.progress("persisting", 0, len(built), detail="entities, edges, full-text index")

        entity_batches: list[tuple[FileEntities, str]] = []
        for position, result in enumerate(built):
            entity_batches.extend(self._persist(result, stats))
            if self.progress and (position % 5 == 0 or position == len(built) - 1):
                self.progress(
                    "persisting", position + 1, len(built),
                    detail=f"{stats.entities_written} entities, {stats.edges_written} edges",
                )

        if self.backend is not None and stats.semantic:
            self._embed(entity_batches, stats, progress=self.progress)
        elif self.progress:
            self.progress(
                "embedding", 0, 0,
                detail="skipped; run 'poldergraph update' to add vectors",
            )

        with writer_transaction(self.workspace.con):
            set_meta(self.workspace.con, "last_scan_at", int(time.time()))
            set_meta(self.workspace.con, "index_generation", uuid.uuid4().hex)
            # Stamp the format this index actually holds, never optimistically.
            # A no-op run (nothing to re-index) would otherwise assert "this
            # index is current" while every stored span is still in the old
            # format, permanently disarming the rebuild guard. Only a run that
            # really rewrote files may advance the stamp.
            if built:
                set_meta(
                    self.workspace.con, "index_format_version", INDEX_FORMAT_VERSION
                )
            _branch, head = git_state(self.workspace.root)
            if head:
                set_meta(self.workspace.con, "indexed_head", head)
            set_meta(self.workspace.con, "representation_version", str(REPRESENTATION_VERSION))
            record_change_event(
                self.workspace.con,
                "reindex",
                [e.id for result in built for e in result.entities],
            )

        stats.duration_seconds = time.monotonic() - started
        return stats

    def _register_existing_files(self, current_paths: set[str]) -> None:
        """Re-register unchanged files so resolution sees the whole workspace."""
        current = current_paths
        for record in self.repo.all_files(self.workspace.root_id()):
            if record["path"] in current:
                continue
            index = self.builder.resolver.files.get(record["path"])
            if index is not None:
                continue
            # Rebuild a light index for files indexed in earlier runs.
            entities = self.repo.entities_owned_by_path(record["path"], root_id=self.workspace.root_id())
            if not entities:
                continue
            from ..parsing.resolver import FileIndex

            file_index = FileIndex(
                root_id=self.workspace.root_id(),
                path=record["path"],
                language=record["language"],
                symbol_ids={},
            )
            for entity in entities:
                if entity.qualified_name:
                    file_index.symbols[entity.qualified_name] = entity.id
                    leaf = entity.qualified_name.rsplit(".", 1)[-1]
                    file_index.by_name.setdefault(leaf, []).append(entity.id)
            self.builder.resolver.register_file(file_index)
            for module in _modules_for_path(record["path"]):
                self.builder.resolver.index_module_path(module, record["path"])

    def _persist(self, result: FileEntities, stats: IndexStats) -> list[tuple[FileEntities, str]]:
        """Write one file's entities/edges/FTS rows and return embeddable pairs."""
        con = self.workspace.con
        discovered = DiscoveredFile(
            path=result.path,
            abs_path=self.workspace.root / result.path,
            size=len(result.source_bytes or b""),
            mtime_ns=0,
            language=result.file_index.language if result.file_index else None,
        )
        with writer_transaction(con):
            existing = self.repo.entities_owned_by_path(result.path, root_id=self.workspace.root_id())
            if existing:
                removed_ids = [e.id for e in existing]
                self.repo.delete_edges_touching(removed_ids)
                self.repo.delete_entities(removed_ids)

            self.repo.upsert_entities(result.entities)
            self.repo.upsert_edges(result.edges)
            self.repo.delete_embeddings_for([e.id for e in result.entities])

            for entity in result.entities:
                self.repo.fts.index_entity(
                    entity.id,
                    {
                        "name": entity.name,
                        "qualified_name": entity.qualified_name,
                        "path": entity.path,
                        "signature": entity.signature,
                        "docstring": entity.docstring,
                        "semantic_text": self._fts_semantic_text(entity, result),
                    },
                )

            for record in getattr(result, "unresolved_refs", []):
                self.repo.record_unresolved(**record)

            self.repo.record_file(
                root_id=self.workspace.root_id(),
                path=result.path,
                size=len(result.source_bytes or b""),
                mtime_ns=discovered.mtime_ns,
                content_hash=result.content_hash,
                language=result.file_index.language if result.file_index else None,
                parse_status=result.parse_status,
                is_generated=discovered.is_generated,
                is_media=result.path.lower().endswith((".png", ".jpg", ".mp4", ".mp3", ".wav")),
            )

        stats.files_indexed += 1
        stats.entities_written += len(result.entities)
        stats.edges_written += len(result.edges)
        stats.unresolved += len(getattr(result, "unresolved_refs", []))
        return [(result, entity.id) for entity in result.entities]

    def _fts_semantic_text(self, entity: Entity, result: FileEntities) -> str:
        """FTS payload: name, signature and documentation, without the body."""
        parts = [entity.name or "", entity.qualified_name or "", entity.signature or "", entity.docstring or ""]
        return " ".join(part for part in parts if part)[:2000]

    def _remove_paths(self, paths: list[str]) -> int:
        """Delete every trace of the given paths from the index."""
        removed = 0
        for path in paths:
            entities = self.repo.entities_owned_by_path(path, root_id=self.workspace.root_id())
            ids = [e.id for e in entities]
            if ids:
                with writer_transaction(self.workspace.con):
                    self.repo.delete_edges_touching(ids)
                    self.repo.delete_entities(ids)
                    self.repo.delete_embeddings_for(ids)
                removed += len(ids)
            with writer_transaction(self.workspace.con):
                self.repo.delete_files(self.workspace.root_id(), [path])
        return removed

    # ------------------------------------------------------------ embeddings

    def _representations(self, batches: list[tuple[FileEntities, str]]) -> list[tuple[str, str]]:
        """Build (entity_id, normalized representation) for embedding.

        Only entities that add retrieval value are embedded: code symbols,
        tests, documents, and media. Containers (directories, workspace,
        repository) and file entities with no exported symbols or meaningful
        docstring are skipped — they add no retrieval signal and dominate the
        entity count on large repos.
        """
        out: list[tuple[str, str]] = []
        for result, entity_id in batches:
            entity = next((e for e in result.entities if e.id == entity_id), None)
            if entity is None:
                continue
            if not self._needs_embedding(entity, result):
                continue
            body = self._body_for(result, entity)
            text = representation_for(
                entity,
                body=body,
                exports=_exports_for(result, entity),
                module_doc=result.module_doc if entity.kind in {"file", "document"} else None,
                ancestry=_ancestry_for(entity),
            )
            out.append((entity.id, normalize_representation(text)))
        return out

    def _needs_embedding(self, entity: Entity, result: FileEntities) -> bool:
        """Decide whether an entity contributes retrieval value as a vector.

        Containers and metadata-only file entities are skipped — they would
        add latency without improving search quality.
        """
        kind = entity.kind
        # Never embed workspace/directory/repository nodes.
        if kind in {"workspace", "repository", "directory"}:
            return False
        # Media and section entities always need embeddings.
        if kind in {"image", "audio_segment", "video_segment", "section", "document"}:
            return True
        # File entities: only embed when they have a real docstring or are
        # documents. A pure file container with no text body adds no signal.
        if kind in {"file", "module", "namespace", "package"}:
            return bool(entity.docstring and len(entity.docstring) > 20)
        # Code symbols, tests: always embed.
        return True

    def _body_for(self, result: FileEntities, entity: Entity) -> str | None:
        """Extract the source text belonging to an entity."""
        source = result.source_bytes
        if source is None or entity.start_byte is None or entity.end_byte is None:
            return None
        return source[entity.start_byte : entity.end_byte].decode("utf-8", errors="replace")

    def _embed(self, batches: list[tuple[FileEntities, str]], stats: IndexStats, *, progress: Any = None) -> None:
        """Embed changed/new representations and persist vectors."""
        if self.backend is None:
            return
        representations = self._representations(batches)
        if not representations:
            return

        by_id = {eid: text for eid, text in representations}
        # Reuse vectors whose semantic input did not change.
        to_embed: list[str] = []
        for position, (entity_id, text) in enumerate(representations):
            existing = self.repo.embedding_info(entity_id)
            digest = semantic_hash(text)
            if any(record["input_hash"] == digest for record in existing):
                stats.embeddings_reused += 1
                continue
            to_embed.append(entity_id)
            if progress and (position % 100 == 0 or position == len(representations) - 1):
                progress(
                    "embedding", position + 1, len(representations),
                    detail=f"checking {stats.embeddings_reused} reusable vectors",
                )
        if not to_embed:
            if progress:
                progress(
                    "embedding", len(representations), len(representations),
                    detail=f"all {stats.embeddings_reused} vectors reused; nothing to embed",
                )
            return

        info = self.backend.model_info()
        texts = [by_id[entity_id] for entity_id in to_embed]
        if progress:
            progress("embedding", 0, len(texts), detail=f"encoding on {_device_of(self.backend)}")

        def on_batch(done: int, total: int) -> None:
            if progress:
                rate = f"{done / max(0.001, time.monotonic() - embed_started):.0f}/s"
                progress(
                    "embedding", done, total,
                    detail=f"{done}/{total} vectors  {rate}",
                )

        embed_started = time.monotonic()
        try:
            vectors = self.backend.embed_texts(
                texts, task=DOCUMENT_TASK, dimensions=info.dimensions, on_batch=on_batch
            )
        except TypeError:
            # Backends that predate the progress callback.
            vectors = self.backend.embed_texts(texts, task=DOCUMENT_TASK, dimensions=info.dimensions)
        except Exception as exc:
            # Semantic failure degrades the index but never destroys it.
            stats.semantic = False
            stats.degraded.append(f"embedding failed: {exc}")
            return

        store = create_vector_store(
            self.workspace.con, dimensions=info.dimensions, model_id=info.model_id
        )
        records: list[VectorRecord] = []
        with writer_transaction(self.workspace.con):
            for entity_id, vector in zip(to_embed, vectors, strict=False):
                text = by_id[entity_id]
                digest = semantic_hash(text)
                embedding_id = embedding_id_for(
                    entity_id, info.model_id, info.revision, info.dimensions, DOCUMENT_TASK, digest
                )
                records.append(
                    VectorRecord(
                        embedding_id=embedding_id,
                        entity_id=entity_id,
                        vector=vector,
                        dimensions=info.dimensions,
                        model_id=info.model_id,
                        model_revision=info.revision,
                        task_type=DOCUMENT_TASK,
                        input_hash=digest,
                        modality="text",
                    )
                )
                self.repo.record_embedding(
                    {
                        "embedding_id": embedding_id,
                        "entity_id": entity_id,
                        "modality": "text",
                        "model_id": info.model_id,
                        "model_revision": info.revision,
                        "dimensions": info.dimensions,
                        "task_type": DOCUMENT_TASK,
                        "input_hash": digest,
                        "norm": 1.0,
                    }
                )
                # Mirror the hash onto the entity so a consumer can tell what
                # text its vector was built from without joining the embeddings
                # table. The column existed but was never populated, which
                # made every row read as "no semantic representation".
                self.repo.set_entity_semantic_hash(entity_id, digest)
            store.upsert(records)
        stats.embeddings_written += len(records)

    # --------------------------------------------------------------- helpers

    def representation_version(self) -> int:
        return REPRESENTATION_VERSION


def _device_of(backend: Any) -> str:
    """Short label for the device an embedding backend is using."""
    return str(getattr(backend, "device", "unknown"))


def git_state(root: Path) -> tuple[str | None, str | None]:
    """Read current branch and HEAD without requiring Git to be present."""
    import shutil
    import subprocess

    binary = shutil.which("git")
    if binary is None or not (root / ".git").exists():
        return None, None

    def run(args: list[str]) -> str | None:
        try:
            completed = subprocess.run(
                [binary, *args], cwd=root, capture_output=True, timeout=10, check=False
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        return completed.stdout.decode("utf-8", errors="replace").strip() or None

    return run(["rev-parse", "--abbrev-ref", "HEAD"]), run(["rev-parse", "HEAD"])


def _exports_for(result: FileEntities, entity: Entity) -> list[tuple[str, str]]:
    if entity.kind not in {"file", "document"}:
        return []
    out: list[tuple[str, str]] = []
    for candidate in result.entities:
        if candidate.parent_id == entity.id and candidate.signature:
            out.append((candidate.qualified_name or candidate.name, candidate.signature))
    return out


def _ancestry_for(entity: Entity) -> list[str] | None:
    if entity.kind == "section" and entity.qualified_name:
        return [entity.qualified_name]
    return None


def _modules_for_path(path: str) -> list[str]:
    stem = path.rsplit(".", 1)[0] if "." in path else path
    dotted = stem.replace("/", ".")
    out = [dotted]
    leaf = dotted.rsplit(".", 1)[-1]
    if leaf != dotted:
        out.append(leaf)
    return out
