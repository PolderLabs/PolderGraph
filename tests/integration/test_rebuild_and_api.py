"""Rebuild atomicity and dashboard API contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from poldergraph.config.models import Config
from poldergraph.errors import API_VERSION, PolderGraphError
from poldergraph.workspace import create_index, open_workspace


class TestRebuild:
    def test_each_completed_scan_advances_generation(self, indexed_workspace):
        from poldergraph.indexing.pipeline import Indexer
        from poldergraph.storage.sqlite import get_meta

        before = get_meta(indexed_workspace.con, "index_generation")
        indexer = Indexer(indexed_workspace, backend=None)
        indexer.run(indexer.discover())
        after = get_meta(indexed_workspace.con, "index_generation")
        assert before
        assert after
        assert after != before

    def test_rebuild_replaces_the_live_index(self, sample_repo: Path):
        """A successful rebuild must actually install the new index."""
        from poldergraph.indexing.pipeline import Indexer
        from poldergraph.rebuild import rebuild_index
        from poldergraph.storage.repository import Repository

        create_index(sample_repo, Config())
        workspace = open_workspace(sample_repo)
        indexer = Indexer(workspace, backend=None)
        indexer.ensure_root()
        indexer.run(indexer.discover())
        workspace.close()

        (sample_repo / "pkg" / "new_module.py").write_text(
            "class BrandNew:\n    def added_later(self):\n        return 1\n"
        )

        result = rebuild_index(sample_repo, use_backend=False)

        # The rebuilt index must be the live one, not the discarded staging copy.
        workspace = open_workspace(sample_repo)
        try:
            repo = Repository(workspace.con)
            names = {
                row[0]
                for row in repo.con.execute(
                    "SELECT name FROM entities WHERE path='pkg/new_module.py'"
                )
            }
            assert "BrandNew" in names, f"rebuilt index missing new entity: {sorted(names)}"
            assert result["entities_written"] > 0
        finally:
            workspace.close()

    def test_rebuild_leaves_no_staging_directory(self, sample_repo: Path):
        from poldergraph.rebuild import rebuild_index

        create_index(sample_repo, Config())
        rebuild_index(sample_repo, use_backend=False)
        assert not (sample_repo / ".poldergraph.rebuild").exists()

    def test_failed_rebuild_preserves_existing_index(self, sample_repo: Path, monkeypatch):
        """If the new index fails checks, the working index must survive."""
        from poldergraph.rebuild import rebuild_index
        from poldergraph.storage import integrity

        create_index(sample_repo, Config())
        workspace = open_workspace(sample_repo)
        from poldergraph.indexing.pipeline import Indexer

        indexer = Indexer(workspace, backend=None)
        indexer.ensure_root()
        indexer.run(indexer.discover())
        workspace.close()

        before = (sample_repo / ".poldergraph" / "index.sqlite3").read_bytes()

        def broken_report(repo, *, dimensions=256):
            report = integrity.DoctorReport()
            report.add("forced_failure", False, "injected failure")
            return report

        monkeypatch.setattr(integrity, "run_doctor", broken_report)

        with pytest.raises(PolderGraphError):
            rebuild_index(sample_repo, use_backend=False)

        assert (sample_repo / ".poldergraph" / "index.sqlite3").read_bytes() == before
        assert not (sample_repo / ".poldergraph.rebuild").exists()


@pytest.fixture()
def api_client(sample_repo: Path, tmp_path: Path, monkeypatch):
    """A FastAPI test client bound to an indexed repository."""
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from poldergraph.api.server import create_app

    monkeypatch.setenv("POLDERGRAPH_MEMORY_DB", str(tmp_path / "shared-memory.sqlite3"))

    create_index(sample_repo, Config())
    workspace = open_workspace(sample_repo)
    from poldergraph.graph import run_graph_stage
    from poldergraph.indexing.pipeline import Indexer
    from poldergraph.storage.repository import Repository

    indexer = Indexer(workspace, backend=None)
    indexer.ensure_root()
    indexer.run(indexer.discover())
    run_graph_stage(workspace, workspace.config, Repository(workspace.con), None)

    client = TestClient(create_app(workspace, skip_backend=True))
    yield client
    workspace.close()


class TestDashboardApi:
    def test_status(self, api_client):
        payload = api_client.get("/api/status").json()
        assert payload["ok"] is True
        assert payload["api_version"] == API_VERSION
        assert payload["data"]["counts"]["entities"] > 0
        assert set(payload["data"]["communities"]) == {"structural", "hybrid"}
        assert payload["data"]["schema_version"] > 0
        assert payload["data"]["languages"]
        assert payload["data"]["roots"][0]["path"]

    def test_status_freshness_uses_workspace_root(self, indexed_workspace, tmp_path: Path, monkeypatch):
        """An explicit workspace stays fresh when the client runs elsewhere."""
        from poldergraph.retrieval.service import QueryService
        from poldergraph.storage.repository import Repository

        service = QueryService(
            Repository(indexed_workspace.con),
            indexed_workspace.config,
            root_id=indexed_workspace.root_id(),
            workspace=indexed_workspace,
        )
        assert service.freshness()["fresh"] is True

        caller_dir = tmp_path / "different-cwd"
        caller_dir.mkdir()
        monkeypatch.chdir(caller_dir)

        assert service.freshness()["fresh"] is True

    def test_freshness_reports_revision_and_stale_source_read_requirement(self, indexed_workspace):
        from poldergraph.retrieval.service import QueryService
        from poldergraph.storage.repository import Repository

        service = QueryService(
            Repository(indexed_workspace.con),
            indexed_workspace.config,
            root_id=indexed_workspace.root_id(),
            workspace=indexed_workspace,
        )
        current = service.freshness()
        assert current["generation"]
        assert current["revision"] == current["indexed_head"]
        assert current["structural"] == "fresh"
        assert current["semantic"] == "unknown"
        assert current["source_read_required"] is False

        source = indexed_workspace.root / "pkg" / "auth.py"
        source.write_text(source.read_text() + "\n# freshness probe\n")
        stale = service.freshness()
        assert stale["fresh"] is False
        assert stale["structural"] == "stale"
        assert stale["pending_changes"] > 0
        assert stale["source_read_required"] is True

    def test_freshness_skips_full_scan_until_directory_entries_change(
        self, indexed_workspace, monkeypatch
    ):
        from poldergraph.discovery.scanner import Discovery
        from poldergraph.retrieval.service import QueryService
        from poldergraph.storage.repository import Repository

        service = QueryService(
            Repository(indexed_workspace.con),
            indexed_workspace.config,
            root_id=indexed_workspace.root_id(),
            workspace=indexed_workspace,
        )
        assert service.freshness()["fresh"] is True  # populate directory snapshot
        original_scan = Discovery.scan
        scans = 0

        def counted_scan(discovery):
            nonlocal scans
            scans += 1
            return original_scan(discovery)

        monkeypatch.setattr(Discovery, "scan", counted_scan)
        assert service.freshness()["fresh"] is True
        assert scans == 0

        edited_file = indexed_workspace.root / "pkg" / "auth.py"
        edited_file.write_text(edited_file.read_text() + "\n# source edit\n")
        stale_edit = service.freshness()
        assert stale_edit["fresh"] is False
        assert "pkg/auth.py" in stale_edit["stale_files"]
        assert scans == 0

        new_file = indexed_workspace.root / "pkg" / "new_module.py"
        new_file.write_text("def new_entrypoint():\n    return True\n")
        stale = service.freshness()
        assert stale["fresh"] is False
        assert "pkg/new_module.py" in stale["stale_files"]
        assert scans == 1

    def test_freshness_detects_same_size_edit_with_older_mtime(self, indexed_workspace):
        from poldergraph.retrieval.service import QueryService
        from poldergraph.storage.repository import Repository

        repo = Repository(indexed_workspace.con)
        service = QueryService(
            repo,
            indexed_workspace.config,
            root_id=indexed_workspace.root_id(),
            workspace=indexed_workspace,
        )
        source = indexed_workspace.root / "pkg" / "auth.py"
        original = source.read_text()
        source.write_text(original.replace("Validate", "Verifies", 1))
        indexed = repo.get_file(indexed_workspace.root_id(), "pkg/auth.py")
        assert indexed is not None
        import os

        old_mtime = source.stat().st_mtime_ns + 1_000_000_000
        repo.con.execute(
            "UPDATE files SET mtime_ns=? WHERE root_id=? AND path=?",
            (old_mtime, indexed_workspace.root_id(), "pkg/auth.py"),
        )
        source_mtime = old_mtime - 2_000_000_000
        os.utime(source, ns=(source_mtime, source_mtime))
        freshness = service.freshness()
        assert freshness["fresh"] is False
        assert "pkg/auth.py" in freshness["stale_files"]

    def test_strict_search_detects_same_size_edit_with_preserved_mtime(self, indexed_workspace):
        import os

        from poldergraph.errors import IndexStaleError
        from poldergraph.retrieval.service import QueryService
        from poldergraph.storage.repository import Repository

        repo = Repository(indexed_workspace.con)
        service = QueryService(
            repo,
            indexed_workspace.config,
            root_id=indexed_workspace.root_id(),
            workspace=indexed_workspace,
        )
        source = indexed_workspace.root / "pkg" / "auth.py"
        original_stat = source.stat()
        source.write_text(source.read_text().replace("Validate", "Verifies", 1))
        os.utime(source, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

        with pytest.raises(IndexStaleError) as exc_info:
            service.search("AuthService", include_semantic=False, consistency="strict")
        freshness = exc_info.value.details["freshness"]
        assert "pkg/auth.py" in freshness["stale_files"]

    def test_strict_search_rechecks_freshness_after_retrieval(
        self, indexed_workspace, monkeypatch
    ):
        import poldergraph.retrieval.service as service_module
        from poldergraph.errors import IndexStaleError
        from poldergraph.retrieval.service import QueryService
        from poldergraph.storage.repository import Repository

        service = QueryService(
            Repository(indexed_workspace.con),
            indexed_workspace.config,
            root_id=indexed_workspace.root_id(),
            workspace=indexed_workspace,
        )
        source = indexed_workspace.root / "pkg" / "auth.py"
        original_exact = service_module.exact_matches
        changed = False

        def edit_during_search(*args, **kwargs):
            nonlocal changed
            if not changed:
                source.write_text(source.read_text() + "\n# changed during retrieval\n")
                changed = True
            return original_exact(*args, **kwargs)

        monkeypatch.setattr(service_module, "exact_matches", edit_during_search)
        with pytest.raises(IndexStaleError):
            service.search("AuthService", include_semantic=False, consistency="strict")

    def test_strict_path_impact_entity_and_test_queries_reject_stale_index(
        self, indexed_workspace
    ):
        from poldergraph.errors import IndexStaleError
        from poldergraph.retrieval.service import QueryService
        from poldergraph.storage.repository import Repository

        service = QueryService(
            Repository(indexed_workspace.con),
            indexed_workspace.config,
            root_id=indexed_workspace.root_id(),
            workspace=indexed_workspace,
        )
        source = indexed_workspace.root / "pkg" / "auth.py"
        source.write_text(source.read_text() + "\n# changed\n")
        operations = (
            lambda: service.explain("AuthService", consistency="strict"),
            lambda: service.path("AuthService", "validate_session", consistency="strict"),
            lambda: service.impact("AuthService", consistency="strict"),
            lambda: service.find_tests(entity_ref="AuthService", consistency="strict"),
        )
        for operation in operations:
            with pytest.raises(IndexStaleError):
                operation()

    def test_strict_path_detects_generation_change_during_query(
        self, indexed_workspace, monkeypatch
    ):
        import poldergraph.retrieval.service as service_module
        from poldergraph.errors import IndexStaleError
        from poldergraph.retrieval.service import QueryService
        from poldergraph.storage.repository import Repository
        from poldergraph.storage.sqlite import set_meta

        service = QueryService(
            Repository(indexed_workspace.con),
            indexed_workspace.config,
            root_id=indexed_workspace.root_id(),
            workspace=indexed_workspace,
        )
        original_find_path = service_module.find_path

        def change_generation(*args, **kwargs):
            result = original_find_path(*args, **kwargs)
            set_meta(indexed_workspace.con, "index_generation", "concurrent-generation")
            return result

        monkeypatch.setattr(service_module, "find_path", change_generation)
        with pytest.raises(IndexStaleError) as exc_info:
            service.path("AuthService", "validate_session", consistency="strict")
        assert exc_info.value.details["freshness"]["generation_changed"] is True

    def test_bounded_path_reports_source_edit_during_query(
        self, indexed_workspace, monkeypatch
    ):
        import poldergraph.retrieval.service as service_module
        from poldergraph.retrieval.service import QueryService
        from poldergraph.storage.repository import Repository

        service = QueryService(
            Repository(indexed_workspace.con),
            indexed_workspace.config,
            root_id=indexed_workspace.root_id(),
            workspace=indexed_workspace,
        )
        original_find_path = service_module.find_path
        source = indexed_workspace.root / "pkg" / "auth.py"

        def edit_during_query(*args, **kwargs):
            result = original_find_path(*args, **kwargs)
            source.write_text(source.read_text() + "\n# edited during query\n")
            return result

        monkeypatch.setattr(service_module, "find_path", edit_during_query)
        result = service.path("AuthService", "validate_session", consistency="bounded")
        report = result["consistency_report"]
        assert report["status"] == "stale"
        assert report["source_read_required"] is True
        assert "pkg/auth.py" in report["stale_files"]
        assert report["structural_freshness"] == "stale"

    def test_strict_path_rejects_changed_git_revision(self, indexed_workspace, monkeypatch):
        import poldergraph.indexing.pipeline as pipeline
        from poldergraph.errors import IndexStaleError
        from poldergraph.retrieval.service import QueryService
        from poldergraph.storage.repository import Repository
        from poldergraph.storage.sqlite import set_meta

        service = QueryService(
            Repository(indexed_workspace.con),
            indexed_workspace.config,
            root_id=indexed_workspace.root_id(),
            workspace=indexed_workspace,
        )
        set_meta(indexed_workspace.con, "indexed_head", "old-revision")
        monkeypatch.setattr(pipeline, "git_state", lambda _root: ("main", "new-revision"))

        with pytest.raises(IndexStaleError) as exc_info:
            service.path("AuthService", "validate_session", consistency="strict")
        freshness = exc_info.value.details["freshness"]
        assert freshness["revision_changed"] is True
        assert freshness["current_revision"] == "new-revision"

    def test_strict_path_detects_external_database_commit_during_query(
        self, indexed_workspace, monkeypatch
    ):
        import sqlite3

        import poldergraph.retrieval.service as service_module
        from poldergraph.errors import IndexStaleError
        from poldergraph.retrieval.service import QueryService
        from poldergraph.storage.repository import Repository

        service = QueryService(
            Repository(indexed_workspace.con),
            indexed_workspace.config,
            root_id=indexed_workspace.root_id(),
            workspace=indexed_workspace,
        )
        original_find_path = service_module.find_path

        def commit_during_query(*args, **kwargs):
            result = original_find_path(*args, **kwargs)
            with sqlite3.connect(indexed_workspace.index_dir / "index.sqlite3") as connection:
                connection.execute(
                    "INSERT INTO meta(key, value) VALUES('concurrent_touch', '1') "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value"
                )
            return result

        monkeypatch.setattr(service_module, "find_path", commit_during_query)
        with pytest.raises(IndexStaleError) as exc_info:
            service.path("AuthService", "validate_session", consistency="strict")
        assert exc_info.value.details["freshness"]["database_changed"] is True

    def test_strict_path_detects_same_connection_write_during_query(
        self, indexed_workspace, monkeypatch
    ):
        import poldergraph.retrieval.service as service_module
        from poldergraph.errors import IndexStaleError
        from poldergraph.retrieval.service import QueryService
        from poldergraph.storage.repository import Repository
        from poldergraph.storage.sqlite import set_meta

        service = QueryService(
            Repository(indexed_workspace.con),
            indexed_workspace.config,
            root_id=indexed_workspace.root_id(),
            workspace=indexed_workspace,
        )
        original_find_path = service_module.find_path

        def write_during_query(*args, **kwargs):
            result = original_find_path(*args, **kwargs)
            set_meta(indexed_workspace.con, "concurrent_touch", "1")
            return result

        monkeypatch.setattr(service_module, "find_path", write_during_query)
        with pytest.raises(IndexStaleError) as exc_info:
            service.path("AuthService", "validate_session", consistency="strict")
        assert exc_info.value.details["freshness"]["connection_changed"] is True

    def test_global_graph_payload_shape(self, api_client):
        data = api_client.get("/api/graph/global?limit=50").json()["data"]
        assert data["nodes"] and data["edges"]
        node = data["nodes"][0]
        for key in ("id", "label", "kind", "is_container", "degree", "importance", "community"):
            assert key in node, f"node missing {key}"
        edge = data["edges"][0]
        # The dashboard client reads `source`/`target`.
        for key in ("id", "source", "target", "type", "provenance", "confidence"):
            assert key in edge, f"edge missing {key}"

    def test_graph_edges_reference_known_nodes(self, api_client):
        data = api_client.get("/api/graph/global?limit=100").json()["data"]
        ids = {node["id"] for node in data["nodes"]}
        for edge in data["edges"]:
            assert edge["source"] in ids
            assert edge["target"] in ids

    def test_neighborhood_is_bounded(self, api_client):
        graph = api_client.get("/api/graph/global?limit=100").json()["data"]
        entity_id = graph["nodes"][0]["id"]
        data = api_client.get(f"/api/graph/neighborhood/{entity_id}?depth=1").json()["data"]
        assert data["nodes"]
        assert len(data["nodes"]) <= 400

    def test_search_evidence_and_features(self, api_client):
        data = api_client.get("/api/search?q=AuthService&limit=5").json()["data"]
        assert data["results"]
        result = data["results"][0]
        assert result["evidence"] in {"exact", "lexical", "semantic", "graph-expanded"}
        assert isinstance(result["score_features"], dict)

    def test_search_strict_consistency_returns_freshness_contract(self, api_client):
        payload = api_client.get("/api/search?q=AuthService&include_semantic=false&consistency=strict").json()
        assert payload["ok"] is True
        assert payload["index"]["fresh"] is True
        assert payload["index"]["generation"]
        assert payload["data"]["consistency"] == "strict"

    def test_search_strict_consistency_reports_stale_files(self, api_client, sample_repo):
        source = sample_repo / "pkg" / "auth.py"
        source.write_text(source.read_text() + "\n# stale evidence\n")
        response = api_client.get(
            "/api/search?q=AuthService&include_semantic=false&consistency=strict"
        )
        payload = response.json()
        assert response.status_code == 400
        assert payload["error"]["code"] == "INDEX_STALE"
        assert "pkg/auth.py" in payload["error"]["details"]["freshness"]["stale_files"]

    def test_path_api_strict_consistency_returns_generation_report(self, api_client):
        response = api_client.get(
            "/api/path?from=AuthService&to=validate_session&consistency=strict"
        )
        assert response.status_code == 200
        assert response.json()["data"]["consistency_report"]["verified"] is True

    def test_search_graph_context_is_bounded_and_valid(self, api_client):
        data = api_client.get(
            "/api/search?q=AuthService&limit=5&include_graph_context=true&graph_context_limit=2&graph_fanout=3"
        ).json()["data"]
        graph = data["graph"]
        assert graph["nodes"]
        assert len(graph["nodes"]) <= 8
        ids = {node["id"] for node in graph["nodes"]}
        assert all(edge["source"] in ids and edge["target"] in ids for edge in graph["edges"])

    def test_configured_typed_decision_routes_ambiguous_graph_search(
        self, api_client, monkeypatch
    ):
        from poldergraph.retrieval import service as retrieval_service

        monkeypatch.setattr(retrieval_service, "provider_enabled", lambda config: True)
        monkeypatch.setattr(retrieval_service, "exact_matches", lambda *args, **kwargs: [])
        monkeypatch.setattr(retrieval_service, "lexical_candidates", lambda *args, **kwargs: [])
        monkeypatch.setattr(
            retrieval_service,
            "decide_query_route",
            lambda *args: {
                "status": "applied",
                "provider": "typesafe",
                "model": "test-model",
                "intent": {"value": "architecture", "confidence": 0.97},
                "retrieval": {"value": "lexical", "confidence": 0.94},
            },
        )
        monkeypatch.setattr(
            retrieval_service,
            "semantic_candidates",
            lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("lexical route must skip vectors")),
        )
        data = api_client.get("/api/search?q=explain+the+overall+organization").json()["data"]
        assert data["intent"] == "architecture"
        assert data["routing"] == {
            "intent": "architecture",
            "strategy": "lexical",
            "decision_plan": "lexical",
            "source": "decision",
            "provider": "typesafe",
            "model": "test-model",
            "decision_status": "applied",
            "confidence": {"intent": 0.97, "retrieval": 0.94},
        }

        from types import SimpleNamespace

        from poldergraph.retrieval.lexical import Candidate

        expansions = []
        monkeypatch.setattr(
            retrieval_service,
            "decide_query_route",
            lambda *args: {
                "status": "applied",
                "provider": "typesafe",
                "model": "test-model",
                "intent": {"value": "how_reaches", "confidence": 0.97},
                "retrieval": {"value": "graph", "confidence": 0.94},
            },
        )
        monkeypatch.setattr(
            retrieval_service,
            "lexical_candidates",
            lambda *args, **kwargs: [Candidate("seed", features={"score": 0.5})],
        )
        monkeypatch.setattr(
            retrieval_service,
            "expand",
            lambda _repo, seeds, **kwargs: (
                expansions.append((seeds, kwargs))
                or SimpleNamespace(entity_ids=[], truncated=False)
            ),
        )
        monkeypatch.setattr(retrieval_service, "fuse", lambda *args, **kwargs: [])
        graph_data = api_client.get(
            "/api/search?q=trace+the+service+flow&include_semantic=false"
        ).json()["data"]
        assert graph_data["routing"]["strategy"] == "graph"
        assert graph_data["intent"] == "how_reaches"
        assert expansions and expansions[0][0] == ["seed"]

    def test_memory_api_crud_is_project_scoped(self, api_client):
        created = api_client.post(
            "/api/memory", json={"content": "Use the repository's shared API client", "scope": "project", "kind": "workflow", "tags": ["dashboard"]}
        ).json()
        assert created["ok"] is True
        memory_id = created["data"]["id"]
        found = api_client.get("/api/memory?scope=project").json()["data"]["results"]
        assert any(item["id"] == memory_id for item in found)
        updated = api_client.post(f"/api/memory/{memory_id}/update", json={"content": "Keep the dashboard API client shared"}).json()
        assert updated["ok"] is True
        forgotten = api_client.post(f"/api/memory/{memory_id}/forget").json()
        assert forgotten["ok"] is True
        after = api_client.get("/api/memory?scope=project").json()["data"]["results"]
        assert all(item["id"] != memory_id for item in after)

    def test_memory_search_api_applies_shared_typed_relevance_gate(self, api_client, monkeypatch):
        from poldergraph import decision_runtime

        added = api_client.post(
            "/api/memory", json={"content": "The repository uses a stable project API", "scope": "project"}
        ).json()["data"]
        assert added["id"]
        monkeypatch.setattr(
            decision_runtime,
            "decide_memory_relevance",
            lambda query, results, config: ([], {"status": "applied", "filtered": 1}),
        )
        result = api_client.get("/api/memory/search?q=project+api&semantic=false").json()["data"]
        assert result["results"] == []
        assert result["memory_decision"] == {"status": "applied", "filtered": 1}

    def test_query_service_calls_typed_decisions_and_uses_selected_route(
        self, indexed_workspace, monkeypatch
    ):
        from poldergraph import decisions
        from poldergraph.retrieval import service as retrieval_service
        from poldergraph.retrieval.lexical import Candidate
        from poldergraph.retrieval.service import QueryService
        from poldergraph.storage.repository import Repository

        workspace = indexed_workspace
        workspace.config.decisions.provider = "typesafe"
        workspace.config.decisions.remote_authorized = True
        workspace.config.decisions.authorized_remote_providers = ["typesafe"]
        repo = Repository(workspace.con)
        service = QueryService(repo, workspace.config, root_id=workspace.root_id(), workspace=workspace)
        monkeypatch.setattr(retrieval_service, "exact_matches", lambda *args, **kwargs: [])
        monkeypatch.setattr(retrieval_service, "lexical_candidates", lambda *args, **kwargs: [])
        semantic_calls = []
        monkeypatch.setattr(
            retrieval_service,
            "semantic_candidates",
            lambda *args, **kwargs: semantic_calls.append(args[1]) or ([], None),
        )
        request = {}
        provider_calls = []

        def fake_post(url, token, payload, timeout):
            provider_calls.append(1)
            request.update(url=url, token=token, payload=payload, timeout=timeout)
            return {
                "model": "jev-test",
                "answers": {
                    "intent": {
                        "choice": "architecture",
                        "probabilities": {"architecture": 0.97, "semantic": 0.03},
                    },
                    "retrieval": {
                        "choice": "lexical",
                        "probabilities": {"lexical": 0.96, "hybrid": 0.04},
                    },
                },
                "usage": {},
            }

        monkeypatch.setattr(decisions, "_post_json", fake_post)
        monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
        response = service.search("what happens with requests across layers")
        assert request["url"] == "https://api.typesafe.ai/v1/systemone"
        assert request["payload"]["questions"]["retrieval"]["type"] == "choice"
        assert response.routing["source"] == "decision"
        assert response.routing["strategy"] == "lexical"
        assert response.intent == "architecture"
        assert semantic_calls == []
        assert provider_calls == [1]

        monkeypatch.setattr(
            retrieval_service,
            "lexical_candidates",
            lambda *args, **kwargs: [Candidate("strong-hit", features={"score": 0.91})],
        )
        fast_response = service.search("what happens with requests across layers")
        assert fast_response.routing["decision_status"] == "fast_path"
        assert fast_response.routing["provider"] == "typesafe"
        assert provider_calls == [1]

    def test_entity_relations_use_entity_key(self, api_client):
        graph = api_client.get("/api/graph/global?limit=100").json()["data"]
        entity_id = graph["nodes"][0]["id"]
        data = api_client.get(f"/api/entity/{entity_id}").json()["data"]
        assert data["entity"]["id"] == entity_id
        for group in ("inbound", "outbound"):
            for relation in data[group]:
                assert "entity" in relation, f"{group} relation missing `entity` key"

    def test_source_endpoint_rejects_traversal(self, api_client):
        for bad in ("../../etc/passwd", "/etc/passwd", "pkg/../../../etc/passwd"):
            payload = api_client.get(f"/api/source?path={bad}").json()
            assert payload["ok"] is False
            assert payload["error"]["code"]

    def test_source_endpoint_serves_indexed_file(self, api_client):
        payload = api_client.get("/api/source?path=pkg/auth.py&start_line=1&end_line=3").json()
        assert payload["ok"] is True
        assert "from .models import Session" in payload["data"]["content"]
        # 1-based inclusive: line 1 is the first line, not the second.
        assert payload["data"]["content"].splitlines()[0] == "from .models import Session"

    def test_errors_use_the_envelope(self, api_client):
        payload = api_client.get("/api/entity/nonexistent_id").json()
        assert payload["ok"] is False
        assert set(payload["error"]) >= {"code", "message"}

    def test_path_and_impact(self, api_client):
        data = api_client.get("/api/path?from=AuthService&to=Session").json()
        assert "found" in data["data"]
        impact = api_client.get("/api/impact/Session").json()
        assert "direct" in impact["data"]

    def test_responses_are_json_serializable(self, api_client):
        for url in ("/api/status", "/api/graph/global?limit=20", "/api/communities"):
            json.dumps(api_client.get(url).json())
