"""FTS5 lexical retrieval.

Exact symbol matching is handled by dedicated B-tree indexes outside FTS scoring
so an exact hit is never buried by relevance ranking.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")

#: Very common words carry no discriminating signal in a natural-language
#: question, and including them would match nearly every document.
STOPWORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "but", "by", "do", "does", "for", "from",
        "has", "have", "how", "i", "if", "in", "is", "it", "its", "of", "on", "or", "our",
        "so", "that", "the", "their", "then", "there", "these", "they", "this", "to", "was",
        "we", "were", "what", "when", "where", "which", "who", "why", "will", "with", "you",
        "your",
    }
)


def _tokens(query: str) -> list[str]:
    """Significant tokens from a query, stopwords removed."""
    return [token for token in _TOKEN_RE.findall(query) if token.lower() not in STOPWORDS]

#: FTS5 operators that must never reach the MATCH expression.
_UNSAFE_QUERY_RE = re.compile(r'["*():^-]')


def sanitize_match(query: str) -> str:
    """Turn free text into a safe FTS5 AND expression.

    User input is untrusted; quoting every token makes the query a literal
    phrase list and removes any operator interpretation.
    """
    tokens = _tokens(query)
    if not tokens:
        return ""
    quoted = ['"' + token.replace('"', "") + '"' for token in tokens]
    return " AND ".join(quoted)


def sanitize_match_or(query: str) -> str:
    """Same, but matching any token.

    Natural-language questions rarely contain every term of a target document,
    so an AND-only query returns nothing. The OR form lets BM25 rank partial
    matches instead of failing outright.
    """
    tokens = _tokens(query)
    if not tokens:
        return ""
    quoted = ['"' + token.replace('"', "") + '"' for token in tokens]
    return " OR ".join(quoted)


def _bm25_query(con: sqlite3.Connection, entity_ids: list[str]) -> str:  # pragma: no cover
    return ""


class LexicalStore:
    """Search the FTS5 mirror and exact symbol indexes."""

    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def index_entity(self, entity_id: str, fields: dict[str, str | None]) -> None:
        self.con.execute("DELETE FROM entity_fts WHERE entity_id=?", (entity_id,))
        self.con.execute(
            "INSERT INTO entity_fts(entity_id, name, qualified_name, path, signature, docstring, semantic_text)"
            " VALUES(?,?,?,?,?,?,?)",
            (
                entity_id,
                fields.get("name") or "",
                fields.get("qualified_name") or "",
                fields.get("path") or "",
                fields.get("signature") or "",
                fields.get("docstring") or "",
                fields.get("semantic_text") or "",
            ),
        )

    def bulk_index(self, rows: list[tuple[str, dict[str, str | None]]]) -> None:
        if not rows:
            return
        ids = [r[0] for r in rows]
        self.con.executemany("DELETE FROM entity_fts WHERE entity_id=?", [(i,) for i in ids])
        self.con.executemany(
            "INSERT INTO entity_fts(entity_id, name, qualified_name, path, signature, docstring, semantic_text)"
            " VALUES(?,?,?,?,?,?,?)",
            [
                (
                    entity_id,
                    fields.get("name") or "",
                    fields.get("qualified_name") or "",
                    fields.get("path") or "",
                    fields.get("signature") or "",
                    fields.get("docstring") or "",
                    fields.get("semantic_text") or "",
                )
                for entity_id, fields in rows
            ],
        )

    def remove_entity(self, entity_id: str) -> None:
        self.con.execute("DELETE FROM entity_fts WHERE entity_id=?", (entity_id,))

    def search(
        self,
        query: str,
        *,
        limit: int = 40,
        kinds: list[str] | None = None,
        languages: list[str] | None = None,
        root_ids: list[str] | None = None,
        path_prefixes: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Run a lexical query, returning ranked entities with BM25 scores.

        Tries a strict AND match first so an exact multi-term phrase still
        ranks highest, then falls back to OR so a natural-language question
        that shares no single document with every term still returns results.
        """
        match = sanitize_match(query)
        if not match:
            return []
        return self._run(match, limit, kinds, languages, root_ids, path_prefixes) or self._run(
            sanitize_match_or(query), limit, kinds, languages, root_ids, path_prefixes
        )

    def _run(
        self,
        match: str,
        limit: int,
        kinds: list[str] | None,
        languages: list[str] | None,
        root_ids: list[str] | None,
        path_prefixes: list[str] | None,
    ) -> list[dict[str, Any]]:
        clauses = ["entity_fts MATCH ?"]
        params: list[Any] = [match]
        if kinds:
            clauses.append(f"e.kind IN ({','.join('?' * len(kinds))})")
            params.extend(kinds)
        if languages:
            clauses.append(f"e.language IN ({','.join('?' * len(languages))})")
            params.extend(languages)
        if root_ids:
            clauses.append(f"e.root_id IN ({','.join('?' * len(root_ids))})")
            params.extend(root_ids)
        if path_prefixes:
            ors = " OR ".join("e.path LIKE ?" for _ in path_prefixes)
            clauses.append(f"({ors})")
            params.extend([f"{p}%" for p in path_prefixes])

        sql = (
            "SELECT f.entity_id AS entity_id, bm25(entity_fts, 8.0, 4.0, 2.0, 1.5, 1.5, 0.5) AS score "
            "FROM entity_fts f JOIN entities e ON e.id = f.entity_id "
            f"WHERE {' AND '.join(clauses)} "
            "ORDER BY score LIMIT ?"
        )
        params.append(limit)
        rows = self.con.execute(sql, params).fetchall()
        # bm25() returns better (more negative) values first; invert to a
        # positive magnitude so fusion weights behave monotonically.
        return [{"entity_id": r["entity_id"], "score": abs(float(r["score"]))} for r in rows]

    def count(self) -> int:
        return int(self.con.execute("SELECT COUNT(*) FROM entity_fts").fetchone()[0])