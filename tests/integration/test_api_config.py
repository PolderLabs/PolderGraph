"""The dashboard's configuration surface: read, write, and download guards."""

from __future__ import annotations

from fastapi.testclient import TestClient

from poldergraph.api.server import create_app
from poldergraph.workspace import open_workspace


def _client(root):
    """A client over a freshly created index, as the dashboard always sees one."""
    from poldergraph.config.models import Config
    from poldergraph.workspace import create_index

    (root / "app.py").write_text("def run() -> int:\n    return 1\n", encoding="utf-8")
    create_index(root, Config(embedding={"backend": "none"}))
    return TestClient(
        create_app(open_workspace(root), watch=False), raise_server_exceptions=False
    )


def test_config_api_rejects_unknown_and_writes(tmp_path):
    client = _client(tmp_path)

    payload = client.get("/api/config").json()["data"]
    assert set(payload) == {
        "index",
        "embedding",
        "semantic_edges",
        "graph",
        "retrieval",
        "privacy",
        "decisions",
    }
    # A typo must be reported rather than silently ignored, otherwise a broken
    # setting looks exactly like a working one.
    assert client.put("/api/config", json={"nope": {}}).status_code == 400
    assert client.put("/api/config", json={"embedding": {"nonsense": 1}}).status_code == 400

    written = client.put(
        "/api/config", json={"decisions": {"provider": "disabled", "timeout": 5.0}}
    )
    assert written.status_code == 200
    assert written.json()["data"]["applied"] == ["decisions"]
    assert client.get("/api/config").json()["data"]["decisions"]["timeout"] == 5.0


def test_written_config_is_persisted_to_the_workspace(tmp_path):
    client = _client(tmp_path)

    assert (
        client.put("/api/config", json={"index": {"dimensions": 384}}).status_code == 200
    )
    written = (tmp_path / ".poldergraph" / "config.toml").read_text(encoding="utf-8")
    assert "384" in written


def test_model_download_respects_the_privacy_switch(tmp_path):
    client = _client(tmp_path)

    assert client.get("/api/models/status").json()["data"]["allow_downloads"] is True
    assert (
        client.put("/api/config", json={"privacy": {"allow_model_downloads": False}}).status_code
        == 200
    )

    denied = client.post("/api/models/download")
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "DOWNLOAD_DISABLED"


def test_model_status_reports_what_is_actually_local(tmp_path):
    client = _client(tmp_path)

    status = client.get("/api/models/status").json()["data"]
    assert status["backend"] in {"native", "ollama", "api", "none"}
    assert isinstance(status["cached"], bool)
    assert status["vectors"] == 0


def test_remote_embedding_stays_off_by_default(tmp_path):
    """The dashboard must not be able to switch egress on by accident."""
    data = _client(tmp_path).get("/api/config").json()["data"]

    assert data["privacy"]["allow_remote_embedding"] is False
    assert data["privacy"]["allow_remote_decisions"] is False
    assert data["decisions"]["provider"] == "disabled"