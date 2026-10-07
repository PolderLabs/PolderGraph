"""Vector storage behind a replaceable backend interface.

The default backend is sqlite-vec, which keeps the one-database/no-daemon UX.
When the extension is unavailable we fall back to an explicitly implemented
brute-force backend rather than silently disabling semantic search.
"""

from __future__ import annotations

import array
import json
import math
import sqlite3
import struct
from typing import Any, Protocol, runtime_checkable

from ..errors import BackendUnavailableError
from .sqlite import load_vec_extension


@runtime_checkable
class VectorStore(Protocol):
    """Minimal vector storage contract."""

    def upsert(self, records: list[VectorRecord]) -> None: ...
    def delete(self, ids: list[str]) -> None: ...
    def search(
        self, vector: list[float], *, top_k: int, filters: dict[str, Any] | None = None
    ) -> list[VectorHit]: ...
    def available(self) -> bool: ...


def l2_normalize(vector: list[float]) -> list[float]:
    """Return a unit-norm copy, leaving a zero vector untouched."""
    norm = math.sqrt(sum(v * v for v in vector))
    if norm <= 0.0:
        return list(vector)
    return [v / norm for v in vector]


def vector_norm(vector: list[float]) -> float:
    return math.sqrt(sum(v * v for v in vector))


class VectorRecord:
    """One stored embedding with the metadata needed to invalidate it exactly."""

    __slots__ = (
        "dimensions",
        "embedding_id",
        "entity_id",
        "input_hash",
        "modality",
        "model_id",
        "model_revision",
        "norm",
        "task_type",
        "vector",
    )

    def __init__(
        self,
        *,
        embedding_id: str,
        vector: list[float],
        dimensions: int,
        model_id: str,
        model_revision: str,
        task_type: str,
        input_hash: str,
        entity_id: str | None = None,
        modality: str = "text",
        norm: float | None = None,
    ) -> None:
        self.embedding_id = embedding_id
        self.entity_id = entity_id
        self.vector = vector
        self.dimensions = dimensions
        self.model_id = model_id
        self.model_revision = model_revision
        self.task_type = task_type
        self.input_hash = input_hash
        self.modality = modality
        self.norm = norm

    def to_blob(self) -> bytes:
        """Serialize float32 little-endian, matching sqlite-vec's expected layout."""
        return struct.pack(f"{len(self.vector)}f", *self.vector)

    def normalized(self) -> VectorRecord:
        """Return a unit-norm copy.

        The canonical index stores normalized vectors so cosine similarity is a
        dot product; sqlite-vec then converts L2 distance with cos = 1 - d^2/2.
        Normalizing here keeps that identity exact instead of approximate.
        """
        normalized = l2_normalize(self.vector)
        norm = vector_norm(normalized)
        clone = VectorRecord(
            embedding_id=self.embedding_id,
            entity_id=self.entity_id,
            vector=normalized,
            dimensions=self.dimensions,
            model_id=self.model_id,
            model_revision=self.model_revision,
            task_type=self.task_type,
            input_hash=self.input_hash,
            modality=self.modality,
            norm=norm,
        )
        return clone


class VectorHit:
    """A search result: which embedding matched and how far."""

    __slots__ = ("distance", "embedding_id", "entity_id", "modality", "similarity")

    def __init__(
        self,
        embedding_id: str,
        entity_id: str | None,
        distance: float,
        modality: str = "text",
    ) -> None:
        self.embedding_id = embedding_id
        self.entity_id = entity_id
        self.distance = distance
        self.similarity = 1.0 - distance
        self.modality = modality

    def to_dict(self) -> dict[str, Any]:
        return {
            "embedding_id": self.embedding_id,
            "entity_id": self.entity_id,
            "similarity": round(self.similarity, 6),
            "modality": self.modality,
        }


def _vec_table_name(dimensions: int, model_id: str, task_type: str) -> str:
    """Deterministic table name for a (dimensions, model, task) combination.

    Embeddings from different revisions/dimensions are never mixed or
    overwritten in place, per the data model contract.
    """
    safe_model = model_id.replace("/", "_").replace("-", "_")
    return f"vec_{safe_model}_{task_type}_{dimensions}"


