# Agent interaction contract

Agent interaction is a primary product surface. A coding agent should discover PolderGraph automatically, know exactly when to use it, and receive compact machine-readable results.

The agent must not need to understand the internal database.

## Golden path

After a human runs:

```bash
poldergraph init
```

the repository contains/updates a small PolderGraph section in `AGENTS.md` and optionally detected agent-specific instruction files.

For an agent, the expected flow is:

```text
question/task about repository
        |
        v
check PolderGraph index status
        |
        +-- stale --> poldergraph update --quiet
        |
        v
poldergraph context "<task/question>" --json
        |
        v
receive relevant user and project memories with grounded source context
        |
        v
read only the returned source locations needed
        |
        v
modify/test code normally
        |
        v
poldergraph update --quiet
```

If MCP is available, use MCP tools instead of shelling out.

### Project-level auto-index opt-out

Automatic structural indexing can be disabled or re-enabled explicitly for a
project. This does not delete its existing index or change global agent setup:

```bash
poldergraph agent-auto-index /path/to/project
poldergraph agent-auto-index /path/to/project --enable
```

The command creates or removes `.poldergraph-disable` at the detected project
root. `POLDERGRAPH_AUTO_INDEX=0` remains available as a global opt-out.

## MCP server

Command:

```bash
poldergraph mcp
```

Support stdio first because local coding agents commonly spawn MCP servers. An optional local HTTP transport may be offered separately.

### Required tools

#### `pg_status`
Returns index existence, freshness, root, model/dimensions, capabilities, counts and last update.

#### `pg_search`
Arguments:
- `query`
- `limit`
- filters: kinds, languages, roots, paths, provenance
- `include_semantic`
- `include_structural_context`

Returns ranked entities with score decomposition.

#### `pg_context`
Arguments:
- `query`
- `token_budget`
- optional filters
- optional `new_evidence_since` cursor from a previous response

Returns the same canonical context schema as CLI `context --json`.
The response includes an opaque `evidence_cursor`; pass it on the next task turn
to suppress already delivered chunks while allowing changed source evidence
through. The OMP adapter carries this cursor within a session automatically.

This is the preferred first tool for broad repository tasks.

#### `pg_entity`
Stable entity ID or resolvable symbol/path. Returns entity details and bounded neighborhood.

#### `pg_path`
Source/target plus structural-only/include-semantic options.

#### `pg_related`
Entity/query plus limit and filters.

#### `pg_impact`
Entity/path plus max depth and edge classes.

#### `pg_update`
Incrementally refreshes the graph. Must be safe for agents to invoke repeatedly.

#### `pg_find_tests`
Convenience query that returns structurally or lexically linked tests for symbols/files.

#### Shared memory tools

- `pg_memory_status`
- `pg_memory_search`
- `pg_memory_list`
- `pg_memory_add`
- `pg_memory_update`
- `pg_memory_forget`

`pg_context` automatically includes matching shared user preferences and
current-project memories under its existing token budget. Agents should save
lasting user preferences and well-supported project decisions when they become
clear, without interrupting the user. Do not save secrets or transient task
details. See [memory.md](memory.md) for the storage, scoping, vector retrieval,
CLI, and retention contract.

### Optional resources

Expose lightweight MCP resources when useful:
- `poldergraph://status`
- `poldergraph://communities`
- `poldergraph://entity/{id}`

Do not expose the entire graph as one giant resource.

## Tool response principles

Every response contains:
- stable IDs
- source path + line span when applicable
- evidence/provenance
- freshness
- truncation marker
- actionable errors

Never return thousands of nodes unless explicitly requested.

## Generated AGENTS.md block

`poldergraph setup-agent` inserts an idempotent fenced section:

```markdown
<!-- poldergraph:start -->
## PolderGraph repository intelligence

This repository uses PolderGraph for local structural and semantic code intelligence.

When a task depends on understanding repository structure, finding implementations,
tracing dependencies, locating tests, or estimating change impact:

1. Prefer the PolderGraph MCP tools when available.
2. Start with `pg_context`, which includes matching user preferences and project
   memories. Otherwise run:
   `poldergraph context "<your task or question>" --json`
3. If the result says the index is stale, run:
   `poldergraph update --quiet`
   then query again.
4. Use `poldergraph path "<A>" "<B>" --json` for relationship/path questions.
5. Use `poldergraph explain "<symbol>" --json` for a focused symbol.
6. Use `poldergraph impact "<symbol-or-path>" --json` before broad refactors.
7. Read/edit the actual source files returned by PolderGraph; do not treat semantic
   similarity as proof of a source-code dependency.
8. After substantial source changes, run `poldergraph update --quiet`.
9. When the user states a lasting preference or work establishes durable project
   knowledge, save it using `pg_memory_add` (or `poldergraph memory add`) with
   the correct scope. Do not store credentials or one-off task details.

Do not read `.poldergraph/index.sqlite3` directly.
<!-- poldergraph:end -->
```

