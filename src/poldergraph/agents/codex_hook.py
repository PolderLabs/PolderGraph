"""Codex UserPromptSubmit hook: return local PolderGraph context as hook JSON."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
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


def _context_cursor_path(event: dict[str, Any], root: Path) -> Path | None:
    """Return a private per-session cursor path without using session data as a path."""
    session_id = event.get("session_id")
    if not isinstance(session_id, str) or not session_id or len(session_id) > 512:
        return None
    from ..memory import default_memory_path

    key = hashlib.sha256(f"{session_id}\0{root.resolve()}".encode()).hexdigest()
    directory = default_memory_path().parent / "context-cursors"
    try:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        directory.chmod(0o700)
        candidates = list(directory.glob("*.json"))
        now = time.time()
        metadata = []
        for candidate in candidates:
            try:
                modified = candidate.stat().st_mtime
                if now - modified > 7 * 24 * 60 * 60:
                    candidate.unlink(missing_ok=True)
                else:
                    metadata.append((modified, candidate))
            except OSError:
                continue
        for _modified, old_path in sorted(metadata)[:-128]:
            with contextlib.suppress(OSError):
                old_path.unlink(missing_ok=True)
    except OSError:
        return None
    return directory / f"{key}.json"


def _read_context_cursor(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        if time.time() - path.stat().st_mtime > 7 * 24 * 60 * 60:
            path.unlink(missing_ok=True)
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    cursor = value.get("cursor") if isinstance(value, dict) else None
    return cursor if isinstance(cursor, str) and len(cursor) <= 16_384 else None


def _write_context_cursor(path: Path | None, cursor: str) -> None:
    if path is None or len(cursor) > 16_384:
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as output:
            temporary = Path(output.name)
            json.dump({"cursor": cursor, "updated_at": int(time.time())}, output)
        with contextlib.suppress(OSError):
            temporary.chmod(0o600)
        os.replace(temporary, path)
    except OSError:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


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
    if not ready or not ready.get("ok") or ready.get("state") == "unavailable":
        return None

    cursor_path = _context_cursor_path(event, root)
    previous_cursor = _read_context_cursor(cursor_path)
    context_args = [
        "context",
        prompt,
        "--root",
        str(root),
        "--budget",
        str(CONTEXT_BUDGET),
        "--offline",
        "--json",
    ]
    if previous_cursor:
        context_args.extend(["--new-evidence-since", previous_cursor])
    result = _run(root, context_args, timeout=60)
    if not result or not result.get("ok"):
        return None
    data = result.get("data")
    if not isinstance(data, dict) or (data.get("plan") or {}).get("skipped"):
        return None
    cursor = data.get("evidence_cursor")
    if isinstance(cursor, str):
        _write_context_cursor(cursor_path, cursor)
    freshness = data.get("index") or result.get("index") or {}
    if previous_cursor and data.get("new_evidence_count") == 0 and freshness.get("fresh") is True:
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
