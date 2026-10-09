"""Agent instruction generation.

The generated AGENTS.md block is idempotent: re-running replaces only the
fenced PolderGraph section and leaves all user content untouched.
"""

from __future__ import annotations

import json
import shlex
import shutil
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config.models import Config

START_MARKER = "<!-- poldergraph:start -->"
END_MARKER = "<!-- poldergraph:end -->"

#: The canonical block. Agent-specific adapters point back to this contract
#: rather than duplicating pages of instructions.
AGENTS_BLOCK = """<!-- poldergraph:start -->
## PolderGraph repository intelligence

This repository uses PolderGraph for local structural and semantic code intelligence.

When a task depends on understanding repository structure, finding implementations,
tracing dependencies, locating tests, or estimating change impact:

1. Prefer the PolderGraph MCP tools when available.
2. Start with `pg_status` and `pg_context`; context includes relevant shared user
   preferences and this project's saved knowledge. Without MCP, run:
   `poldergraph context "<your task or question>" --json`
3. If the result says the code index is stale, run:
   `poldergraph update --quiet`
   then query again.
4. Use `pg_memory_search` to recall preferences or prior decisions directly.
   When the user states a lasting preference or you establish durable project
   knowledge, save it with `pg_memory_add` using `user` or `project` scope.
   Do this without interrupting the user; do not store secrets or transient task data.
5. Use `poldergraph path "<A>" "<B>" --json` for relationship/path questions.
6. Use `poldergraph explain "<symbol>" --json` for a focused symbol.
7. Use `poldergraph impact "<symbol-or-path>" --json` before broad refactors.
8. Read/edit the actual source files returned by PolderGraph; do not treat semantic
   similarity as proof of a source-code dependency.
9. After substantial source changes, run `poldergraph update --quiet`.

Do not read `.poldergraph/index.sqlite3` directly.
<!-- poldergraph:end -->"""

#: Minimal guidance for a specific agent; it defers to the canonical contract.
ADAPTER_BLOCK = """<!-- poldergraph:start -->
## PolderGraph repository intelligence

This repository is indexed by PolderGraph. Before reading files broadly, use
`pg_context` or run `poldergraph context "<task>" --json`; relevant saved
project knowledge and user preferences are included automatically. Save lasting
user preferences with `pg_memory_add(scope="user", kind="preference")` and
durable project decisions with `pg_memory_add(scope="project", kind="decision")`.
Do not store credentials or transient task details. Run `poldergraph update --quiet`
after substantial edits.
Do not read `.poldergraph/index.sqlite3` directly.
<!-- poldergraph:end -->"""

CODEX_SKILL_BLOCK = """<!-- poldergraph:start -->
## Use PolderGraph for repository intelligence

When the Codex `UserPromptSubmit` lifecycle hook is installed, a small local
context pack is added automatically for relevant user tasks. Avoid repeating
the same broad context request; use focused graph tools for follow-up questions.

Before broad source exploration, use the `poldergraph` MCP tools when available, starting
with `pg_status` and `pg_context` for the current task. Context automatically includes
relevant shared user preferences and memories scoped to this project. If MCP is
unavailable, run `poldergraph context "<task>" --json`. Refresh a stale index with
`pg_update` or `poldergraph update --quiet` and query again.

`pg_context` retrieves matching memories and is read-only. Do not use it to infer or save
user preferences; only use an explicit memory action when the user directly asks. When a task
establishes a durable project decision, save it with `pg_memory_add(scope="project")`;
search prior notes with `pg_memory_search` before making decisions. When a user corrects a
previous preference, update or forget the older note instead of keeping conflicting versions.
Never store credentials, private keys, or one-off task details.

Use `pg_path`, `pg_entity`, `pg_impact`, and `pg_find_tests` for focused graph
questions. Read the cited source files before drawing conclusions; semantic
similarity is a retrieval hint, not proof of a dependency. After edits, call
`pg_update` when MCP is enabled; otherwise run `poldergraph update --quiet`.
<!-- poldergraph:end -->"""

CODEX_SKILL_FRONTMATTER = """---
name: poldergraph
description: Use PolderGraph's local structural and semantic code graph to find implementations, trace relationships, locate tests, and estimate change impact in this repository.
---"""

CODEX_MCP_START = "# poldergraph:start"
CODEX_MCP_END = "# poldergraph:end"


@dataclass
class AgentAdapter:
    """An agent-specific instruction file and how to update it."""

    name: str
    relative_path: str
    block: str = ADAPTER_BLOCK

    def path(self, root: Path) -> Path:
        return root / self.relative_path


