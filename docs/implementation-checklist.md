# Complete one-shot implementation checklist

This is not a phased roadmap. The initial implementation is considered complete only when the integrated system satisfies this checklist.

## Packaging and project
- [ ] Python package installable with uv/pip
- [ ] bundled production dashboard assets
- [ ] Linux/macOS/Windows support documented
- [ ] versioned config/schema/API formats
- [ ] concise README quick start
- [ ] license selected and added
- [ ] no mandatory Docker/Node/database server at runtime

## Discovery
- [ ] root detection
- [ ] multi-root workspace support
- [ ] gitignore semantics
- [ ] .ignore and .poldergraphignore
- [ ] generated/vendor/minified detection
- [ ] safe symlink policy
- [ ] file type/language detection

## Structural parsing
- [ ] tree-sitter-language-pack integration
- [ ] robust parse error handling
- [ ] common entity model
- [ ] TypeScript/TSX strong adapter
- [ ] JavaScript/JSX strong adapter
- [ ] Python strong adapter
- [ ] Rust strong adapter
- [ ] Go strong adapter
- [ ] Java strong adapter
- [ ] C strong adapter
- [ ] C++ strong adapter
- [ ] C# strong adapter
- [ ] Kotlin strong adapter
- [ ] Swift strong adapter
- [ ] Astro strong adapter (frontmatter re-parsed as TypeScript)
- [ ] baseline indexing for additional supported grammars
- [ ] cross-file resolver
- [ ] aliases/re-exports
- [ ] ambiguous target preservation
- [ ] structural provenance/confidence

## Documentation and media
- [ ] Markdown/text
- [ ] PDF text/page indexing
- [ ] image entities/embeddings
- [ ] audio segmentation/embeddings
- [ ] video segmentation/embeddings
- [ ] parent document/media relationships
- [ ] lazy modality encoder loading

## EmbeddingGemma 2
- [ ] canonical native backend
- [ ] optional Ollama backend
- [ ] documented task prompts/roles
- [ ] 128/256/512/768 support
- [ ] renormalization after dimension truncation
- [ ] model revision persistence
- [ ] representation versioning
- [ ] batching/device auto-selection
- [ ] offline mode
- [ ] cache reuse
- [ ] no remote inference by default

## Persistence
- [ ] SQLite schema
- [ ] WAL/concurrency policy
- [ ] migrations
- [ ] FTS5
- [ ] sqlite-vec backend
- [ ] vector backend abstraction
- [ ] stable canonical IDs
- [ ] integrity/doctor checks
- [ ] safe rebuild/atomic swap

## Incremental indexing
- [ ] content/semantic hashes
- [ ] skip unchanged files
- [ ] targeted reparse
- [ ] targeted re-embedding
- [ ] deletion cleanup
- [ ] rename behavior
- [ ] affected resolution recompute
- [ ] affected semantic-neighbor recompute
- [ ] watch mode
- [ ] dashboard change events

## Graph
- [ ] common edge taxonomy
- [ ] semantic edge separation
- [ ] bounded semantic materialization policy
- [ ] mutual-neighbor preference
- [ ] structural communities
- [ ] hybrid communities
- [ ] Leiden integration
- [ ] degree/centrality metrics
- [ ] cached metrics invalidation

## Retrieval
- [ ] exact symbol/path
- [ ] lexical FTS
- [ ] semantic vector
- [ ] bounded structural expansion
- [ ] hybrid candidate fusion
- [ ] inspectable score features
- [ ] path search
- [ ] explain
- [ ] related
- [ ] impact
- [ ] find tests
- [ ] deterministic context packing
- [ ] token budget
- [ ] dedupe
- [ ] freshness metadata

## CLI
- [ ] init
- [ ] update
- [ ] watch
- [ ] status
- [ ] search
- [ ] explain
- [ ] related
- [ ] path
- [ ] impact
- [ ] context
- [ ] ui
- [ ] mcp
- [ ] setup-agent
- [ ] doctor
- [ ] rebuild
- [ ] config
- [ ] stable --json
- [ ] stable exit codes

## MCP and agents
- [ ] stdio MCP server
- [ ] pg_status
- [ ] pg_search
- [ ] pg_context
- [ ] pg_entity
- [ ] pg_path
- [ ] pg_related
- [ ] pg_impact
- [ ] pg_update
- [ ] pg_find_tests
- [ ] bounded outputs
- [ ] actionable errors
- [ ] AGENTS.md idempotent block
- [ ] agent-specific adapter framework
- [ ] MCP config helper
- [ ] stale-index guidance
- [ ] post-change refresh guidance
- [ ] no agent loop behavior

## Shared coding-agent memory
- [x] one central per-user SQLite memory database outside repositories
- [x] isolated per-project scope plus user-wide facts and preferences
- [x] lexical and vector memory retrieval with bounded hybrid RAG context
- [x] CLI and MCP create/read/update/delete operations
- [x] automatic context recall for OMP and Codex
- [x] agent guidance for saving durable preferences/decisions without storing secrets
- [x] memory retrieval/token budget and project-scope tests

## Dashboard
- [ ] FastAPI local server
- [ ] React/TypeScript
- [ ] Graphology
- [ ] Sigma.js WebGL graph
- [ ] ForceAtlas2 worker
- [ ] global graph
- [ ] local graph
- [ ] search graph
- [ ] path view
- [ ] inspector
- [ ] filters
- [ ] node/edge legends
- [ ] semantic similarity filter
- [ ] provenance visualization
- [ ] community color/collapse
- [ ] structural/hybrid toggle
- [ ] node pinning/dragging
- [ ] layout force controls
- [ ] selection history
- [ ] source open action
- [ ] impact/path context actions
- [ ] aggregation/progressive expansion
- [ ] live update handling
- [ ] loopback-only default
- [ ] persisted local view preferences

## Testing and benchmarks
- [ ] unit tests
- [ ] parser fixtures
- [ ] integration graph snapshots
- [ ] incremental mutation tests
- [ ] dashboard E2E
- [ ] MCP contract tests
- [ ] retrieval benchmark corpus
- [ ] dimension comparison benchmark
- [ ] semantic-edge calibration
- [ ] scale benchmarks
- [ ] security/path traversal tests
- [ ] offline/privacy test
- [ ] packaging smoke tests

## Documentation
- [ ] architecture matches implementation
- [ ] data model reference
- [ ] CLI reference
- [ ] MCP/tool reference
- [ ] dashboard controls
- [ ] configuration
- [ ] privacy/security
- [ ] troubleshooting
- [ ] adding a language adapter
- [ ] adding an embedding/vector backend
- [ ] benchmark methodology/results

## Definition of done

A clean machine with supported Python can:

```bash
uv tool install poldergraph
git clone <some-repo>
cd <some-repo>
poldergraph init
poldergraph ui
```

and receive a useful interactive structural + semantic graph.

An MCP-capable coding agent can then discover PolderGraph, issue `pg_context` for an unfamiliar task, follow exact source references, run impact/path queries, and update the index after editing without manually inspecting the database or learning implementation details.

The same repository can be edited, files added/deleted/renamed, and `poldergraph update` keeps structural, lexical, semantic, community and dashboard views consistent without a full rebuild.
