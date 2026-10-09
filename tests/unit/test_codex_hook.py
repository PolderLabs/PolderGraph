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


def test_codex_hook_bootstraps_fresh_repo_and_injects_real_context(tmp_path, monkeypatch):
    root = tmp_path / "fresh-repository"
    root.mkdir()
    (root / "auth.py").write_text(
        "class AuthService:\n    def validate(self, token):\n        return token\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("POLDERGRAPH_MEMORY_DB", str(tmp_path / "memory" / "memory.sqlite3"))
    monkeypatch.setenv("POLDERGRAPH_NO_DAEMON", "1")
    event = {
        "hook_event_name": "UserPromptSubmit",
        "prompt": "Find the AuthService validation entry point",
        "cwd": str(root),
        "session_id": "fresh-repo-session",
        "turn_id": "turn-1",
    }
    output = io.StringIO()

    assert codex_hook.run_hook(io.StringIO(json.dumps(event)), output) == 0
    payload = json.loads(output.getvalue())
    context = payload["hookSpecificOutput"]["additionalContext"]

    assert "AuthService" in context
    assert "auth.py" in context
    assert (root / ".poldergraph" / "index.sqlite3").is_file()


def test_codex_user_event_captures_explicit_preference_only(tmp_path, monkeypatch):
    from poldergraph import memory

    database = tmp_path / "shared-memory.sqlite3"
    monkeypatch.setattr(memory, "default_memory_path", lambda: database)
    monkeypatch.setattr(codex_hook, "_context_for", lambda event: None)
    event = {
        "hook_event_name": "UserPromptSubmit",
        "prompt": "I prefer concise explanations.",
        "cwd": str(tmp_path),
        "session_id": "session-2",
        "turn_id": "turn-2",
    }
    output = io.StringIO()

    assert codex_hook.run_hook(io.StringIO(json.dumps(event)), output) == 0
    saved = memory.MemoryStore(tmp_path).list(scope="user")
    assert [item["content"] for item in saved] == ["I prefer concise explanations."]
    assert saved[0]["provenance"] == {
        "source": "codex.UserPromptSubmit",
        "session_id": "session-2",
        "turn_id": "turn-2",
    }
    assert "I prefer concise explanations." not in output.getvalue()

    # Hook retries/re-entry are idempotent for the same durable preference.
    assert codex_hook.run_hook(io.StringIO(json.dumps(event)), io.StringIO()) == 0
    assert len(memory.MemoryStore(tmp_path).list(scope="user")) == 1


def test_codex_non_user_event_cannot_capture_memory(tmp_path, monkeypatch):
    from poldergraph import memory

    database = tmp_path / "shared-memory.sqlite3"
    monkeypatch.setattr(memory, "default_memory_path", lambda: database)
    event = {
        "hook_event_name": "AfterAgentTurn",
        "prompt": "I prefer concise explanations.",
        "cwd": str(tmp_path),
    }
    output = io.StringIO()

    assert codex_hook.run_hook(io.StringIO(json.dumps(event)), output) == 0
    assert not database.exists()


def test_codex_hook_uses_offline_context_and_skips_social_plan(tmp_path, monkeypatch):
    calls = []

    def fake_run(root, args, timeout):
        calls.append(args)
        if args[0] == "agent-ready":
            return {"ok": True}
        assert "--offline" in args
        return {"ok": True, "data": {"plan": {"skipped": True}}}

    monkeypatch.setattr(codex_hook, "_run", fake_run)
    event = {"prompt": "thanks", "cwd": str(tmp_path)}
    assert codex_hook._context_for(event) is None
    assert calls[0][0] == "agent-ready"
    assert calls[1][0] == "context"


def test_codex_hook_reuses_per_session_context_cursor(tmp_path, monkeypatch):
    cursor_path = tmp_path / "session-context.json"
    calls = []
    context_calls = 0

    def fake_run(root, args, timeout):
        nonlocal context_calls
        calls.append(args)
        if args[0] == "agent-ready":
            return {"ok": True}
        context_calls += 1
        if context_calls == 1:
            return {
                "ok": True,
                "data": {
                    "plan": {"skipped": False},
                    "index": {"fresh": True},
                    "entities": [{"id": "entity-a"}],
                    "evidence_cursor": "opaque-cursor-1",
                    "new_evidence_count": 1,
                },
            }
        return {
            "ok": True,
            "data": {
                "plan": {"skipped": False},
                "index": {"fresh": True},
                "entities": [],
                "evidence_cursor": "opaque-cursor-1",
                "new_evidence_count": 0,
            },
        }

    monkeypatch.setattr(codex_hook, "_run", fake_run)
    monkeypatch.setattr(codex_hook, "_context_cursor_path", lambda _event, _root: cursor_path)
    event = {
        "prompt": "explain the authentication entry point",
        "cwd": str(tmp_path),
        "session_id": "codex-session-1",
    }

    assert codex_hook._context_for(event) is not None
    assert json.loads(cursor_path.read_text())["cursor"] == "opaque-cursor-1"
    assert event["prompt"] not in cursor_path.read_text()

    assert codex_hook._context_for(event) is None
    context_calls_made = [call for call in calls if call[0] == "context"]
    assert "--new-evidence-since" not in context_calls_made[0]
    assert context_calls_made[1][
        context_calls_made[1].index("--new-evidence-since") + 1
    ] == "opaque-cursor-1"


def test_codex_hook_refreshes_stale_index_without_model(tmp_path, monkeypatch):
    calls = []

    def fake_run(root, args, timeout):
        calls.append(args)
        if args[0] == "agent-ready":
            return {"ok": True}
        return {"ok": True, "data": {"plan": {"skipped": True}}}

    monkeypatch.setattr(codex_hook, "_run", fake_run)
    assert codex_hook._context_for({"prompt": "fix the parser", "cwd": str(tmp_path)}) is None
    assert [call[0] for call in calls] == ["agent-ready", "context"]


def test_codex_hook_uses_enclosing_git_root_from_nested_folder(tmp_path, monkeypatch):
    project = tmp_path / "project"
    nested = project / "packages" / "api"
    nested.mkdir(parents=True)
    (project / ".git").write_text("gitdir: /tmp/worktree-metadata\n")
    roots = []

    def fake_run(root, args, timeout):
        roots.append(root)
        if args[0] == "agent-ready":
            return {"ok": True}
        return {"ok": True, "data": {"plan": {"skipped": True}}}

    monkeypatch.setattr(codex_hook, "_run", fake_run)
    codex_hook._context_for({"prompt": "thanks", "cwd": str(nested)})

    assert roots == [project, project]


def test_codex_hook_setup_preserves_existing_handlers_and_is_idempotent(tmp_path):
    path = tmp_path / ".codex" / "hooks.json"
    path.parent.mkdir()
    path.write_text(
        json.dumps(
            {
                "description": "existing",
                "hooks": {
                    "SessionStart": [{"hooks": [{"type": "command", "command": "existing"}]}],
                },
            }
        )
    )

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
    monkeypatch.setattr(
        agent_setup.shutil, "which", lambda _: r"C:\Program Files\PolderGraph\poldergraph.exe"
    )

    changed, _ = write_codex_hooks_config(tmp_path)

    assert changed
    handler = json.loads((tmp_path / ".codex" / "hooks.json").read_text())["hooks"][
        "UserPromptSubmit"
    ][0]["hooks"][0]
    assert handler["commandWindows"] == handler["command"]
    assert "Program Files" in handler["commandWindows"]


def test_setup_agent_reports_explicit_codex_hook_installation(tmp_path):
    result = setup_agent_guidance(
        tmp_path,
        Config(),
        targets=["codex"],
        hooks=True,
    )
    assert result["hooks_requested"] is True
    assert result["hooks_installed"] is True
    assert (tmp_path / ".codex" / "hooks.json").is_file()
