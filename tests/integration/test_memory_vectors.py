"""Memory vector-store correctness.

Two defects were found by measuring semantic recall rather than trusting the
`vectorized` flag:

* the vector table name folded in the model revision, so re-resolving the model
  silently created a fresh table and orphaned every previously written vector
* the semantic-only acceptance gate was set above real paraphrase scores, so
  genuine matches were discarded and memory search degraded to keyword-only
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from poldergraph.memory import MemoryStore, memory_backend


@pytest.fixture(scope="module")
def backend():
    return memory_backend()


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """A memory store on an isolated database."""
    monkeypatch.setenv("POLDERGRAPH_MEMORY_DB", str(tmp_path / "memory.sqlite3"))
    return MemoryStore(tmp_path)


class TestVectorTableIdentity:
    def test_table_name_does_not_include_revision(self, store, backend):
        """A revision-keyed table name orphans vectors on every re-resolve."""
        con = store._connect()
        try:
            with pytest.MonkeyPatch.context():
                pass
            import poldergraph.memory as M

            with M._backend_lock:
                info = backend.model_info()
            vector_store = store._vector_store(con, info)
            vector_store.ensure_table()
            assert "memory" in vector_store.table
            # A revision hash would appear as "_r<hex>" in the table name.
            assert "_r" not in vector_store.table.replace("_r_utf8", "")
        finally:
            con.close()

    def test_table_is_stable_across_repeated_calls(self, store, backend):
        import poldergraph.memory as M

        with M._backend_lock:
            info = backend.model_info()
        names = {store._vector_store(store._connect(), info).table for _ in range(3)}
        assert len(names) == 1


class TestVectorWriteAndRecall:
    def test_added_memory_gets_a_vector(self, store, backend):
        created = store.add(
            "Session tokens expire after one hour",
            scope="user",
            kind="decision",
            backend=backend,
        )
        assert store._has_vector(created["id"], backend)

    def test_vector_survives_a_new_store_instance(self, tmp_path, monkeypatch, backend):
        """A separate process must see the same vectors."""
        db = tmp_path / "memory.sqlite3"
        monkeypatch.setenv("POLDERGRAPH_MEMORY_DB", str(db))
        first = MemoryStore(tmp_path)
        first.add("Prefer pytest fixtures", scope="user", kind="preference", backend=backend)

        second = MemoryStore(tmp_path)
        assert second._has_vector(
            second.list(scope="user")[0]["id"], backend
        )

    def test_repair_restores_vectors_missing_from_the_current_table(
        self, store, backend
    ):
        created = store.add(
            "Database migrations run on deploy", scope="user", kind="workflow", backend=backend
        )
        con = store._connect()
        try:
            with backend.model_info() if False else _noop():
                pass
            import poldergraph.memory as M

            with M._backend_lock:
                info = backend.model_info()
            vector_store = store._vector_store(con, info)
            # Simulate the pre-fix layout: vectors written elsewhere.
            con.execute(f"DELETE FROM {vector_store.shadow_table} WHERE entity_id=?", (created["id"],))
            con.commit()
            assert not store._has_vector_in(con, vector_store, created["id"])
        finally:
            con.close()

        repaired = store.repair_vectors(backend)
        assert repaired["repaired"] >= 1

        con = store._connect()
        try:
            import poldergraph.memory as M

            with M._backend_lock:
                info = backend.model_info()
            vector_store = store._vector_store(con, info)
            assert store._has_vector_in(con, vector_store, created["id"])
        finally:
            con.close()


class _noop:
    def __enter__(self):
        return None

    def __exit__(self, *exc):
        return False


class TestSearchRecall:
    def test_paraphrase_is_recalled(self, store, backend):
        """A wording-different query must still find the memory."""
        store.add(
            "Prefer concise answers with a short example",
            scope="user",
            kind="preference",
            backend=backend,
        )
        results = store.search(
            "how should responses be written",
            scope="user",
            backend=backend,
        )
        assert results, "paraphrase query returned nothing"

    def test_unrelated_query_abstains(self, store, backend):
        """Relaxing the gate must not let unrelated memories through."""
        store.add(
            "Prefer concise answers with a short example",
            scope="user",
            kind="preference",
            backend=backend,
        )
        results = store.search(
            "photosynthesis chlorophyll wavelength absorption",
            scope="user",
            backend=backend,
        )
        assert results == []

    def test_exact_match_still_works_without_embedding(self, store, backend):
        created = store.add(
            "Session tokens expire after one hour",
            scope="user",
            kind="decision",
            backend=backend,
        )
        results = store.search("session tokens expire", scope="user", backend=None)
        assert [r["id"] for r in results] == [created["id"]]

    def test_semantic_score_is_reported(self, store, backend):
        store.add(
            "Database migrations run on deploy", scope="user", kind="workflow", backend=backend
        )
        results = store.search(
            "when do schema changes ship", scope="user", backend=backend
        )
        assert results
        assert results[0]["semantic_score"] is not None