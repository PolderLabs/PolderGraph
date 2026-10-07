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
