# Candidate technologies and reusable designs

This is a selection matrix, **not** an instruction to add all listed dependencies. Verify license, supported platform, project maintenance and compatibility at implementation time.

| Component | Existing PolderGraph baseline | Candidate mechanism | Default? | Evidence / risk |
| --- | --- | --- | --- | --- |
| Structural parsing | tree-sitter-language-pack + adapters | Keep and improve resolution fixtures | Yes | [Tree-sitter code navigation](https://tree-sitter.github.io/tree-sitter/) |
| Precise symbols | cross-file resolver | Import [SCIP](https://github.com/scip-code/scip) indexes, optional installed LSP | No, opt-in enrichment | Compiler/indexer tools often heavyweight; path/commit matching required |
| Semantic embedding | EmbeddingGemma 2 + sqlite-vec | Keep canonical model, choose 128/256/512/768 using measured retrieval quality | Yes, when installed | [Official model card](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2); pin model revision/dims |
| Text/code lightweight cold start | EmbeddingGemma 2 modular encoders | Load 270M text path rather than multimodal modules for code-only repos | Yes when supported | [Google developer guide, Oct 6 2026](https://developers.googleblog.com/en/embeddinggemma-2-the-developer-guide/) |
| Better ranking | FTS + vector + graph expansion | Intent-conditional lane weights, source-anchored reranking, query-specific candidate diversity | Measure first | [Agent Retrieval Bench](https://arxiv.org/abs/2607.24882) |
| Late interaction reranking | Current rerank service | Local ColBERT-like reranker over 20–100 candidates only | Experimental | [ColBERT](https://github.com/stanford-futuredata/ColBERT); adds model/RAM/latency |
| Exact indexes | SQLite FTS5/graph | Persistent stable symbol-to-reference postings and branch-aware identities | Incrementally | Schema/renames/reindex correctness |
| Live sync | explicit watch + OMP events | One supervised per-workspace watcher, event queue, checkpoint generation | Yes | Competing SQLite writers and missed events |
| Runtime/test evidence | structural `pg_find_tests` | Read-only imports from coverage.py, LCOV, JUnit/Vitest reports, test manifests | Optional local artifact discovery | Evidence scoped to one execution; stale by default |
| Build graph | import/call relationships | Parse `pyproject.toml`, `Cargo.toml`, `package.json`, `go.mod`, CMake File API, CI workflows | Layered local sources | [RIG/SPADE paper](https://arxiv.org/abs/2601.10112) |
| Code slicing | file/symbol graph | Lazy intra-function definition-use graphs via language AST/CFG adapters | Opt-in on debug/trace task | [ARISE](https://arxiv.org/abs/2605.03117); dynamic semantics incomplete |
| Agent protocol | MCP tools and OMP extension | One `pg_context` planner plus precise, bounded navigation tools | Yes | [RepoNavigator](https://proceedings.mlr.press/v306/zhang26an.html) |
| Editor integration | generated skills + MCP | Client-specific verified lifecycle hooks + fallback mode | Capability gated | [GitNexus](https://github.com/johnman/gitnexus) |
| Checkpoint/rationale | user/project memory | Optional provenance links to Git commits and local agent checkpoints | Never auto-import raw transcripts | [Entire](https://github.com/entireio/cli) |

## EmbeddingGemma 2: actionable technical notes

Google's Oct 6, 2026 official developer guide confirms a unified 768-dim space, a 270M text/code component, additional vision/audio modules, and Matryoshka truncation to 128/256/512 dims. The [model card](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2) specifies:
- **L2-normalize after slicing** and use identical query/corpus dimensions.
- Load only required modalities; don't incur multimodal cold-start cost for text-only repos.
- Persist model/version, task prompt, dimensions, normalization and input-representation version in the index.
- Re-evaluate retrieval using ARB-style task cases before changing default 256 dimensions.
- Enforce explicit, user-authorized first-time download; subsequent queries need no internet.

## Avoid dependency pitfalls

- [GitHub Stack Graphs](https://github.com/github/stack-graphs) was **archived September 2025**; it remains an architectural reference for name-resolution graphs, but is not a recommended new core runtime dependency.
- Local language servers can execute project configuration or plugins: never silently spawn arbitrary workspace commands; sandbox/safe launch policy and consent.
- Binary/native indexes must be invalidated on version/ABI/representation change with recovery into a known-good generation.
- More storage and model complexity is not necessarily improved agent quality; maintain a deterministic lexical/graph fallback.
