"""Agent instruction generation.

The generated AGENTS.md block is idempotent: re-running replaces only the
fenced PolderGraph section and leaves all user content untouched.
"""

from __future__ import annotations

import json
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
2. Otherwise run:
   `poldergraph context "<your task or question>" --json`
3. If the result says the index is stale, run:
   `poldergraph update --quiet`
   then query again.
4. Use `poldergraph path "<A>" "<B>" --json` for relationship/path questions.
5. Use `poldergraph explain "<symbol>" --json` for a focused symbol.
6. Use `poldergraph impact "<symbol-or-path>" --json` before broad refactors.
7. Read/edit the actual source files returned by PolderGraph; do not treat semantic
   similarity as proof of a source-code dependency.
8. After substantial source changes, run `poldergraph update --quiet`.

Do not read `.poldergraph/index.sqlite3` directly.
<!-- poldergraph:end -->"""

#: Minimal guidance for a specific agent; it defers to the canonical contract.
ADAPTER_BLOCK = """<!-- poldergraph:start -->
## PolderGraph repository intelligence

This repository is indexed by PolderGraph. Before reading files broadly, run
`poldergraph context "<task>" --json` (or use the PolderGraph MCP tools) to
locate the exact implementations, then read only the source locations returned.
Run `poldergraph update --quiet` after substantial edits.
Do not read `.poldergraph/index.sqlite3` directly.
<!-- poldergraph:end -->"""

CODEX_SKILL_BLOCK = """<!-- poldergraph:start -->
## Use PolderGraph for repository intelligence

Before broad source exploration, use the `poldergraph` MCP tools when available, starting
with `pg_status` and `pg_context` for the current task. If MCP is unavailable,
run `poldergraph context "<task>" --json`. Refresh a stale index with
`pg_update` or `poldergraph update --quiet` and query again.

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

    separator = "" if not existing or existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
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
        f"args = {json.dumps(['mcp', str(root)])}\n{CODEX_MCP_END}"
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
        separator = "" if not existing or existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
        updated = f"{existing}{separator}{block}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")
    return True, str(path.relative_to(root))


def detect_agents(root: Path) -> list[AgentAdapter]:
    """Detect agent integrations already present in the workspace."""
    found: list[AgentAdapter] = []
    for adapter in AGENT_ADAPTERS:
        if adapter.path(root).exists():
            found.append(adapter)
    return found


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
    if targets:
        selected = [a for a in AGENT_ADAPTERS if a.name in targets and a.relative_path != "AGENTS.md"]
    elif all_agents:
        selected = [a for a in AGENT_ADAPTERS if a.relative_path != "AGENTS.md"]
    else:
        selected = [a for a in detect_agents(root) if a.relative_path != "AGENTS.md"]

    for adapter in selected:
        path = adapter.path(root)
        if path == agents_md:
            continue
        changed = write_codex_skill(path) if adapter.name == "codex" else write_instructions(path, adapter.block)
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

    return {
        "root": str(root),
        "written": written,
        "skipped": skipped,
        "mcp_config": mcp_config_snippet(root),
        "hooks_installed": False,
        "hooks_requested": hooks,
    }


def main() -> int:  # pragma: no cover - console helper
    """Print the generated MCP configuration for the current directory."""
    sys.stdout.write(mcp_config_snippet(Path.cwd().resolve()) + "\n")
    return 0
