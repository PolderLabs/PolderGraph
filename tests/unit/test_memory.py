"""Shared, project-scoped agent memory and vector retrieval tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from poldergraph.embedding.protocol import ModelInfo
from poldergraph.errors import UsageError
from poldergraph.memory import MemoryStore, add_memories_to_context


class FakeMemoryBackend:
    """Small deterministic embedding backend for memory RAG tests."""

    def capabilities(self) -> set[str]:
        return {"text"}

    def model_info(self) -> ModelInfo:
        return ModelInfo(model_id="fake/memory-test", revision="r1", dimensions=3)

    def embed_texts(self, items: list[str], *, task: str, dimensions: int) -> list[list[float]]:
        vectors = []
        for text in items:
            lowered = text.casefold()
            if any(term in lowered for term in ("token", "credential", "auth", "secret")):
                vectors.append([1.0, 0.0, 0.0])
            elif any(term in lowered for term in ("concise", "brief", "short")):
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.0, 0.0, 1.0])
        return vectors


@pytest.fixture()
def shared_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[MemoryStore, Path]:
    db_path = tmp_path / "shared" / "memory.sqlite3"
    monkeypatch.setenv("POLDERGRAPH_MEMORY_DB", str(db_path))
    root = tmp_path / "project-a"
    root.mkdir()
    return MemoryStore(root), db_path


class TestMemoryStore:
    def test_project_and_user_memories_share_one_store_without_cross_project_leaks(
        self, shared_store: tuple[MemoryStore, Path], tmp_path: Path
    ):
        store, db_path = shared_store
        backend = FakeMemoryBackend()
        project_item = store.add("API refresh decisions belong in auth/session.py", backend=backend)
        user_item = store.add(
            "Prefer concise explanations with examples",
            scope="user",
            kind="preference",
            tags=["communication"],
            backend=backend,
        )

        other_project = tmp_path / "project-b"
        other_project.mkdir()
        other = MemoryStore(other_project, db_path)

        assert store.database == other.database == db_path.resolve()
        assert {item["id"] for item in store.list()} == {project_item["id"], user_item["id"]}
        assert [item["id"] for item in other.list()] == [user_item["id"]]
        assert other.get(project_item["id"]) is None

    def test_add_is_idempotent_and_update_and_forget_keep_fts_and_vectors_in_sync(
        self, shared_store: tuple[MemoryStore, Path]
    ):
        store, _ = shared_store
        backend = FakeMemoryBackend()
        first = store.add("Check bearer tokens before API access", backend=backend)
        duplicate = store.add("  CHECK bearer tokens before API access  ", backend=backend)
        assert first["created"] is True
        assert duplicate["created"] is False
        assert first["id"] == duplicate["id"]
        assert first["vectorized"] is True

        semantic = store.search("credential authorization", backend=backend)
        assert semantic[0]["id"] == first["id"]
        assert semantic[0]["retrieval"] == "semantic"

        updated = store.update(
            first["id"], content="Use brief validation messages", kind="decision", backend=backend
        )
        assert updated["vectorized"] is True
        assert store.search("credential authorization", backend=backend) == []
        assert store.search("short concise response", backend=backend)[0]["id"] == first["id"]

        store.forget(first["id"])
        assert store.list() == []

    def test_search_combines_keyword_vectors_and_scope_filters(
        self, shared_store: tuple[MemoryStore, Path], tmp_path: Path
    ):
        store, db_path = shared_store
        backend = FakeMemoryBackend()
        project = store.add("Validate bearer credentials before routes", backend=backend)
        user = store.add(
            "Keep explanations concise", scope="user", kind="preference", backend=backend
        )

        hybrid = store.search("bearer credentials", backend=backend)
        assert hybrid[0]["id"] == project["id"]
        assert hybrid[0]["retrieval"] == "hybrid"
        assert store.search("brief answers", scope="project", backend=backend) == []
        assert store.search("brief answers", scope="user", backend=backend)[0]["id"] == user["id"]

        other_root = tmp_path / "other"
        other_root.mkdir()
        other = MemoryStore(other_root, db_path)
        assert other.search("brief answers", backend=backend)[0]["id"] == user["id"]

    def test_missing_vectors_are_built_automatically_during_retrieval(
        self, shared_store: tuple[MemoryStore, Path]
    ):
        store, _ = shared_store
        item = store.add("Bearer token validation is mandatory")
        assert item["vectorized"] is False

        result = store.search("credential authorization", backend=FakeMemoryBackend())
        assert result[0]["id"] == item["id"]
        assert result[0]["retrieval"] == "semantic"

    def test_secret_material_is_rejected_and_scope_is_validated(
        self, shared_store: tuple[MemoryStore, Path]
    ):
        store, _ = shared_store
        with pytest.raises(UsageError, match="credential"):
            store.add("Use token ghp_" + "a" * 36)
        with pytest.raises(UsageError, match="scope"):
            store.list(scope="everything")

    def test_context_includes_relevant_memories_within_the_budget(
        self, shared_store: tuple[MemoryStore, Path]
    ):
        store, _ = shared_store
        store.add(
            "The API uses bearer tokens. Validate expiry before reading protected resources.",
            kind="decision",
            tags=["auth", "security"],
            backend=FakeMemoryBackend(),
        )
        data = {"token_estimate": 150, "truncated": False}
        add_memories_to_context(
            data, store, "How does auth token expiry work?", 500, backend=FakeMemoryBackend()
        )

        assert data["memories"]
        assert data["memory_retrieval"] in {"hybrid", "semantic"}
        assert data["token_estimate"] <= 500
        assert data["memories"][0]["scope"] == "project"
