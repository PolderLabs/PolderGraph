# PolderGraph research library

**Updated:** 2026-10-08. **Mission:** make PolderGraph an entirely local **repository intelligence engine** that coding agents use automatically, with self-maintained, verifiably fresh state.

This directory collects external research and maps it to the actual PolderGraph architecture. It is **not** a substitute for implementation specifications under `docs/`. Vendor and project README statements are design references, not independent benchmarks. Dates below refer to publication or research review, not guaranteed latest releases.

## Read in this order

1. [01 — Projects and competitive implementations](01-projects.md): local graph engines, agent integrations, actual differentiation.
2. [02 — Papers and benchmarks](02-papers.md): newer empirical work through October 2026, experiment design, limitations.
3. [03 — Technologies and architectural patterns](03-technologies.md): practical candidate components with licensing/operational considerations.
4. [04 — Autonomous lifecycle and agent integration](04-autonomy.md): target design and concrete execution states.
5. [05 — Retrieval and verification experiments](05-evaluation.md): how to measure correctness, quality, overhead and real adoption.
6. [06 — Recommendation and issue map](06-recommendations.md): what to build, avoid, and track.

## Product constraints (from AGENTS.md and existing design)

- Default **offline/local** operation after user-authorized first-time dependencies are obtained.
- Single canonical local SQLite index shared by CLI, MCP, HTTP and dashboard; no compulsory server, cloud database, account or API key.
- Keep deterministic source-derived edges, compiler-verified relationships, inference and embedding similarity **distinct**, with provenance.
- EmbeddingGemma 2 remains canonical semantic model; native structural/keyword fallback works without it.
- No mandatory hosted LLM or remote inference. Do not persist raw prompts, transcripts or secrets by default.
- Zero-touch **after one-time consent/setup**: project discovery, initial usable index, continuous updates, context injection, repair and idle resource management.
- Source/graph freshness and content relevance are separate dimensions; neither should be silently assumed.
- Human verification remains required for risky edits. PolderGraph is evidence, not proof of runtime behavior.

## Current baseline (source-checked)

- `src/poldergraph/parsing/`: tree-sitter adapters and cross-file resolver.
- `src/poldergraph/graph/`: structurally separate semantic and typed source relationships.
- `src/poldergraph/indexing/watcher.py`: standalone debounced filesystem watcher.
- `src/poldergraph/query_daemon.py`: per-workspace warm query process and fallback.
- `src/poldergraph/retrieval/service.py`: search, context, path, impact, related and find-tests.
- `src/poldergraph/mcp/server.py`: MCP graph/memory tools.
- `omp/index.ts`: existing automatic session bootstrap, per-task context injection and post-edit update.
- `src/poldergraph/agents/setup.py`: adapters and Codex config; does not install generic hook lifecycle (`hooks_installed: False`).
- `docs/research.md`: original October 7, 2026 research baseline; continue to treat it as a historical technology-decision record.

## Evidence classification

- **Primary paper:** peer-reviewed publication or linked preprint; report author-measured numbers as **paper-reported** and note dataset.
- **Primary project:** author-maintained repository/documentation; implementation claim **not independently verified** here.
- **Vendor documentation:** authoritative for its contract, not for comparative accuracy/performance.
- **Proposed:** hypothesis or PolderGraph recommendation; test before adopting.

## Cross references

Autonomy issues: [#26](https://github.com/PolderLabs/PolderGraph/issues/26), [#27](https://github.com/PolderLabs/PolderGraph/issues/27), [#28](https://github.com/PolderLabs/PolderGraph/issues/28), [#29](https://github.com/PolderLabs/PolderGraph/issues/29), [#30](https://github.com/PolderLabs/PolderGraph/issues/30). Existing memory roadmap: [#22](https://github.com/PolderLabs/PolderGraph/issues/22). Do not duplicate delivered PRs #23–#25.