class BruteForceStore:
    """Explicit fallback backend used when sqlite-vec is unavailable.

    Correctness over speed; documented as unsuitable for large indexes.
    """

    def __init__(
        self,
        con: sqlite3.Connection,
        *,
        dimensions: int,
        model_id: str,
        task_type: str = "document",
    ) -> None:
        self.con = con
        self.dimensions = dimensions
        self.model_id = model_id
        self.task_type = task_type
        self.table = "_bruteforce_vectors"

    def available(self) -> bool:
        return True

    def ensure_table(self) -> None:
        self.con.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.table} (
                embedding_id TEXT PRIMARY KEY,
                entity_id    TEXT,
                modality     TEXT,
                dimensions   INTEGER NOT NULL,
                model_id     TEXT NOT NULL,
                vector       BLOB NOT NULL
            )"""
        )

    def upsert(self, records: list[VectorRecord]) -> None:
        if not records:
            return
        self.ensure_table()
        self.con.executemany(
            f"INSERT OR REPLACE INTO {self.table}"
            "(embedding_id, entity_id, modality, dimensions, model_id, vector) VALUES(?,?,?,?,?,?)",
            [
                (
                    r.embedding_id,
                    r.entity_id,
                    r.modality,
                    r.dimensions,
                    r.model_id,
                    r.normalized().to_blob(),
                )
                for r in records
            ],
        )

    def delete(self, ids: list[str]) -> None:
        if not ids:
            return
        self.ensure_table()
        self.con.executemany(f"DELETE FROM {self.table} WHERE embedding_id=?", [(i,) for i in ids])

    def delete_by_entity(self, entity_ids: list[str]) -> None:
        if not entity_ids:
            return
        self.ensure_table()
        self.con.executemany(
            f"DELETE FROM {self.table} WHERE entity_id=?", [(e,) for e in entity_ids]
        )

    def search(
        self, vector: list[float], *, top_k: int, filters: dict[str, Any] | None = None
    ) -> list[VectorHit]:
        self.ensure_table()
        query = array.array("f", vector)
        qnorm = math.sqrt(sum(v * v for v in query)) or 1.0
        clause = ""
        params: list[Any] = []
        conditions = []
        if filters and filters.get("modality"):
            conditions.append("modality = ?")
            params.append(filters["modality"])
        if filters and filters.get("model_id"):
            conditions.append("model_id = ?")
            params.append(filters["model_id"])
        if conditions:
            clause = " WHERE " + " AND ".join(conditions)
        rows = self.con.execute(
            f"SELECT embedding_id, entity_id, modality, vector, dimensions FROM {self.table}{clause}",
            params,
        ).fetchall()
        hits: list[VectorHit] = []
        for row in rows:
            if row[4] != self.dimensions:
                continue
            stored = array.array("f")
            stored.frombytes(row[3])
            snorm = math.sqrt(sum(v * v for v in stored)) or 1.0
            dot = sum(a * b for a, b in zip(query, stored, strict=False))
            hits.append(VectorHit(row[0], row[1], 1.0 - dot / (qnorm * snorm), row[2]))
        hits.sort(key=lambda h: h.similarity, reverse=True)
        return hits[:top_k]

    def count(self) -> int:
        self.ensure_table()
        return int(self.con.execute(f"SELECT COUNT(*) FROM {self.table}").fetchone()[0])


class SQLiteVecStore:
    """Default vector backend using the sqlite-vec extension."""

    def __init__(
        self,
        con: sqlite3.Connection,
        *,
        dimensions: int,
        model_id: str,
        task_type: str = "document",
    ) -> None:
        self.con = con
        self.dimensions = dimensions
        self.model_id = model_id
        self.task_type = task_type
        self.table = _vec_table_name(dimensions, model_id, task_type)
        #: Readable mirror of the stored vectors.
        #
        #: A `vec0` virtual table cannot be selected from to recover the raw
        #: float vector, but neighbours-of-an-entity and semantic-edge
        #: computation need exactly that. This shadow table holds the same
        #: blobs and is kept in step by the same upsert/delete calls.
        self.shadow_table = f"{self.table}_vectors"
        self._enabled = load_vec_extension(con)

    def available(self) -> bool:
        return self._enabled

    def ensure_table(self) -> None:
        if not self._enabled:
            raise BackendUnavailableError(
                "sqlite-vec extension is not loaded.",
                remediation="Install the vector extra: uv pip install 'poldergraph[vectors]'",
            )
        self.con.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS {self.table} USING vec0("
            f"embedding_id TEXT PRIMARY KEY, "
            f"entity_id TEXT, "
            f"modality TEXT, "
            f"embedding float[{self.dimensions}])"
        )
        self.con.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.shadow_table} (
                embedding_id TEXT PRIMARY KEY,
                entity_id    TEXT,
                modality     TEXT,
                dimensions   INTEGER NOT NULL,
                vector       BLOB NOT NULL
            )"""
        )
        self.con.execute(
            f"CREATE INDEX IF NOT EXISTS {self.shadow_table}_entity ON {self.shadow_table}(entity_id)"
        )

    def upsert(self, records: list[VectorRecord]) -> None:
        if not records:
            return
        self.ensure_table()
        for record in records:
            record = record.normalized()
            self.con.execute(
                f"DELETE FROM {self.table} WHERE embedding_id=?", (record.embedding_id,)
            )
            self.con.execute(
                f"INSERT INTO {self.table}(embedding_id, entity_id, modality, embedding) VALUES(?, ?, ?, ?)",
                (record.embedding_id, record.entity_id, record.modality, record.to_blob()),
            )
            self.con.execute(
                f"INSERT OR REPLACE INTO {self.shadow_table}"
                "(embedding_id, entity_id, modality, dimensions, vector) VALUES(?,?,?,?,?)",
                (
                    record.embedding_id,
                    record.entity_id,
                    record.modality,
                    record.dimensions,
                    record.to_blob(),
                ),
            )

    def delete(self, ids: list[str]) -> None:
        if not ids or not self._enabled:
            return
        self.ensure_table()
        self.con.executemany(f"DELETE FROM {self.table} WHERE embedding_id=?", [(i,) for i in ids])
        self.con.executemany(
            f"DELETE FROM {self.shadow_table} WHERE embedding_id=?", [(i,) for i in ids]
        )

    def delete_by_entity(self, entity_ids: list[str]) -> None:
        if not entity_ids or not self._enabled:
            return
        self.ensure_table()
        self.con.executemany(
            f"DELETE FROM {self.table} WHERE entity_id=?", [(e,) for e in entity_ids]
        )
        self.con.executemany(
            f"DELETE FROM {self.shadow_table} WHERE entity_id=?", [(e,) for e in entity_ids]
        )

    def get_entity_vector(self, entity_id: str) -> list[float] | None:
        """Read back the stored vector for an entity."""
        if not self._enabled:
            return None
        self.ensure_table()
        row = self.con.execute(
            f"SELECT vector FROM {self.shadow_table} WHERE entity_id=? LIMIT 1", (entity_id,)
        ).fetchone()
        if row is None:
            return None
        values = array.array("f")
        values.frombytes(row[0])
        return [float(v) for v in values]

    def search(
        self, vector: list[float], *, top_k: int, filters: dict[str, Any] | None = None
    ) -> list[VectorHit]:
        if not self._enabled:
            raise BackendUnavailableError(
                "sqlite-vec extension is not loaded.",
                remediation="Install the vector extra: uv pip install 'poldergraph[vectors]'",
            )
        self.ensure_table()
        # Vectors are L2-normalized at rest, so L2 distance maps monotonically
        # to cosine similarity: similarity = 1 - (distance^2 / 2).
        query = l2_normalize(vector)
        blob = struct.pack(f"{self.dimensions}f", *query)
        clauses = ["embedding MATCH ?", f"k = {int(max(1, top_k))}"]
        params: list[Any] = [blob]
        if filters and filters.get("modality"):
            clauses.append("modality = ?")
            params.append(filters["modality"])
        rows = self.con.execute(
            f"SELECT embedding_id, entity_id, modality, distance FROM {self.table} "
            f"WHERE {' AND '.join(clauses)}",
            params,
        ).fetchall()
        hits: list[VectorHit] = []
        for row in rows:
            distance = float(row[3])
            similarity = 1.0 - (distance * distance) / 2.0
            hits.append(VectorHit(row[0], row[1], 1.0 - similarity, row[2]))
        hits.sort(key=lambda h: h.similarity, reverse=True)
        return hits[:top_k]


