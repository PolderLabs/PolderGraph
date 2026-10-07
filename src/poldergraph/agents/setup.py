"""Agent instruction generation.

The generated AGENTS.md block is idempotent: re-running replaces only the
fenced PolderGraph section and leaves all user content untouched.
"""

from __future__ import annotations

import json
import shutil
import sys
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
    AgentAdapter("codex", "AGENTS.md"),
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
    if changed or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated, encoding="utf-8")
        return True
    return False


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
        if write_instructions(path, ADAPTER_BLOCK):
            written.append(adapter.relative_path)
        else:
            skipped.append(f"{adapter.relative_path} (already current)")

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