#: Detected agent integrations. Each contains minimal guidance pointing back to
#: the canonical CLI/MCP contract.
AGENT_ADAPTERS: tuple[AgentAdapter, ...] = (
    AgentAdapter("claude", "CLAUDE.md"),
    AgentAdapter("cursor", ".cursor/rules/poldergraph.mdc"),
    AgentAdapter("copilot", ".github/copilot-instructions.md"),
    AgentAdapter("codex", ".agents/skills/poldergraph/SKILL.md", CODEX_SKILL_BLOCK),
    AgentAdapter("gemini", "GEMINI.md"),
    AgentAdapter("opencode", "AGENTS.md"),
    AgentAdapter("omp", ".omp/skills/poldergraph/SKILL.md"),
)


def update_block(existing: str, block: str) -> tuple[str, bool]:
    """Replace the fenced PolderGraph block, preserving all other content.

    Returns (new_content, changed).
    """
    if START_MARKER in existing and END_MARKER in existing:
        start = existing.index(START_MARKER)
        end = existing.index(END_MARKER) + len(END_MARKER)
        updated = existing[:start] + block + existing[end:]
        return updated, updated != existing

    separator = (
        ""
        if not existing or existing.endswith("\n\n")
        else ("\n" if existing.endswith("\n") else "\n\n")
    )
    return f"{existing}{separator}{block}\n", True


def write_instructions(path: Path, block: str) -> bool:
    """Write or update an instruction file idempotently."""
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    updated, changed = update_block(existing, block)
    should_write = changed or not path.exists()
    if should_write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated, encoding="utf-8")
    return should_write


def write_codex_skill(path: Path) -> bool:
    """Write a valid Codex skill while preserving existing user instructions."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{CODEX_SKILL_FRONTMATTER}\n\n{CODEX_SKILL_BLOCK}\n", encoding="utf-8")
        return True

    existing = path.read_text(encoding="utf-8")
    if START_MARKER in existing and END_MARKER in existing:
        updated, changed = update_block(existing, CODEX_SKILL_BLOCK)
    elif existing.startswith("---\n"):
        marker = existing.find("\n---", 4)
        if marker == -1:
            return False
        insert_at = marker + len("\n---")
        updated = f"{existing[:insert_at]}\n\n{CODEX_SKILL_BLOCK}{existing[insert_at:]}"
        changed = updated != existing
    else:
        updated = f"{CODEX_SKILL_FRONTMATTER}\n\n{existing.rstrip()}\n\n{CODEX_SKILL_BLOCK}\n"
        changed = updated != existing
    if changed:
        path.write_text(updated, encoding="utf-8")
    return changed


def write_codex_mcp_config(root: Path) -> tuple[bool, str]:
    """Add the repository-scoped MCP server without replacing other Codex config."""
    path = root / ".codex" / "config.toml"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    try:
        config = tomllib.loads(existing) if existing.strip() else {}
    except tomllib.TOMLDecodeError as exc:
        return False, f"{path.relative_to(root)} is invalid TOML ({exc}); MCP entry was not changed"

    executable = shutil.which("poldergraph") or "poldergraph"
    block = (
        f"{CODEX_MCP_START}\n[mcp_servers.poldergraph]\n"
        f"command = {json.dumps(executable)}\n"
        f"args = {json.dumps(['mcp'])}\n{CODEX_MCP_END}"
    )
    if CODEX_MCP_START in existing and CODEX_MCP_END in existing:
        start = existing.index(CODEX_MCP_START)
        end = existing.index(CODEX_MCP_END, start) + len(CODEX_MCP_END)
        updated = existing[:start] + block + existing[end:]
        if updated == existing:
            return False, f"{path.relative_to(root)} already configures the poldergraph MCP server"
    else:
        servers = config.get("mcp_servers", {})
        if isinstance(servers, dict) and "poldergraph" in servers:
            return False, f"{path.relative_to(root)} already configures the poldergraph MCP server"
        separator = (
            ""
            if not existing or existing.endswith("\n\n")
            else ("\n" if existing.endswith("\n") else "\n\n")
        )
        updated = f"{existing}{separator}{block}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")
    return True, str(path.relative_to(root))


def write_codex_hooks_config(root: Path) -> tuple[bool, str]:
    """Install an idempotent Codex UserPromptSubmit context hook."""
    path = root / ".codex" / "hooks.json"
    try:
        config = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"{path.relative_to(root)} is invalid JSON ({exc}); hook was not changed"
    if not isinstance(config, dict):
        return False, f"{path.relative_to(root)} must contain a JSON object; hook was not changed"
    hooks = config.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        return False, f"{path.relative_to(root)} has an invalid hooks object; hook was not changed"
    groups = hooks.setdefault("UserPromptSubmit", [])
    if not isinstance(groups, list):
        return False, f"{path.relative_to(root)} has invalid UserPromptSubmit hooks; hook was not changed"
    if any(
        isinstance(group, dict)
        and any(
            isinstance(item, dict)
            and isinstance(item.get("command"), str)
            and "codex-hook" in item["command"]
            and "poldergraph" in item["command"].lower()
            for item in group.get("hooks", [])
        )
        for group in groups
    ):
        return False, f"{path.relative_to(root)} already installs PolderGraph context"

    executable = shutil.which("poldergraph")
    command_args = (
        [executable, "codex-hook"]
        if executable
        else [sys.executable, "-c", "from poldergraph.cli import main; main()", "codex-hook"]
    )
    command = shlex.join(command_args) if sys.platform != "win32" else subprocess_list2cmdline(command_args)
    handler: dict[str, Any] = {"type": "command", "command": command, "timeout": 300}
    if sys.platform == "win32":
        handler["commandWindows"] = command
    groups.append({"hooks": [handler]})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return True, str(path.relative_to(root))


def subprocess_list2cmdline(args: list[str]) -> str:
    """Quote a command for Codex's Windows command runner."""
    import subprocess

    return subprocess.list2cmdline(args)


