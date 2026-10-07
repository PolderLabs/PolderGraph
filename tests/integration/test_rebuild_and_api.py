"""Rebuild atomicity and dashboard API contract tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from poldergraph.config.models import Config
from poldergraph.errors import API_VERSION
from poldergraph.workspace import create_index, open_workspace


class TestRebuild:
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
        from poldergraph.storage import integrity
        from poldergraph.rebuild import rebuild_index

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

        with pytest.raises(Exception):
            rebuild_index(sample_repo, use_backend=False)

        assert (sample_repo / ".poldergraph" / "index.sqlite3").read_bytes() == before
        assert not (sample_repo / ".poldergraph.rebuild").exists()


@pytest.fixture()
def api_client(sample_repo: Path):
    """A FastAPI test client bound to an indexed repository."""
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from poldergraph.api.server import create_app

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
        payload = api_client.get("/api/source?path=pkg/auth.py&start_line=0&end_line=3").json()
        assert payload["ok"] is True
        assert "from .models import Session" in payload["data"]["content"]

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