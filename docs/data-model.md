# Data model reference

This document describes the canonical data model as implemented. The design
intent lives in [data-model.md](data-model.md); this file is the reference for
what the code actually stores.

## Identity

Every entity ID is derived from semantic identity, never from storage order:

```
sha256(root_id | kind | language | normalized_path | qualified_name | discriminator)
```

rendered as `<kind>:<32 hex chars>`. Line and byte positions are excluded, so
moving a definition inside its file keeps its ID. Overloads in one file are
separated by a `discriminator` derived from the declaration's byte offset.

`normalize_path` converts backslashes to forward slashes and strips `./` and
leading/trailing separators, so the same logical path written differently yields
the same ID.

### Line base

Line numbers are **1-based** throughout the public surface — stored spans, CLI
output, JSON envelopes, the HTTP API and MCP payloads. This matches `grep -n`
and every editor, so an indexed line can be used directly.

Tree-sitter reports 0-based coordinates. Adapters copy those coordinates
straight off the syntax node, so `ParseEngine.parse` converts them once, at the
single boundary every adapter returns through, rather than at ~20 adapter call
sites. Anything slicing a file by a stored span must subtract 1 to get a list
index. Columns stay 0-based, matching the byte/column convention.

## Entity

`entities` table columns:

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT | Primary key, stable |
| `root_id` | TEXT | Owning workspace root |
| `kind` | TEXT | See the kind enum below |
| `language` | TEXT | Parser language key |
| `name` | TEXT | Simple name |
| `qualified_name` | TEXT | Dotted qualified name |
| `path` | TEXT | Root-relative POSIX path |
| `parent_id` | TEXT | Owning entity, NULL at file level |
| `start_byte`, `end_byte` | INTEGER | Byte span in the source file |
| `start_line`, `end_line` | INTEGER | **1-based** inclusive line span, as editors and `grep -n` report |
| `visibility` | TEXT | `public` / `private` / `protected` where known |
| `signature` | TEXT | Declaration head, without the body |
| `docstring` | TEXT | Leading docstring or doc comment |
| `content_hash` | TEXT | SHA-256 of raw file bytes |
| `semantic_hash` | TEXT | SHA-256 of the normalized embedding input |
| `is_generated` | INTEGER | 1 when detected as generated |
| `is_external` | INTEGER | 1 for external/unresolved symbols |
| `metadata_json` | TEXT | Adapter-specific extras |
| `created_at`, `updated_at` | INTEGER | Unix seconds |

`content_hash` drives change detection; `semantic_hash` decides whether a file
must be re-embedded. A reformat that leaves the semantic representation intact
keeps the same `semantic_hash` and therefore does not trigger re-embedding.

### Entity kinds

`workspace`, `repository`, `directory`, `file`, `module`, `namespace`,
`package`, `class`, `interface`, `trait`, `enum`, `type_alias`, `function`,
`method`, `constructor`, `property`, `field`, `constant`, `variable`,
`endpoint`, `test`, `document`, `section`, `image`, `audio_segment`,
`video_segment`, `unknown_symbol`.

Language adapters may emit namespaced kinds for adapter-specific detail;
generic consumers work on the set above.

## Edge

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT | `edge:` + hash(source, type, target, provenance, resolver) |
| `source_id`, `target_id` | TEXT | Entity IDs |
| `type` | TEXT | See the taxonomy below |
| `provenance` | TEXT | `extracted`/`resolved`/`inferred`/`ambiguous`/`semantic`/`manual` |
| `confidence` | REAL | Meaningful within the provenance class |
| `resolver` | TEXT | Resolution strategy: `same_file`, `cross_file`, `local`, `vector_knn` |
| `source_path`, `source_line`, `source_col` | | Where the relationship was seen |
| `metadata_json` | TEXT | Model/revision/threshold for semantic edges |

On the wire, edges carry both `source`/`target` (the dashboard and MCP contract)
and `source_id`/`target_id` (the database column names).

### Resolution scope

Name resolution never crosses a language boundary. A JavaScript
`headers.delete()` must not bind to a Python `def delete(...)`: the resulting
edge would be syntactically plausible and semantically false, which is worse for
a consuming tool than a missing edge. An unclassified (`NULL`) language is not a
match either, so an unknown file binds only to another unknown one.

