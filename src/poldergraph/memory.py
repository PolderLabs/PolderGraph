"""Private, per-user memory shared by every PolderGraph project.

Memories are stored in one SQLite database in the user's application-data
directory. A project root scopes repository-specific memories without placing
them in the repository or exposing them to another project.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import sqlite3
import threading
import time
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from platformdirs import user_data_path

from .config.models import EMBEDDING_MODEL
from .embedding.protocol import DOCUMENT_TASK, QUERY_TASK, EmbeddingBackend
from .errors import UsageError

MemoryScope = Literal["project", "user"]
MemoryKind = Literal["fact", "preference", "decision", "workflow", "reference"]
SCOPES = {"project", "user", "all"}
KINDS = {"fact", "preference", "decision", "workflow", "reference"}
MAX_CONTENT_CHARS = 32_000
MAX_TAGS = 20
MAX_RESULTS = 100
MEMORY_DIMENSIONS = 256
VECTOR_BATCH_SIZE = 32
MEMORY_MIN_VECTOR_SIMILARITY = 0.28
_backend_lock = threading.RLock()
_STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "for",
    "from",
    "how",
    "into",
    "its",
    "that",
    "the",
    "their",
    "then",
    "there",
    "this",
    "what",
    "when",
    "where",
    "which",
    "with",
    "would",
    "your",
    "you",
    "task",
    "project",
    "code",
    "work",
    "prefer",
}
_SECRET_PATTERNS = (
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def default_memory_path() -> Path:
    """Return the single cross-project memory database path for this user."""
    override = os.environ.get("POLDERGRAPH_MEMORY_DB")
    if override:
        return Path(override).expanduser().resolve()
    return user_data_path("PolderGraph", "PolderLabs") / "memory.sqlite3"


def project_root(path: Path | str | None = None) -> Path:
    """Resolve the project root used to isolate project memories."""
    root = Path(path or Path.cwd()).expanduser().resolve()
    return root.parent if root.is_file() else root


def _project_key(root: Path) -> str:
    identity = str(root)
    if os.name == "nt":
        identity = identity.casefold()
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _normalize_content(value: str) -> str:
    return " ".join(value.split()).casefold()


def _checked_scope(scope: str) -> str:
    if scope not in SCOPES:
        raise UsageError("Memory scope must be 'project', 'user', or 'all'.")
    return scope


def _checked_kind(kind: str) -> str:
    if kind not in KINDS:
        raise UsageError(f"Memory kind must be one of: {', '.join(sorted(KINDS))}.")
    return kind


def _checked_content(content: str) -> str:
    content = content.strip()
    if not content:
        raise UsageError("Memory content cannot be empty.")
    if len(content) > MAX_CONTENT_CHARS:
        raise UsageError(f"Memory content is limited to {MAX_CONTENT_CHARS} characters.")
    if any(pattern.search(content) for pattern in _SECRET_PATTERNS):
        raise UsageError(
            "This looks like a credential or private key and cannot be stored in memory.",
            code="MEMORY_SECRET_REJECTED",
            remediation="Keep credentials in an OS keychain or secrets manager, not PolderGraph memory.",
        )
    return content


def _checked_tags(tags: list[str] | None) -> list[str]:
    normalized = list(dict.fromkeys(" ".join(tag.split()) for tag in (tags or []) if tag.strip()))
    if len(normalized) > MAX_TAGS:
        raise UsageError(f"A memory can have at most {MAX_TAGS} tags.")
    if any(len(tag) > 80 for tag in normalized):
        raise UsageError("Memory tags are limited to 80 characters each.")
    return normalized


@lru_cache(maxsize=1)
def _default_memory_backend() -> EmbeddingBackend:
    """Construct the one canonical vector model for cross-project memories."""
    from .embedding.gemma import NativeGemmaBackend

    return NativeGemmaBackend(model_id=EMBEDDING_MODEL, dimensions=MEMORY_DIMENSIONS)


def memory_backend(preferred: EmbeddingBackend | None = None) -> EmbeddingBackend:
    """Reuse a loaded model, otherwise use the canonical local memory model."""
    if preferred is not None:
        return preferred
    return _default_memory_backend()


class MemoryStore:
    """CRUD and lexical retrieval over the user's centralized memory database."""

    def __init__(self, root: Path | str | None = None, database: Path | str | None = None) -> None:
        self.root = project_root(root)
        self.project_key = _project_key(self.root)
        self.database = Path(database).expanduser().resolve() if database else default_memory_path()

    def _connect(self) -> sqlite3.Connection:
        self.database.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with contextlib.suppress(OSError):
            self.database.parent.chmod(0o700)
        con = sqlite3.connect(self.database, timeout=5.0)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA busy_timeout = 5000")
        con.execute("PRAGMA journal_mode = WAL")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                scope TEXT NOT NULL CHECK (scope IN ('project', 'user')),
                project_key TEXT NOT NULL,
                project_root TEXT,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                tags_json TEXT NOT NULL DEFAULT '[]',
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                CHECK (
                    (scope = 'user' AND project_key = '' AND project_root IS NULL)
                    OR (scope = 'project' AND project_key <> '' AND project_root IS NOT NULL)
                ),
                UNIQUE(scope, project_key, content_hash)
            )
            """
        )
        con.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(id UNINDEXED, searchable)"
        )
        con.commit()
        with contextlib.suppress(OSError):
            self.database.chmod(0o600)
        return con

    @staticmethod
    def _searchable(content: str, kind: str, tags: list[str]) -> str:
        return " ".join((content, kind, *tags))

    @staticmethod
    def _decode(
        row: sqlite3.Row, *, score: float | None = None, matched_terms: list[str] | None = None
    ) -> dict[str, Any]:
        item = {
            "id": row["id"],
            "scope": row["scope"],
            "project_root": row["project_root"],
            "kind": row["kind"],
            "content": row["content"],
            "tags": json.loads(row["tags_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        if score is not None:
            item["score"] = round(score, 4)
            item["matched_terms"] = matched_terms or []
        return item

    def _visible_sql(self, scope: str, *, alias: str = "") -> tuple[str, list[str]]:
        scope = _checked_scope(scope)
        prefix = f"{alias}." if alias else ""
        if scope == "user":
            return f"{prefix}scope = 'user'", []
        if scope == "project":
            return f"{prefix}scope = 'project' AND {prefix}project_key = ?", [self.project_key]
        return (
            f"({prefix}scope = 'user' OR ({prefix}scope = 'project' AND {prefix}project_key = ?))",
            [self.project_key],
        )

    def add(
        self,
        content: str,
        *,
        scope: MemoryScope = "project",
        kind: MemoryKind = "fact",
        tags: list[str] | None = None,
        backend: EmbeddingBackend | None = None,
    ) -> dict[str, Any]:
        scope = _checked_scope(scope)
        if scope == "all":
            raise UsageError("New memories must use 'project' or 'user' scope.")
        content = _checked_content(content)
        kind = _checked_kind(kind)
        tags = _checked_tags(tags)
        project_key = self.project_key if scope == "project" else ""
        root_value = str(self.root) if scope == "project" else None
        content_hash = hashlib.sha256(_normalize_content(content).encode("utf-8")).hexdigest()
        now = int(time.time())
        con = self._connect()
        try:
            row = con.execute(
                "SELECT * FROM memories WHERE scope = ? AND project_key = ? AND content_hash = ?",
                (scope, project_key, content_hash),
            ).fetchone()
            created = row is None
            if row is None:
                memory_id = f"mem_{uuid.uuid4().hex[:20]}"
                con.execute(
                    "INSERT INTO memories(id,scope,project_key,project_root,kind,content,content_hash,tags_json,created_at,updated_at) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        memory_id,
                        scope,
                        project_key,
                        root_value,
                        kind,
                        content,
                        content_hash,
                        json.dumps(tags),
                        now,
                        now,
                    ),
                )
            else:
                memory_id = row["id"]
                con.execute(
                    "UPDATE memories SET kind=?, tags_json=?, updated_at=? WHERE id=?",
                    (kind, json.dumps(tags), now, memory_id),
                )
            con.execute("DELETE FROM memory_fts WHERE id = ?", (memory_id,))
            con.execute(
                "INSERT INTO memory_fts(id, searchable) VALUES(?, ?)",
                (memory_id, self._searchable(content, kind, tags)),
            )
            con.commit()
            row = con.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            result = self._decode(row)
            result["created"] = created
        finally:
            con.close()
        vector_count, vector_warning = self._index_memories([memory_id], backend)
        result["vectorized"] = vector_count > 0
        if vector_warning:
            result["vector_warning"] = vector_warning
        result["store"] = str(self.database)
        return result

    def list(self, *, scope: str = "all", limit: int = 50) -> list[dict[str, Any]]:
        if not 1 <= limit <= MAX_RESULTS:
            raise UsageError(f"Memory result limit must be between 1 and {MAX_RESULTS}.")
        where, params = self._visible_sql(scope)
        con = self._connect()
        try:
            rows = con.execute(
                f"SELECT * FROM memories WHERE {where} ORDER BY updated_at DESC, id LIMIT ?",
                (*params, limit),
            ).fetchall()
            return [self._decode(row) for row in rows]
        finally:
            con.close()

    def search(
        self,
        query: str,
        *,
        scope: str = "all",
        limit: int = 10,
        backend: EmbeddingBackend | None = None,
    ) -> list[dict[str, Any]]:
        if not 1 <= limit <= MAX_RESULTS:
            raise UsageError(f"Memory result limit must be between 1 and {MAX_RESULTS}.")
        where, params = self._visible_sql(scope)
        terms = [
            term
            for term in re.findall(r"[\w'-]+", query.casefold())
            if len(term) > 1 and term not in _STOP_WORDS
        ]
        con = self._connect()
        try:
            if not terms:
                rows = con.execute(
                    f"SELECT * FROM memories WHERE {where} ORDER BY updated_at DESC, id LIMIT ?",
                    (*params, limit),
                ).fetchall()
                return [self._decode(row) | {"score": 0.0, "matched_terms": []} for row in rows]

            match = " OR ".join(
                f'"{term.replace(chr(34), chr(34) * 2)}"' for term in dict.fromkeys(terms[:20])
            )
            lexical_rows = con.execute(
                f"SELECT m.* FROM memory_fts JOIN memories m ON m.id = memory_fts.id "
                f"WHERE memory_fts MATCH ? AND {where} LIMIT 500",
                (match, *params),
            ).fetchall()
            lexical_scores: dict[str, tuple[float, list[str]]] = {}
            phrase = " ".join(terms)
            for row in lexical_rows:
                tags = json.loads(row["tags_json"])
                content = row["content"].casefold()
                tag_text = " ".join(tags).casefold()
                matched = [
                    term
                    for term in set(terms)
                    if term in content or term in tag_text or term in row["kind"].casefold()
                ]
                if not matched:
                    continue
                weighted = sum(1.6 if term in tag_text else 1.0 for term in matched)
                score = weighted / max(1, len(set(terms)))
                if phrase in content:
                    score += 0.35
                lexical_scores[row["id"]] = (score, matched)

            vector_scores, vector_warning = self._vector_search(con, query, where, params, backend)
            ids = set(lexical_scores) | set(vector_scores)
            if not ids:
                return []
            placeholders = ",".join("?" for _ in ids)
            result_rows = con.execute(
                f"SELECT * FROM memories WHERE id IN ({placeholders})", tuple(ids)
            ).fetchall()
            lookup = {row["id"]: row for row in result_rows}
            max_lexical = max((value[0] for value in lexical_scores.values()), default=1.0) or 1.0
            ranked: list[dict[str, Any]] = []
            for memory_id in ids:
                row = lookup.get(memory_id)
                if row is None:
                    continue
                lexical_score, matched = lexical_scores.get(memory_id, (0.0, []))
                semantic_score = vector_scores.get(memory_id)
                lexical_normalized = min(1.0, lexical_score / max_lexical)
                if semantic_score is None:
                    score = lexical_normalized
                    strategy = "lexical"
                else:
                    semantic_normalized = max(0.0, min(1.0, (semantic_score + 1.0) / 2.0))
                    score = 0.45 * lexical_normalized + 0.55 * semantic_normalized
                    strategy = "hybrid" if lexical_score else "semantic"
                if row["scope"] == "project":
                    score += 0.04
                item = self._decode(row, score=min(score, 1.0), matched_terms=matched)
                item["lexical_score"] = round(lexical_normalized, 4)
                item["semantic_score"] = (
                    round(semantic_score, 4) if semantic_score is not None else None
                )
                item["retrieval"] = strategy
                if vector_warning:
                    item["vector_warning"] = vector_warning
                ranked.append(item)
            ranked.sort(key=lambda item: (item["score"], item["updated_at"]), reverse=True)
            return ranked[:limit]
        finally:
            con.close()

    def get(self, memory_id: str) -> dict[str, Any] | None:
        where, params = self._visible_sql("all")
        con = self._connect()
        try:
            row = con.execute(
                f"SELECT * FROM memories WHERE id = ? AND {where}", (memory_id, *params)
            ).fetchone()
            return self._decode(row) if row else None
        finally:
            con.close()

    @staticmethod
    def _memory_text(row: sqlite3.Row) -> str:
        tags = json.loads(row["tags_json"])
        return f"{row['kind']}: {row['content']}\nTags: {', '.join(tags)}"

    def _upsert_vectors(
        self,
        con: sqlite3.Connection,
        rows: list[sqlite3.Row],
        backend: EmbeddingBackend,
        store: Any,
        info: Any,
    ) -> int:
        from .storage.vectors import VectorRecord, embedding_id_for

        written = 0
        for start in range(0, len(rows), VECTOR_BATCH_SIZE):
            batch = rows[start : start + VECTOR_BATCH_SIZE]
            texts = [self._memory_text(row) for row in batch]
            with _backend_lock:
                vectors = backend.embed_texts(texts, task=DOCUMENT_TASK, dimensions=info.dimensions)
            records = []
            for row, vector, source in zip(batch, vectors, texts, strict=True):
                input_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
                records.append(
                    VectorRecord(
                        embedding_id=embedding_id_for(
                            row["id"],
                            store.model_id,
                            info.revision,
                            info.dimensions,
                            "memory",
                            input_hash,
                        ),
                        entity_id=row["id"],
                        vector=vector,
                        dimensions=info.dimensions,
                        model_id=store.model_id,
                        model_revision=info.revision,
                        task_type="memory",
                        input_hash=input_hash,
                        modality="memory",
                    )
                )
            store.upsert(records)
            written += len(records)
        con.commit()
        return written

    def _index_memories(
        self, memory_ids: list[str], backend: EmbeddingBackend | None
    ) -> tuple[int, str | None]:
        if not memory_ids:
            return 0, None
        if backend is None:
            return 0, "Memory saved for keyword search; vector encoder is unavailable."
        if not backend.capabilities():
            return 0, "Memory saved for keyword search; vector encoding is disabled."
        con = self._connect()
        try:
            with _backend_lock:
                info = backend.model_info()
            store = self._vector_store(con, info)
            store.ensure_table()
            placeholders = ",".join("?" for _ in memory_ids)
            rows = con.execute(
                f"SELECT * FROM memories WHERE id IN ({placeholders})", tuple(memory_ids)
            ).fetchall()
            if not rows:
                return 0, None
            for memory_id in memory_ids:
                self._delete_vector(con, memory_id)
            return self._upsert_vectors(con, rows, backend, store, info), None
        except Exception as exc:
            return 0, f"Memory saved for keyword search; vector encoding failed: {str(exc)[:220]}"
        finally:
            con.close()

    @staticmethod
    def _vector_store(con: sqlite3.Connection, info: Any) -> Any:
        from .storage.vectors import create_vector_store

        model_id = re.sub(r"[^A-Za-z0-9_]+", "_", info.model_id)
        revision = hashlib.sha256(str(info.revision).encode("utf-8")).hexdigest()[:12]
        return create_vector_store(
            con, dimensions=info.dimensions, model_id=f"{model_id}_r{revision}", task_type="memory"
        )

    def _delete_vector(self, con: sqlite3.Connection, memory_id: str) -> None:
        from .storage.sqlite import load_vec_extension

        load_vec_extension(con)
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            name = row[0]
            if name == "_bruteforce_vectors":
                con.execute(f'DELETE FROM "{name}" WHERE entity_id=?', (memory_id,))
            elif name.startswith("vec_") and "_memory_" in name and not name.endswith("_vectors"):
                # sqlite-vec may be absent in a lexical-only install.
                with contextlib.suppress(sqlite3.OperationalError):
                    con.execute(f'DELETE FROM "{name}" WHERE entity_id=?', (memory_id,))
                shadow = name + "_vectors"
                if con.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (shadow,)
                ).fetchone():
                    con.execute(f'DELETE FROM "{shadow}" WHERE entity_id=?', (memory_id,))

    def _vector_search(
        self,
        con: sqlite3.Connection,
        query: str,
        visible_clause: str,
        visible_params: list[str],
        backend: EmbeddingBackend | None,
    ) -> tuple[dict[str, float], str | None]:
        if backend is None:
            return {}, "Vector retrieval is unavailable; using keyword matching."
        try:
            with _backend_lock:
                info = backend.model_info()
            store = self._vector_store(con, info)
            store.ensure_table()
            visible_rows = con.execute(
                f"SELECT * FROM memories WHERE {visible_clause}", visible_params
            ).fetchall()
            if not visible_rows:
                return {}, None
            visible_ids = {row["id"] for row in visible_rows}
            if hasattr(store, "shadow_table"):
                existing = {
                    row[0]
                    for row in con.execute(
                        f'SELECT DISTINCT entity_id FROM "{store.shadow_table}" WHERE dimensions=?',
                        (info.dimensions,),
                    ).fetchall()
                }
            else:
                store.ensure_table()
                existing = {
                    row[0]
                    for row in con.execute(
                        f'SELECT DISTINCT entity_id FROM "{store.table}" WHERE dimensions=? AND model_id=?',
                        (info.dimensions, info.model_id),
                    ).fetchall()
                }
            missing = [row for row in visible_rows if row["id"] not in existing]
            if missing:
                for row in missing[:256]:
                    self._delete_vector(con, row["id"])
                self._upsert_vectors(con, missing[:256], backend, store, info)
            with _backend_lock:
                query_vector = backend.embed_texts(
                    [query], task=QUERY_TASK, dimensions=info.dimensions
                )[0]
            hits = store.search(
                query_vector,
                top_k=min(MAX_RESULTS, max(20, len(visible_ids))),
                filters={"modality": "memory", "model_id": store.model_id},
            )
            return {
                hit.entity_id: hit.similarity
                for hit in hits
                if (
                    hit.entity_id
                    and hit.entity_id in visible_ids
                    and hit.similarity >= MEMORY_MIN_VECTOR_SIMILARITY
                )
            }, None
        except Exception as exc:
            return {}, f"Vector retrieval failed; using keyword matching: {str(exc)[:220]}"

    def update(
        self,
        memory_id: str,
        *,
        content: str | None = None,
        kind: str | None = None,
        tags: list[str] | None = None,
        backend: EmbeddingBackend | None = None,
    ) -> dict[str, Any]:
        if content is None and kind is None and tags is None:
            raise UsageError("Provide at least one of content, kind, or tags to update.")
        current = self.get(memory_id)
        if current is None:
            raise UsageError(
                f"No memory '{memory_id}' exists in the current project or user scope."
            )
        content = _checked_content(content) if content is not None else current["content"]
        kind = _checked_kind(kind) if kind is not None else current["kind"]
        tags = _checked_tags(tags) if tags is not None else current["tags"]
        content_hash = hashlib.sha256(_normalize_content(content).encode("utf-8")).hexdigest()
        con = self._connect()
        try:
            con.execute(
                "UPDATE memories SET content=?, content_hash=?, kind=?, tags_json=?, updated_at=? WHERE id=?",
                (content, content_hash, kind, json.dumps(tags), int(time.time()), memory_id),
            )
            con.execute("DELETE FROM memory_fts WHERE id = ?", (memory_id,))
            con.execute(
                "INSERT INTO memory_fts(id, searchable) VALUES(?, ?)",
                (memory_id, self._searchable(content, kind, tags)),
            )
            con.commit()
            row = con.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            result = self._decode(row)
        except sqlite3.IntegrityError as exc:
            raise UsageError("That memory duplicates an existing item in the same scope.") from exc
        finally:
            con.close()
        vector_count, vector_warning = self._index_memories([memory_id], backend)
        result["vectorized"] = vector_count > 0
        if vector_warning:
            result["vector_warning"] = vector_warning
        return result

    def forget(self, memory_id: str) -> dict[str, Any]:
        current = self.get(memory_id)
        if current is None:
            raise UsageError(
                f"No memory '{memory_id}' exists in the current project or user scope."
            )
        con = self._connect()
        try:
            con.execute("DELETE FROM memory_fts WHERE id = ?", (memory_id,))
            con.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            self._delete_vector(con, memory_id)
            con.commit()
            return current
        finally:
            con.close()

    def status(self) -> dict[str, Any]:
        con = self._connect()
        try:
            total = con.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            user = con.execute("SELECT COUNT(*) FROM memories WHERE scope='user'").fetchone()[0]
            project = con.execute(
                "SELECT COUNT(*) FROM memories WHERE scope='project' AND project_key=?",
                (self.project_key,),
            ).fetchone()[0]
            return {
                "store": str(self.database),
                "current_project": str(self.root),
                "user_memories": user,
                "project_memories": project,
                "total_memories": total,
                "scope_note": "Other projects' memories are stored here but are never returned in this project.",
            }
        finally:
            con.close()


def add_memories_to_context(
    data: dict[str, Any],
    store: MemoryStore,
    query: str,
    budget: int,
    *,
    backend: EmbeddingBackend | None = None,
) -> dict[str, Any]:
    """Attach matching shared/project memories while respecting the context budget."""
    from .retrieval.context import estimate_tokens

    data["memories"] = []
    data["memory_truncated"] = False
    remaining = max(0, budget - int(data.get("token_estimate", 0)) - 80)
    available = store.list(limit=1)
    active_backend: EmbeddingBackend | None = None
    if available:
        try:
            active_backend = memory_backend(backend)
        except Exception:
            active_backend = None
    matches = store.search(query, limit=12, backend=active_backend)
    data["memory_retrieval"] = (
        matches[0]["retrieval"] if matches else ("lexical" if available else "none")
    )
    for memory in matches:
        if remaining <= 28:
            data["memory_truncated"] = True
            break
        item = {
            key: memory[key]
            for key in ("id", "scope", "kind", "content", "tags", "score", "matched_terms")
        }
        room_chars = max(0, (remaining - 28) * 4)
        original_content = item["content"]
        if len(original_content) > room_chars:
            item["content"] = original_content[:room_chars].rsplit(" ", 1)[0].rstrip()
            item["content_truncated"] = True
            data["memory_truncated"] = True
        cost = 28 + estimate_tokens(item["content"])
        if not item["content"]:
            data["memory_truncated"] = True
            break
        data["memories"].append(item)
        remaining = max(0, remaining - cost)
        data["token_estimate"] = int(data.get("token_estimate", 0)) + cost
    if data["memory_truncated"]:
        data["truncated"] = True
    data["memory_token_estimate"] = max(0, budget - max(0, remaining) - 80)
    return data
