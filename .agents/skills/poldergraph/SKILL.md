---
name: poldergraph
description: Use PolderGraph's local structural and semantic code graph to find implementations, trace relationships, locate tests, and estimate change impact in this repository.
---

<!-- poldergraph:start -->
## Use PolderGraph for repository intelligence

Before broad source exploration, use the `poldergraph` MCP tools when available, starting
with `pg_status` and `pg_context` for the current task. Context automatically includes
relevant shared user preferences and memories scoped to this project. If MCP is
unavailable, run `poldergraph context "<task>" --json`. Refresh a stale index with
`pg_update` or `poldergraph update --quiet` and query again.

`pg_context` retrieves matching memories and automatically captures explicit first-person
preferences such as “I prefer concise answers.” Do not redundantly save those. When a task
establishes a durable project decision, save it with `pg_memory_add(scope="project")`;
search prior notes with `pg_memory_search` before making decisions. When a user corrects a
previous preference, update or forget the older note instead of keeping conflicting versions.
Never store credentials, private keys, or one-off task details.

Use `pg_path`, `pg_entity`, `pg_impact`, and `pg_find_tests` for focused graph
questions. Read the cited source files before drawing conclusions; semantic
similarity is a retrieval hint, not proof of a dependency. After edits, call
`pg_update` when MCP is enabled; otherwise run `poldergraph update --quiet`.
<!-- poldergraph:end -->
