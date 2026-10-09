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
## Freshness barrier latency (2026-10-09)

Measured on the checked-out 195-file PolderGraph repository on Linux, Python 3.12.14, CPU, with 40 warm lexical queries (`authentication session`). The index was refreshed using `uv run poldergraph update --no-embed`; these measurements exercise structural/lexical retrieval and the filesystem freshness barrier, not semantic embedding latency.

| Freshness check | p50 | p95 |
|---|---:|---:|
| Reuse directory snapshot between unchanged queries | 17.41 ms | 27.26 ms |
| Rediscover directories on every query | 37.44 ms | 69.64 ms |

The unchanged-query path was 2.15x faster at p50 and 2.55x faster at p95 in this run. These are one-machine baseline measurements, not a cross-platform performance guarantee.

Reproduce from the repository root:

```bash
uv run poldergraph update --no-embed
uv run python scripts/benchmark_freshness.py . --samples 40
```

The harness fails if any sample is stale, so it cannot silently record latency for an invalid freshness state.

## Context planner benchmark

The planner comparison uses the synthetic multi-module repository in
`tests/benchmarks/corpus_manifest.json`, plus two explicit abstention cases
(`Hello!` and `What is the weather?`). Each request runs 30 times. Both
configurations use the same offline lexical/structural index and expected
entity annotations (300 requests total per configuration):

- **Adaptive planner** calls `QueryService.context` with a 6,000-token caller
  ceiling. The task planner selects its intent, lanes, and effective budget.
- **Fixed baseline** runs one lexical/structural search and packs with a
  3,000-token budget, matching the former fixed-budget OMP behavior.

The report records estimated content tokens, p50/p95 and mean wall latency,
internal search-call count, expected-entity case recall, and expected-entity
precision among returned context entity/snippet names. The planner benchmark
can be reproduced with:

```bash
uv run python tests/benchmarks/benchmark_context_planner.py --repeats 30
```

The Linux/Python 3.12.14 run on 2026-10-09 kept expected-entity case recall
equal at 0.875 and reduced mean estimated tokens from 1,026 to 520 per
request. Expected-entity precision rose from 0.104 to 0.237; mean latency rose
from 3.1 ms to 4.0 ms and p95 from 5.5 ms to 7.2 ms. Adaptive context avoided
retrieval for greetings and the unrelated weather prompt. This dataset is small
and synthetic. Entity overlap
is only an evidence-selection proxy; it is not answer grounding judged by a
model, end-to-end task completion, or developer productivity. The semantic
channel is intentionally disabled to isolate the deterministic planner and
packing path. Latencies are machine-specific. A real task benchmark still
needs paired coding-agent runs and independent answer/task evaluation.

## Watcher contention benchmark

`tests/benchmarks/benchmark_watcher_contention.py` creates a structural-only
index, runs three concurrent readers (40 searches each), and writes the same
source file 100 times at 3 ms intervals while the supervised watcher is live.
It waits for the final revision to appear, and reports read errors, p50/p95/max
latency, wall time, and process CPU time. Run five isolated samples with:

```bash
uv run python tests/benchmarks/benchmark_watcher_contention.py --repeats 5
```

In the Linux/Python 3.12.14 run on 2026-10-09, all five runs indexed the final
revision and completed all 120 reads without errors. Median burst+reconcile
wall time was 1.050 s, process CPU time was 0.293 s (0.29 CPU cores average),
read p50/p95 were 3.6/9.9 ms, and the worst single read across runs was 23.7
ms. During each 2-second idle observation, median process CPU use was 0.0011 s
(0.0006 CPU cores average). This supplies a local contention observation, not
a cross-platform CPU or starvation guarantee; the harness intentionally
reports measurements instead of imposing machine-dependent latency thresholds.
CI separately runs the functional 100-write/three-reader scenario on supported
operating systems. A separate live supervisor test switches between two Git
branches and verifies that each checked-out symbol appears while the other is
removed from the index; rename and delete propagation are covered as well.

## Rust graph traversal proof of concept

`research/rust_graph_poc/` contains a dependency-free Rust CSR breadth-first
traversal and an equivalent Python list-of-lists baseline. Both generate the
same deterministic graph and compare traversal checksums at 100, 10,000, and
100,000 nodes; the harness exits if results differ. Reproduce on Linux with
Rust/Cargo installed:

```bash
python research/rust_graph_poc/benchmark.py --repeats 7
```

On Linux x86_64, Python 3.12.14 / Rust 1.99.0, seven samples per size agreed
exactly. At 100,000 nodes and 800,000 edges, Rust CSR reached the same results
with 19.5 ms traversal p50 vs 424.0 ms for Python (21.8x), 36.2 ms vs 465.6 ms
p95 (12.9x), and 8.7 MiB vs 47.5 MiB peak RSS (5.5x lower). Process wall p50,
including startup and graph construction, was 28.8 ms vs 611.7 ms. The release
binary built offline with no external crates in 0.631 seconds after a clean
target.

This is only one traversal primitive on synthetic regular graphs. It does not
include parsing, indexing, SQLite, Python/Rust FFI, or EmbeddingGemma, and the
Python baseline is idiomatic rather than an optimized PolderGraph hot path.
It shows that Rust is promising for this isolated kernel; it does not establish
end-to-end product gains or justify a full rewrite. The next useful check is to
profile real workloads, then compare one representative production path with
golden output and database parity.
