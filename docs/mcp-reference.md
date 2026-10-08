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
- `consistency` (`bounded` by default; `best_effort` or `strict`)

Returns ranked entities with score decomposition and evidence badges (`exact`, `lexical`, `semantic`, `graph-expanded`).

### `pg_context`

Arguments:
- `query` (required)
- `token_budget` (default 6000)
- `kinds`, `languages` — optional filters
- `consistency` (`bounded` by default; `best_effort` or `strict`)

Returns the canonical context pack: entities, relationships, snippets, paths, communities, unresolved references, freshness metadata and token estimate. This is the preferred first tool for broad repository tasks.

`bounded` returns promptly with freshness and stale-file metadata. `best_effort`
uses the same retrieval behavior without a freshness barrier. `strict` checks
source content before and after retrieval and returns `INDEX_STALE` with stale
paths instead of results when any indexed source changed. Strict mode can read
the indexed source files to verify their content hashes.

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

### Shared memory

`pg_context` automatically returns relevant memories under the supplied token
budget. These tools operate on one central per-user memory database and only
show user-wide entries plus entries scoped to the current project:

- `pg_memory_status`: store location and visible-scope counts.
- `pg_memory_search(query, scope="all", limit=10)`: semantic vector and keyword search.
- `pg_memory_list(scope="all", limit=50)`: list accessible records.
- `pg_memory_add(content, scope="project", kind="fact", tags=[])`: save a durable note.
- `pg_memory_update(memory_id, content?, kind?, tags?, clear_tags=false)`: edit and re-vectorize a note.
- `pg_memory_forget(memory_id)`: permanently delete a note and its vectors.

See [memory.md](memory.md) for scope, storage location, privacy, and fallback behavior.

## Error handling

All tools return structured error envelopes with `code`, `message` and `remediation` fields. The agent sees the error message and the remediation step, never a crash.

## MCP configuration

```bash
poldergraph setup-agent --print-mcp-config
```

Generates a JSON MCP server configuration pointing at the current executable and workspace root.

For Codex, `poldergraph setup --agent codex` writes a project-scoped
`[mcp_servers.poldergraph]` entry to `.codex/config.toml` and installs the
PolderGraph skill under `.agents/skills/poldergraph/`. Codex must trust the
repository before loading project MCP configuration.
