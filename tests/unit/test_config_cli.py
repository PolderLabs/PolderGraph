"""Regression coverage for workspace configuration edits and inspection."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from typer.testing import CliRunner

from poldergraph.cli import app
from poldergraph.config.loader import load_config


def _workspace(root: Path) -> Path:
    index_dir = root / ".poldergraph"
    index_dir.mkdir()
    return index_dir


def test_config_set_parses_list_values_and_preserves_file_after_invalid_input(tmp_path: Path):
    root = tmp_path / "workspace"
    root.mkdir()
    index_dir = _workspace(root)
    runner = CliRunner()

    success = runner.invoke(
        app,
        ["config", "set", "decisions.remote_providers", '["typesafe"]', str(root)],
    )

    assert success.exit_code == 0, success.output
    assert tomllib.loads((index_dir / "config.toml").read_text(encoding="utf-8")) == {
        "decisions": {"remote_providers": ["typesafe"]}
    }

    before = (index_dir / "config.toml").read_text(encoding="utf-8")
    invalid = runner.invoke(
        app,
        ["config", "set", "decisions.remote_providers", "[typesafe]", str(root)],
    )

    assert invalid.exit_code == 2
    assert "Invalid TOML value" in invalid.output
    assert (index_dir / "config.toml").read_text(encoding="utf-8") == before


def test_config_set_preserves_user_trust_origins(tmp_path: Path, monkeypatch):
    root = tmp_path / "workspace"
    root.mkdir()
    index_dir = _workspace(root)
    (index_dir / "config.toml").write_text(
        "[decisions]\nprovider = 'typesafe'\n",
        encoding="utf-8",
    )
    user_config = tmp_path / "user.toml"
    user_config.write_text(
        "[privacy]\nallow_remote_embedding = true\nallow_remote_decisions = true\n\n"
        "[embedding]\napi_endpoint = 'https://embedding.example'\n\n"
        "[decisions]\nremote_providers = ['typesafe']\nendpoint = 'https://decisions.example'\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("poldergraph.config.loader.user_config_path", lambda: user_config)

    result = CliRunner().invoke(app, ["config", "set", "ui.port", "8000", str(root)])

    assert result.exit_code == 0, result.output
    workspace_data = tomllib.loads((index_dir / "config.toml").read_text(encoding="utf-8"))
    assert workspace_data == {"decisions": {"provider": "typesafe"}, "ui": {"port": 8000}}
    loaded = load_config(index_dir, environ={}, user_path=user_config)
    assert loaded.config.embedding.remote_authorized is True
    assert loaded.config.embedding.endpoint_authorized is True
    assert loaded.config.decisions.remote_authorized is True
    assert loaded.config.decisions.authorized_remote_providers == ["typesafe"]
    assert loaded.config.decisions.endpoint_authorized is True
    assert loaded.origin_of("privacy.allow_remote_decisions") == "user"
    assert loaded.origin_of("ui.port") == "workspace"


def test_config_show_reports_all_origins_and_hosted_authorization(tmp_path: Path, monkeypatch):
    root = tmp_path / "workspace"
    root.mkdir()
    index_dir = _workspace(root)
    (index_dir / "config.toml").write_text(
        "[privacy]\nallow_remote_decisions = true\n\n"
        "[decisions]\nprovider = 'typesafe'\nremote_providers = ['typesafe']\n"
        "endpoint = 'https://workspace.example'\n",
        encoding="utf-8",
    )
    user_config = tmp_path / "user.toml"
    user_config.write_text(
        "[privacy]\nallow_remote_decisions = true\n\n"
        "[decisions]\nremote_providers = ['typesafe']\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("poldergraph.config.loader.user_config_path", lambda: user_config)

    result = CliRunner().invoke(app, ["config", "show", "--effective", "--json", str(root)])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["origins"]["index.dimensions"] == "default"
    assert data["origins"]["privacy.allow_remote_decisions"] == "workspace"
    assert data["origins"]["decisions.provider"] == "workspace"
    assert data["origins"]["decisions.remote_providers"] == "workspace"
    authorization = data["hosted_authorization"]["decisions"]
    assert authorization["remote_authorized"] is False
    assert authorization["endpoint_authorized"] is False
    assert authorization["consent_origin"] == "workspace"
    assert authorization["provider_allowlist_origin"] == "workspace"
    assert authorization["endpoint_origin"] == "workspace"
    assert "user config" in authorization["reason"].lower()
