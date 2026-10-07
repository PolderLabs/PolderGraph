# CLI reference

## Installation

```bash
uv tool install poldergraph
```

## Commands

### `poldergraph init [PATH]`

Create the index and run complete indexing. Downloads the embedding model on first use.

Options:
- `--force` — discard existing index and rebuild
- `--no-agent` — skip agent instruction generation
- `--dimensions 128|256|512|768` — embedding dimensions (default 256)
- `--embedding-backend native|ollama` — embedding backend (default native)
- `--include-media/--no-media` — index media files
- `--json` — machine-readable output

### `poldergraph update [PATH]`

Incrementally update the index. Only re-indexes changed files and re-embeds changed semantic inputs.

Options:
- `--quiet` — print nothing on success
- `--force` — re-verify hashes for every file
- `--json` — machine-readable output
- `--offline` — forbid network access

### `poldergraph watch [PATH]`

Continuously update the index as files change. Coalesces file events and applies incremental transactions.

### `poldergraph status`

Show roots, schema/index versions, freshness, file/entity/edge/vector counts, model/revision/dimensions, language capability and last update.

Options:
- `--json` — machine-readable output

### `poldergraph search QUERY`

Hybrid search across exact, lexical, semantic and structural channels.

Options:
- `--limit N` — maximum results (default 20)
- `--kind KIND` — filter by entity kind (repeatable)
- `--language LANG` — filter by language (repeatable)
- `--path PREFIX` — restrict to path prefix
- `--semantic/--no-semantic` — use semantic retrieval
- `--structural-context` — expand around strong candidates
- `--explain-score` — show score breakdown per result
- `--json` — machine-readable output

### `poldergraph explain ENTITY`

Show identity, ownership, inbound/outbound relations, semantic neighbours, communities, metrics and a source excerpt.

Options:
- `--json` — machine-readable output

### `poldergraph related ENTITY`

Semantic neighbours with optional graph-aware reranking. Shows whether two nodes are structurally connected.

Options:
- `--limit N` — maximum neighbours (default 10)
- `--json` — machine-readable output

### `poldergraph path SOURCE TARGET`

Find the relationship path between two entities.

Options:
- `--structural-only/--include-semantic` — edge classes to traverse
- `--max-hops N` — maximum path length (default 12)
- `--json` — machine-readable output

### `poldergraph impact TARGET`

Show what may be affected if this entity changes.

Options:
- `--max-depth N` — reverse dependency depth (default 3)
- `--edge-type TYPE` — restrict edge classes (repeatable)
- `--json` — machine-readable output

### `poldergraph context QUERY`

Agent-optimized repository context under a token budget.

Options:
- `--budget N` — token budget (default 6000)
- `--json/--no-json` — machine-readable output (default json)

### `poldergraph ui`

Start the local dashboard.

Options:
- `--host HOST` — bind address (default 127.0.0.1)
- `--port PORT` — port (default 7432)
- `--no-open` — do not open a browser
- `--watch` — also run the file watcher

### `poldergraph mcp`

Start the stdio MCP server.

### `poldergraph setup-agent`

Install or update agent instructions and MCP configuration.

Options:
- `--all` — update every detected agent integration
- `--agent NAME` — target one agent adapter (repeatable)
- `--print-mcp-config` — print MCP server configuration
- `--hooks` — explicitly allow installing git hooks

For Codex, `poldergraph setup-agent --agent codex` writes a project skill and
the repository-scoped MCP server config at `.codex/config.toml`.

### `poldergraph doctor`

Verify index integrity: SQLite integrity, schema/version, orphan edges/embeddings, acyclic parent chains, line spans, FTS namespace, vector dimensions/norms, path safety.

Options:
- `--json` — machine-readable output
- `--fix` — attempt to repair recoverable problems

### `poldergraph rebuild`

Rebuild the index in a replacement database and swap it atomically. The existing index is preserved as a backup until the new one passes integrity checks.

Options:
- `--json` — machine-readable output

### `poldergraph config show`

Print configuration values.

Options:
- `--effective` — show merged values and origins
- `--json` — machine-readable output

### `poldergraph config set KEY VALUE`

Set one configuration value in the workspace config.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | Usage/config error |
| 3 | Index missing |
| 4 | Index stale when command requires fresh index |
| 5 | Model/backend unavailable |
| 6 | Index locked/busy |
| 7 | Corrupt/incompatible index |
| 8 | Degraded capability |

JSON mode always returns the documented envelope, even on errors.
