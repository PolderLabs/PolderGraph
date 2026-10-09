"""Codex native lifecycle hook contract and setup behavior."""

import io
import json

from poldergraph.agents import codex_hook
from poldergraph.agents import setup as agent_setup
from poldergraph.agents.setup import setup_agent_guidance, write_codex_hooks_config
from poldergraph.config.models import Config


def test_codex_hook_emits_user_prompt_submit_context_json(tmp_path, monkeypatch):
    monkeypatch.setattr(
        codex_hook,
        "_context_for",
        lambda event: "grounded local context" if event.get("prompt") else None,
    )
    event = {
        "hook_event_name": "UserPromptSubmit",
        "prompt": "find the login handler",
        "cwd": str(tmp_path),
        "session_id": "session-1",
        "turn_id": "turn-1",
    }
    output = io.StringIO()
    assert codex_hook.run_hook(io.StringIO(json.dumps(event)), output) == 0
    payload = json.loads(output.getvalue())
    assert payload["hookSpecificOutput"] == {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "grounded local context",
    }


def test_codex_hook_uses_offline_context_and_skips_social_plan(tmp_path, monkeypatch):
    calls = []

    def fake_run(root, args, timeout):
        calls.append(args)
        if args[0] == "status":
            return {"ok": True, "index": {"fresh": True}}
        assert "--offline" in args
        return {"ok": True, "data": {"plan": {"skipped": True}}}

    monkeypatch.setattr(codex_hook, "_run", fake_run)
    event = {"prompt": "thanks", "cwd": str(tmp_path)}
    assert codex_hook._context_for(event) is None
    assert calls[0][0] == "status"
    assert calls[1][0] == "context"


def test_codex_hook_refreshes_stale_index_without_model(tmp_path, monkeypatch):
    calls = []

    def fake_run(root, args, timeout):
        calls.append(args)
        if args[0] == "status":
            return {"ok": True, "index": {"fresh": False}}
        if args[0] == "update":
            assert "--no-embed" in args
            return {"ok": True}
        return {"ok": True, "data": {"plan": {"skipped": True}}}

    monkeypatch.setattr(codex_hook, "_run", fake_run)
    assert codex_hook._context_for({"prompt": "fix the parser", "cwd": str(tmp_path)}) is None
    assert [call[0] for call in calls] == ["status", "update", "context"]


def test_codex_hook_setup_preserves_existing_handlers_and_is_idempotent(tmp_path):
    path = tmp_path / ".codex" / "hooks.json"
    path.parent.mkdir()
    path.write_text(json.dumps({"description": "existing", "hooks": {
        "SessionStart": [{"hooks": [{"type": "command", "command": "existing"}]}],
    }}))

    changed, _ = write_codex_hooks_config(tmp_path)
    assert changed
    config = json.loads(path.read_text())
    assert config["description"] == "existing"
    assert config["hooks"]["SessionStart"][0]["hooks"][0]["command"] == "existing"
    handler = config["hooks"]["UserPromptSubmit"][0]["hooks"][0]
    assert handler["type"] == "command"
    assert "codex-hook" in handler["command"]
    assert handler["timeout"] == 300
    changed, _ = write_codex_hooks_config(tmp_path)
    assert not changed
    assert len(config["hooks"]["UserPromptSubmit"]) == 1


def test_codex_hook_setup_fallback_command_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(agent_setup.shutil, "which", lambda _: None)
    changed, _ = write_codex_hooks_config(tmp_path)
    assert changed
    changed, message = write_codex_hooks_config(tmp_path)
    assert not changed
    assert "already installs" in message


def test_codex_hook_setup_writes_windows_command(tmp_path, monkeypatch):
    monkeypatch.setattr(agent_setup.sys, "platform", "win32")
    monkeypatch.setattr(agent_setup.shutil, "which", lambda _: r"C:\Program Files\PolderGraph\poldergraph.exe")

    changed, _ = write_codex_hooks_config(tmp_path)

    assert changed
    handler = json.loads((tmp_path / ".codex" / "hooks.json").read_text())[
        "hooks"]["UserPromptSubmit"][0]["hooks"][0]
    assert handler["commandWindows"] == handler["command"]
    assert "Program Files" in handler["commandWindows"]


def test_setup_agent_reports_explicit_codex_hook_installation(tmp_path):
    result = setup_agent_guidance(
        tmp_path, Config(), targets=["codex"], hooks=True,
    )
    assert result["hooks_requested"] is True
    assert result["hooks_installed"] is True
    assert (tmp_path / ".codex" / "hooks.json").is_file()
