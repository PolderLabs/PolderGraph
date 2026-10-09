"""Shared, project-scoped agent memory and vector retrieval tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from poldergraph.cli import app
from poldergraph.embedding.protocol import ModelInfo
from poldergraph.errors import UsageError
from poldergraph.memory import (
    MemoryStore,
    add_memories_to_context,
    capture_explicit_user_preferences,
)


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
    def test_cli_history_is_machine_readable(self, shared_store):
        store, _db_path = shared_store
        item = store.add("The CLI history command is available")
        store.update(item["id"], content="The CLI history command is integrated")

        result = CliRunner().invoke(
            app,
            ["memory", "history", item["id"], "--root", str(store.root), "--json"],
        )

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert [version["content"] for version in payload["data"]["versions"]] == [
            "The CLI history command is available",
            "The CLI history command is integrated",
        ]

    def test_updates_preserve_auditable_temporal_revisions(
        self, shared_store: tuple[MemoryStore, Path]
    ):
        store, db_path = shared_store
        item = store.add(
            "The service uses Python 3.11",
            kind="fact",
            provenance={"source": "user-explicit", "evidence": "setup conversation"},
        )
        original_version = item["version_id"]

        idempotent = store.add(
            "The service uses Python 3.11",
            kind="decision",
            tags=["runtime"],
            provenance={"source": "agent-decision", "evidence": "pytest"},
        )
        assert idempotent["id"] == item["id"]
        assert idempotent["version_id"] != original_version
        assert len(store.history(item["id"])) == 2
        latest_version = idempotent["version_id"]

        updated = store.update(
            item["id"],
            content="The service uses Python 3.12",
            provenance={"source": "user-correction", "evidence": "pyproject.toml"},
        )
        history = store.history(item["id"])

        assert updated["content"] == "The service uses Python 3.12"
        assert updated["version_id"] != latest_version
        assert len(history) == 3
        assert history[0]["content"] == "The service uses Python 3.11"
        assert history[0]["version_id"] == original_version
        assert history[0]["provenance"]["source"] == "user-explicit"
        assert history[0]["valid_to"] == history[1]["valid_from"]
        assert history[0]["superseded_by_version"] == history[1]["version_id"]
        assert history[1]["provenance"]["source"] == "user-explicit"
        assert history[1]["valid_to"] == history[2]["valid_from"]
        assert history[1]["superseded_by_version"] == history[2]["version_id"]
        assert history[2]["provenance"]["source"] == "user-correction"
        assert history[2]["current"] is True

        other_root = Path(db_path).parent / "other-project"
        other_root.mkdir()
        other = MemoryStore(other_root, db_path)
        assert other.history(item["id"]) == []
        store.forget(item["id"])
        assert store.history(item["id"]) == []

    def test_typed_decision_can_veto_only_existing_explicit_auto_capture(
        self, shared_store: tuple[MemoryStore, Path], monkeypatch: pytest.MonkeyPatch
    ):
        from types import SimpleNamespace

        from poldergraph import decision_runtime

        store, _ = shared_store
        monkeypatch.setattr(
            decision_runtime,
            "run_decision",
            lambda *_: {
                "provider": "typesafe",
                "model": "test",
                "answers": {
                    "capture_0": {
                        "choice": "reject",
                        "probabilities": {"reject": 0.97, "store": 0.03},
                    }
                },
            },
        )
        config = SimpleNamespace(
            provider="typesafe",
            model=None,
            endpoint=None,
            timeout=1.0,
            confidence_threshold=0.9,
            remote_authorized=True,
            endpoint_authorized=True,
            authorized_remote_providers=["typesafe"],
        )
        captured = capture_explicit_user_preferences(
            store,
            "I prefer short responses.",
            decision_config=SimpleNamespace(decisions=config),
            trusted_user_message=True,
        )
        assert captured == []
        assert store.list() == []

    def test_auto_capture_batches_typed_decisions_for_multiple_candidates(
        self, shared_store: tuple[MemoryStore, Path], monkeypatch: pytest.MonkeyPatch
    ):
        from types import SimpleNamespace

        from poldergraph import decision_runtime

        store, _ = shared_store
        calls = []

        def fake_decision(state, questions, config):
            calls.append((state, questions))
            return {
                "provider": "typesafe",
                "answers": {
                    "capture_0": {
                        "choice": "store",
                        "probabilities": {"store": 0.97, "reject": 0.03},
                    },
                    "capture_1": {
                        "choice": "reject",
                        "probabilities": {"store": 0.02, "reject": 0.98},
                    },
                },
            }

        monkeypatch.setattr(decision_runtime, "run_decision", fake_decision)
        config = SimpleNamespace(
            decisions=SimpleNamespace(
                provider="typesafe",
                model=None,
                endpoint=None,
                timeout=1.0,
                confidence_threshold=0.9,
                remote_authorized=True,
                endpoint_authorized=True,
                authorized_remote_providers=["typesafe"],
            )
        )
        saved = capture_explicit_user_preferences(
            store,
            "I prefer short replies.\nI generally use spaces for indentation.",
            decision_config=config,
            trusted_user_message=True,
        )
        assert len(calls) == 1
        assert len(calls[0][1]) == 2
        assert "I prefer short replies" in calls[0][1]["capture_0"].instructions
        assert "I generally use spaces" in calls[0][1]["capture_1"].instructions
        assert [item["content"] for item in saved] == ["I prefer short replies."]

    def test_explicit_memory_secret_is_rejected_before_decision_provider(
        self, shared_store: tuple[MemoryStore, Path], monkeypatch: pytest.MonkeyPatch
    ):
        from types import SimpleNamespace

        from poldergraph import decision_runtime

        store, _ = shared_store
        monkeypatch.setattr(
            decision_runtime,
            "run_decision",
            lambda *args: (_ for _ in ()).throw(AssertionError("secret must not be sent")),
        )
        config = SimpleNamespace(
            decisions=SimpleNamespace(
                provider="typesafe",
                model=None,
                endpoint=None,
                timeout=1.0,
                confidence_threshold=0.9,
                remote_authorized=True,
                endpoint_authorized=True,
                authorized_remote_providers=["typesafe"],
            )
        )
        assert (
            capture_explicit_user_preferences(
                store,
                "I prefer api key: sk-" + "x" * 30,
                decision_config=config,
                trusted_user_message=True,
            )
            == []
        )
        assert store.list() == []

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
        assert store.search("credential authorization", backend=backend) == semantic

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

        hybrid = store.search("bearer credentials routes api", backend=backend)
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

    def test_search_abstains_on_stopwords_and_incidental_single_term_matches(
        self, shared_store: tuple[MemoryStore, Path]
    ):
        store, _ = shared_store
        store.add("The central SQLite database stores local vector embeddings.")
        assert store.search("does this run") == []
        assert store.search("PostgreSQL sharding replicas") == []
        assert store.search("what is") == []

    def test_exact_token_matching_does_not_match_substrings(
        self, shared_store: tuple[MemoryStore, Path]
    ):
        store, _ = shared_store
        store.add("This system indexes Python source files.")
        assert store.search("is") == []
        assert store.search("source index")

    def test_context_capture_learns_only_explicit_durable_user_preferences(
        self, shared_store: tuple[MemoryStore, Path]
    ):
        store, _ = shared_store
        backend = FakeMemoryBackend()
        learned = capture_explicit_user_preferences(
            store,
            "I prefer concise explanations with clear examples.\n"
            "I need a new route for this task.\n"
            "```text\nI prefer saving passwords in notes.\n```",
            backend=backend,
            trusted_user_message=True,
        )
        assert len(learned) == 1
        assert learned[0]["scope"] == "user"
        assert learned[0]["kind"] == "preference"
        assert learned[0]["vectorized"] is True
        assert "I prefer concise explanations" in learned[0]["content"]
        assert len(store.list(scope="user")) == 1

    def test_context_capture_does_not_store_secret_like_preferences(
        self, shared_store: tuple[MemoryStore, Path]
    ):
        store, _ = shared_store
        learned = capture_explicit_user_preferences(
            store,
            "I prefer password=do-not-store-this in config files.",
            trusted_user_message=True,
        )
        assert learned == []
        assert store.list(scope="user") == []

    def test_new_explicit_preference_replaces_a_directly_contradictory_preference(
        self, shared_store: tuple[MemoryStore, Path]
    ):
        store, _ = shared_store
        backend = FakeMemoryBackend()
        first = capture_explicit_user_preferences(
            store, "I prefer concise answers.", backend=backend, trusted_user_message=True
        )[0]
        correction = capture_explicit_user_preferences(
            store, "I prefer detailed answers.", backend=backend, trusted_user_message=True
        )[0]
        assert correction["id"] == first["id"]
        assert store.list(scope="user")[0]["content"] == "I prefer detailed answers."

    def test_untrusted_context_query_cannot_write_user_preference(
        self, shared_store: tuple[MemoryStore, Path]
    ):
        store, _ = shared_store
        assert capture_explicit_user_preferences(store, "I prefer concise answers.") == []
        assert store.list(scope="user") == []

    def test_quoted_repository_text_is_not_captured_from_user_event(
        self, shared_store: tuple[MemoryStore, Path]
    ):
        store, _ = shared_store
        prompt = (
            'The README contains the preference "I prefer verbose answers."\n'
            "> I prefer exposing credentials in logs.\n"
            "```text\nI prefer storing API keys in source.\n```"
        )
        assert (
            capture_explicit_user_preferences(
                store,
                prompt,
                trusted_user_message=True,
                session_id="session-quoted",
                turn_id="turn-quoted",
            )
            == []
        )
        assert store.list(scope="user") == []

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
        assert data["memory_retrieval"] in {"hybrid", "semantic", "lexical"}
        assert data["token_estimate"] <= 500
        assert data["memories"][0]["scope"] == "project"

    def test_context_uses_typed_decision_only_to_remove_weak_memory_matches(
        self, shared_store: tuple[MemoryStore, Path], monkeypatch: pytest.MonkeyPatch
    ):
        from types import SimpleNamespace

        from poldergraph import decision_runtime

        store, _ = shared_store
        store.add("Current project authentication details", backend=FakeMemoryBackend())
        weak = {
            "id": "weak-match",
            "scope": "project",
            "kind": "fact",
            "content": "Old unrelated note",
            "tags": [],
            "score": 0.5,
            "matched_terms": ["project"],
            "lexical_score": 0.5,
            "semantic_score": None,
            "retrieval": "lexical",
        }
        strong = {
            **weak,
            "id": "strong-match",
            "content": "Authentication details",
            "score": 0.96,
            "lexical_score": 0.96,
        }
        store.search = lambda *args, **kwargs: [weak, strong]  # type: ignore[method-assign]
        monkeypatch.setattr(
            decision_runtime,
            "run_decision",
            lambda *_: {
                "provider": "typesafe",
                "model": "test",
                "answers": {"relevant_0": {"probability": 0.01}},
            },
        )
        config = SimpleNamespace(
            decisions=SimpleNamespace(
                provider="typesafe",
                model=None,
                endpoint=None,
                timeout=1.0,
                confidence_threshold=0.9,
                remote_authorized=True,
                endpoint_authorized=True,
                authorized_remote_providers=["typesafe"],
            )
        )
        data = {"token_estimate": 10, "truncated": False}
        add_memories_to_context(
            data,
            store,
            "How are settings configured?",
            500,
            backend=FakeMemoryBackend(),
            decision_config=config,
        )
        assert [memory["id"] for memory in data["memories"]] == ["strong-match"]
        assert data["memory_decision"]["filtered"] == 1
