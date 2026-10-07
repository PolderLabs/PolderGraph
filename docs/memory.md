# Shared coding-agent memory

PolderGraph memory gives coding agents persistent context across sessions while
keeping project knowledge separate and local. One SQLite database belongs to the
current OS user. It contains user-wide preferences and facts plus project-scoped
notes keyed by the canonical absolute workspace root.

## Storage and privacy

The default store is provided by `platformdirs`:

- Linux: `$XDG_DATA_HOME/PolderGraph/memory.sqlite3`, falling back to
  `~/.local/share/PolderGraph/memory.sqlite3`
- macOS: `~/Library/Application Support/PolderGraph/memory.sqlite3`
- Windows: `%LOCALAPPDATA%\PolderLabs\PolderGraph\memory.sqlite3`

Set `POLDERGRAPH_MEMORY_DB` to use a different database path. The parent
directory is created with user-only permissions where the platform supports
POSIX modes. SQLite uses WAL and a five-second busy timeout. Memory content is
never written into the repository and is never sent to a remote service.

Project records include the local absolute project path so another project
cannot retrieve them. User-scoped records are intentionally visible in every
project. Moving a checkout changes its project identity; use `--scope user` for
preferences and cross-project knowledge. This is a per-user local database, not
a sync or team store.

PolderGraph rejects common credential formats and private-key blocks. Agents
must not save passwords, API keys, private keys, transient task details, or
private data that is not useful for future coding work. The user can inspect,
edit, export through JSON output, or delete entries at any time.

## Record structure

Each record includes a stable ID, scope, type, text, tags, creation/update times,
and (for project scope) a project root. Types are `fact`, `preference`,
`decision`, `workflow`, and `reference`. Re-adding the same normalized text to
the same scope is idempotent and updates its type/tags rather than duplicating
it.

The central store keeps vectors separate from code-index vectors. It reuses the
active local project embedding backend when one is available; standalone memory
commands use local EmbeddingGemma 2. Memory text uses the document embedding
role and task queries use the query role. Vector tables include model revision
and dimensions in their identity, so memories work across projects even when
they use different embedding backends. Retrieval uses sqlite-vec when available
and a bounded in-process brute-force fallback otherwise. Results combine
semantic neighbors with FTS5 keyword matches, prefer project-scoped notes when
scores tie, and cap results before they enter agent context. If the embedding model is
unavailable, keyword search remains available and reports that it degraded.
Lexical matching removes common stop words, uses token boundaries and a small
set of common inflections, and requires meaningful term coverage. Semantic-only
matches must clear a conservative similarity threshold. High-coverage exact
keyword matches skip embedding inference, which improves latency and avoids
weak embedding neighbors crowding out precise evidence.

## Automatic agent flow

OMP and Codex receive matching user/project memories automatically in
`poldergraph context` / `pg_context` before repository work. Context packing
counts memory text against the same token budget and marks truncation. An
explicit first-person statement such as “I prefer concise answers” is captured
as a user preference during context construction. This local deterministic
extractor does not send prompts elsewhere and ignores task-specific statements
such as “for this task.” Agents also receive memory tools for direct search and
maintenance. Generated instructions tell agents to save stable user preferences
and non-obvious project decisions when they become clear, without interrupting
the user. Agents must not write speculative facts or one-time task data.

Project decisions are not inferred from arbitrary task prose; the coding agent
must save them when it establishes durable, evidence-backed knowledge.
Automatic recall and explicit first-person preference capture do not depend on
the agent remembering to search or write first.

## CLI

```bash
poldergraph memory status
poldergraph memory add "Prefer concise explanations" --scope user --kind preference --tag style
poldergraph memory add "Use the shared settings loader" --scope project --kind decision
poldergraph memory search "where should I add config" --json
poldergraph memory list --scope all --json
poldergraph memory update mem_123 --content "Updated durable note"
poldergraph memory forget mem_123
```

`--scope all` means user memories plus only the current project's records; it
never returns records from other projects. Use `--lexical-only` for a memory
search that should skip local vector inference. `--root PATH` selects a project
scope when running the command outside that project.

## MCP tools

- `pg_memory_status`: central store path and visible-scope counts.
- `pg_memory_search`: hybrid semantic/keyword recall with scope and result cap.
- `pg_memory_list`: list accessible memories.
- `pg_memory_add`: save a project fact/decision or user preference.
- `pg_memory_update`: edit an accessible record and refresh its vector.
- `pg_memory_forget`: delete an accessible record and its vectors.

Every memory MCP tool uses the existing JSON envelope. `pg_context` also
includes retrieved memories automatically; direct memory search is useful when
the agent wants to inspect additional preferences or older decisions.

## OMP and Codex

The OMP extension injects budgeted `context` (including memory) before each
agent task and exposes memory search, save, update, and forget tools. Its
instructions say to persist stable preferences and durable repository
knowledge as the task progresses.

Codex uses the same project-scoped MCP server. `pg_context` automatically
recalls memory and the generated PolderGraph skill explains when to call
`pg_memory_search`, `pg_memory_add`, `pg_memory_update`, and
`pg_memory_forget`. Run `poldergraph setup --agent codex` to refresh the skill
and MCP configuration after upgrading.
