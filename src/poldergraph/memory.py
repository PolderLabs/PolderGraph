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
    "a",
    "about",
    "after",
    "again",
    "against",
    "all",
    "also",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "between",
    "both",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "doing",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "him",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "just",
    "me",
    "more",
    "most",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "would",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
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
    re.compile(r"(?i)\b(?:password|passwd|api[_ -]?key|access[_ -]?token|secret)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{16,}"),
)
_USER_PREFERENCE_PATTERNS = (
    re.compile(
        r"(?im)^[ \t]*(?:remember that\s+)?(?P<statement>I\s+(?:always|usually|generally|typically|prefer|like|dislike|don't like|do not like)\b[^\n.!?]{1,400}[.!?]?)"
    ),
)
_SEARCH_SYNONYMS = {
    "response": {"output", "reply", "result", "envelope"},
    "responses": {"output", "reply", "result", "envelope"},
    "formatted": {"format", "envelope"},
    "format": {"formatted", "envelope"},
    "upload": {"send"},
    "uploads": {"send"},
    "checks": {"test", "tests", "validation"},
    "check": {"test", "tests", "validation"},
    "integration": {"test", "tests"},
    "unit": {"test", "tests"},
    "suite": {"test", "tests"},
}
_PREFERENCE_CONTRADICTIONS = {
    frozenset(("brief", "verbose")),
    frozenset(("concise", "detailed")),
    frozenset(("concise", "verbose")),
    frozenset(("short", "long")),
    frozenset(("formal", "casual")),
}


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


def _term_variants(term: str) -> set[str]:
    """Return a tiny deterministic stem set for common inflections."""
    variants = {term}
    if len(term) > 5 and term.endswith("ies"):
        variants.add(term[:-3] + "y")
    elif len(term) > 5 and term.endswith(("ches", "shes", "sses", "xes", "zes")):
        variants.add(term[:-2])
    elif len(term) > 4 and term.endswith("s"):
        variants.add(term[:-1])
    if len(term) > 5 and term.endswith("ing"):
        stem = term[:-3]
        variants.add(stem[:-1] if len(stem) > 2 and stem[-1] == stem[-2] else stem)
    elif len(term) > 4 and term.endswith("ed"):
        stem = term[:-2]
        variants.add(stem[:-1] if len(stem) > 2 and stem[-1] == stem[-2] else stem)
    return variants


def _matches_term(term: str, tokens: set[str]) -> bool:
    return any(
        variant == token
        or (len(variant) >= 5 and token.startswith(variant))
        or (len(token) >= 5 and variant.startswith(token))
        for variant in _term_variants(term) | _SEARCH_SYNONYMS.get(term, set())
        for token in tokens
    )


def _preference_conflicts(existing: str, incoming: str) -> bool:
    old_tokens = set(re.findall(r"[\w'-]+", existing.casefold()))
    new_tokens = set(re.findall(r"[\w'-]+", incoming.casefold()))
    if not (old_tokens & new_tokens):
        return False
    return any(
        len(pair & old_tokens) == 1
        and len(pair & new_tokens) == 1
        and (pair & old_tokens) != (pair & new_tokens)
        for pair in _PREFERENCE_CONTRADICTIONS
    )


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