The exceptions are dialects that genuinely call into each other: TypeScript/TSX
into JavaScript, and the C family (`c`/`cpp`/`csharp`).

`resolver` records what actually happened, not merely that something resolved.
Most references resolve inside the file that makes them and are labelled
`same_file`; only genuine cross-file resolution is `cross_file`. A consumer that
wants to know whether a dependency is local can trust this field.

### Edge types

Structural: `contains`, `defines`, `imports`, `exports`, `calls`,
`constructs`, `inherits`, `implements`, `overrides`, `references`, `reads`,
`writes`, `returns_type`, `accepts_type`, `decorates`, `routes_to`, `tests`,
`documents`, `contained_by`, `describes`.

Semantic: `semantically_related`.

A semantic edge is never translated into a structural edge. `STRUCTURAL_EDGE_TYPES`
and `SEMANTIC_EDGE_TYPES` are disjoint frozensets, and callers must opt into
semantic edges explicitly.

### Provenance

| Value | Meaning | Default confidence |
|---|---|---|
| `extracted` | Syntax directly establishes it | 1.0 |
| `resolved` | Resolver mapped a reference confidently | 0.9 |
| `inferred` | Deterministic rule over incomplete syntax | 0.6 |
| `ambiguous` | Several plausible targets | 0.4 |
| `semantic` | Embedding similarity | 0.5 |
| `manual` | User-defined extension | 1.0 |

## Embeddings

`embeddings` rows record `entity_id`, `modality`, `model_id`,
`model_revision`, `dimensions`, `task_type`, `input_hash` and `norm`. The
embedding ID is a hash of `(entity_id, model_id, revision, dimensions, task,
input_hash)`, so a revision or dimension change creates a new identity instead
of overwriting an existing vector.

Vectors are stored in a `vec0` virtual table named
`vec_<model>_<task>_<dimensions>` (default `document` task), with a readable
shadow table `<name>_vectors` holding the same float32 blobs. The shadow table
exists because a `vec0` table cannot be selected from to recover a raw vector,
and neighbour-of-entity queries need exactly that.

Vectors are L2-normalized on write, so `cos = 1 - d²/2` converts sqlite-vec's
L2 distance exactly.

## Communities

`communities` is keyed by `(community_id, algorithm, mode)` where mode is
`structural` or `hybrid`. Membership lives in `community_members` with the same
key plus `entity_id`. Both are replaced wholesale on each graph stage.

Hybrid communities include only semantic edges that pass the configured
threshold.

## Other tables

- `files` — discovery metadata keyed by `(root_id, path)` with `size`,
  `mtime_ns`, `content_hash`, `language`, `parse_status`. Incremental scans read
  this table, not entities.
- `metrics` — per-entity `metric`/`value` pairs (`degree`, `in_degree`,
  `out_degree`, `pagerank`, optional `betweenness`), invalidated by a graph
  fingerprint.
- `unresolved_refs` — references with no unique target, storing the candidate
  list so ambiguity is preserved rather than guessed.
- `change_events` — bounded log consumed by the dashboard SSE stream.
- `entity_fts` — FTS5 mirror of name, qualified name, path, signature,
  docstring and normalized semantic text, with per-column BM25 weights.
- `meta` — schema version, index format version, representation version, last
  scan time, indexed HEAD, metric cache key.

Coding-agent memories live in a separate centralized per-user SQLite database
under the OS application-data directory. This intentionally keeps user
preferences and private memory data out of every repository index. Each project
record is scoped by the resolved workspace root; user-scoped records are
available in all projects. Memory vectors use a separate `memory` vector task
table in that same central database.

## Versions

`SCHEMA_VERSION` tracks table layout. `INDEX_FORMAT_VERSION` tracks the meaning
of stored representations; a bump invalidates derived data. `REPRESENTATION_VERSION`
tracks the semantic-text construction so targeted re-embedding happens when the
representation changes.

`poldergraph doctor` verifies: SQLite integrity, schema and format versions,
orphan edges, orphan embeddings, acyclic parent chains, in-file line spans, FTS
namespace consistency, vector dimensions, unit norms, and path safety.
