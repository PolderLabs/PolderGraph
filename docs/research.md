# Research notes and technology decisions

Research performed 2026-10-07. Prefer primary sources; pin concrete dependency versions during implementation rather than assuming these notes remain current.

## EmbeddingGemma 2

Primary sources:
- https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/
- https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2
- https://huggingface.co/google/embeddinggemma-2

Relevant findings:
- released by Google DeepMind as an on-device multimodal embedding model
- shared embedding space for text/code, images, audio and video
- full model is 740M parameters, with modular text/vision/audio components
- text-only workloads can use the 270M text component
- native output is 768 dimensions
- Matryoshka truncation supports 512, 256 and 128 dimensions
- truncated vectors must be L2-normalized again before cosine similarity
- query and corpus vectors must use the same dimensions
- model is Apache 2.0
- code retrieval is explicitly part of its benchmark/training story

Decision:
EmbeddingGemma 2 is the canonical semantic model. Default to 256 dimensions pending repository benchmark confirmation. Load non-text modality encoders only when required.

## Graphify

Primary sources:
- https://github.com/Graphify-Labs/graphify
- https://github.com/Graphify-Labs/graphify/blob/v8/ARCHITECTURE.md
- https://github.com/Graphify-Labs/graphify/blob/v8/docs/how-it-works.md

Relevant findings:
- deterministic tree-sitter code extraction
- explicit/inferred/ambiguous provenance
- graph query/path/explain operations
- Leiden communities
- persistent graph output
- local-first code parsing
- current design deliberately treats the graph itself as the primary structure rather than relying on a vector store

Decision:
Preserve Graphify's strongest idea: deterministic graph facts with honest provenance. Do not copy its no-vector constraint. PolderGraph adds EmbeddingGemma 2 as an independent semantic evidence layer and hybrid retriever.

## GitNexus

Primary source:
- https://github.com/johnman/gitnexus

Relevant findings:
- local code graph intended for AI coding agents
- CLI + MCP integration
- index command installs agent guidance
- creates AGENTS.md/CLAUDE.md context
- editor setup automates MCP configuration
- agent hooks can enrich searches and update after changes

Decision:
Adopt the low-friction agent interaction pattern: index once, expose MCP, generate small canonical instructions, keep stale-index remediation obvious. Avoid tying PolderGraph to one editor/agent.

## Obsidian graph UX

Primary source:
- https://help.obsidian.md/plugins/graph

Relevant interaction ideas to mirror, not clone visually:
- global and local graph concepts
- search/filter-driven visibility
- groups/coloring
- interactive force-directed layout
- neighborhood exploration
- force controls for advanced users

Decision:
Dashboard should be graph-first, minimal, dark-mode capable and exploratory. Local graph is a first-class view. Filters and force settings are controls over a single canonical graph, not separate reports.

## Sigma.js / Graphology

Primary source:
- https://www.sigmajs.org/docs/

Relevant findings:
- Sigma.js is designed for graph visualization using WebGL
- built on Graphology
- intended for thousands of nodes/edges
- compatible with graph layout tooling including ForceAtlas2 in the Graphology ecosystem

Decision:
Use Graphology client-side, Sigma.js for rendering, ForceAtlas2 in a worker. For graphs too large to render meaningfully, rely on server-side aggregation/progressive expansion rather than expecting WebGL alone to solve information density.

## tree-sitter-language-pack

Primary source:
- https://github.com/xberg-io/tree-sitter-language-pack
- https://pypi.org/project/tree-sitter-language-pack/

Relevant findings at research time:
- provides hundreds of tree-sitter grammars
- prebuilt Python bindings and on-demand/selective parser support
- substantially reduces parser dependency maintenance

Decision:
Use it as the parser distribution layer, while keeping PolderGraph's own semantic language adapters/resolvers. Grammar availability is not the same as high-quality code intelligence; strong languages still need explicit queries and resolver tests.

## sqlite-vec

Primary source:
- https://github.com/asg017/sqlite-vec
- https://github.com/asg017/sqlite-vec/blob/main/site/api-reference.md

Relevant findings:
- local SQLite vector extension
- supports float32, int8 and bit vectors
- no separate vector database server
- currently pre-v1 and therefore carries API/breakage risk

Decision:
Use sqlite-vec as the default vector backend because it preserves the one-database/no-daemon UX. Hide it behind a VectorStore interface, pin a tested version, and keep migration/alternative-backend escape hatches.

## SQLite/FTS5

Decision:
SQLite remains the canonical store for entities, edges, metadata, configuration state and FTS. It gives a portable single-workspace artifact, transactional updates and simple backup/diagnostics.

Use WAL mode for normal concurrency and explicit schema migrations.

## NetworkX vs igraph

Decision:
Use lightweight Python graph operations where convenient, but use igraph/leidenalg for community detection and workloads where NetworkX overhead becomes material. The persistent database is canonical; neither in-memory library owns the data model.

## FastAPI + React

Decision:
A local HTTP API separates the Python intelligence engine from a polished browser UI while keeping install/runtime simple. Production frontend assets are prebuilt and packaged, so end users do not need a JS toolchain.

## Key architectural conclusion

The product should not choose between a knowledge graph and vector search.

Structural graph answers:
"what is actually connected according to source?"

Embedding space answers:
"what is conceptually relevant to this query?"

Hybrid retrieval answers:
"what small set of repository evidence should a person or coding agent inspect now?"

Keeping those evidence types explicit is the central PolderGraph design rule.