def capture_explicit_user_preferences(
    store: MemoryStore,
    prompt: str,
    *,
    backend: EmbeddingBackend | None = None,
    decision_config: Any = None,
    trusted_user_message: bool = False,
    event_source: str = "codex_user_prompt",
    session_id: str | None = None,
    turn_id: str | None = None,
) -> list[dict[str, Any]]:
    """Save explicit preferences only when called from a trusted user-input hook.

    Deterministic parsing admits only explicit durable statements. An explicitly
    configured typed-decision provider may reject an ambiguous candidate; it
    cannot expand capture beyond these local rules.

    Repository context queries, agent-authored tool arguments, and CLI prompts
    are not proof of user authorship and must leave this flag unset.
    """
    if not trusted_user_message:
        return []
    prompt = re.sub(r"```.*?```|~~~.*?~~~", "", prompt, flags=re.DOTALL)
    candidates: dict[str, str] = {}
    for pattern in _USER_PREFERENCE_PATTERNS:
        for match in pattern.finditer(prompt):
            statement = " ".join(match.group("statement").split())
            lowered = statement.casefold()
            if any(
                phrase in lowered
                for phrase in ("for this task", "this time", "for now", "in this change")
            ):
                continue
            candidates.setdefault(_normalize_content(statement), statement)
    saved = []
    from .decision_runtime import rejected_memory_candidates

    valid_candidates = []
    for statement in candidates.values():
        try:
            _checked_content(statement)
        except UsageError as exc:
            if exc.code == "MEMORY_SECRET_REJECTED":
                continue
            raise
        valid_candidates.append(statement)
    rejected = rejected_memory_candidates(valid_candidates, decision_config)
    for index, statement in enumerate(valid_candidates):
        if index in rejected:
            continue
        try:
            prior = next(
                (
                    item
                    for item in store.list(scope="user", limit=MAX_RESULTS)
                    if item["kind"] == "preference"
                    and _preference_conflicts(item["content"], statement)
                ),
                None,
            )
            if prior is not None:
                saved.append(
                    store.update(
                        prior["id"],
                        content=statement,
                        tags=list(dict.fromkeys([*prior["tags"], "explicit-user-statement"])),
                        backend=backend,
                        provenance={
                            "source": event_source,
                            "session_id": session_id,
                            "turn_id": turn_id,
                        },
                    )
                )
                continue
            saved.append(
                store.add(
                    statement,
                    scope="user",
                    kind="preference",
                    tags=["explicit-user-statement"],
                    backend=backend,
                    provenance={
                        "source": event_source,
                        "session_id": session_id,
                        "turn_id": turn_id,
                    },
                )
            )
        except UsageError as exc:
            # A credential-like line is never persisted; other validation
            # failures should not break the agent's context retrieval.
            if exc.code != "MEMORY_SECRET_REJECTED":
                raise
    return saved


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
                provenance_json TEXT NOT NULL DEFAULT '{}',
                version_id TEXT NOT NULL DEFAULT '',
                valid_from INTEGER NOT NULL DEFAULT 0,
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
        columns = {row[1] for row in con.execute("PRAGMA table_info(memories)")}
        if "provenance_json" not in columns:
            con.execute(
                "ALTER TABLE memories ADD COLUMN provenance_json TEXT NOT NULL DEFAULT '{}'"
            )
        if "version_id" not in columns:
            con.execute("ALTER TABLE memories ADD COLUMN version_id TEXT NOT NULL DEFAULT ''")
        if "valid_from" not in columns:
            con.execute("ALTER TABLE memories ADD COLUMN valid_from INTEGER NOT NULL DEFAULT 0")
        con.execute(
            "UPDATE memories SET version_id='memver_' || id WHERE version_id=''"
        )
        con.execute("UPDATE memories SET valid_from=created_at WHERE valid_from=0")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_revisions (
                version_id TEXT PRIMARY KEY,
                memory_id TEXT NOT NULL,
                content TEXT NOT NULL,
                kind TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                provenance_json TEXT NOT NULL,
                valid_from INTEGER NOT NULL,
                valid_to INTEGER NOT NULL,
                superseded_by_version TEXT NOT NULL
            )
            """
        )
        con.execute(
            "CREATE INDEX IF NOT EXISTS memory_revisions_memory_id "
            "ON memory_revisions(memory_id, valid_from)"
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
            "provenance": json.loads(row["provenance_json"]),
            "version_id": row["version_id"],
            "valid_from": row["valid_from"],
            "valid_to": None,
            "superseded_by_version": None,
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
        provenance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        scope = _checked_scope(scope)
        if scope == "all":
            raise UsageError("New memories must use 'project' or 'user' scope.")
        content = _checked_content(content)
        kind = _checked_kind(kind)
        tags = _checked_tags(tags)
        project_key = self.project_key if scope == "project" else ""
        root_value = str(self.root) if scope == "project" else None
        provenance_json = json.dumps(provenance or {}, sort_keys=True)
        content_hash = hashlib.sha256(_normalize_content(content).encode("utf-8")).hexdigest()
        now = int(time.time())
        con = self._connect()
        needs_index = False
        try:
            row = con.execute(
                "SELECT * FROM memories WHERE scope = ? AND project_key = ? AND content_hash = ?",
                (scope, project_key, content_hash),
            ).fetchone()
            created = row is None
            if row is None:
                needs_index = True
                memory_id = f"mem_{uuid.uuid4().hex[:20]}"
                version_id = f"memver_{uuid.uuid4().hex[:20]}"
                con.execute(
                    "INSERT INTO memories(id,scope,project_key,project_root,kind,content,content_hash,tags_json,provenance_json,version_id,valid_from,created_at,updated_at) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        memory_id,
                        scope,
                        project_key,
                        root_value,
                        kind,
                        content,
                        content_hash,
                        json.dumps(tags),
                        provenance_json,
                        version_id,
                        now,
                        now,
                        now,
                    ),
                )
            else:
                memory_id = row["id"]
                needs_index = row["kind"] != kind or json.loads(row["tags_json"]) != tags
                stored_provenance = json.loads(row["provenance_json"])
                next_provenance = provenance if provenance and not stored_provenance else stored_provenance
                revision_changed = needs_index or next_provenance != stored_provenance
                next_version_id = (
                    f"memver_{uuid.uuid4().hex[:20]}" if revision_changed else row["version_id"]
                )
                valid_from = max(now, int(row["valid_from"]) + 1) if revision_changed else row["valid_from"]
                if revision_changed:
                    con.execute(
                        "INSERT INTO memory_revisions(version_id,memory_id,content,kind,tags_json,"
                        "provenance_json,valid_from,valid_to,superseded_by_version) "
                        "VALUES(?,?,?,?,?,?,?,?,?)",
                        (
                            row["version_id"],
                            memory_id,
                            row["content"],
                            row["kind"],
                            row["tags_json"],
                            row["provenance_json"],
                            row["valid_from"],
                            valid_from,
                            next_version_id,
                        ),
                    )
                    con.execute(
                        "UPDATE memories SET kind=?,tags_json=?,provenance_json=?,version_id=?,"
                        "valid_from=?,updated_at=? WHERE id=?",
                        (
                            kind,
                            json.dumps(tags),
                            json.dumps(next_provenance, sort_keys=True),
                            next_version_id,
                            valid_from,
                            valid_from,
                            memory_id,
                        ),
                    )
                if needs_index:
                    con.execute(
                        "UPDATE memories SET kind=?, tags_json=?, updated_at=? WHERE id=?",
                        (kind, json.dumps(tags), now, memory_id),
                    )
            if needs_index:
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
        already_vectorized = False
        if not needs_index and backend is not None:
            already_vectorized = self._has_vector(memory_id, backend)
            needs_index = not already_vectorized
        vector_count, vector_warning = (
            self._index_memories([memory_id], backend) if needs_index else (0, None)
        )
        result["vectorized"] = vector_count > 0 or already_vectorized
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
                return []

            expanded_terms = set().union(
                *(_term_variants(term) | _SEARCH_SYNONYMS.get(term, set()) for term in terms[:20])
            )
            match = " OR ".join(
                f'"{term.replace(chr(34), chr(34) * 2)}"' for term in sorted(expanded_terms)
            )
            lexical_rows = con.execute(
                f"SELECT m.* FROM memory_fts JOIN memories m ON m.id = memory_fts.id "
                f"WHERE memory_fts MATCH ? AND {where} LIMIT 500",
                (match, *params),
            ).fetchall()
            lexical_scores: dict[str, tuple[float, list[str]]] = {}
            phrase = " ".join(terms)
            query_terms = set(terms)
            for row in lexical_rows:
                tags = json.loads(row["tags_json"])
                content = set(re.findall(r"[\w'-]+", row["content"].casefold()))
                tag_tokens = set(re.findall(r"[\w'-]+", " ".join(tags).casefold()))
                metadata_tokens = tag_tokens | set(row["kind"].casefold().split())
                all_tokens = content | metadata_tokens
                matched = sorted(term for term in query_terms if _matches_term(term, all_tokens))
                if not matched:
                    continue
                weighted = sum(1.25 if term in metadata_tokens else 1.0 for term in matched)
                score = weighted / max(1, len(query_terms))
                normalized_content = " ".join(re.findall(r"[\w'-]+", row["content"].casefold()))
                if phrase and phrase in normalized_content:
                    score += 0.2
                lexical_scores[row["id"]] = (score, matched)

            # Exact, high-coverage FTS matches are already sufficiently precise;
            # avoid loading or invoking a heavyweight embedding model for them.
            precise_lexical_match = any(score >= 0.8 for score, _matched in lexical_scores.values())
            if precise_lexical_match:
                vector_scores, vector_warning = {}, None
            else:
                vector_scores, vector_warning = self._vector_search(
                    con, query, where, params, backend
                )
            ids = set(lexical_scores) | set(vector_scores)
            if not ids:
                return []
            placeholders = ",".join("?" for _ in ids)
            result_rows = con.execute(
                f"SELECT * FROM memories WHERE id IN ({placeholders})", tuple(ids)
            ).fetchall()
            lookup = {row["id"]: row for row in result_rows}
            ranked: list[dict[str, Any]] = []
            for memory_id in ids:
                row = lookup.get(memory_id)
                if row is None:
                    continue
                lexical_score, matched = lexical_scores.get(memory_id, (0.0, []))
                semantic_score = vector_scores.get(memory_id)
                lexical_normalized = min(1.0, lexical_score)
                if semantic_score is None:
                    score = lexical_normalized
                    strategy = "lexical"
                else:
                    semantic_normalized = max(0.0, min(1.0, (semantic_score - 0.35) / 0.5))
                    score = 0.45 * lexical_normalized + 0.55 * semantic_normalized
                    strategy = "hybrid" if lexical_score else "semantic"
                # A single incidental word or a weak embedding neighbour must not enter
                # automatic agent context. Strong lexical coverage survives at any
                # vector score; a semantic-only match must clear this bar.
                # Calibrated against real memories: strong paraphrases land
                # 0.70-0.85, so a 0.75 gate discarded genuine matches while the
                # abstention test showed unrelated pairs stay well below it.
                SEMANTIC_ONLY_MIN = 0.65
                if lexical_normalized < 0.4 and (
                    semantic_score is None or semantic_score < SEMANTIC_ONLY_MIN
                ):
                    continue
                item = self._decode(row, score=min(score, 1.0), matched_terms=matched)
                item["lexical_score"] = round(lexical_normalized, 4)
                item["semantic_score"] = (
                    round(semantic_score, 4) if semantic_score is not None else None
                )
                item["retrieval"] = strategy
                if vector_warning:
                    item["vector_warning"] = vector_warning
                ranked.append(item)
            ranked.sort(
                key=lambda item: (
                    item["score"],
                    item["lexical_score"],
                    item["semantic_score"] if item["semantic_score"] is not None else -1.0,
                    item["scope"] == "project",
                    item["updated_at"],
                    item["content"].casefold(),
                ),
                reverse=True,
            )
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

    def history(self, memory_id: str) -> list[dict[str, Any]]:
        """Return visible prior versions and the current version, oldest first."""
        current = self.get(memory_id)
        if current is None:
            return []
        where, params = self._visible_sql("all", alias="m")
        con = self._connect()
        try:
            rows = con.execute(
                "SELECT r.* FROM memory_revisions r "
                "JOIN memories m ON m.id=r.memory_id "
                f"WHERE r.memory_id=? AND {where} ORDER BY r.valid_from, r.version_id",
                (memory_id, *params),
            ).fetchall()
            versions = [
                {
                    "id": memory_id,
                    "version_id": row["version_id"],
                    "content": row["content"],
                    "kind": row["kind"],
                    "tags": json.loads(row["tags_json"]),
                    "provenance": json.loads(row["provenance_json"]),
                    "valid_from": row["valid_from"],
                    "valid_to": row["valid_to"],
                    "superseded_by_version": row["superseded_by_version"],
                    "current": False,
                }
                for row in rows
            ]
            versions.append(
                {
                    **current,
                    "current": True,
                }
            )
            return versions
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
        """Return the vector store for this model revision.

        The table name is keyed on the model only, never the revision. Folding
        the revision into the table name creates a fresh table whenever the
        model is re-resolved, silently orphaning every previously written
        vector while `memory add` still reports success.
        """
        from .storage.vectors import create_vector_store

        model_id = re.sub(r"[^A-Za-z0-9_]+", "_", info.model_id)
        return create_vector_store(
            con, dimensions=info.dimensions, model_id=model_id, task_type="memory"
        )

    def repair_vectors(self, backend: EmbeddingBackend | None = None) -> dict[str, Any]:
        """Re-embed memories that have no vector in the current table.

        Memories written before the table-name fix live in a revision-keyed
        table that is never read again. This finds them and restores semantic
        recall without losing any record.
        """
        if backend is None:
            backend = memory_backend()
        if not backend.capabilities():
            return {"repaired": 0, "reason": "no embedding backend available"}

        con = self._connect()
        try:
            with _backend_lock:
                info = backend.model_info()
            store = self._vector_store(con, info)
            store.ensure_table()

            stranded = [
                row["id"]
                for row in con.execute("SELECT id FROM memories ORDER BY id").fetchall()
                if not self._has_vector_in(con, store, row["id"])
            ]
            if not stranded:
                return {
                    "repaired": 0,
                    "total": con.execute("SELECT COUNT(*) FROM memories").fetchone()[0],
                }

            placeholders = ",".join("?" for _ in stranded)
            rows = con.execute(
                f"SELECT * FROM memories WHERE id IN ({placeholders})", stranded
            ).fetchall()
            written = self._upsert_vectors(con, rows, backend, store, info)
            return {
                "repaired": written,
                "total": con.execute("SELECT COUNT(*) FROM memories").fetchone()[0],
            }
        except Exception as exc:
            return {"repaired": 0, "error": str(exc)[:200]}
        finally:
            con.close()

    def _has_vector_in(self, con: sqlite3.Connection, store: Any, memory_id: str) -> bool:
        table = getattr(store, "shadow_table", None)
        if not table:
            return False
        try:
            return (
                con.execute(
                    f"SELECT 1 FROM {table} WHERE entity_id=? LIMIT 1", (memory_id,)
                ).fetchone()
                is not None
            )
        except sqlite3.Error:
            return False

    def _has_vector(self, memory_id: str, backend: EmbeddingBackend) -> bool:
        if not backend.capabilities():
            return False
        con = self._connect()
        try:
            with _backend_lock:
                info = backend.model_info()
            store = self._vector_store(con, info)
            store.ensure_table()
            if hasattr(store, "shadow_table"):
                return bool(
                    con.execute(
                        f'SELECT 1 FROM "{store.shadow_table}" WHERE entity_id=? AND dimensions=? LIMIT 1',
                        (memory_id, info.dimensions),
                    ).fetchone()
                )
            return bool(
                con.execute(
                    f'SELECT 1 FROM "{store.table}" WHERE entity_id=? AND dimensions=? AND model_id=? LIMIT 1',
                    (memory_id, info.dimensions, store.model_id),
                ).fetchone()
            )
        finally:
            con.close()

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
        provenance: dict[str, Any] | None = None,
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
        provenance_value = provenance or current["provenance"]
        revision_changed = any(
            (
                content != current["content"],
                kind != current["kind"],
                tags != current["tags"],
                provenance_value != current["provenance"],
            )
        )
        now = max(int(time.time()), int(current["valid_from"]) + 1)
        next_version_id = f"memver_{uuid.uuid4().hex[:20]}" if revision_changed else current["version_id"]
        con = self._connect()
        try:
            if revision_changed:
                row = con.execute("SELECT * FROM memories WHERE id=?", (memory_id,)).fetchone()
                con.execute(
                    "INSERT INTO memory_revisions(version_id,memory_id,content,kind,tags_json,"
                    "provenance_json,valid_from,valid_to,superseded_by_version) "
                    "VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        row["version_id"],
                        memory_id,
                        row["content"],
                        row["kind"],
                        row["tags_json"],
                        row["provenance_json"],
                        row["valid_from"],
                        now,
                        next_version_id,
                    ),
                )
            con.execute(
                "UPDATE memories SET content=?,content_hash=?,kind=?,tags_json=?,provenance_json=?,"
                "version_id=?,valid_from=?,updated_at=? WHERE id=?",
                (
                    content,
                    content_hash,
                    kind,
                    json.dumps(tags),
                    json.dumps(provenance_value, sort_keys=True),
                    next_version_id,
                    now if revision_changed else current["valid_from"],
                    now if revision_changed else current["updated_at"],
                    memory_id,
                ),
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
            con.execute("DELETE FROM memory_revisions WHERE memory_id = ?", (memory_id,))
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
    decision_config: Any = None,
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
    from .decision_runtime import decide_memory_relevance

    matches, decision_info = decide_memory_relevance(query, matches, decision_config)
    if decision_info is not None:
        data["memory_decision"] = decision_info
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
