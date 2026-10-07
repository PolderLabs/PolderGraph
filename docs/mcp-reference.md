# MCP tool reference

## Server

```bash
poldergraph mcp
```

Starts the MCP stdio server. Tools invoke the same query service as the CLI and dashboard.

## Tools

### `pg_status`

Returns index existence, freshness, root, model/dimensions, capabilities, counts and last update. Does not load the embedding model.

### `pg_search`

Arguments:
- `query` (required)
- `limit` (default 25)
- `kinds`, `languages`, `roots`, `paths` — filters
- `include_semantic` (default true)
- `include_structural_context` (default false)

Returns ranked entities with score decomposition and evidence badges (`exact`, `lexical`, `semantic`, `graph-expanded`).

### `pg_context`

Arguments:
- `query` (required)
- `token_budget` (default 6000)
- `kinds`, `languages` — optional filters

Returns the canonical context pack: entities, relationships, snippets, paths, communities, unresolved references, freshness metadata and token estimate. This is the preferred first tool for broad repository tasks.

### `pg_entity`

Arguments:
- `entity` (required) — stable ID, qualified name or path

Returns entity details and a bounded neighborhood: identity, ownership, inbound/outbound relations grouped by type, semantic neighbours, community memberships, metrics and a source excerpt.

### `pg_path`

Arguments:
- `source` (required)
- `target` (required)
- `structural_only` (default true)
- `include_semantic` (default false)
- `max_hops` (default 12)

Returns the relationship path between two entities with per-edge provenance.

### `pg_related`

Arguments:
- `entity` (required)
- `limit` (default 10)

Returns semantic neighbours annotated with structural linkage.

### `pg_impact`

Arguments:
- `entity` (required)
- `max_depth` (default 3)
- `edge_types` (optional list)

Returns direct/transitive dependents, tests, docs and semantically related items.

### `pg_update`

Incrementally refreshes the graph. Safe to invoke repeatedly.

### `pg_find_tests`

Arguments:
- `entity` (optional)
- `query` (optional)
- `limit` (default 25)

Returns structurally or lexically linked tests for a symbol or file.

## Error handling

All tools return structured error envelopes with `code`, `message` and `remediation` fields. The agent sees the error message and the remediation step, never a crash.

## MCP configuration

```bash
poldergraph setup-agent --print-mcp-config
```

Generates a JSON MCP server configuration pointing at the current executable and workspace root.

For Codex, `poldergraph setup-agent --agent codex` writes a project-scoped
`[mcp_servers.poldergraph]` entry to `.codex/config.toml` and installs the
PolderGraph skill under `.agents/skills/poldergraph/`. Codex must trust the
repository before loading project MCP configuration.
