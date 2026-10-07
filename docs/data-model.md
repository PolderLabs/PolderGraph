# Canonical data model

The persistent model must make provenance explicit and allow exact incremental invalidation.

## Node/entity types

Core node kinds:

- `workspace`
- `repository`
- `directory`
- `file`
- `module`
- `namespace`
- `package`
- `class`
- `interface`
- `trait`
- `enum`
- `type_alias`
- `function`
- `method`
- `constructor`
- `property`
- `field`
- `constant`
- `variable` where language semantics make it useful
- `endpoint`
- `test`
- `document`
- `section`
- `image`
- `audio_segment`
- `video_segment`
- `unknown_symbol` for unresolved but useful references

Each entity has a stable ID derived from root identity + language + qualified semantic identity, not from database row order.

Suggested stable key:

```text
sha256(root_id + kind + language + normalized_path + qualified_name + semantic_discriminator)
```

Line numbers are not part of the stable identity.

## Entity fields

```text
id                    TEXT PRIMARY KEY
root_id               TEXT
kind                  TEXT
language              TEXT NULL
name                  TEXT
qualified_name        TEXT NULL
path                  TEXT NULL
parent_id             TEXT NULL
start_byte            INTEGER NULL
end_byte              INTEGER NULL
start_line            INTEGER NULL
end_line              INTEGER NULL
visibility            TEXT NULL
signature             TEXT NULL
docstring              TEXT NULL
content_hash           TEXT
semantic_hash          TEXT
is_generated           BOOLEAN
is_external            BOOLEAN
metadata_json          TEXT
created_at             INTEGER
updated_at             INTEGER
```

`content_hash` tracks source changes. `semantic_hash` tracks the exact normalized text/media input sent to the embedding model.

## Relationship model

Every edge stores:

```text
id
source_id
target_id
type
provenance
confidence
resolver
source_location
metadata_json
created_at
updated_at
```

### Structural edge types

At minimum:

- `contains`
- `defines`
- `imports`
- `exports`
- `calls`
- `constructs`
- `inherits`
- `implements`
- `overrides`
- `references`
- `reads`
- `writes`
- `returns_type`
- `accepts_type`
- `decorates`
- `routes_to`
- `tests`
- `documents`

Language adapters may add namespaced edge types, but generic consumers must work on the common set.

### Semantic edge type

- `semantically_related`

A semantic edge must never be translated into a structural edge based only on embedding similarity.

## Provenance

Required enum:

- `extracted` — syntax directly establishes the relationship
- `resolved` — source contains a reference and resolver maps it confidently to a target
- `inferred` — derived by a deterministic rule with incomplete direct syntax
- `ambiguous` — multiple plausible structural targets
- `semantic` — embedding similarity
- `manual` — user-defined future extension

Confidence is meaningful within provenance class; `extracted` generally uses 1.0.

## Embedding records

```text
embedding_id
entity_id
modality
model_id
model_revision
dimensions
task_type
input_hash
vector
norm
created_at
```

Do not overwrite embeddings from a different model revision/dimension in place. Their metadata is part of identity.

The default index uses normalized vectors. Cosine similarity can therefore use dot product where backend semantics permit.

## Semantic representation construction

For code entities, embed a structured textual representation rather than raw body alone:

```text
kind: method
language: typescript
symbol: AuthService.validateSession
path: src/auth/AuthService.ts

signature:
async validateSession(token: string): Promise<Session>

documentation:
Validate an existing session token.

code:
<entity body>
```

For file-level embeddings, include path, module docs and a bounded summary-like representation composed deterministically from exported symbols/signatures. Do not ask an LLM to summarize files.

For documentation sections, include heading ancestry.

## Chunks

Chunks are subordinate to entities:

```text
chunk_id
entity_id
ordinal
modality
content
content_hash
token_count
metadata_json
```

Use chunks only when content exceeds model/input policy or modality naturally requires segmentation. Search results are mapped back to their owning entity.

## File table

Store discovery metadata separately so incremental scans do not require entity reads:

```text
path
root_id
size
mtime_ns
content_hash
language
parse_status
last_indexed_at
```

mtime is only a fast-change hint; content hash is authoritative.

## Search/FTS data

FTS5 should index:

- entity name
- qualified name
- path
- signature
- docstring
- normalized semantic text

Exact symbol matching gets a dedicated index outside FTS scoring.

## Communities

```text
community_id
algorithm
mode              structural | hybrid
resolution
label
metadata_json
```

Membership:

```text
community_id
entity_id
weight
```

Hybrid community calculation must only include semantic edges that pass the configured high-confidence semantic-edge policy.

## Schema versioning

Store a monotonically increasing schema version and a separate index format version.

Migrations must:
- be transactional where SQLite permits,
- be idempotent with explicit preconditions,
- never delete the only copy of source-derived metadata without backup,
- trigger targeted reindex/re-embedding flags when representation semantics change.

## Deletion semantics

When a file is deleted:
1. delete or tombstone its owned entities,
2. remove outgoing edges,
3. remove incoming edges referencing those entities,
4. delete embeddings/chunks,
5. invalidate affected communities and metrics,
6. update unresolved references because a target may disappear.

A renamed file should preserve entity identity when git/file heuristics can confidently identify it; otherwise deletion + insertion is acceptable but must not leave stale edges.
