# Benchmark methodology and results

## Retrieval benchmark

### Corpus

A small, realistic multi-module repository with predictable answers. Each case names a question, the entity that should be found, and the question class.

Question classes:
- **exact_implementation**: exact symbol lookup
- **synonym_concept**: concept-level synonym query
- **architecture**: module/subsystem overview
- **dependency_path**: how X reaches Y
- **tests_related**: tests linked to code
- **cross_document**: documentation connection
- **change_impact**: what breaks if X changes

### Metrics

- **Recall@K**: fraction of expected entities found in top-K results
- **MRR**: mean reciprocal rank of the first correct result
- **Precision@K**: fraction of top-K results that are correct
- **Context Precision**: precision of the context pack
- **Structural Path Correctness**: dependency_path cases have a valid path
- **Freshness Correctness**: index reports fresh when no changes pending

### Results (2026-10-07, CPU, 256d)

| Configuration | Recall@5 | MRR | Precision@5 | Latency |
|---|---|---|---|---|
| lexical_only | 0.812 | 0.750 | 0.392 | 0.6ms |
| hybrid | 0.917 | 0.775 | 0.275 | 118.8ms |
| semantic_only | 0.917 | 0.775 | 0.275 | 108.9ms |

**Conclusion**: hybrid retrieval (lexical + semantic) outperforms lexical-only on recall (+10.5pp) while maintaining acceptable latency. The hybrid default is justified.

## Embedding dimension comparison

The benchmark harness runs the same retrieval set at 128, 256, 512 and 768 dimensions, recording retrieval quality, DB size, vector size and latency.

Default 256 is a hypothesis to validate, not a sacred value. Run:

```bash
python tests/benchmarks/run_benchmarks.py
```

## Semantic edge calibration

The semantic edge policy uses a per-entity best-neighbour median to derive the threshold, then applies a 0.85 margin. On a small corpus (20 entities), the threshold settles around 0.72-0.78.

Metrics tracked:
- precision of displayed semantic edges
- degree distribution
- noisy hub rate
- mutual-neighbour benefit

Prefer fewer high-confidence semantic graph edges over visual hairballs.

## Performance targets

These are engineering targets enforced by benchmark tests:
- **Warm incremental update**: detect + parse + graph update should feel interactive
- **Query**: sub-second for exact/lexical; low-single-second for semantic/hybrid
- **Dashboard**: initial useful graph visible quickly; pan/zoom remains responsive
- **Memory**: do not require the complete graph plus all vectors duplicated in memory

## Security

Tests verify:
- path traversal blocked
- symlink escape blocked
- malicious filenames rejected
- HTML/script injection prevented in dashboard
- arbitrary file reads blocked through API