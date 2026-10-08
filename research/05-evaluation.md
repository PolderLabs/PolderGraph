# Benchmarks, experiments and acceptance gates

**Purpose:** demonstrate improved **autonomous behavior** and **real coding-task outcomes**, rather than relying on retrieval-only synthetic wins or project README claims. Freeze source versions and record platform, hardware and model settings.

## Evaluation axes

| Axis | Metric | Baseline / failure |
| --- | --- | --- |
| Activation | % sessions receiving usable context without manual `init`/`update`/MCP call | Existing OMP vs Codex/MCP |
| Tool adoption | Fraction of relevant tasks with context delivered or tool invoked | 'Tool exists but agent ignores it' |
| Freshness | event-to-visible-structural index p50/p95; stale answer leakage | Save-then-query races |
| Integrity | corrupted/mixed generations; orphan edges; worktree isolation | Concurrent updates/branch switches |
| Retrieval | relevant region Recall@K, MRR, line-level coverage, budgeted yield | lexical, vector, structural, hybrid |
| Abstention | precision/recall on no-local-context cases | false confident answers |
| Agent task success | repaired tests, accepted solution, regression rate | no engine, current engine, proposed engine |
| Cost | injected tokens/task, duplicate packets, query latency, CPU/RAM/disk | fixed 3k OMP injection |
| Maintenance | manual maintenance commands/task, daemon duplicates, recovery time | current watcher/daemon independent paths |
| Privacy/safety | unexpected outbound traffic, repo script execution, secrets stored | opt-in checks and audit |

## Dataset plan

- **[Agent Retrieval Bench](https://arxiv.org/abs/2607.24882)**: 427 cases / 25 repositories. Use its `code2test`, `comment2context`, `trace2code`, `edit2ripple` and no-gold categories as inspiration; check license, fixture hashes and dataset size before importing.
- **[SWE-Explore](https://arxiv.org/abs/2606.07297)**: rank line regions under fixed budget on diverse languages; distinguish oracle trajectories from necessarily relevant source.
- **[DependEval](https://aclanthology.org/2025.findings-acl.373/)**: cross-file and transitive dependency understanding.
- **[CodeRAG-Bench](https://aclanthology.org/2025.findings-naacl.176/)**: separate retrieval ranking and generated patch quality.
- PolderGraph local fixtures: 20–100 synthetic **version-controlled** tiny repos with precise expected edges, rename, ambiguous identifiers, build tools, dynamic language features and test mapping.
- External task evaluation: fixed issue/commit/task subset; same agent, model, budget and permissions for treatment/baseline.

## Mandatory experiments

1. **Open new repo** with installed agent integration: first useful structural context and no repo-specific setup.
2. **Edit-then-query** within milliseconds: fresh generation or explicit stale status (never confident stale source).
3. **Burst writes**: 100 edits to files, atomic rename, delete/create; no lost update or duplicate embedding job.
4. **Multi-agent concurrency**: at least three clients editing/querying, with one writer and consistent snapshots.
5. **Worktree split**: two active worktrees with same repo but divergent code; no mixed context.
6. **Offline first task** with preinstalled parser and no embedding model: structural/FTS works and degraded signal is explicit.
7. **No-relevance prompts**: zero or tiny context, no unnecessary model warmup.
8. **Hidden dependencies and root-cause signals**: correct source paths, evidence/provenance and uncertainty.
9. **Crashes/restarts** during migration/rebuild: last-good generation survives and automatic repair converges.
10. **Security:** malicious repo files cannot trigger unauthorized shell/network execution, embed secrets or redirect workspace roots.

## Experimental controls

- Record corpus commit SHAs, PolderGraph commit, tree-sitter grammars, EmbeddingGemma model revision/dimension/task prefixes, OS/CPU/GPU, memory, temperature/model/provider for end-to-end agent evaluations, context budgets and random seeds.
- No data leakage: graph created from frozen base commits, not target patches; keep hidden test information separate.
- Compare ablations: lexical only; graph only; embedding only; fixed 3k hybrid; task planner; task planner + auto hooks; optional precise symbol importer and slicing.
- Report confidence intervals and per-task failures. Do not claim production gains from tiny synthetic corpora.
- Distinguish author's paper-reported metrics from PolderGraph-reproduced numbers in README/changelogs.

## Minimal definition of done for autonomy

After one-time opt-in, starting OMP or another actually supported native-hook client on a new repo provides useful verified source context without explicit PolderGraph commands. Multiple quick edits propagate automatically; every answer states freshness and provenance; a failed optional embedding or watcher cannot hide indexed structural facts. The performance cost and incremental value over current behavior are measured.
