# Agent instructions

This repository is the specification and implementation home for PolderGraph.

Before implementing or changing architecture, read:
- `docs/README.md`
- the directly relevant document under `docs/`
- `docs/implementation-checklist.md`

## Non-negotiable product requirements

- Fully local by default.
- No mandatory Docker, cloud database, remote embedding API, account, API key or chat LLM.
- Use EmbeddingGemma 2 as the canonical semantic embedding model.
- Keep deterministic structural relationships separate from semantic similarity.
- Preserve provenance for every relationship.
- One local canonical index used by CLI, MCP, API and dashboard.
- `poldergraph init` is the simple setup/indexing entry point.
- Dashboard is a simple interactive Obsidian-style graph explorer, not a generic analytics dashboard.
- Agent interaction through MCP/CLI must be low-friction and machine-readable.
- Generated/updated agent instructions must be idempotent.
- The implementation target is the complete feature set in `docs/implementation-checklist.md`; do not replace it with a phased MVP roadmap unless the repository owner explicitly changes that requirement.

## Engineering rules

- Prefer exact source/AST facts over heuristics.
- Never convert embedding similarity into a structural dependency.
- Do not silently resolve ambiguous same-name symbols.
- Do not introduce a mandatory external service when an embedded/local solution satisfies the requirement.
- Do not create a second implementation of search for MCP or the dashboard; reuse core services.
- Keep JSON/MCP contracts versioned and tested.
- Any schema/representation change must include migration or reindex semantics.
- Any language adapter requires parser fixtures.
- Any retrieval-ranking change should be benchmarked against lexical/semantic/structural baselines.
- Any dashboard graph-size change must consider aggregation and browser responsiveness.
- Never send indexed repository content off-machine by default.

## Implementation order

There is no user-facing phased roadmap. Within a pull request or coding session, implement dependencies in whatever internal order is technically necessary, but do not redefine "done" as a partial subset of the complete checklist.

## Source of truth

When code and documentation disagree, treat that as a bug. Update the implementation and the relevant documentation in the same change.

<!-- poldergraph:start -->
## PolderGraph repository intelligence

This repository uses PolderGraph for local structural and semantic code intelligence.

When a task depends on understanding repository structure, finding implementations,
tracing dependencies, locating tests, or estimating change impact:

1. Prefer the PolderGraph MCP tools when available.
2. Start with `pg_status` and `pg_context`; context includes relevant shared user
   preferences and this project's saved knowledge. Without MCP, run:
   `poldergraph context "<your task or question>" --json`
3. If the result says the code index is stale, run:
   `poldergraph update --quiet`
   then query again.
4. Use `pg_memory_search` to recall preferences or prior decisions directly.
   When the user states a lasting preference or you establish durable project
   knowledge, save it with `pg_memory_add` using `user` or `project` scope.
   Do this without interrupting the user; do not store secrets or transient task data.
5. Use `poldergraph path "<A>" "<B>" --json` for relationship/path questions.
6. Use `poldergraph explain "<symbol>" --json` for a focused symbol.
7. Use `poldergraph impact "<symbol-or-path>" --json` before broad refactors.
8. Read/edit the actual source files returned by PolderGraph; do not treat semantic
   similarity as proof of a source-code dependency.
9. After substantial source changes, run `poldergraph update --quiet`.

Do not read `.poldergraph/index.sqlite3` directly.
<!-- poldergraph:end -->