def detect_agents(root: Path) -> list[AgentAdapter]:
    """Detect agent integrations already present in the workspace."""
    found: list[AgentAdapter] = []
    for adapter in AGENT_ADAPTERS:
        if adapter.path(root).exists():
            found.append(adapter)
    return found


def detect_installed_agents(root: Path) -> list[str]:
    """Detect coding agents available to this user or configured in the project."""
    home = Path.home()
    signals: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
        "claude": (("claude",), (".claude", "CLAUDE.md")),
        "cursor": (("cursor",), (".cursor",)),
        "copilot": (("copilot",), (".github/copilot-instructions.md",)),
        "codex": (("codex",), (".codex", ".agents/skills")),
        "gemini": (("gemini",), (".gemini",)),
        "opencode": (("opencode",), (".opencode", "opencode.json")),
        "omp": (("omp",), (".omp",)),
    }
    user_paths: dict[str, tuple[str, ...]] = {
        "claude": (".claude",),
        "cursor": (".cursor",),
        "copilot": (".config/github-copilot", ".copilot"),
        "codex": (".codex", ".agents/skills"),
        "gemini": (".gemini",),
        "opencode": (".opencode", ".config/opencode"),
        "omp": (".omp",),
    }
    detected: list[str] = []
    for adapter in AGENT_ADAPTERS:
        commands, project_markers = signals[adapter.name]
        if (
            any(shutil.which(command) for command in commands)
            or any((root / marker).exists() for marker in project_markers)
            or any((home / marker).exists() for marker in user_paths[adapter.name])
        ):
            detected.append(adapter.name)
    return detected


def mcp_config_snippet(root: Path) -> str:
    """Generate MCP server configuration for the current executable.

    Never contains secrets; the command points at the running executable and
    the current workspace root.
    """
    executable = shutil.which("poldergraph") or "poldergraph"
    config = {
        "mcpServers": {
            "poldergraph": {
                "command": executable,
                "args": ["mcp", str(root)],
            }
        }
    }
    return json.dumps(config, indent=2)


