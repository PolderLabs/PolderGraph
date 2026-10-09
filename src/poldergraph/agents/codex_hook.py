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


def _run(root: Path, args: list[str], timeout: float) -> dict[str, Any] | None:
    executable = shutil.which("poldergraph")
    command = (
        [executable, *args]
        if executable
        else [sys.executable, "-c", "from poldergraph.cli import main; main()", *args]
    )
    try:
        result = subprocess.run(
            command, cwd=root,
            capture_output=True, text=True, timeout=timeout, check=False,
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
    root = Path(cwd).resolve()
    if not root.is_dir():
        return None

    status = _run(root, ["status", "--json"], timeout=15)
    if status is None:
        return None
    code = (status.get("error") or {}).get("code")
    if code == "INDEX_MISSING":
        initialized = _run(root, ["init", "--no-embed", "--quiet", "--json"], timeout=300)
        if not initialized or not initialized.get("ok"):
            return None
    elif not status.get("ok"):
        return None
    elif (status.get("index") or {}).get("fresh") is False:
        updated = _run(root, ["update", "--no-embed", "--quiet", "--json"], timeout=180)
        if not updated or not updated.get("ok"):
            return None

    result = _run(
        root,
        ["context", prompt, "--root", str(root), "--budget", str(CONTEXT_BUDGET), "--offline", "--json"],
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
