# Indexing and semantic processing

## Single command behavior

`poldergraph init` must:

1. locate repository/workspace root,
2. create `.poldergraph/`,
3. load defaults/config,
4. ensure an EmbeddingGemma 2 backend is usable,
5. discover files,
6. parse supported source languages,
7. build deterministic entities/relationships,
8. index documentation and supported media,
9. generate embeddings,
10. build the vector index,
11. create conservative semantic edges,
12. compute structural and hybrid communities,
13. compute graph metrics,
14. persist index metadata,
15. optionally generate agent integration if not already present,
16. print concise results and exact next commands.

No separate database/setup command should be required.

## File discovery

Respect:
- `.gitignore`
- nested gitignore rules
- `.ignore`
- `.poldergraphignore`
- configured include/exclude globs

Default exclusions include:
- `.git`
- `.poldergraph`
- `node_modules`
- build/dist/output directories
- virtual environments
- package caches
- generated vendored dependency trees
- minified bundles
- binary blobs without a supported media type

Generated code should be detected using path conventions, file headers and language metadata where possible. Keep generated files searchable only when configured; exclude them from default graph/community importance.

## Language support

Use tree-sitter-language-pack as the preferred grammar distribution. Implement language adapters for semantic extraction/resolution.

First implementation target must include strong adapters for:
- TypeScript
- TSX
- JavaScript
- JSX
- Python
- Rust
- Go
- Java
- C
- C++
- C#
- Kotlin
- Swift

Other tree-sitter-supported languages get baseline entities (files, definitions when generic queries support them) and lexical/semantic indexing even before advanced resolvers exist.

Language capability must be visible in `poldergraph status`.

## AST extraction

Each adapter defines:
- declarations
- nested ownership
- imports/exports
- call sites
- inheritance/interfaces
- type references
- decorators/attributes
- route/endpoint conventions where deterministic
- test relationships where deterministic

Do not regex source code when a syntax tree can provide the same fact.

## Symbol resolution

Resolution occurs after extraction.

Resolver inputs:
- local scope
- imports
- exports/re-exports
- module path rules
- package/module configuration
- language-specific namespace semantics
- overload/signature metadata where available

Resolution output:
- unique target -> `resolved`
- several plausible targets -> `ambiguous` edge candidates
- no local target -> external/unresolved symbol node only if useful for graph context

Never silently choose an arbitrary same-name target.

## EmbeddingGemma 2

Canonical model ID:

```text
google/embeddinggemma-2
```

The default local backend uses sentence-transformers/Transformers. Ollama is an optional adapter if a compatible local model endpoint is detected/configured.

Default semantic dimension: 256 using the model's Matryoshka-compatible truncation. Configuration supports 128, 256, 512 and 768 dimensions.

Use the model's documented retrieval task/prompt conventions; query embeddings and corpus embeddings must use their correct task roles.

Model revision, dimensions, normalization behavior and representation version must be recorded so stale vectors can be invalidated.

## Modalities

The implementation target includes:
- code
- plain text / Markdown
- documentation formats convertible to text
- PDF extracted text and page metadata
- images
- audio
- video

EmbeddingGemma 2's multimodal encoders must be loaded lazily. Indexing a source-only repository should not pay the memory/startup cost of unused visual/audio encoders.

### Images

Store image-level embeddings with file metadata. For documentation images, add a `contained_by`/document relationship where applicable.

No cloud OCR. Optional local OCR may augment lexical metadata but is not required for the embedding itself.

### Audio

Segment long audio into bounded overlapping windows according to model/runtime limits. Each segment stores start/end timestamps and maps to the parent file.

### Video

Use deterministic temporal sampling/segmentation appropriate for EmbeddingGemma 2 input support. Persist time ranges so search results can link to the relevant segment.

Do not decode an entire long video into RAM.

### PDFs

Index extracted text by page/section and embedded images where extraction is available. A PDF result must preserve page numbers.

## Incremental update algorithm

Every discovered file follows:

```text
unchanged fast metadata
  -> skip unless verification policy requires hash

changed/new
  -> content hash
  -> parse/extract
  -> diff entities
  -> resolve affected graph neighborhood
  -> compare semantic hashes
  -> embed only changed/new semantic inputs
  -> update vector rows
  -> recompute affected semantic neighbors
  -> invalidate affected communities/metrics
```

A source formatting change that does not alter normalized semantic input should not force re-embedding.

## Semantic neighbor/edge policy

Vector search exists independently of semantic graph edges. Do not materialize every nearest neighbor as an edge.

For each eligible entity:
1. retrieve configurable top-K nearest entities,
2. apply modality/kind filters where appropriate,
3. remove self/ownership trivialities,
4. require a minimum similarity derived from benchmark configuration,
5. prefer mutual-nearest-neighbor relationships,
6. cap semantic degree,
7. persist score and model metadata.

Thresholds must be benchmarked, not presented as universal constants.

Semantic edges primarily support visualization/community discovery; live semantic retrieval queries the vector index directly.

## Watch mode

`poldergraph watch`:
- watches roots,
- debounces/coalesces file events,
- handles atomic-save rename patterns,
- batches re-index work,
- retries a failed dirty batch and performs periodic reconciliation for missed events,
- holds a per-workspace supervisor lock while running and the writer lock only per batch,
- reuses its optional embedding backend across batches,
- publishes graph/index change events to the dashboard,
- remains responsive under rapid editor writes.

The index writer lock uses OS-level advisory locking on Linux/macOS and Windows. Automatic
startup from MCP and the query daemon, plus a polling fallback when native watching is
unavailable, are still being integrated.

## Git awareness

Optional but valuable metadata:
- current branch
- HEAD commit
- tracked/untracked status
- last modification commit per file when inexpensive

Git history is not required to build the graph. PolderGraph must work outside Git repositories.

## Progress reporting

TTY output displays compact progress by operation and counts. `--json` emits machine-readable progress/events and final statistics.

Never print one line per embedded entity by default.
