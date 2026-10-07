# Testing, performance, security and quality bar

PolderGraph must be trustworthy enough that coding agents can rely on it without treating every result as magic.

## Test layers

### Unit tests
Cover:
- ignore/discovery semantics
- stable entity IDs
- semantic representation normalization
- language adapters
- symbol resolution
- provenance assignment
- incremental invalidation
- rank feature calculations
- context budgeting/deduplication
- config precedence
- JSON schemas
- path safety

### Parser fixture tests
Every strong language adapter gets fixtures for:
- nested declarations
- imports/re-exports
- aliases
- methods/calls
- inheritance/interfaces
- overloads/generics where relevant
- ambiguous names
- parse errors/incomplete editor syntax

Expected graph snapshots must be reviewable and deterministic.

### Integration tests
Build indexes for representative multi-file repositories and assert:
- exact node/edge counts within fixture contract
- cross-file resolution
- no stale edges after update/delete/rename
- vector rows match entity semantic hashes
- FTS/vector/graph retrieval agree on canonical IDs
- communities can be persisted/reloaded
- MCP/CLI/API return equivalent semantics

### Dashboard E2E
Use browser automation for:
- graph loads
- search focus
- local graph expansion
- filters
- path visualization
- inspector navigation
- layout controls
- live update behavior
- keyboard navigation

### Agent contract tests
Spawn MCP server and verify every tool schema/response. Test a synthetic agent workflow:
1. status
2. context query
3. update after fixture edit
4. impact query
5. path query

## Retrieval benchmark corpus

Maintain a checked-in benchmark manifest with repositories/fixtures and natural-language questions.

Question classes:
- exact implementation location
- synonym/concept query
- architecture/subsystem
- dependency/path
- tests related to code
- cross-document/code connection
- change impact
- multimodal lookup

Metrics:
- Recall@K
- MRR
- nDCG@K where graded relevance exists
- context precision
- structural path correctness
- index freshness correctness

Benchmark separately:
- lexical only
- embedding only
- structural only
- hybrid

A hybrid default should remain only if it measurably outperforms simpler baselines.

## Embedding dimension benchmark

Run the same retrieval set at 128/256/512/768 dimensions. Record:
- retrieval metrics
- DB/vector size
- embedding/search latency
- memory use

Default 256 is a hypothesis to validate, not a sacred value.

## Semantic-edge calibration

Materialized semantic edges are visualization/clustering aids. Benchmark thresholds using labeled related/unrelated entity pairs.

Track:
- precision of displayed semantic edges
- degree distribution
- noisy hub rate
- mutual-neighbor benefit

Prefer fewer high-confidence semantic graph edges over visual hairballs.

## Performance targets

These are engineering targets and should be enforced by benchmark tests on documented hardware classes.

### Warm incremental update
For one edited normal-sized source file:
- detect + parse + graph update should feel interactive
- only affected semantic entities are re-embedded
- dashboard receives update without full reload

### Query
For a warmed local index:
- exact/lexical search: sub-second target
- semantic/hybrid search: interactive sub-second to low-single-second depending on hardware/index size
- neighborhood/path: sub-second for ordinary bounded queries

### Dashboard
- initial useful graph visible quickly without loading entire huge graph
- pan/zoom remains responsive
- layout computation off UI thread
- API payloads are bounded and cancellable

### Memory
Do not require the complete graph plus all vectors duplicated in Python memory for routine queries.

## Scale test tiers

Include generated/reproducible corpora around:
- 1k entities
- 10k
- 100k
- 500k+
- monorepo with many roots/packages

Tests should reveal where aggregation/backend changes become necessary instead of pretending all sizes behave equally.

## Index correctness invariants

A healthy index must satisfy:
- every edge endpoint exists
- every embedding references an existing entity/chunk
- vector dimensions equal recorded dimensions
- normalized vectors are approximately unit norm
- no entity source span lies outside its file
- parent chains are acyclic
- stable IDs do not change for line-only movement
- deleted source entities cannot appear in search
- FTS and vector IDs map to same canonical entity namespace

`poldergraph doctor` verifies these.

## Security threat model

Inputs are untrusted repositories.

Protect against:
- path traversal
- symlink escape
- malicious filenames/control characters
- giant files / decompression bombs
- malformed parsers/media
- HTML/script injection into dashboard
- arbitrary file reads through API
- unsafe shell invocation
- network exfiltration
- model/cache poisoning assumptions
- denial of service from pathological graph fan-out

### Parser execution
Prefer in-process trusted parser libraries; isolate external media helpers where appropriate. Set file size/time/resource limits.

### Dashboard
Loopback by default. Escape all labels/content. API may only access indexed roots.

### Subprocesses
Never build shell strings from repository content. Pass argv arrays and enforce timeouts.

### Network
No indexed content is sent remotely under default configuration.

## Determinism

Given the same source tree, config, parser/model revisions and platform-compatible runtime:
- entity IDs are stable
- structural graph is deterministic
- semantic vectors may have minor floating-point variation but rankings should remain within tolerances
- dashboard layout is not required to be pixel deterministic

## CI

Required checks:
- lint/format
- type check
- unit/integration tests
- parser fixture tests
- frontend type/test/build
- MCP contract tests
- packaging smoke test
- Linux/macOS/Windows matrix where native dependencies support it
- minimal offline index/query test with cached tiny fixture/model substitute

Heavy full-model benchmarks can run separately from every PR but must be reproducible.

## Release quality gate

Do not call a release ready if:
- init needs undocumented manual DB setup
- MCP tool schemas drift from docs
- an update can leave stale deleted nodes
- semantic edges are displayed as structural facts
- dashboard reads arbitrary filesystem paths
- JSON responses are unstable/unversioned
- model revision/dimensions are not recorded
- AGENTS.md modification is non-idempotent
