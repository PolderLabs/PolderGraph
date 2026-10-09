"""Honest capability reporting for supported coding-agent adapters."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .setup import AGENT_ADAPTERS

_CAPABILITIES: dict[str, dict[str, Any]] = {
    "omp": {
        "native_events": ["workspace_open", "task_start", "after_edit"],
        "description": "Native extension injects task context and refreshes after writes.",
    },
    "codex": {
        "native_events": ["task_start"],
        "description": "UserPromptSubmit hook injects bounded task context.",
    },
}


def _codex_hook_configured(root: Path) -> bool:
    for path in (root / ".codex" / "hooks.json", Path.home() / ".codex" / "hooks.json"):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        hooks = value.get("hooks", {})
        for event, groups in hooks.items():
            if event != "UserPromptSubmit" or not isinstance(groups, list):
                continue
            for group in groups:
                handlers = group.get("hooks", []) if isinstance(group, dict) else []
                if any(
                    isinstance(handler, dict)
                    and "codex-hook" in str(handler.get("command", ""))
                    for handler in handlers
                ):
                    return True
    return False


def _omp_extension_configured() -> bool:
    for path in (
        Path.home() / ".omp" / "agent" / "config.yml",
        Path.home() / ".omp" / "config.yml",
    ):
        try:
            content = path.read_text(encoding="utf-8").lower()
        except OSError:
            continue
        if "poldergraph" in content:
            return True
    return False


def _mcp_configured(root: Path) -> bool:
    candidates = (
        root / ".mcp.json",
        root / ".cursor" / "mcp.json",
        root / ".codex" / "config.toml",
    )
    for path in candidates:
        try:
            if "poldergraph" in path.read_text(encoding="utf-8").lower():
                return True
        except OSError:
            continue
    return False


def integration_capabilities(root: Path | None = None) -> dict[str, Any]:
    """Report detection and actual PolderGraph activation per supported client."""
    from .setup import detect_installed_agents

    workspace = (root or Path.cwd()).resolve()
    detected = set(detect_installed_agents(workspace))
    results: list[dict[str, Any]] = []
    for adapter in AGENT_ADAPTERS:
        name = adapter.name
        instruction_present = adapter.path(workspace).is_file()
        installed = name in detected
        if (name == "codex" and _codex_hook_configured(workspace)) or (
            name == "omp" and _omp_extension_configured()
        ):
            mode = "native-hooks"
        elif _mcp_configured(workspace):
            mode = "MCP-only" if installed else "guidance-only"
        elif instruction_present:
            mode = "guidance-only"
        else:
            mode = "unconfigured"
        known = _CAPABILITIES.get(name, {})
        events = known.get("native_events", []) if mode == "native-hooks" else []
        if mode != "native-hooks" and known:
            events = []
        results.append(
            {
                "agent": name,
                "installed": installed,
                "mode": mode,
                "native_events": events,
                "description": known.get(
                    "description",
                    "Agent instructions and optional MCP support; no native lifecycle hook is configured.",
                ),
                "remediation": (
                    None
                    if mode in {"native-hooks", "MCP-only"}
                    else f"Run poldergraph setup-agent --agent {name} to add guidance."
                ),
            }
        )
    return {"workspace": str(workspace), "integrations": results}
