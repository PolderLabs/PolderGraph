# PolderGraph

PolderGraph is a fully local, zero-cloud code intelligence graph for developers and coding agents.

It combines deterministic source-code relationships with EmbeddingGemma 2 semantic embeddings, stores everything locally, exposes a simple MCP/CLI interface for agents, and provides an Obsidian-style interactive graph dashboard.

> This repository currently contains the complete implementation specification. See [docs/README.md](docs/README.md).

## Core goals

- Fully local by default: source, embeddings, graph, and search stay on the user's machine.
- One-command setup and indexing.
- Deterministic AST relationships plus semantic retrieval; semantic similarity never pretends to be a source-code dependency.
- A fast interactive graph UI inspired by Obsidian's graph view.
- Agent-first integration through MCP, CLI, generated `AGENTS.md` instructions, and optional editor hooks.
- No external database daemon, Docker requirement, cloud account, API key, or LLM required.
- Full feature set from the initial implementation target; this specification intentionally does not define a phased/MVP roadmap.

## Intended command surface

```bash
# Install
uv tool install poldergraph

# Index the current repository and install local agent guidance
poldergraph init

# Open the interactive graph dashboard
poldergraph ui

# Search and inspect
poldergraph search "where is authorization enforced?"
poldergraph explain AuthService
poldergraph path AuthController UserRepository
poldergraph related AuthService
poldergraph context "how does login work?" --json

# Keep the index current
poldergraph update
poldergraph watch

# Agent integration
poldergraph setup-agent
poldergraph mcp
```

The exact behavior, data model, UI, agent protocol, configuration, algorithms, performance requirements, and acceptance criteria are defined under `docs/`.
