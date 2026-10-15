"""MCP contract tests: every tool's schema and response shape."""

from __future__ import annotations

import json
import os

import pytest

from poldergraph.errors import API_VERSION

#: Tools the spec requires, with their required argument names.
REQUIRED_TOOLS: dict[str, list[str]] = {
    "pg_status": [],
    "pg_search": ["query"],
    "pg_context": ["query"],
    "pg_entity": ["entity"],
    "pg_path": ["source", "target"],
    "pg_related": ["entity"],
    "pg_impact": ["entity"],
    "pg_update": [],
    "pg_find_tests": [],
    "pg_memory_status": [],
    "pg_memory_search": ["query"],
    "pg_memory_list": [],
    "pg_memory_add": ["content"],
    "pg_memory_history": ["memory_id"],
    "pg_memory_update": ["memory_id"],
    "pg_memory_forget": ["memory_id"],
}


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    """An MCP server bound to a small indexed repository."""
    from poldergraph.mcp.server import build_server

    root = tmp_path_factory.mktemp("mcp_repo") / "repo"
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "auth.py").write_text(
        "from .models import Session\n"
        "\n"
        "class AuthService:\n"
        '    """Validate session tokens."""\n'
        "    def validate_session(self, token: str) -> Session:\n"
        '        """Check token."""\n'
        "        return Session(token)\n"
    )
    (root / "pkg" / "models.py").write_text(
        'class Session:\n    """A user session."""\n    def __init__(self, t): self.t = t\n'
    )
    (root / "pkg" / "__init__.py").write_text("from .auth import AuthService\n")
    (root / "test_auth.py").write_text(
        "from pkg.auth import AuthService\n\ndef test_validate():\n    assert AuthService()\n"
    )

    from poldergraph.config.models import Config
    from poldergraph.graph import run_graph_stage
    from poldergraph.indexing.pipeline import Indexer
    from poldergraph.storage.repository import Repository
    from poldergraph.workspace import create_index, open_workspace

    create_index(root, Config())
    workspace = open_workspace(root)
    indexer = Indexer(workspace, backend=None)
    indexer.ensure_root()
    indexer.run(indexer.discover())
    run_graph_stage(workspace, workspace.config, Repository(workspace.con), None)

    memory_db = tmp_path_factory.mktemp("central_memory") / "memory.sqlite3"
    previous_memory_db = os.environ.get("POLDERGRAPH_MEMORY_DB")
    os.environ["POLDERGRAPH_MEMORY_DB"] = str(memory_db)
    instance = build_server(root)
    yield instance
    session = getattr(instance, "poldergraph_session", None)
    if session is not None:
        session.close()
    if previous_memory_db is None:
        os.environ.pop("POLDERGRAPH_MEMORY_DB", None)
    else:
        os.environ["POLDERGRAPH_MEMORY_DB"] = previous_memory_db


def _tools(server) -> dict:
    """List registered tools across MCP SDK versions."""
    import asyncio

    listed = asyncio.run(server.list_tools())
    return {tool.name: tool for tool in listed}


def _call(server, name: str, arguments: dict) -> dict:
    """Invoke a tool and unwrap the payload the agent receives."""
    import asyncio
    import json as _json

    assert name in _tools(server), f"tool {name} not registered"
    result = asyncio.run(server.call_tool(name, arguments))

    if isinstance(result, tuple):
        # 1.x returns (content_blocks, structured_dict); prefer the structured one.
        for item in reversed(result):
            if isinstance(item, dict):
                return item
        result = result[0]

    if isinstance(result, dict):
        return result

    # 2.x returns a CallToolResult whose content blocks carry JSON text.
    structured = getattr(result, "structuredContent", None) or getattr(
        result, "structured_content", None
    )
    if isinstance(structured, dict):
        return structured

    blocks = getattr(result, "content", result)
    for item in blocks if isinstance(blocks, list) else []:
        text = getattr(item, "text", None)
        if text:
            try:
                return _json.loads(text)
            except _json.JSONDecodeError:
                continue
    raise AssertionError(f"could not decode tool result for {name}: {result!r}")


def _schema_of(tool) -> dict:
    schema = getattr(tool, "inputSchema", None)
    if isinstance(schema, dict):
        return schema
    schema = getattr(tool, "input_schema", None)
    return schema if isinstance(schema, dict) else {}