If `AGENTS.md` exists, preserve all user content and replace only the fenced PolderGraph block.

## Agent-specific integration

Run `poldergraph setup` to detect agents available on the machine or already
configured in the repository. Detected agents are preselected; choose a
comma-separated list of agent names, `all`, or `none` at the prompt. Use
`poldergraph setup --agent codex --agent omp` or `poldergraph setup --all` for
non-interactive setup. Supported integrations are Claude Code, Cursor, GitHub
Copilot, Codex, Gemini CLI, OpenCode, and OMP.

`poldergraph setup-agent --all` configures every supported instruction mechanism:
- Claude Code
- Codex
- Cursor
- GitHub Copilot
- Gemini CLI
- OpenCode
- OMP/oh-my-pi compatible instruction/skill locations

For native OMP runtime integration, install the repository as an OMP plugin
using `omp install github:PolderLabs/PolderGraph`. See [omp.md](omp.md). The
plugin adds task context automatically and exposes focused graph tools; the
generated OMP skill remains a lightweight fallback when the extension is not
installed.

For Codex, run `poldergraph setup --agent codex` in the repository. This
installs a Codex skill in `.agents/skills/poldergraph/SKILL.md` and adds a
repository-scoped `poldergraph` MCP server to `.codex/config.toml` without
replacing other Codex settings. Codex project MCP servers require a trusted
repository; restart/reload Codex after setup. The server runs `poldergraph mcp`
from Codex's current workspace and queries the same local index as the CLI.
Initialize the index once with `poldergraph init` if it does not exist.

These adapters contain minimal guidance that points back to the canonical CLI/MCP contract. Avoid duplicating pages of instructions in each integration.

## MCP configuration generation

`poldergraph setup-agent` should print or write supported local MCP configuration where safe.

Codex setup writes TOML directly to the repository's `.codex/config.toml`,
using marker comments to keep repeated setup idempotent. Existing
`mcp_servers.poldergraph` configuration is left untouched; malformed TOML is
reported without overwriting the file.

The generated server command must point to the current `poldergraph` executable and current workspace root; it must not contain secrets.

## Exit codes

Stable exit codes are important for agents:
- 0 success
- 2 usage/config error
- 3 index missing
- 4 index stale when command explicitly requires fresh index
- 5 model/backend unavailable
- 6 index locked/busy
- 7 corrupt/incompatible index
- 8 partial result/degraded capability only when command cannot represent degradation in JSON

JSON mode must still return a structured error envelope.

## Agent-friendly JSON envelope

```json
{
  "ok": true,
  "command": "context",
  "index": {"fresh": true},
  "data": {},
  "warnings": [],
  "error": null
}
```

Errors:

```json
{
  "ok": false,
  "command": "context",
  "data": null,
  "warnings": [],
  "error": {
    "code": "INDEX_MISSING",
    "message": "No PolderGraph index found.",
    "remediation": "Run: poldergraph init"
  }
}
```

## Avoiding agent loops

Commands must be deterministic and concise.

- `update --quiet` prints nothing on success unless `--json`.
- A query must not tell the agent to recursively run the same query.
- Context output identifies exact next source files.
- Staleness checks should be cheap.
- MCP errors include one remediation step.

## Hooks

Optional hooks may keep indexes fresh, but they are not mandatory for correct use.

Supported optional patterns:
- post-checkout/update
- editor file-save integrations
- background `poldergraph watch`
- agent post-edit update

Do not install repository hooks silently. `setup-agent` requires an explicit
`--hooks` flag before writing Codex's `.codex/hooks.json` lifecycle integration.

## Safety and trust

Agents must be told:
- extracted/resolved structural edges are stronger evidence than semantic edges,
- ambiguous edges need source verification,
- semantic neighbors are retrieval hints,
- PolderGraph does not prove runtime behavior,
- actual modifications still require reading/testing the target code.
