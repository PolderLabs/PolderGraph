"""Query daemon behaviour.

The daemon exists so repeated agent queries do not each pay embedding-model
setup. These tests cover its contract: identical results to in-process
execution, correct invalidation after an index update, and safe fallback.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from poldergraph.query_daemon import (
    Daemon,
    _named,
    _without,
    resolve_index_dir,
    socket_path,
)


@pytest.fixture(scope="module")
def daemon(tmp_path_factory):
    """A daemon bound to the shared indexed workspace, loaded once."""
    workspace = tmp_path_factory.mktemp("daemon_repo") / "repo"
    workspace.mkdir(parents=True)
    (workspace / "auth.py").write_text(
        'from models import Session\n'
        '\n'
        'class AuthService:\n'
        '    """Validate sessions."""\n'
        '    def validate_session(self, token: str) -> Session:\n'
        '        return Session(token)\n'
    )
    (workspace / "models.py").write_text(
        'class Session:\n    """A session."""\n    def __init__(self, t): self.t = t\n'
    )

    from poldergraph.config.models import Config
    from poldergraph.graph import run_graph_stage
    from poldergraph.indexing.pipeline import Indexer
    from poldergraph.storage.repository import Repository
    from poldergraph.workspace import create_index, open_workspace

    create_index(workspace, Config())
    ws = open_workspace(workspace)
    indexer = Indexer(ws, backend=None)
    indexer.ensure_root()
    indexer.run(indexer.discover())
    run_graph_stage(ws, ws.config, Repository(ws.con), None)
    ws.close()

    instance = Daemon(workspace)
    instance._ensure_loaded()
    yield instance
    if instance._supervisor:
        instance._supervisor.stop()
    instance._workspace.close() if instance._workspace else None


class TestArgumentMapping:
    def test_named_prefers_service_key(self):
        assert _named({"entity_ref": "A", "entity": "B"}, "entity_ref", "entity") == "A"

    def test_named_falls_back_to_client_key(self):
        assert _named({"entity": "B"}, "entity_ref", "entity") == "B"

    def test_without_removes_keys(self):
        assert _without({"a": 1, "b": 2, "entity": 3}, "entity") == {"a": 1, "b": 2}


class TestDaemonResults:
    def test_daemon_starts_workspace_supervisor(self, daemon):
        assert daemon._supervisor is not None
        assert daemon._supervisor.status()["state"] in {"running", "supervised_elsewhere"}

    def test_search_matches_in_process(self, daemon):
        """A daemon answer must equal the answer computed in-process.

        Both sides use the same backend, otherwise the only difference would be
        the semantic channel being present on one side.
        """
        service = daemon._service
        remote = daemon.handle("search", {"query": "AuthService", "limit": 5})
        local = service.search("AuthService", limit=5).to_dict()
        assert remote["results"] == local["results"]
        assert remote["intent"] == local["intent"]

    def test_explain_accepts_client_argument_names(self, daemon):
        result = daemon.handle("explain", {"entity": "AuthService"})
        assert result["entity"]["qualified_name"] == "AuthService"

    def test_related_accepts_client_argument_names(self, daemon):
        result = daemon.handle("related", {"entity": "Session", "limit": 3})
        assert "related" in result

    def test_path_accepts_client_argument_names(self, daemon):
        result = daemon.handle(
            "path", {"source": "AuthService", "target": "Session"}
        )
        assert result["found"] is True

    def test_impact_accepts_client_argument_names(self, daemon):
        result = daemon.handle("impact", {"entity": "Session", "max_depth": 2})
        assert "direct" in result

    def test_unknown_entity_reports_actionable_error(self, daemon):
        result = daemon.handle("explain", {"entity": "no_such_symbol_here"})
        assert result["ok"] is False
        assert result["error"]["code"]

    def test_filters_survive_the_process_boundary(self, daemon):
        result = daemon.handle(
            "search",
            {"query": "Session", "limit": 5, "filters": {"kinds": ["class"]}},
        )
        assert all(item["kind"] == "class" for item in result["results"])

    def test_strict_freshness_error_survives_the_process_boundary(self, daemon):
        source = daemon.root / "auth.py"
        source.write_text(source.read_text() + "\n# stale after indexing\n")
        result = daemon.handle(
            "search", {"query": "AuthService", "include_semantic": False, "consistency": "strict"}
        )
        assert result["ok"] is False
        assert result["error"]["code"] == "INDEX_STALE"
        assert "auth.py" in result["error"]["details"]["freshness"]["stale_files"]

    def test_supervisor_indexes_an_edit_without_manual_update(self, daemon):
        source = daemon.root / "auth.py"
        source.write_text(
            source.read_text() + "\n\ndef automatic_watch_probe():\n    return True\n"
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if daemon._service.resolve_entity("automatic_watch_probe") is not None:
                break
            time.sleep(0.1)
        assert daemon._service.resolve_entity("automatic_watch_probe") is not None, (
            daemon._supervisor.status() if daemon._supervisor else None
        )

    def test_supervisor_coalesces_rapid_edits_with_three_readers(self, daemon):
        source = daemon.root / "auth.py"
        baseline = source.read_text()

        def read_client(_client):
            results = []
            for _ in range(12):
                result = daemon.handle("search", {"query": "AuthService", "limit": 3})
                results.append(result.get("ok", True))
                time.sleep(0.01)
            return results

        with ThreadPoolExecutor(max_workers=3) as clients:
            reads = [clients.submit(read_client, client) for client in range(3)]
            for revision in range(100):
                source.write_text(
                    baseline + f"\n\ndef burst_probe_{revision}():\n    return {revision}\n"
                )
                time.sleep(0.003)

            results = [future.result(timeout=15) for future in reads]

        assert all(all(client_results) for client_results in results)
        expected = "burst_probe_99"
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if daemon._service.resolve_entity(expected) is not None:
                break
            time.sleep(0.1)
        assert daemon._service.resolve_entity(expected) is not None


class TestSocketPaths:
    def test_socket_lives_inside_index_dir(self, indexed_workspace):
        index_dir = indexed_workspace.index_dir
        path = socket_path(index_dir)
        # A nested ".poldergraph/.poldergraph" path would never resolve.
        assert path.parent == index_dir

    def test_resolve_finds_index_dir(self, indexed_workspace):
        resolved = resolve_index_dir(indexed_workspace.root)
        assert resolved == indexed_workspace.index_dir
