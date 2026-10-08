# Autonomous repository intelligence: target operating model

The user wants **a background-capable local intelligence subsystem**, not a passive command-line tool. Define autonomy precisely: after explicit one-time installation/permissions, it should discover each project, build a useful index, keep it fresh, deliver context when appropriate, recover errors, and stop consuming resources when idle.

## State machine

```text
UNSEEN -> DISCOVERING -> STRUCTURAL_READY -> SEMANTIC_WARMING -> READY
                          |                       |              |
                          +----[file events]------> UPDATING <---+
                          |                           |
                          +--[index corruption]--> REPAIRING --+--> STRUCTURAL_READY
                          +--[unsupported/model]--> DEGRADED --+--> STRUCTURAL_READY
READY/DEGRADED --> IDLE --> SUSPENDED --> READY (on demand)
```

A query must report `index_generation`, `workspace_revision`, `structural_freshness`, `semantic_freshness`, `pending_files`, `degraded_reasons`. The service should distinguish *known fresh* from *not checked*, *stale*, *currently updating* and *unavailable*. No model-created stale-state claims.

## Architecture sketch

```text
client adapter(s) [OMP native | native hooks | MCP fallback]
           |
      local supervisor (root/worktree registry, state machine, job dedupe)
           |       |           |           |
       discovery  watcher     update queue  context planner
           |       |           |           |
           +-------+----- SQLite generations / WAL --------+
                             |
                     FTS, graph, vectors
                             |
                   bounded evidence results
```

- Exactly one local writer per workspace generation; many readers; use atomic commit/swap semantics.
- Root/worktree fingerprint must include real path, Git identity/branch/HEAD and dirty-state generation; do not mix different worktree evidence.
- Observers: filesystem event watcher, agent post-edit signal, Git HEAD/branch reconciliation, periodic low-cost verification.
- Coalesce bursts; prioritize structural/FTS deltas then asynchronously update embeddings, communities and optional test coverage.
- Supervisor owns model warming/eviction, idle shutdown, crash recovery, backoff, job progress and cancellation.
- During indexing, either serve last valid generation with explicit stale warning, wait for bounded freshness, or provide deterministic source-read fallback.
- Prefer on-demand activation over an always-running privileged daemon; configuration must allow no watcher and low-resource mode.
- No new account, network backend, hosted API or mandatory separate data store.

## Agent event contract

`workspace_open` → detect, restore or bootstrap index.  
`task_start` → classify task using cheap local signals; inject only relevant source-backed evidence.  
`search/navigation` → enrich with named symbols, paths, tests; suppress duplicate injection.  
`after_edit` → enqueue changed paths and invalidate context generation.  
`before_test/review` → show affected tests and confidence, never silently skip testing.  
`session_end/idle` → flush checkpoint and release costly resources.

Client capability matrix should say `native lifecycle`, `MCP-only`, or `instructions-only`; never claim an agent has hooks unless verified with that agent version. Global config and automatic source indexing are distinct consent categories.

## Fault handling

- **Model missing/offline:** lexical/structural response immediately; don't block on model download.
- **Watcher missing:** reconcile on query + low-frequency polling.
- **SQLite corruption:** retain old index, rebuild into separate generation, validate then swap.
- **Editor atomic rename/Git checkout:** deterministic rescan of impacted paths.
- **Concurrent agents:** dedupe identical updates, share warm query model; no ref conflict or lock starvation.
- **Stale coverage/trace:** evidence explicitly scoped by test execution timestamp + commit.
- **Huge monorepo:** partial capabilities with source coverage report; no false 'complete graph'.
- **Untrusted repository:** never execute repo scripts, hooks or arbitrary LSP/CI commands without explicit authorization.

## Existing issue mapping

- [#26 — Zero-touch bootstrap](https://github.com/PolderLabs/PolderGraph/issues/26)
- [#27 — Unified index lifecycle](https://github.com/PolderLabs/PolderGraph/issues/27)
- [#28 — Freshness barrier](https://github.com/PolderLabs/PolderGraph/issues/28)
- [#29 — Agent native hooks](https://github.com/PolderLabs/PolderGraph/issues/29)
- [#30 — Adaptive context planning](https://github.com/PolderLabs/PolderGraph/issues/30)

## Open design decisions

1. How to obtain a client-neutral project root for each MCP client without trusting `cwd` implicitly.
2. Whether a single per-user daemon should supervise many workspace stores or one coordinator per active workspace is enough.
3. Which client versions genuinely provide a pre-turn hook; do not extrapolate OMP support.
4. How to cap auto-index CPU/disk/model loads and how to recover aborted runs.
5. Whether opt-in agent telemetry should record only counters/events or source-linked anonymized traces.
