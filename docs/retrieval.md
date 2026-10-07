# Retrieval, graph algorithms and context assembly

PolderGraph answers repository questions by combining independent evidence channels. No single channel is authoritative for every task.

## Retrieval channels

### Exact symbol/path lookup
Highest priority for exact identifiers, qualified names and paths. Exact symbol matches must not be buried by semantic ranking.

### Lexical retrieval
SQLite FTS5 over symbol names, signatures, docs, paths and normalized semantic text.

### Semantic retrieval
EmbeddingGemma 2 query vector against the local vector index. Query and corpus use the model's documented retrieval task roles and identical dimensions.

### Structural retrieval
Graph traversal over deterministic relationships such as calls/imports/inheritance/containment/references.

## Hybrid query flow

```text
user/agent query
      |
      +--> exact identifier/path detection
      |
      +--> lexical candidate retrieval
      |
      +--> semantic candidate retrieval
      |
      +--> merge + normalize evidence
      |
      +--> graph expansion around strong candidates
      |
      +--> structural/importance features
      |
      +--> rerank
      |
      +--> redundancy removal
      |
      +--> token-budget-aware context pack
```

## Candidate fusion

Do not hard-code unvalidated universal weights. Implement a configurable scoring model with sane defaults and benchmark it.

Candidate features should include:
- semantic similarity
- lexical/FTS score
- exact-name boost
- exact-path boost
- graph distance from other high-confidence candidates
- edge provenance
- entity degree/PageRank-like importance
- public/exported API status
- entity kind prior
- same-community affinity
- recency/change hint only where relevant

A default weighted ranker is acceptable, but all feature contributions must be inspectable in debug output.

`poldergraph search --explain-score` should show why an item ranked.

## Query intent hints

The query planner may detect:
- exact symbol lookup
- "where" questions
- "how does X reach Y" path questions
- architecture/subsystem questions
- semantic concept search
- change-impact questions

Intent detection must be deterministic/heuristic and never require an LLM.

## Graph expansion

After selecting seed entities, expand only a bounded neighborhood.

Expansion policy should consider edge type:
- calls/imports/inherits/implements: high structural value
- contains/defines: ownership context
- references: useful but potentially high fan-out
- semantic: disabled or strongly bounded during structural expansion because semantic candidates were already retrieved from the vector index

Expansion has:
- max hops
- per-node fan-out cap
- total node cap
- edge-type allow/deny list
- provenance filter

## Path search

`poldergraph path A B` resolves A/B to entities then computes:
- unweighted shortest path by default
- optional weighted path where extracted/resolved structural edges cost less than inferred/semantic edges
- `--structural-only`
- `--include-semantic`

Path output always prints edge type and provenance.

## Explain

`poldergraph explain <entity>` returns:
- identity/location/signature
- ownership
- inbound/outbound structural relations grouped by type
- related docs/media
- strongest semantic neighbors
- community memberships
- graph importance metrics
- compact source excerpt
- unresolved/ambiguous relationships relevant to the entity

No generative prose is required. Output should be structured enough for humans and agents.

## Related

`poldergraph related <entity>` is primarily vector similarity, with optional graph-aware reranking. It must make clear whether two nodes are structurally connected.

## Impact analysis

`poldergraph impact <entity-or-path>` traverses reverse dependency edges with configurable edge classes. It answers "what may be affected if this changes?" without pretending to prove runtime impact.

Output classifies:
- direct structural dependents
- transitive dependents
- tests
- related docs
- semantically related but structurally unlinked items

## Context command

`poldergraph context "<question>" --budget <tokens> --json` is the main agent primitive.

Required JSON shape:

```json
{
  "query": "how does login work?",
  "index": {
    "root": ".",
    "head": "optional git sha",
    "fresh": true,
    "model": "google/embeddinggemma-2",
    "dimensions": 256
  },
  "entities": [],
  "relationships": [],
  "snippets": [],
  "paths": [],
  "communities": [],
  "unresolved": [],
  "retrieval": {
    "semantic": true,
    "lexical": true,
    "structural": true
  },
  "token_estimate": 0,
  "truncated": false
}
```

Each entity/snippet includes stable ID, qualified name, path and line span.

The context pack should maximize distinct useful evidence, not simply concatenate top-K chunks. Prefer:
1. exact/central entry points,
2. short definitions/signatures,
3. critical neighboring entities,
4. implementation excerpts,
5. related docs/tests,
6. lower-confidence semantic context.

## Token budgeting

Budget is a hard upper bound except for a small documented envelope for JSON framing.

Use deterministic token estimation for the configured downstream tokenizer when known; otherwise use a conservative approximation.

Deduplicate:
- overlapping code spans
- parent/child snippets containing the same text
- repeated relationship descriptions
- equivalent path segments

## Community detection

Maintain two community views:

### Structural
Only extracted/resolved/inferred structural edges. Represents implementation topology.

### Hybrid
Structural edges plus only high-confidence materialized semantic edges. Represents conceptual topology.

Use Leiden through igraph/leidenalg for scalable clustering.

Community labels must be generated without an LLM using representative:
- symbol names
- paths
- high-centrality entities
- lexical terms

## Graph metrics

Compute/cache:
- degree/in-degree/out-degree by edge class
- PageRank or equivalent centrality
- betweenness only when scale permits or on sampled/subgraphs
- community membership
- articulation/bridge-like signals where useful

Do not block normal indexing on quadratic metrics for huge graphs.

## Freshness

Every query returns index freshness information.

Fresh:
- tracked source state matches indexed hashes, or watcher has processed all events.

Possibly stale:
- source metadata changed after last scan.
- current Git HEAD differs from recorded state.

Agents must see this flag. If stale, recommended behavior is `poldergraph update --quiet` before deep repository questions.
