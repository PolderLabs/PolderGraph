# Ranked technology recommendations and issue map

These are **design priorities, not chronological implementation phases**. PolderGraph's existing one-shot feature-set requirement still applies. Prioritize measurable additions to its **local autonomous intelligence core**, not separate platforms.

## Must-have autonomy

1. **Unified workspace startup:** detect workspace/root/worktree, provide structural-first index, then semantic background warming. [Issue #26](https://github.com/PolderLabs/PolderGraph/issues/26).
2. **One live supervisor:** combine watcher, update, query model and daemon lifecycle with job deduplication and idle cleanup. [Issue #27](https://github.com/PolderLabs/PolderGraph/issues/27).
3. **Generation-consistent query barrier:** source revision, structural/semantic freshness and bounded wait/fallback. [Issue #28](https://github.com/PolderLabs/PolderGraph/issues/28).
4. **Native agent lifecycle adapters:** automatic context delivery where supported, plain MCP fallback where not. [Issue #29](https://github.com/PolderLabs/PolderGraph/issues/29).
5. **Task-specific evolving context:** budget according to task, current files/edits and evidence, avoid duplicate injection. [Issue #30](https://github.com/PolderLabs/PolderGraph/issues/30). Inspired especially by [RepoAtlas](https://arxiv.org/abs/2609.16936) and [ARB](https://arxiv.org/abs/2607.24882).

## Intelligence improvements worth dedicated design work

- **Build/test/CI dependency graph** from manifests and actual tool metadata (RIG/SPADE): converts static code graph into complete repository architecture. Local, parser-only default. Add typed nodes for package, build target, test target and CI job, explicit source spans, stale-state guarantees. [RIG paper](https://arxiv.org/abs/2601.10112).
- **Failure→code and edit→ripple retrieval**: parse test failures/stack traces and edit hunks, rank candidate source/affected tests with evidence and abstention. [ARB paper](https://arxiv.org/abs/2607.24882). Extend existing `pg_find_tests`/`pg_impact`; no duplicate search backend.
- **Lazy intraprocedural def-use slicing** for difficult debugging tasks (ARISE): keep default entity graph sparse; produce slices only on demand with strict analysis limits and provenance. [ARISE](https://arxiv.org/abs/2605.03117).
- **Optional precise SCIP/LSP evidence:** import only installed, authorized locally produced symbol indexes and safely merge with canonical entities. [SCIP](https://github.com/scip-code/scip).
- **Branch/diff-aware intelligence:** map diff hunks to symbols and typed impact paths; worktree isolation crucial for parallel agents. Inspired by [GitNexus](https://github.com/johnman/gitnexus), [OntoIndex](https://github.com/ontograph/ontoindex).
- **Self-diagnostics and repair:** `doctor` should run automatically before query if generation/schema/coverage is unusable, and atomically restore last good or rebuild safely. Ensure visible but unobtrusive degraded statuses.

## Defer pending benchmark evidence

- Always-on image/graph screenshots sent to agent models: RepoAtlas is interesting but not proof that visuals help text-only code agents.
- A second hosted memory DB or nonlocal RAG service: contrary to the product contract.
- Mandatory learned routing, special agent RL finetune, local LLM summarization: useful hypotheses, disproportionate maintenance until benchmarks justify them.
- Full raw transcript ingestion: privacy/integrity costs; keep optional evidence-linked snapshots only.
- Wholesale Rust rewrite/alternative vector database: optimize only confirmed bottlenecks.

## Architecture rules

- Graph facts are authoritative only **relative to their provenance and index generation**.
- Code index is **derived data**, recoverable from local repository without hidden manual actions.
- Agent context must be **task-conditional and source-linked**, not an obligatory 3k-token preamble.
- Agent-specific hooks must be verified against real host contracts, fall back cleanly, and never fake capabilities.
- Security/privacy and no mandatory cloud are acceptance gates, not stretch goals.

## New issue candidates not yet included in #26–#30

1. **Build/test/CI architecture graph importer** — new typed package/build/test edges, CMake/CTest first plus JS/Python/Rust/Go manifests; source and generation provenance.
2. **Trace-to-code localization and diagnostic evidence importer** — parse local test failure traces, rank source causes and changed-code impact with ARB-like fixtures.
3. **Lazy intra-function def-use slicing** — ARISE-inspired local CFG/def-use tool behind debugging intent.
4. **Automatic integrity repair and quota-aware idle management** — make derived index resilient to crashes and large workspaces; operator-free normal recovery.
5. **Agent autonomy end-to-end test matrix** — verify actual hook invocation, zero-manual setup and no stale leakage, rather than just contract-level MCP unit tests.

Create separately only when implementation is scoped and checked against open issues; do not duplicate existing memory issue #22.
