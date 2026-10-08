"""Persistence operations for entities, edges, roots, files and derived data.

All mutation happens inside a caller-provided transaction so an indexing batch
either lands completely or not at all.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from ..models.edge import Edge
from ..models.entity import Entity, utcnow
from .fts import LexicalStore

_ENTITY_COLUMNS = (
    "id, root_id, kind, language, name, qualified_name, path, parent_id, "
    "start_byte, end_byte, start_line, end_line, visibility, signature, docstring, "
    "content_hash, semantic_hash, is_generated, is_external, metadata_json, created_at, updated_at"
)


class Repository:
    """Read/write access to the canonical index."""

    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con
        self.fts = LexicalStore(con)

    # ---------------------------------------------------------------- roots

    def upsert_root(
        self,
        *,
        root_id: str,
        path: str,
        name: str,
        is_primary: bool = False,
        vcs_branch: str | None = None,
        vcs_head: str | None = None,
    ) -> None:
        now = utcnow()
        self.con.execute(
            "INSERT INTO roots(root_id, path, name, is_primary, vcs_branch, vcs_head, created_at, updated_at)"
            " VALUES(?,?,?,?,?,?,?,?)"
            " ON CONFLICT(root_id) DO UPDATE SET path=excluded.path, name=excluded.name,"
            " is_primary=excluded.is_primary, vcs_branch=excluded.vcs_branch,"
            " vcs_head=excluded.vcs_head, updated_at=excluded.updated_at",
            (root_id, path, name, int(is_primary), vcs_branch, vcs_head, now, now),
        )

    def list_roots(self) -> list[dict[str, Any]]:
        rows = self.con.execute(
            "SELECT root_id, path, name, is_primary, vcs_branch, vcs_head, updated_at FROM roots ORDER BY is_primary DESC, name"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_root(self, root_id: str) -> dict[str, Any] | None:
        row = self.con.execute("SELECT * FROM roots WHERE root_id=?", (root_id,)).fetchone()
        return dict(row) if row else None

    def set_root_vcs(self, root_id: str, branch: str | None, head: str | None) -> None:
        self.con.execute(
            "UPDATE roots SET vcs_branch=?, vcs_head=?, updated_at=? WHERE root_id=?",
            (branch, head, utcnow(), root_id),
        )

    # ------------------------------------------------------------- entities

    def upsert_entities(self, entities: list[Entity]) -> None:
        if not entities:
            return
        self.con.executemany(
            f"INSERT INTO entities({_ENTITY_COLUMNS}) VALUES({','.join('?' * 22)})"
            " ON CONFLICT(id) DO UPDATE SET kind=excluded.kind, language=excluded.language,"
            " name=excluded.name, qualified_name=excluded.qualified_name, path=excluded.path,"
            " parent_id=excluded.parent_id, start_byte=excluded.start_byte, end_byte=excluded.end_byte,"
            " start_line=excluded.start_line, end_line=excluded.end_line, visibility=excluded.visibility,"
            " signature=excluded.signature, docstring=excluded.docstring, content_hash=excluded.content_hash,"
            " semantic_hash=excluded.semantic_hash, is_generated=excluded.is_generated,"
            " is_external=excluded.is_external, metadata_json=excluded.metadata_json, updated_at=excluded.updated_at",
            [e.to_row() for e in entities],
        )

    def get_entity(self, entity_id: str) -> Entity | None:
        row = self.con.execute(
            f"SELECT {_ENTITY_COLUMNS} FROM entities WHERE id=?", (entity_id,)
        ).fetchone()
        return Entity.from_row(tuple(row)) if row else None

    def get_entities(self, entity_ids: list[str]) -> dict[str, Entity]:
        if not entity_ids:
            return {}
        out: dict[str, Entity] = {}
        for chunk in _chunks(entity_ids, 500):
            placeholders = ",".join("?" * len(chunk))
            rows = self.con.execute(
                f"SELECT {_ENTITY_COLUMNS} FROM entities WHERE id IN ({placeholders})", chunk
            ).fetchall()
            for row in rows:
                entity = Entity.from_row(tuple(row))
                out[entity.id] = entity
        return out

    def find_by_qualified_name(self, qualified_name: str, *, root_id: str | None = None) -> list[Entity]:
        if root_id:
            rows = self.con.execute(
                f"SELECT {_ENTITY_COLUMNS} FROM entities WHERE qualified_name=? AND root_id=? ORDER BY LENGTH(path)",
                (qualified_name, root_id),
            ).fetchall()
        else:
            rows = self.con.execute(
                f"SELECT {_ENTITY_COLUMNS} FROM entities WHERE qualified_name=? ORDER BY LENGTH(path)",
                (qualified_name,),
            ).fetchall()
        return [Entity.from_row(tuple(r)) for r in rows]

    def find_by_name(self, name: str, *, limit: int = 50) -> list[Entity]:
        rows = self.con.execute(
            f"SELECT {_ENTITY_COLUMNS} FROM entities WHERE name=? ORDER BY LENGTH(COALESCE(qualified_name,'')) LIMIT ?",
            (name, limit),
        ).fetchall()
        return [Entity.from_row(tuple(r)) for r in rows]

    def find_by_path(self, path: str, *, root_id: str | None = None) -> list[Entity]:
        if root_id:
            rows = self.con.execute(
                f"SELECT {_ENTITY_COLUMNS} FROM entities WHERE path=? AND root_id=?",
                (path, root_id),
            ).fetchall()
        else:
            rows = self.con.execute(
                f"SELECT {_ENTITY_COLUMNS} FROM entities WHERE path=?", (path,)
            ).fetchall()
        return [Entity.from_row(tuple(r)) for r in rows]

    def find_file_entity(self, path: str, *, root_id: str | None = None) -> Entity | None:
        candidates = self.find_by_path(path, root_id=root_id)
        for entity in candidates:
            if entity.kind == "file":
                return entity
        return candidates[0] if candidates else None

    def entities_owned_by_path(self, path: str, *, root_id: str) -> list[Entity]:
        rows = self.con.execute(
            f"SELECT {_ENTITY_COLUMNS} FROM entities WHERE path=? AND root_id=?",
            (path, root_id),
        ).fetchall()
        return [Entity.from_row(tuple(r)) for r in rows]

    def delete_entities(self, entity_ids: list[str]) -> None:
        if not entity_ids:
            return
        for chunk in _chunks(entity_ids, 500):
            placeholders = ",".join("?" * len(chunk))
            self.con.execute(f"DELETE FROM entities WHERE id IN ({placeholders})", chunk)
            self.con.executemany("DELETE FROM entity_fts WHERE entity_id=?", [(i,) for i in chunk])

    def iter_entities(
        self,
        *,
        root_id: str | None = None,
        kinds: list[str] | None = None,
        batch: int = 1000,
    ) -> list[Entity]:
        clauses, params = [], []
        if root_id:
            clauses.append("root_id=?")
            params.append(root_id)
        if kinds:
            clauses.append(f"kind IN ({','.join('?' * len(kinds))})")
            params.extend(kinds)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.con.execute(
            f"SELECT {_ENTITY_COLUMNS} FROM entities {where} LIMIT ?", (*params, batch)
        ).fetchall()
        return [Entity.from_row(tuple(r)) for r in rows]

    def count_entities(self, *, root_id: str | None = None) -> int:
        if root_id:
            return int(
                self.con.execute("SELECT COUNT(*) FROM entities WHERE root_id=?", (root_id,)).fetchone()[0]
            )
        return int(self.con.execute("SELECT COUNT(*) FROM entities").fetchone()[0])

    def children_of(self, entity_id: str) -> list[Entity]:
        rows = self.con.execute(
            f"SELECT {_ENTITY_COLUMNS} FROM entities WHERE parent_id=?", (entity_id,)
        ).fetchall()
        return [Entity.from_row(tuple(r)) for r in rows]

    # ---------------------------------------------------------------- edges

    def upsert_edges(self, edges: list[Edge]) -> None:
        if not edges:
            return
        self.con.executemany(
            "INSERT INTO edges(id, source_id, target_id, type, provenance, confidence, resolver,"
            " source_path, source_line, source_col, metadata_json, created_at, updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET confidence=excluded.confidence,"
            " metadata_json=excluded.metadata_json, updated_at=excluded.updated_at",
            [e.to_row() for e in edges],
        )

    def delete_edges(self, edge_ids: list[str]) -> None:
        if not edge_ids:
            return
        for chunk in _chunks(edge_ids, 500):
            placeholders = ",".join("?" * len(chunk))
            self.con.execute(f"DELETE FROM edges WHERE id IN ({placeholders})", chunk)

    def delete_edges_touching(self, entity_ids: list[str]) -> None:
        """Remove every edge incident to the given entities, in either direction.

        Both directions must go: leaving an inbound edge would resurrect a
        dangling reference to a deleted entity.
        """
        if not entity_ids:
            return
        for chunk in _chunks(entity_ids, 400):
            placeholders = ",".join("?" * len(chunk))
            self.con.execute(
                f"DELETE FROM edges WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})",
                (*chunk, *chunk),
            )
            self.con.execute(
                f"DELETE FROM unresolved_refs WHERE source_id IN ({placeholders})", chunk
            )

    def get_edges(
        self,
        entity_id: str,
        *,
        direction: str = "both",
        types: list[str] | None = None,
        provenances: list[str] | None = None,
        limit: int = 500,
    ) -> list[Edge]:
        clauses = []
        params: list[Any] = []
        if direction == "outbound":
            clauses.append("source_id=?")
            params.append(entity_id)
        elif direction == "inbound":
            clauses.append("target_id=?")
            params.append(entity_id)
        else:
            clauses.append("(source_id=? OR target_id=?)")
            params.extend([entity_id, entity_id])
        if types:
            clauses.append(f"type IN ({','.join('?' * len(types))})")
            params.extend(types)
        if provenances:
            clauses.append(f"provenance IN ({','.join('?' * len(provenances))})")
            params.extend(provenances)
        params.append(limit)
        rows = self.con.execute(
            "SELECT id, source_id, target_id, type, provenance, confidence, resolver,"
            " source_path, source_line, source_col, metadata_json, created_at, updated_at"
            f" FROM edges WHERE {' AND '.join(clauses)} ORDER BY confidence DESC LIMIT ?",
            params,
        ).fetchall()
        return [Edge.from_row(tuple(r)) for r in rows]

    def count_edges(self, *, root_id: str | None = None, types: list[str] | None = None) -> int:
        clauses, params = [], []
        if types:
            clauses.append(f"e.type IN ({','.join('?' * len(types))})")
            params.extend(types)
        if root_id:
            clauses.append("(s.root_id=? OR t.root_id=?)")
            params.extend([root_id, root_id])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            "SELECT COUNT(*) FROM edges e "
            "LEFT JOIN entities s ON s.id=e.source_id LEFT JOIN entities t ON t.id=e.target_id "
            f"{where}"
        )
        return int(self.con.execute(sql, params).fetchone()[0])

    def iter_edges(self, *, root_id: str | None = None, batch: int = 20000) -> list[Edge]:
        if root_id:
            rows = self.con.execute(
                "SELECT e.id, e.source_id, e.target_id, e.type, e.provenance, e.confidence, e.resolver,"
                " e.source_path, e.source_line, e.source_col, e.metadata_json, e.created_at, e.updated_at"
                " FROM edges e JOIN entities s ON s.id=e.source_id WHERE s.root_id=? LIMIT ?",
                (root_id, batch),
            ).fetchall()
        else:
            rows = self.con.execute(
                "SELECT id, source_id, target_id, type, provenance, confidence, resolver,"
                " source_path, source_line, source_col, metadata_json, created_at, updated_at FROM edges LIMIT ?",
                (batch,),
            ).fetchall()
        return [Edge.from_row(tuple(r)) for r in rows]

    def all_edges_between(self, source_id: str, target_id: str) -> list[Edge]:
        rows = self.con.execute(
            "SELECT id, source_id, target_id, type, provenance, confidence, resolver,"
            " source_path, source_line, source_col, metadata_json, created_at, updated_at"
            " FROM edges WHERE source_id=? AND target_id=?",
            (source_id, target_id),
        ).fetchall()
        return [Edge.from_row(tuple(r)) for r in rows]

    # --------------------------------------------------------------- files

    def record_file(
        self,
        *,
        root_id: str,
        path: str,
        size: int,
        mtime_ns: int,
        content_hash: str,
        language: str | None,
        parse_status: str,
        is_generated: bool = False,
        is_media: bool = False,
    ) -> None:
        self.con.execute(
            "INSERT INTO files(root_id, path, size, mtime_ns, content_hash, language, parse_status,"
            " is_generated, is_media, last_indexed_at) VALUES(?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(root_id, path) DO UPDATE SET size=excluded.size, mtime_ns=excluded.mtime_ns,"
            " content_hash=excluded.content_hash, language=excluded.language,"
            " parse_status=excluded.parse_status, is_generated=excluded.is_generated,"
            " is_media=excluded.is_media, last_indexed_at=excluded.last_indexed_at",
            (root_id, path, size, mtime_ns, content_hash, language, parse_status,
             int(is_generated), int(is_media), utcnow()),
        )

    def get_file(self, root_id: str, path: str) -> dict[str, Any] | None:
        row = self.con.execute(
            "SELECT * FROM files WHERE root_id=? AND path=?", (root_id, path)
        ).fetchone()
        return dict(row) if row else None

    def all_files(self, root_id: str | None = None) -> list[dict[str, Any]]:
        if root_id:
            rows = self.con.execute("SELECT * FROM files WHERE root_id=?", (root_id,)).fetchall()
        else:
            rows = self.con.execute("SELECT * FROM files").fetchall()
        return [dict(r) for r in rows]

    def delete_files(self, root_id: str, paths: list[str]) -> None:
        for path in paths:
            self.con.execute("DELETE FROM files WHERE root_id=? AND path=?", (root_id, path))

    # ------------------------------------------------------ unresolved refs

    def record_unresolved(
        self,
        *,
        id: str,
        source_id: str,
        name: str,
        path: str | None,
        line: int | None,
        edge_type: str,
        resolver: str | None,
        candidates: list[str],
        root_id: str | None,
    ) -> None:
        self.con.execute(
            "INSERT INTO unresolved_refs(id, source_id, name, path, line, edge_type, resolver, candidates, root_id)"
            " VALUES(?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET name=excluded.name, path=excluded.path, line=excluded.line,"
            " edge_type=excluded.edge_type, resolver=excluded.resolver, candidates=excluded.candidates",
            (id, source_id, name, path, line, edge_type, resolver,
             json.dumps(candidates, separators=(",", ":")), root_id),
        )

    def unresolved_for(self, entity_id: str) -> list[dict[str, Any]]:
        rows = self.con.execute(
            "SELECT * FROM unresolved_refs WHERE source_id=?", (entity_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def count_unresolved(self) -> int:
        return int(self.con.execute("SELECT COUNT(*) FROM unresolved_refs").fetchone()[0])

    # ------------------------------------------------------------- metrics

    def store_metrics(self, metrics: dict[str, dict[str, float]]) -> None:
        now = utcnow()
        self.con.executemany(
            "INSERT INTO metrics(entity_id, metric, value, computed_at) VALUES(?,?,?,?)"
            " ON CONFLICT(entity_id, metric) DO UPDATE SET value=excluded.value, computed_at=excluded.computed_at",
            [(eid, name, float(value), now) for eid, values in metrics.items() for name, value in values.items()],
        )

    def metrics_for(self, entity_id: str) -> dict[str, float]:
        rows = self.con.execute(
            "SELECT metric, value FROM metrics WHERE entity_id=?", (entity_id,)
        ).fetchall()
        return {r[0]: float(r[1]) for r in rows}

    def metrics_map(self) -> dict[str, dict[str, float]]:
        rows = self.con.execute("SELECT entity_id, metric, value FROM metrics").fetchall()
        out: dict[str, dict[str, float]] = {}
        for entity_id, metric, value in rows:
            out.setdefault(entity_id, {})[metric] = float(value)
        return out

    def clear_metrics(self) -> None:
        self.con.execute("DELETE FROM metrics")

    # --------------------------------------------------------- communities

    def replace_communities(
        self, mode: str, algorithm: str, resolution: float, memberships: dict[str, list[str]],
        labels: dict[str, str],
    ) -> None:
        now = utcnow()
        self.con.execute(
            "DELETE FROM community_members WHERE mode=? AND algorithm=?", (mode, algorithm)
        )
        self.con.execute("DELETE FROM communities WHERE mode=? AND algorithm=?", (mode, algorithm))
        for community_id, entity_ids in memberships.items():
            self.con.execute(
                "INSERT INTO communities(community_id, algorithm, mode, resolution, label, size, metadata_json, computed_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (community_id, algorithm, mode, resolution, labels.get(community_id),
                 len(entity_ids), "{}", now),
            )
            self.con.executemany(
                "INSERT OR REPLACE INTO community_members(community_id, algorithm, mode, entity_id, weight)"
                " VALUES(?,?,?,?,1.0)",
                [(community_id, algorithm, mode, e) for e in entity_ids],
            )

    def communities(self, mode: str) -> list[dict[str, Any]]:
        rows = self.con.execute(
            "SELECT community_id, label, size, resolution FROM communities WHERE mode=? ORDER BY size DESC",
            (mode,),
        ).fetchall()
        return [dict(r) for r in rows]

    def community_of(self, entity_id: str, mode: str) -> dict[str, Any] | None:
        row = self.con.execute(
            "SELECT c.community_id, c.label, c.size FROM community_members m"
            " JOIN communities c ON c.community_id=m.community_id AND c.mode=m.mode AND c.algorithm=m.algorithm"
            " WHERE m.entity_id=? AND m.mode=?",
            (entity_id, mode),
        ).fetchone()
        return dict(row) if row else None

    def community_map(self, mode: str) -> dict[str, str]:
        rows = self.con.execute(
            "SELECT entity_id, community_id FROM community_members WHERE mode=?", (mode,)
        ).fetchall()
        return {r[0]: r[1] for r in rows}

    # ---------------------------------------------------------- embeddings

    def record_embedding(self, record: dict[str, Any]) -> None:
        self.con.execute(
            "INSERT INTO embeddings(embedding_id, entity_id, chunk_id, modality, model_id, model_revision,"
            " dimensions, task_type, input_hash, norm, created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(embedding_id) DO UPDATE SET input_hash=excluded.input_hash, norm=excluded.norm",
            (
                record["embedding_id"], record.get("entity_id"), record.get("chunk_id"),
                record.get("modality", "text"), record["model_id"], record["model_revision"],
                record["dimensions"], record["task_type"], record["input_hash"],
                record.get("norm"), utcnow(),
            ),
        )

    def set_entity_semantic_hash(self, entity_id: str, input_hash: str) -> None:
        """Record which semantic text an entity's stored vector was built from."""
        self.con.execute(
            "UPDATE entities SET semantic_hash=? WHERE id=?", (input_hash, entity_id)
        )

    def embedding_ids_for(self, entity_ids: list[str]) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for chunk in _chunks(entity_ids, 400):
            placeholders = ",".join("?" * len(chunk))
            rows = self.con.execute(
                f"SELECT entity_id, embedding_id FROM embeddings WHERE entity_id IN ({placeholders})",
                chunk,
            ).fetchall()
            for entity_id, embedding_id in rows:
                out.setdefault(entity_id, []).append(embedding_id)
        return out

    def delete_embeddings_for(self, entity_ids: list[str]) -> None:
        if not entity_ids:
            return
        for chunk in _chunks(entity_ids, 400):
            placeholders = ",".join("?" * len(chunk))
            self.con.execute(f"DELETE FROM embeddings WHERE entity_id IN ({placeholders})", chunk)

    def embedding_info(self, entity_id: str) -> list[dict[str, Any]]:
        rows = self.con.execute(
            "SELECT embedding_id, modality, model_id, model_revision, dimensions, task_type, input_hash, norm"
            " FROM embeddings WHERE entity_id=?",
            (entity_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def embedding_counts(self) -> dict[str, int]:
        row = self.con.execute(
            "SELECT model_id, model_revision, dimensions, task_type, COUNT(*) FROM embeddings"
            " GROUP BY model_id, model_revision, dimensions, task_type"
        ).fetchall()
        return {
            f"{r[0]}@{r[1][:8]}:{r[2]}:{r[3]}": int(r[4]) for r in row
        }

    # -------------------------------------------------------------- chunks

    def replace_chunks(self, entity_id: str, chunks: list[dict[str, Any]]) -> None:
        self.con.execute("DELETE FROM chunks WHERE entity_id=?", (entity_id,))
        if not chunks:
            return
        self.con.executemany(
            "INSERT INTO chunks(chunk_id, entity_id, ordinal, modality, content, content_hash,"
            " token_count, start_line, end_line, start_time, end_time, metadata_json)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    c["chunk_id"], entity_id, c["ordinal"], c.get("modality", "text"),
                    c.get("content"), c["content_hash"], c.get("token_count"),
                    c.get("start_line"), c.get("end_line"), c.get("start_time"),
                    c.get("end_time"), json.dumps(c.get("metadata", {}), separators=(",", ":")),
                )
                for c in chunks
            ],
        )

    def chunks_for(self, entity_id: str) -> list[dict[str, Any]]:
        rows = self.con.execute(
            "SELECT chunk_id, ordinal, modality, content, content_hash, token_count,"
            " start_line, end_line, start_time, end_time, metadata_json FROM chunks"
            " WHERE entity_id=? ORDER BY ordinal",
            (entity_id,),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["metadata"] = json.loads(d.pop("metadata_json") or "{}")
            out.append(d)
        return out

    # -------------------------------------------------------- index health

    def counts(self) -> dict[str, int]:
        return {
            "roots": int(self.con.execute("SELECT COUNT(*) FROM roots").fetchone()[0]),
            "files": int(self.con.execute("SELECT COUNT(*) FROM files").fetchone()[0]),
            "entities": int(self.con.execute("SELECT COUNT(*) FROM entities").fetchone()[0]),
            "edges": int(self.con.execute("SELECT COUNT(*) FROM edges").fetchone()[0]),
            "embeddings": int(self.con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]),
            "chunks": int(self.con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]),
            "unresolved": int(self.con.execute("SELECT COUNT(*) FROM unresolved_refs").fetchone()[0]),
            "communities": int(self.con.execute("SELECT COUNT(*) FROM communities").fetchone()[0]),
            "fts_rows": int(self.con.execute("SELECT COUNT(*) FROM entity_fts").fetchone()[0]),
        }


def _chunks(items: list[Any], size: int) -> list[list[Any]]:
    """Split a list into batches to respect SQLite's variable limit."""
    return [items[i : i + size] for i in range(0, len(items), size)]