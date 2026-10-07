# CLI, installation and configuration

## Installation contract

Primary:

```bash
uv tool install poldergraph
```

Also support standard Python packaging installation.

End users should not need Node.js; compiled dashboard assets ship in the Python wheel.

Native/vector dependencies must have documented platform support and actionable fallback errors.

## Commands

### `poldergraph init [PATH]`
Create/update index, download/prepare configured model if needed, run complete indexing, optionally generate agent guidance.

Options include:
- `--force`
- `--no-agent`
- `--dimensions 128|256|512|768`
- `--embedding-backend native|ollama`
- `--include-media/--no-media`
- `--json`

Running `init` on an existing index performs a compatible update unless `--force` requests rebuild.

### `poldergraph update [PATH]`
Incremental update. `--quiet` for agents/hooks.

### `poldergraph watch [PATH]`
Continuous incremental updater.

### `poldergraph status`
Shows:
- roots
- index/schema versions
- freshness
- file/entity/edge/vector counts
- model/revision/dimensions
- modality capabilities loaded/available
- languages and structural resolver capability
- last index duration/update
- database size

### `poldergraph search QUERY`
Hybrid search.

Options:
- `--limit`
- `--kind`
- `--language`
- `--path`
- `--semantic/--no-semantic`
- `--structural-context`
- `--explain-score`
- `--json`

### `poldergraph explain ENTITY`
Focused entity/neighborhood.

### `poldergraph related ENTITY`
Semantic neighbors with optional graph reranking.

### `poldergraph path SOURCE TARGET`
Graph path.

### `poldergraph impact TARGET`
Reverse dependency/change-impact view.

### `poldergraph context QUERY`
Agent-optimized context.

Options:
- `--budget`
- `--json`
- filters

### `poldergraph ui`
Starts local API/dashboard.

Options:
- `--host 127.0.0.1`
- `--port 7432`
- `--no-open`
- `--watch`

### `poldergraph mcp`
Starts MCP server.

### `poldergraph setup-agent`
Installs/updates agent instructions/config guidance.

### `poldergraph setup [PATH]`
Interactively detects installed coding agents and lets you select the
integrations to configure. Use `--agent NAME` or `--all` for non-interactive
setup.

### `poldergraph doctor`
Verifies:
- SQLite integrity
- schema/index version
- sqlite-vec availability
- model/backend
- vector dimensions/norm sanity
- orphan entities/edges
- index/root paths
- dashboard asset version

### `poldergraph rebuild`
Safe complete rebuild. Prefer building a replacement DB then atomically swapping after success.

### `poldergraph config`
Get/set/show effective configuration.

## Default configuration

`.poldergraph/config.toml`:

```toml
version = 1

[index]
dimensions = 256
include_media = true
include_generated = false
follow_symlinks = false
max_file_bytes = 5000000

[embedding]
backend = "native"
model = "google/embeddinggemma-2"
batch_size = 0              # auto
device = "auto"
normalize = true

[semantic_edges]
enabled = true
top_k = 12
mutual_preferred = true
max_degree = 8
minimum_similarity = "auto"

[graph]
community_algorithm = "leiden"
compute_structural_communities = true
compute_hybrid_communities = true

[retrieval]
semantic_candidates = 40
lexical_candidates = 40
graph_hops = 2
max_graph_candidates = 150
default_context_tokens = 6000

[ui]
host = "127.0.0.1"
port = 7432
open_browser = true

[privacy]
allow_model_downloads = true
allow_remote_embedding = false
telemetry = false
```

## Configuration precedence

Lowest to highest:
1. built-in defaults
2. user config
3. workspace `.poldergraph/config.toml`
4. environment variables
5. CLI flags

`poldergraph config show --effective` prints merged values and origins.

## Environment variables

Use `POLDERGRAPH_` prefix. Nested values use double underscores, e.g.:

```text
POLDERGRAPH_EMBEDDING__DEVICE=cuda
POLDERGRAPH_INDEX__DIMENSIONS=256
```

## Device selection

`device=auto` selects a supported accelerator when the chosen runtime can use it, otherwise CPU.

The tool must report what it selected.

Do not require CUDA.

## Model acquisition

The first command requiring embeddings:
- checks configured local cache,
- explains download requirement if model absent,
- honors offline mode,
- downloads once through the model runtime,
- records resolved revision.

`--offline` forbids network access and fails with exact cache remediation if missing.

## Gitignore behavior

During init, offer/add only a minimal idempotent entry:

```gitignore
.poldergraph/
```

Do not rewrite unrelated ignore rules.

## Logging

Human CLI defaults to concise output.

Detailed logs live under `.poldergraph/logs/` with size/retention limits.

`-v/-vv` controls console diagnostics.

Never log complete source bodies or vectors unless an explicit debug-data option is used.

## Stable machine output

Every query/status command supports `--json`.

Schema changes to JSON outputs require versioning. Include:

```json
{"api_version": 1}
```

Agent/MCP behavior depends on this stability.
