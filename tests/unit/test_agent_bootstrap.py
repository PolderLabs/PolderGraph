import json
from concurrent.futures import ThreadPoolExecutor

from typer.testing import CliRunner

from poldergraph.agents.bootstrap import ensure_workspace_ready
from poldergraph.cli import app
from poldergraph.workspace import find_index_dir, open_workspace


def test_agent_bootstrap_creates_structural_index_without_embedding(tmp_path):
    (tmp_path / "main.py").write_text("def handler():\n    return 1\n", encoding="utf-8")

    result = ensure_workspace_ready(tmp_path)

    assert result["ok"] is True
    assert result["created"] is True
    assert result["state"] == "ready_structural"
    assert find_index_dir(tmp_path) == tmp_path / ".poldergraph"
    workspace = open_workspace(tmp_path)
    try:
        assert workspace.con.execute("SELECT COUNT(*) FROM files").fetchone()[0] >= 1
        assert workspace.con.execute("SELECT COUNT(*) FROM entities").fetchone()[0] >= 1
    finally:
        workspace.close()


def test_agent_bootstrap_refreshes_existing_index_idempotently(tmp_path):
    (tmp_path / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
    first = ensure_workspace_ready(tmp_path)
    (tmp_path / "main.py").write_text("VALUE = 2\n", encoding="utf-8")

    second = ensure_workspace_ready(tmp_path)

    assert first["created"] is True
    assert second["created"] is False
    assert second["plan"]["changed"] == 1
    assert second["index"]["files_indexed"] == 1


def test_project_opt_out_prevents_automatic_index_creation(tmp_path):
    (tmp_path / ".poldergraph-disable").touch()

    result = ensure_workspace_ready(tmp_path)

    assert result["state"] == "unavailable"
    assert "Remove .poldergraph-disable" in result["recovery"]
    assert find_index_dir(tmp_path) is None


def test_agent_auto_index_command_disables_and_reenables_project(tmp_path):
    marker = tmp_path / ".poldergraph-disable"
    runner = CliRunner()

    disabled = runner.invoke(app, ["agent-auto-index", str(tmp_path), "--json"])
    assert disabled.exit_code == 0, disabled.output
    assert json.loads(disabled.output)["data"] == {
        "root": str(tmp_path),
        "enabled": False,
        "changed": True,
        "opt_out_file": str(marker),
    }
    assert marker.is_file()
    assert ensure_workspace_ready(tmp_path)["state"] == "unavailable"

    enabled = runner.invoke(
        app, ["agent-auto-index", str(tmp_path), "--enable", "--json"]
    )
    assert enabled.exit_code == 0, enabled.output
    assert json.loads(enabled.output)["data"]["enabled"] is True
    assert json.loads(enabled.output)["data"]["changed"] is True
    assert not marker.exists()
    assert ensure_workspace_ready(tmp_path)["state"] == "ready_structural"


def test_environment_opt_out_prevents_automatic_index_creation(tmp_path, monkeypatch):
    monkeypatch.setenv("POLDERGRAPH_AUTO_INDEX", "0")

    result = ensure_workspace_ready(tmp_path)

    assert result["state"] == "unavailable"
    assert find_index_dir(tmp_path) is None


def test_concurrent_first_bootstrap_creates_one_valid_index(tmp_path):
    (tmp_path / "main.py").write_text("def handler():\n    return 1\n", encoding="utf-8")

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _n: ensure_workspace_ready(tmp_path), range(4)))

    assert all(result["state"] == "ready_structural" for result in results)
    workspace = open_workspace(tmp_path)
    try:
        assert workspace.con.execute("SELECT COUNT(*) FROM files").fetchone()[0] == 1
        assert workspace.con.execute("SELECT COUNT(*) FROM entities").fetchone()[0] >= 1
    finally:
        workspace.close()