def get_entity_vector(store: Any, entity_id: str) -> list[float] | None:
    """Read the stored vector for an entity from either backend."""
    if isinstance(store, SQLiteVecStore):
        return store.get_entity_vector(entity_id)
    if isinstance(store, BruteForceStore):
        store.ensure_table()
        row = store.con.execute(
            f"SELECT vector FROM {store.table} WHERE entity_id=? LIMIT 1", (entity_id,)
        ).fetchone()
        if row is None:
            return None
        values = array.array("f")
        values.frombytes(row[0])
        return [float(v) for v in values]
    return None


def create_vector_store(
    con: sqlite3.Connection, *, dimensions: int, model_id: str, task_type: str = "document"
) -> VectorStore:
    """Build the best available vector backend.

    Prefers sqlite-vec; falls back to the explicit brute-force backend rather
    than disabling semantic search.
    """
    store = SQLiteVecStore(con, dimensions=dimensions, model_id=model_id, task_type=task_type)
    if store.available():
        return store
    return BruteForceStore(con, dimensions=dimensions, model_id=model_id, task_type=task_type)


def backend_name(store: VectorStore) -> str:
    return "sqlite-vec" if isinstance(store, SQLiteVecStore) else "brute-force"


def embedding_id_for(
    entity_id: str, model_id: str, revision: str, dimensions: int, task: str, input_hash: str
) -> str:
    """Stable embedding identity including model revision and dimensions."""
    import hashlib

    payload = "\x1f".join([entity_id, model_id, revision, str(dimensions), task, input_hash])
    return "emb:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def serialize_vector_row(row: dict[str, Any]) -> str:  # pragma: no cover - diagnostics helper
    return json.dumps(row, separators=(",", ":"), sort_keys=True)
