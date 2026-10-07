# PolderGraph

PolderGraph is a fully local, zero-cloud code intelligence graph for developers and coding agents.

It combines deterministic source-code relationships with EmbeddingGemma 2 semantic embeddings, stores everything locally in a single SQLite database, exposes a simple MCP/CLI interface for agents, and provides an Obsidian-style interactive graph dashboard.

No Docker, cloud database, remote embedding API, account, API key, or chat LLM is required.

## Quick start

Requirements: Python 3.11 or newer and about 2 GB of free disk space for the
EmbeddingGemma 2 model downloaded on first indexing. The installers below set up
`uv` if needed and install the full feature set from the latest GitHub release.
Git is required to install the release source, which includes the compiled
dashboard assets.

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/PolderLabs/PolderGraph/v0.1.3/scripts/install.sh | sh
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/PolderLabs/PolderGraph/v0.1.3/scripts/install.ps1 | iex
```

Alternatively, install `uv` and Git yourself and run:

```bash
uv tool install --force --upgrade "poldergraph[all] @ git+https://github.com/PolderLabs/PolderGraph.git@v0.1.3"

# Index the current repository
poldergraph init

# Open the interactive graph dashboard
poldergraph ui
```

That's it. PolderGraph discovers your files, parses them with tree-sitter, extracts entities and relationships, generates embeddings, builds the graph, and opens a browser with an interactive visualization.

## What it does

PolderGraph answers repository questions by combining independent evidence channels:

- **Exact lookup**: identifiers, qualified names, paths
- **Lexical search**: BM25-ranked full-text search over names, signatures, docs and paths
- **Semantic search**: EmbeddingGemma 2 vector similarity
- **Structural graph**: calls, imports, inheritance, containment, references

No single channel is authoritative for every task. Hybrid retrieval fuses all channels with inspectable score features so you can see why an item ranked where it did.

## Command surface

```bash
# Index and update
poldergraph init                          # Full index with embedding model download
poldergraph update                        # Incremental update (only changed files)
poldergraph watch                         # Continuous incremental updates

# Search and inspect
poldergraph search "where is authorization enforced?"
poldergraph search "session" --explain-score --kind method
poldergraph explain AuthService
poldergraph path AuthController UserRepository
poldergraph related AuthService
pandergraph impact Session --max-depth 3
poldergraph context "how does login work?" --json --budget 4000

# Dashboard and MCP
poldergraph ui                            # Interactive graph dashboard
poldergraph mcp                           # MCP server for coding agents
poldergraph setup-agent                   # Generate AGENTS.md + MCP config

# Diagnostics
poldergraph status                        # Index health, model, language support
poldergraph doctor                        # Integrity checks
poldergraph rebuild                       # Atomic safe rebuild
poldergraph config show --effective       # Merged configuration
```

Every command supports `--json` with a stable, versioned envelope. Exit codes are documented for agent scripting.

## Architecture

```
Repository
    │
    ├── Discovery (gitignore, .ignore, .poldergraphignore, symlink safety)
    │
    ├── Parsing (tree-sitter, 13 strong adapters, cross-file resolver)
    │
    ├── Embedding (EmbeddingGemma 2, Ollama, lazy multimodal encoders)
    │
    ├── Indexing (incremental, content/semantic hashing, watch mode)
    │
    └── Graph (Leiden communities, metrics, semantic edge policy)
            │
            ├── SQLite + FTS5 + sqlite-vec (single .poldergraph/index.sqlite3)
            │
            ├── Hybrid retrieval (fusion, rerank, context packing)
            │
            └── CLI · MCP · FastAPI API · React/Sigma.js Dashboard
```

## Supported languages

**Strong adapters** (full semantic extraction: imports, calls, inheritance, type references):

Python · TypeScript · TSX · JavaScript · JSX · Rust · Go · Java · C · C++ · C# · Kotlin · Swift

**Baseline indexing** (file + definition symbols from tree-sitter grammars):

Ruby · PHP · Scala · Perl · Lua · Haskell · Elixir · Erlang · OCaml · Zig · Dart · Groovy · Objective-C · R · Julia · Shell · SQL · Vue · Svelte

**Documentation**: Markdown (heading-ancestry sections) · PDF (per-page text extraction)

**Media**: Images (dimensions) · Audio (segmented, ffprobe) · Video (temporal sampling)

## Agent integration

After `poldergraph init`, coding agents discover PolderGraph through generated `AGENTS.md` instructions:

```markdown
<!-- poldergraph:start -->
## PolderGraph repository intelligence

When a task depends on understanding repository structure, finding implementations,
tracing dependencies, locating tests, or estimating change impact:

1. Prefer the PolderGraph MCP tools when available.
2. Otherwise run: `poldergraph context "<your task or question>" --json`
3. If the result says the index is stale, run: `poldergraph update --quiet`
4. Use `poldergraph path "<A>" "<B>" --json` for relationship/path questions.
5. Use `poldergraph explain "<symbol>" --json` for a focused symbol.
6. Use `poldergraph impact "<symbol-or-path>" --json` before broad refactors.
<!-- poldergraph:end -->
```

### MCP tools

| Tool | Description |
|------|-------------|
| `pg_status` | Index existence, freshness, model, counts |
| `pg_search` | Hybrid search with score decomposition |
| `pg_context` | Agent-optimized context pack under a token budget |
| `pg_entity` | Entity details and bounded neighborhood |
| `pg_path` | Relationship path between two entities |
| `pg_related` | Semantic neighbours with structural linkage |
| `pg_impact` | Reverse dependency / change impact analysis |
| `pg_update` | Incremental index refresh |
| `pg_find_tests` | Structurally or lexically linked tests |

## Dashboard

The interactive graph dashboard uses Sigma.js (WebGL), Graphology, and ForceAtlas2 in a web worker. Run `poldergraph ui` to open it at `http://127.0.0.1:7432`.

Features:
- Global graph with community aggregation
- Local graph (N-hop neighborhood with depth/direction controls)
- Search with evidence badges (exact, lexical, semantic, graph-expanded)
- Path visualization
- Inspector with structural + semantic relations
- Filters: kind, language, community, edge type, provenance, semantic similarity
- Community collapse with structural/hybrid labeling
- Node pinning, dragging, back/forward selection history
- Live updates via SSE when `poldergraph watch` is active
- Dark mode, persisted view preferences

## Configuration

```toml
# .poldergraph/config.toml
version = 1

[index]
dimensions = 256
include_media = true

[embedding]
backend = "native"          # native, ollama, or none
model = "google/embeddinggemma-2"
device = "auto"             # auto, cpu, cuda, mps

[semantic_edges]
enabled = true
top_k = 12
mutual_preferred = true
max_degree = 8

[graph]
community_algorithm = "leiden"

[retrieval]
default_context_tokens = 6000

[ui]
host = "127.0.0.1"
port = 7432

[privacy]
allow_model_downloads = true
allow_remote_embedding = false
telemetry = false
```

Override with environment variables: `POLDERGRAPH_EMBEDDING__DEVICE=cuda`

## Design principles

**Structural truth and semantic evidence are different.** A parsed call edge is a fact. A cosine similarity is evidence. They never share a type, and a semantic edge is never promoted to a structural one.

**Index entities, not arbitrary chunks.** The primary retrieval unit is a semantic entity: function, class, module, section, etc.

**Local-first means local-first.** All indexed content, embeddings, metadata and search history stay on the user's machine. No telemetry, no remote inference by default.

**Agent-first, not agent-only.** Human UX and agent UX use the same graph/index. The dashboard is for exploration; MCP and CLI are for machine interaction.

**One index, many consumers.** CLI, dashboard, MCP, and IDE integrations all query the same `.poldergraph/` index.

## Documentation

- [docs/architecture.md](docs/architecture.md) — processes, components, boundaries
- [docs/data-model.md](docs/data-model.md) — canonical entities, edges, persistence
- [docs/indexing.md](docs/indexing.md) — discovery, parsing, embeddings, incremental updates
- [docs/retrieval.md](docs/retrieval.md) — semantic/lexical/graph retrieval, ranking, context packing
- [docs/dashboard.md](docs/dashboard.md) — interactive graph explorer
- [docs/agents.md](docs/agents.md) — MCP, CLI, AGENTS.md generation
- [docs/cli-reference.md](docs/cli-reference.md) — CLI command reference
- [docs/mcp-reference.md](docs/mcp-reference.md) — MCP tool reference
- [docs/configuration.md](docs/configuration.md) — configuration reference
- [docs/dashboard-controls.md](docs/dashboard-controls.md) — dashboard UI controls
- [docs/privacy-security.md](docs/privacy-security.md) — privacy and security model
- [docs/troubleshooting.md](docs/troubleshooting.md) — common issues and fixes
- [docs/benchmark-methodology.md](docs/benchmark-methodology.md) — benchmark methodology and results
- [docs/implementation-checklist.md](docs/implementation-checklist.md) — acceptance criteria

## Requirements

- Python 3.11+
- tree-sitter-language-pack (bundled in the `semantic` extra)
- sqlite-vec (bundled in the `vectors` extra)
- ~2GB disk for the EmbeddingGemma 2 model on first use

## License

Apache-2.0