def setup_agent_guidance(
    root: Path,
    config: Config,
    *,
    all_agents: bool = False,
    targets: list[str] | None = None,
    hooks: bool = False,
) -> dict[str, Any]:
    """Write the canonical AGENTS.md block plus detected adapter instructions."""
    written: list[str] = []
    skipped: list[str] = []

    agents_md = root / "AGENTS.md"
    if write_instructions(agents_md, AGENTS_BLOCK):
        written.append("AGENTS.md")
    else:
        skipped.append("AGENTS.md (already current)")

    selected: list[AgentAdapter]
    if targets is not None:
        selected = [
            a for a in AGENT_ADAPTERS if a.name in targets and a.relative_path != "AGENTS.md"
        ]
    elif all_agents:
        selected = [a for a in AGENT_ADAPTERS if a.relative_path != "AGENTS.md"]
    else:
        selected = [a for a in detect_agents(root) if a.relative_path != "AGENTS.md"]

    for adapter in selected:
        path = adapter.path(root)
        if path == agents_md:
            continue
        changed = (
            write_codex_skill(path)
            if adapter.name == "codex"
            else write_instructions(path, adapter.block)
        )
        if changed:
            written.append(adapter.relative_path)
        else:
            skipped.append(f"{adapter.relative_path} (already current)")

    if any(adapter.name == "codex" for adapter in selected):
        changed, result = write_codex_mcp_config(root)
        if changed:
            written.append(result)
        else:
            skipped.append(result)

    hooks_installed = False
    if hooks:
        if any(adapter.name == "codex" for adapter in selected):
            changed, result = write_codex_hooks_config(root)
            hooks_installed = changed or "already installs PolderGraph" in result
            if changed:
                written.append(result)
            else:
                skipped.append(result)
        else:
            skipped.append("Codex lifecycle hook not installed (select the codex adapter)")

    return {
        "root": str(root),
        "written": written,
        "skipped": skipped,
        "mcp_config": mcp_config_snippet(root),
        "hooks_installed": hooks_installed,
        "hooks_requested": hooks,
    }


def remove_agent_guidance(root: Path, *, targets: list[str] | None = None) -> dict[str, Any]:
    """Remove only PolderGraph-managed project guidance and Codex entries.

    Unrelated text, MCP servers, hook handlers, and user-level configuration are
    left untouched. Invalid Codex hook JSON is reported without being rewritten.
    """
    selected = [adapter for adapter in AGENT_ADAPTERS if targets is None or adapter.name in targets]
    removed: list[str] = []
    skipped: list[str] = []

    for adapter in selected:
        path = adapter.path(root)
        if not path.exists():
            continue
        existing = path.read_text(encoding="utf-8")
        if START_MARKER not in existing or END_MARKER not in existing:
            skipped.append(f"{adapter.relative_path} (no managed PolderGraph block)")
            continue
        start = existing.index(START_MARKER)
        end = existing.index(END_MARKER, start) + len(END_MARKER)
        before = existing[:start].rstrip()
        after = existing[end:].lstrip()
        updated = "\n\n".join(part for part in (before, after) if part)
        if adapter.name == "codex" and updated.strip() == CODEX_SKILL_FRONTMATTER:
            path.unlink()
        elif updated.strip():
            path.write_text(updated + "\n", encoding="utf-8")
        else:
            path.unlink()
        removed.append(adapter.relative_path)

    codex_selected = targets is None or "codex" in targets
    if codex_selected:
        mcp_path = root / ".codex" / "config.toml"
        if mcp_path.exists():
            content = mcp_path.read_text(encoding="utf-8")
            if CODEX_MCP_START in content and CODEX_MCP_END in content:
                start = content.index(CODEX_MCP_START)
                end = content.index(CODEX_MCP_END, start) + len(CODEX_MCP_END)
                updated = (content[:start].rstrip() + "\n\n" + content[end:].lstrip()).strip()
                mcp_path.write_text(updated + ("\n" if updated else ""), encoding="utf-8")
                removed.append(".codex/config.toml (managed MCP entry)")

        hooks_path = root / ".codex" / "hooks.json"
        if hooks_path.exists():
            try:
                config = json.loads(hooks_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                skipped.append(".codex/hooks.json (invalid JSON; left untouched)")
            else:
                hooks = config.get("hooks") if isinstance(config, dict) else None
                groups = hooks.get("UserPromptSubmit") if isinstance(hooks, dict) else None
                if isinstance(groups, list):
                    def is_managed(group: Any) -> bool:
                        handlers = group.get("hooks", []) if isinstance(group, dict) else []
                        return any(
                            isinstance(handler, dict)
                            and any(
                                isinstance(handler.get(key), str)
                                and "poldergraph" in handler[key].lower()
                                and "codex-hook" in handler[key].lower()
                                for key in ("command", "commandWindows")
                            )
                            for handler in handlers
                        )

                    kept = [group for group in groups if not is_managed(group)]
                    if len(kept) != len(groups):
                        if kept:
                            hooks["UserPromptSubmit"] = kept
                        else:
                            hooks.pop("UserPromptSubmit", None)
                        if not hooks:
                            config.pop("hooks", None)
                        hooks_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
                        removed.append(".codex/hooks.json (managed UserPromptSubmit hook)")

    return {"root": str(root), "removed": removed, "skipped": skipped}


def main() -> int:  # pragma: no cover - console helper
    """Print the generated MCP configuration for the current directory."""
    sys.stdout.write(mcp_config_snippet(Path.cwd().resolve()) + "\n")
    return 0
