# Comparable projects: useful patterns and boundaries

Review as of **2026-10-08**. These are **source-project descriptions**, not installation, code audit or reproduced performance results. Pin version/commit and check licenses before copying implementation patterns.

| Project | Core idea | Candidate for PolderGraph | What not to copy |
| --- | --- | --- | --- |
| [GitNexus](https://github.com/johnman/gitnexus) | Agent-oriented code graph, setup automation, generated guidance and hooks | Global MCP onboarding, automatic injection and post-edit actions | Another graph database; redundant user-facing setup |
| [Serena](https://github.com/oraios/serena) | Symbol-level navigation/editing using language-server tooling and project onboarding | LSP-verified source anchors, low-token symbol navigation, client capability mapping | Agent-specific editor assumptions; duplicate editing implementation |
| [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | Shared daemon, auto-index on MCP start, per-project watchers, compact tools | Auto-index configuration, shared jobs, session-aware resource scheduling, structured staleness | Treat its speed/token claims as independently verified |
| [codegraph-mcp](https://github.com/Cameloo1/codegraph-mcp) | Evidence/proof-labeled context, lifecycle-aware reads, edit validation outcomes | Distinguish proved, candidate and unknown, validation after edits | Imply static analysis proves runtime correctness |
| [mcp-context-graph](https://github.com/padobrik/mcp-context-graph) | First query triggers indexing and later queries check staleness | No manual init, bounded lightweight project context | Full-project re-scan on every request |
| [OntoIndex](https://github.com/ontograph/ontoindex) | Graph, process nodes, changed-code analysis, multi-repo contracts | Derive execution/process views and inter-repo packages | Build a second graph model or mandatory web UI |
| [CodeGraph / code-intelligence-mcp](https://github.com/sscba/code-intelligence-mcp) | Structural graph, metrics, architectural governance tools | Architecture constraints and targeted anomaly diagnostics | 37 tools exposed to an agent unnecessarily |
| [ckg](https://github.com/phins-group/ckg) | Small Rust/SQLite/tree-sitter task-context engine | Compact task-context responses and measurable low-overhead local mode | Rewrite stable Python components merely for language choice |
| [GitHub code navigation](https://github.com/github/code-navigation) | Tree-sitter tagging and reference navigation | Language-level definitions/references as fallback | Claim regex/name heuristics are typed resolution |
| [SCIP](https://github.com/scip-code/scip) | Language-agnostic precise code-navigation index interchange | Import compiler/indexer facts into current entity IDs | Mandatory compiler/toolchain launches |
| [Entire CLI](https://github.com/entireio/cli) | Agent session checkpoints and optional Git-linked provenance | Optional source-linked workflow history and rollback hints | Automatically ingest or share raw private transcripts |
| [RepoMaster](https://github.com/wanghuacan/RepoMaster) | Autonomous repository exploration and progressive graph navigation | Selective expansion of architecture, calls and modules | Model-dependent autonomous crawling as prerequisite |

## Takeaways that differ from features already present

**One-time onboarding, then no manual commands.** Codebase-memory-mcp exposes session-triggered automatic index creation and configurable watchers; mcp-context-graph triggers indexing at first query. PolderGraph has parts of both (OMP lifecycle, watcher, query daemon), but they are currently separate. Prefer one coordinator and a small capability-specific client adapter over universal hook assumptions.

**Proof-labeled results.** codegraph-mcp distinguishes graph/source verification from retrieval candidates and unknowns. PolderGraph already records extracted/resolved/inferred/semantic provenance, but should carry this discipline into *every* agent response, especially stale source spans.

**Precise navigation as enrichment.** Serena and SCIP complement tree-sitter rather than replacing it. A narrow locally available SCIP/LSP import can improve renames, overloads and references; keep existing extracted graph when precision providers are unavailable.

**Do not proliferate agent tools.** More commands can reduce adoption and increase tool-selection cost. Provide one intelligent `pg_context` or small task-aware surface, with more focused calls for deliberate investigations.

**Autonomous maintenance is a measurable product feature.** Count time from first use to structurally useful answer, index freshness after edit, number of manual maintenance commands, duplicate daemons and indexing overhead—not just source-line indexing throughput.

## Source/claims caveats

- codebase-memory-mcp reports strong performance, language support and many integrations in its README. No equivalent PolderGraph-controlled comparative run was conducted here.
- RepoMaster's dramatic token/task claims are from author evaluation and may not generalize to a passive intelligence engine.
- LSPs differ substantially across languages and agent hosts. Only enable actually supported hooks and indexers per client.
- Local-first projects may still fetch runtime/model artifacts during initial setup; design an explicit offline and download policy.
