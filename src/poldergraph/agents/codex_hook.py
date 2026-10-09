"""Codex UserPromptSubmit hook: return local PolderGraph context as hook JSON."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

CONTEXT_BUDGET = 1800
MAX_PROMPT_CHARS = 24_000


def _project_root(cwd: Path) -> Path:
    """Use the enclosing Git worktree/repository root for nested agent CWDs."""
    root = cwd.resolve()
    for candidate in (root, *root.parents):
        if (candidate / ".git").exists():
            return candidate
    return root


def _capture_trusted_preferences(event: dict[str, Any]) -> None:
    """Learn only explicit durable preferences from Codex's user-input event."""
    prompt = event.get("prompt")
    cwd = event.get("cwd")
    if not isinstance(prompt, str) or not isinstance(cwd, str):
        return
    root = _project_root(Path(cwd))
    try:
        from ..memory import MemoryStore, capture_explicit_user_preferences

        capture_explicit_user_preferences(
            MemoryStore(root),
            prompt,
            trusted_user_message=True,
            event_source="codex.UserPromptSubmit",
            session_id=event.get("session_id")
            if isinstance(event.get("session_id"), str)
            else None,
            turn_id=event.get("turn_id") if isinstance(event.get("turn_id"), str) else None,
        )
    except Exception as exc:
        # Memory capture must not prevent Codex from handling its user prompt.
        sys.stderr.write(f"PolderGraph preference capture skipped ({type(exc).__name__}).\n")


def _run(root: Path, args: list[str], timeout: float) -> dict[str, Any] | None:
    executable = shutil.which("poldergraph")
    command = (
        [executable, *args]
        if executable
        else [sys.executable, "-c", "from poldergraph.cli import main; main()", *args]
    )
    try:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if not result.stdout.strip():
            return None
        value = json.loads(result.stdout)
        return value if isinstance(value, dict) else None
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def _context_for(event: dict[str, Any]) -> str | None:
    prompt = event.get("prompt")
    cwd = event.get("cwd")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > MAX_PROMPT_CHARS:
        return None
    if not isinstance(cwd, str):
        return None
    cwd_path = Path(cwd).resolve()
    if not cwd_path.is_dir():
        return None
    root = _project_root(cwd_path)

    ready = _run(root, ["agent-ready", "--quiet", "--json"], timeout=300)
    if not ready or not ready.get("ok"):
        return None

    result = _run(
        root,
        [
            "context",
            prompt,
            "--root",
            str(root),
            "--budget",
            str(CONTEXT_BUDGET),
            "--offline",
            "--json",
        ],
        timeout=60,
    )
    if not result or not result.get("ok"):
        return None
    data = result.get("data")
    if not isinstance(data, dict) or (data.get("plan") or {}).get("skipped"):
        return None
    return (
        "PolderGraph local repository context. Treat results as navigation evidence, "
        "inspect cited source files, and do not treat semantic similarity as proof.\n"
        + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    )


def run_hook(stdin: Any = None, stdout: Any = None) -> int:
    """Read one Codex hook event and emit only the documented JSON response."""
    source = stdin or sys.stdin
    target = stdout or sys.stdout
    try:
        event = json.loads(source.read(1_000_000))
    except (OSError, json.JSONDecodeError):
        target.write("{}\n")
        return 0
    if not isinstance(event, dict) or event.get("hook_event_name") != "UserPromptSubmit":
        target.write("{}\n")
        return 0
    _capture_trusted_preferences(event)
    context = _context_for(event)
    if context is None:
        target.write("{}\n")
        return 0
    response = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    target.write(json.dumps(response, ensure_ascii=False) + "\n")
    return 0
