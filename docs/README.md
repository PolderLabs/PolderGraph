# PolderGraph implementation specification

This directory is the source of truth for implementing PolderGraph.

PolderGraph is not a generic chatbot and not a vector database wrapper. It is a local code-intelligence system that combines:

1. deterministic structural knowledge extracted from source code,
2. EmbeddingGemma 2 semantic representations,
3. local graph algorithms,
4. hybrid retrieval,
5. an interactive Obsidian-style graph dashboard,
6. agent access through MCP and a stable CLI.

The full feature set is the implementation target from the start. There is intentionally no staged MVP/phase plan in this specification.

## Product contract

A user should be able to install PolderGraph, enter a repository, run one command, and get a persistent local semantic/structural map:

```bash
uv tool install poldergraph
cd my-project
poldergraph init
```

After initial indexing:

```bash
poldergraph ui
poldergraph search "where is authorization checked?"
poldergraph context "how does session refresh work?" --json
poldergraph mcp
```

No Docker, hosted vector database, API key, cloud account, or chat LLM is required.

## Design principles

### Structural truth and semantic evidence are different

A parsed call edge is a fact extracted from source code. A high cosine similarity is evidence of conceptual relatedness. They must remain separate in storage and UI.

Every relationship has provenance and confidence. Semantic edges never claim that one symbol calls/imports/inherits another.

### Index entities, not arbitrary chunks

The primary retrieval unit is a semantic entity: function, method, class, module, type, section, file, image, audio segment, video segment, etc. Chunking is used only where an entity is too large or naturally segmented.

### Local-first means local-first

All indexed source content, embeddings, metadata, graph data, and search history are stored locally. PolderGraph performs no telemetry and no remote inference by default.

### Agent-first, not agent-only

Human UX and agent UX use the same graph/index. The dashboard is for exploration; MCP and CLI are for machine interaction. Their semantics must match.

### One index, many consumers

The persistent index under `.poldergraph/` is canonical. CLI, dashboard, MCP, IDE/editor integrations, and external coding agents must query the same index.

## Specification map

- [architecture.md](architecture.md) — processes, components, boundaries and repository layout
- [data-model.md](data-model.md) — canonical entities, edges, persistence and migrations
- [indexing.md](indexing.md) — discovery, parsing, embeddings, multimodal processing and incremental updates
- [retrieval.md](retrieval.md) — semantic/lexical/graph retrieval, ranking, context packing and graph algorithms
- [dashboard.md](dashboard.md) — interactive Obsidian-style graph explorer
- [agents.md](agents.md) — MCP, CLI, AGENTS.md generation and agent interaction contract
- [memory.md](memory.md) — centralized per-user and per-project agent memory, vector RAG and privacy
- [decisions.md](decisions.md) — provider-neutral typed decisions using Jev, OpenAI Decisions, or local Laya
- [cli-config.md](cli-config.md) — command surface, configuration and installation UX
- [testing-performance.md](testing-performance.md) — correctness, scale, benchmark and security requirements
- [implementation-checklist.md](implementation-checklist.md) — complete one-shot implementation acceptance checklist
- [research.md](research.md) — researched technologies, rationale and source links

## Non-goals

PolderGraph does not initially own code generation, autonomous editing, chat-model inference, cloud syncing, team accounts, or hosted authentication. It supplies grounded repository intelligence to tools that already perform those tasks.

An optional LLM may consume PolderGraph context, but PolderGraph itself must remain useful with no generative model installed.
