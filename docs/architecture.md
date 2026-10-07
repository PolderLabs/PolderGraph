# Architecture

## System overview

```text
                        repository/workspace
                               |
            +------------------+------------------+
            |                                     |
      deterministic pass                       semantic pass
            |                                     |
    tree-sitter parsing                     EmbeddingGemma 2
    language resolvers                  text/code/image/audio/video
            |                                     |
  symbols + structural edges                    vectors
            |                                     |
            +------------------+------------------+
                               |
                       canonical entity layer
                               |
               +---------------+---------------+
               |                               |
          SQLite graph                    vector index
          + FTS metadata                  sqlite-vec
               |                               |
               +---------------+---------------+
                               |
                        hybrid retrieval
                               |
        +----------------------+-----------------------+
        |                      |                       |
       CLI                   MCP server             HTTP API
                                                        |
                                                  React dashboard
                                                  Sigma.js/Graphology
```

## Runtime topology

The default runtime is a single local Python process plus a browser tab.

- Core/indexer: Python 3.11+
- Packaging/environment: uv
- CLI: Typer
- Config/models: Pydantic
- Source parsing: tree-sitter via tree-sitter-language-pack where practical
- Embeddings: sentence-transformers/Transformers using `google/embeddinggemma-2`
- Optional embedding backend: Ollama
- Persistent metadata/graph: SQLite
- Vector extension: sqlite-vec behind a backend interface
- Full-text lexical retrieval: SQLite FTS5
- In-memory graph algorithms: NetworkX for normal operations; igraph/leidenalg for large community detection workloads
- Local API: FastAPI
- Dashboard: React + TypeScript + Vite
- Graph rendering: Sigma.js + Graphology + ForceAtlas2 worker
- File watching: watchfiles
- Agent protocol: official Model Context Protocol Python SDK/FastMCP-compatible implementation

No external daemon is required.

## Repository implementation layout

```text
PolderGraph/
├── pyproject.toml
├── README.md
├── AGENTS.md
├── docs/
├── src/poldergraph/
│   ├── cli.py
│   ├── application.py
│   ├── config/
│   ├── discovery/
│   ├── parsing/
│   │   ├── engine.py
│   │   ├── queries/
│   │   ├── symbols.py
│   │   ├── references.py
│   │   └── languages/
│   ├── embedding/
│   │   ├── protocol.py
│   │   ├── gemma.py
│   │   ├── ollama.py
│   │   ├── batching.py
│   │   └── multimodal.py
│   ├── indexing/
│   │   ├── pipeline.py
│   │   ├── incremental.py
│   │   └── watcher.py
│   ├── storage/
│   │   ├── sqlite.py
│   │   ├── schema.py
│   │   ├── migrations/
│   │   ├── vectors.py
│   │   └── fts.py
│   ├── graph/
│   │   ├── builder.py
│   │   ├── traversal.py
│   │   ├── communities.py
│   │   └── metrics.py
│   ├── retrieval/
│   │   ├── semantic.py
│   │   ├── lexical.py
│   │   ├── structural.py
│   │   ├── hybrid.py
│   │   ├── rerank.py
│   │   └── context.py
│   ├── api/
│   ├── mcp/
│   ├── agents/
│   └── models/
├── web/
│   ├── src/
│   └── dist/
└── tests/
    ├── fixtures/
    ├── unit/
    ├── integration/
    ├── e2e/
    └── benchmarks/
```

The built dashboard assets are packaged with the Python distribution so `poldergraph ui` requires no Node.js installation on an end-user machine.

## Process boundaries

### Indexer

Responsible for file discovery, parsing, entity extraction, dependency/reference resolution, content normalization, embedding generation, semantic neighbor computation and persistence.

It must be restart-safe. Indexing writes use transactions and checkpointed batches so interrupted indexing cannot leave a logically inconsistent graph.

### Query engine

Read-mostly service that loads graph slices from SQLite instead of requiring the entire workspace graph in memory for every query. Expensive graph algorithms may materialize an in-memory subgraph or cached full graph.

### Dashboard API

The HTTP layer is a projection over the query engine, not a second implementation of search logic.

### MCP server

MCP tools invoke the same query service classes as the CLI and dashboard. There must be no separate agent-only retrieval implementation.

## Backend interfaces

Keep replaceable interfaces around parts most likely to evolve:

```python
class EmbeddingBackend(Protocol):
    def capabilities(self) -> set[str]: ...
    def embed_texts(self, items: list[str], *, task: str, dimensions: int) -> Matrix: ...
    def embed_images(self, ...): ...
    def embed_audio(self, ...): ...
    def embed_video(self, ...): ...

class VectorStore(Protocol):
    def upsert(self, records): ...
    def delete(self, ids): ...
    def search(self, vector, *, top_k, filters=None): ...

class Parser(Protocol):
    def parse(self, file): ...
    def extract_entities(self, tree): ...
    def extract_relationships(self, tree): ...
```

The default configuration must work without selecting implementations.

## Local index directory

Each workspace gets:

```text
.poldergraph/
├── index.sqlite3
├── config.toml
├── state.json
├── logs/
├── cache/
│   ├── model/
│   └── media/
└── lock
```

`.poldergraph/` is ignored by generated `.gitignore` guidance and should not be committed.

## Multi-root workspaces

A PolderGraph index may contain multiple repository roots. Each root gets a stable `root_id`. Paths are stored root-relative plus root identity; absolute paths are runtime metadata only.

Cross-repository edges may be created for resolvable local workspace imports/references. This is important for monorepos and adjacent frontend/backend repositories.

## Concurrency

- One writer lock per index.
- Unlimited read processes when SQLite WAL mode allows it.
- `watch` coalesces events and executes incremental transactions.
- Dashboard and MCP may operate while watch mode is running.
- Schema migration obtains an exclusive migration lock.

## Privacy and network policy

The core must expose an explicit network policy:

```toml
[privacy]
allow_model_downloads = true
allow_remote_embedding = false
telemetry = false
```

Only model/package downloads are allowed by default. Indexed content must never leave the machine.

## Failure strategy

Unsupported language: index file metadata/text and mark structural parsing unsupported.

Embedding failure: retain structural index and mark semantic status degraded.

sqlite-vec unavailable: fail clearly for semantic search or fall back to an explicitly implemented brute-force backend for small indexes; do not silently disable semantics.

Corrupt index: preserve the database, report diagnostics, and offer `poldergraph doctor` / `poldergraph rebuild`; never auto-delete user state.