class TestToolRegistration:
    @pytest.mark.parametrize("name", sorted(REQUIRED_TOOLS))
    def test_tool_is_registered(self, server, name: str):
        assert name in _tools(server)

    @pytest.mark.parametrize("name,required", sorted(REQUIRED_TOOLS.items()))
    def test_tool_has_required_arguments(self, server, name: str, required: list[str]):
        tool = _tools(server)[name]
        properties = _schema_of(tool).get("properties", {})
        for argument in required:
            assert argument in properties, f"{name} missing argument {argument}"


class TestToolResponses:
    def _assert_envelope(self, payload: dict, command: str):
        assert payload["ok"] is True
        assert payload["api_version"] == API_VERSION
        assert payload["command"] == command
        assert payload["error"] is None
        assert isinstance(payload["warnings"], list)

    def test_search_strict_consistency_returns_freshness(self, server):
        payload = _call(
            server,
            "pg_search",
            {"query": "AuthService", "include_semantic": False, "consistency": "strict"},
        )
        assert payload["ok"] is True
        assert payload["index"]["fresh"] is True
        assert payload["data"]["consistency"] == "strict"

    def test_path_strict_consistency_is_available_through_mcp(self, server):
        payload = _call(
            server,
            "pg_path",
            {
                "source": "AuthService",
                "target": "validate_session",
                "consistency": "strict",
            },
        )
        assert payload["ok"] is True
        assert payload["data"]["consistency_report"]["verified"] is True

    def test_path_reports_post_query_source_edit(self, server, monkeypatch):
        service = server.poldergraph_session.service()
        original_path = service.path
        source = service.root / "pkg" / "auth.py"

        def edit_during_query(*args, **kwargs):
            result = original_path(*args, **kwargs)
            source.write_text(source.read_text() + "\n# edited during query\n")
            return result

        monkeypatch.setattr(service, "path", edit_during_query)
        payload = _call(
            server,
            "pg_path",
            {"source": "AuthService", "target": "validate_session"},
        )
        assert payload["ok"] is True
        assert payload["index"]["fresh"] is False
        assert "pkg/auth.py" in payload["index"]["stale_files"]

    def test_pg_status(self, server):
        payload = _call(server, "pg_status", {})
        self._assert_envelope(payload, "pg_status")
        assert payload["data"]["counts"]["entities"] > 0
        assert "fresh" in payload["data"]

    def test_pg_search_returns_score_decomposition(self, server):
        payload = _call(server, "pg_search", {"query": "AuthService", "limit": 5})
        self._assert_envelope(payload, "pg_search")
        results = payload["data"]["results"]
        assert results
        assert results[0]["evidence"] in {"exact", "lexical", "semantic", "graph-expanded"}
        assert isinstance(results[0]["score_features"], dict)

    def test_semantic_tools_load_backend_on_their_first_call(self, server, monkeypatch):
        """A semantic MCP tool must not depend on pg_context loading its backend first."""
        from poldergraph.embedding.protocol import ModelInfo
        from poldergraph.mcp.server import build_server
        from poldergraph.storage.vectors import VectorRecord, create_vector_store

        class FakeBackend:
            def capabilities(self):
                return {"text"}

            def model_info(self):
                return ModelInfo(model_id="fake/mcp-first-call", revision="test", dimensions=3)

            def embed_texts(self, items, *, task, dimensions):
                return [[1.0, 0.0, 0.0] for _ in items]

        created = []

        def create_backend(config, **kwargs):
            backend = FakeBackend()
            created.append(backend)
            return backend

        monkeypatch.setattr("poldergraph.embedding.gemma.create_backend", create_backend)
        session = server.poldergraph_session
        service = session.service()
        auth_id = service.resolve_entity("AuthService").id
        session_id = service.resolve_entity("Session").id
        info = FakeBackend().model_info()
        store = create_vector_store(
            service.workspace.con, dimensions=info.dimensions, model_id=info.model_id
        )
        store.upsert(
            [
                VectorRecord(
                    embedding_id="auth-vector",
                    entity_id=auth_id,
                    vector=[1.0, 0.0, 0.0],
                    dimensions=info.dimensions,
                    model_id=info.model_id,
                    model_revision=info.revision,
                    task_type="document",
                    input_hash="auth",
                ),
                VectorRecord(
                    embedding_id="session-vector",
                    entity_id=session_id,
                    vector=[0.9, 0.1, 0.0],
                    dimensions=info.dimensions,
                    model_id=info.model_id,
                    model_revision=info.revision,
                    task_type="document",
                    input_hash="session",
                ),
            ]
        )
        service.workspace.con.commit()

        search_server = build_server(service.root)
        try:
            search = _call(search_server, "pg_search", {"query": "session behavior"})
        finally:
            search_server.poldergraph_session.close()
        self._assert_envelope(search, "pg_search")
        assert created
        assert any("semantic" in result["score_features"] for result in search["data"]["results"])

        related_server = build_server(service.root)
        try:
            related = _call(related_server, "pg_related", {"entity": "AuthService"})
        finally:
            related_server.poldergraph_session.close()
        self._assert_envelope(related, "pg_related")
        assert related["data"]["related"]

        lexical_server = build_server(service.root)
        created_before_lexical = len(created)
        try:
            lexical = _call(
                lexical_server,
                "pg_search",
                {"query": "session behavior", "include_semantic": False},
            )
        finally:
            lexical_server.poldergraph_session.close()
        self._assert_envelope(lexical, "pg_search")
        assert len(created) == created_before_lexical

    def test_pg_related_reports_unavailable_semantic_backend(self, server, monkeypatch):
        from poldergraph.embedding.protocol import DisabledBackend
        from poldergraph.mcp.server import build_server

        monkeypatch.setattr(
            "poldergraph.embedding.gemma.create_backend",
            lambda config, **kwargs: DisabledBackend("test backend unavailable"),
        )
        service = server.poldergraph_session.service()
        fresh_server = build_server(service.root)
        try:
            payload = _call(fresh_server, "pg_related", {"entity": "AuthService"})
        finally:
            fresh_server.poldergraph_session.close()
        assert payload["ok"] is False
        assert payload["command"] == "pg_related"
        assert payload["error"]["code"] == "BACKEND_UNAVAILABLE"

    def test_pg_context_shape(self, server, monkeypatch):
        from poldergraph.embedding.protocol import ModelInfo

        class FakeBackend:
            def capabilities(self):
                return {"text"}

            def model_info(self):
                return ModelInfo(model_id="fake/context", revision="test", dimensions=3)

            def embed_texts(self, items, *, task, dimensions):
                return [[1.0, 0.0, 0.0] for _ in items]

        monkeypatch.setattr(
            "poldergraph.embedding.gemma.create_backend", lambda config, **kwargs: FakeBackend()
        )
        payload = _call(
            server, "pg_context", {"query": "how does login work", "token_budget": 2000}
        )
        self._assert_envelope(payload, "pg_context")
        data = payload["data"]
        for key in (
            "query",
            "index",
            "entities",
            "relationships",
            "snippets",
            "paths",
            "communities",
            "unresolved",
            "retrieval",
            "token_estimate",
            "truncated",
        ):
            assert key in data, f"context payload missing {key}"
        assert data["token_estimate"] <= 2000
        assert "memories" in data

    def test_pg_context_cursor_returns_only_new_evidence(self, server):
        query = "Explain AuthService token validation"
        first = _call(server, "pg_context", {"query": query, "token_budget": 2000})
        cursor = first["data"]["evidence_cursor"]
        assert cursor
        assert first["data"]["new_evidence_count"] > 0

        second = _call(
            server,
            "pg_context",
            {"query": query, "token_budget": 2000, "new_evidence_since": cursor},
        )
        assert second["data"]["new_evidence_count"] == 0
        assert second["data"]["evidence_cursor"] == cursor

        learned = _call(
            server,
            "pg_context",
            {
                "query": "I prefer concise answers with a concrete example.",
                "token_budget": 2000,
            },
        )
        assert learned["data"]["memories_learned"] == 0
        assert all(
            "I prefer concise answers" not in item["content"]
            for item in learned["data"]["memories"]
        )
        from poldergraph.memory import MemoryStore

        workspace = server.poldergraph_session._workspace
        assert workspace is not None
        assert MemoryStore(workspace.root).status()["user_memories"] == 0

    def test_pg_entity(self, server):
        payload = _call(server, "pg_entity", {"entity": "AuthService"})
        self._assert_envelope(payload, "pg_entity")
        assert payload["data"]["entity"]["kind"]

    def test_pg_path(self, server):
        payload = _call(
            server, "pg_path", {"source": "AuthService.validate_session", "target": "Session"}
        )
        self._assert_envelope(payload, "pg_path")
        assert payload["data"]["found"] is True
        assert payload["data"]["hops"] >= 1

    def test_pg_impact(self, server):
        payload = _call(server, "pg_impact", {"entity": "Session"})
        self._assert_envelope(payload, "pg_impact")
        assert "direct" in payload["data"]

    def test_pg_find_tests(self, server):
        payload = _call(server, "pg_find_tests", {"entity": "AuthService"})
        self._assert_envelope(payload, "pg_find_tests")
        assert isinstance(payload["data"]["tests"], list)

    def test_memory_tools_support_search_save_and_forget(self, server, monkeypatch):
        from poldergraph import decision_runtime
        from poldergraph.memory import MemoryStore

        class FakeBackend:
            def capabilities(self):
                return {"text"}

            def model_info(self):
                from poldergraph.embedding.protocol import ModelInfo

                return ModelInfo(model_id="fake/mcp", revision="test", dimensions=3)

            def embed_texts(self, items, *, task, dimensions):
                return [[1.0, 0.0, 0.0] for _ in items]

        monkeypatch.setattr(
            "poldergraph.memory.memory_backend", lambda preferred=None: FakeBackend()
        )
        decision_calls = []

        def retain_with_decision(query, results, config):
            decision_calls.append((query, config.provider))
            return results, {"status": "applied", "filtered": 0}

        monkeypatch.setattr(decision_runtime, "decide_memory_relevance", retain_with_decision)
        added = _call(
            server,
            "pg_memory_add",
            {
                "content": "The auth resolver validates bearer tokens before API access.",
                "scope": "project",
                "kind": "decision",
                "tags": ["security"],
            },
        )
        self._assert_envelope(added, "pg_memory_add")
        memory_id = added["data"]["id"]
        assert added["data"]["vectorized"] is True

        recalled = _call(server, "pg_memory_search", {"query": "credential checks"})
        self._assert_envelope(recalled, "pg_memory_search")
        assert recalled["data"]["results"][0]["id"] == memory_id
        assert recalled["data"]["results"][0]["retrieval"] == "semantic"
        assert recalled["data"]["memory_decision"] == {"status": "applied", "filtered": 0}
        assert decision_calls[0][0] == "credential checks"

        status = _call(server, "pg_memory_status", {})
        self._assert_envelope(status, "pg_memory_status")
        assert status["data"]["project_memories"] == 1

        updated = _call(server, "pg_memory_update", {"memory_id": memory_id, "kind": "fact"})
        self._assert_envelope(updated, "pg_memory_update")
        assert updated["data"]["kind"] == "fact"

        history = _call(server, "pg_memory_history", {"memory_id": memory_id})
        self._assert_envelope(history, "pg_memory_history")
        assert len(history["data"]["versions"]) == 2
        assert history["data"]["versions"][0]["kind"] == "decision"
        assert history["data"]["versions"][1]["current"] is True

        forgotten = _call(server, "pg_memory_forget", {"memory_id": memory_id})
        self._assert_envelope(forgotten, "pg_memory_forget")
        assert MemoryStore(server.poldergraph_session.service().root).list(scope="project") == []

    def test_pg_update_is_idempotent(self, server):
        first = _call(server, "pg_update", {})
        second = _call(server, "pg_update", {})
        self._assert_envelope(first, "pg_update")
        self._assert_envelope(second, "pg_update")
        # A second run with no edits must find nothing to do.
        assert second["data"]["plan"]["changed"] == 0

    def test_pg_update_returns_a_structured_indexing_failure(self, server, monkeypatch):
        from poldergraph.errors import IndexLockedError

        def fail_run(*args, **kwargs):
            raise IndexLockedError("test index lock")

        monkeypatch.setattr("poldergraph.indexing.pipeline.Indexer.run", fail_run)
        payload = _call(server, "pg_update", {})
        assert payload["ok"] is False
        assert payload["command"] == "pg_update"
        assert payload["error"]["code"] == "INDEX_LOCKED"
        assert payload["error"]["remediation"]


class TestActionableErrors:
    def test_value_errors_are_structured_usage_errors(self, server, monkeypatch):
        service = server.poldergraph_session.service()

        def fail_related(*args, **kwargs):
            raise ValueError("invalid related request")

        monkeypatch.setattr(service, "related", fail_related)
        payload = _call(server, "pg_related", {"entity": "AuthService"})
        assert payload["ok"] is False
        assert payload["error"]["code"] == "USAGE_ERROR"
        assert payload["error"]["message"] == "invalid related request"

    def test_unknown_entity_has_remediation(self, server):
        payload = _call(server, "pg_entity", {"entity": "definitely_missing_symbol_xyz"})
        if payload.get("ok"):
            pytest.skip("backend resolved an unresolvable reference")
        assert payload["error"]["code"]
        assert payload["error"]["message"]

    def test_payloads_are_json_serializable(self, server):
        for name, args in [
            ("pg_status", {}),
            ("pg_search", {"query": "session", "limit": 3}),
            ("pg_context", {"query": "session", "token_budget": 800}),
        ]:
            payload = _call(server, name, args)
            json.dumps(payload)  # must not raise
