# Rust core evaluation: maintain, hybrid, or rewrite

Recommendation for [issue #39](https://github.com/PolderLabs/PolderGraph/issues/39).
This is a research spike, not a rewrite commitment. Every number below was
produced by a script in this repository.

## Evidence

| Source | Command |
|---|---|
| Python stage profile | `python scripts/benchmark_indexing_profile.py --files 2000 --repeats 3` |
| Rust CSR traversal POC | `python research/rust_graph_poc/benchmark.py --repeats 7` |

Both run offline on Linux x86_64, CPython 3.12.14.

### Where Python indexing time actually goes

Generated 2,000-file multi-module Python corpus; 2,013 files, 10,013 entities,
12,000 edges, 18.2 MB index, ~440 MB process peak RSS.

| Stage | Wall (ms) | CPU (ms) | Share of indexing |
|---|---|---|---|
| Discovery | 44.8 | 39.4 | 0.5% |
| Parsing | 337.3 | 325.6 | 4.1% |
| **Index and persist** | **7,131.6** | 6,875 | **87.2%** |
| Graph stage (metrics/communities) | 677.1 | 1,805.3 | 8.2% |

Query-side latency on that index (3 repeats, mean): exact search 41.2 ms, lexical
30.6 ms, FTS 32.9 ms, context build 29.1 ms, graph impact 26.5 ms, graph path
27.9 ms.

Not measured here, and deliberately not estimated: the embedding stage (no cached
EmbeddingGemma 2 weights) and any GPU figure. The Leiden backend *is* installed
and the graph stage above includes it — note its CPU time (1,805 ms) far exceeds
its wall time (677 ms), i.e. that stage is already multi-threaded native work.

### Option A: optimize the existing Python

Profiling showed persistence, not traversal, is the bottleneck, and a large part
of it was one SQLite transaction — and therefore one fsync — per file. Batching
`PERSIST_BATCH_SIZE = 64` files per transaction removed that:

| Configuration | Persist stage (ms) | Indexing total |
|---|---|---|
| One transaction per file (before) | 9,434.3 | 10,451 |
| 64 files per transaction | 7,131.6 | 8,182 |
| 256 files per transaction | 7,025 | 8,084 |
| 512 files per transaction | 6,950 | 8,009 |

**24.4% faster end to end**, with correctness unchanged: each batch is still
all-or-nothing, and `tests/unit/test_persist_batching.py` covers multi-batch
persistence, rollback on a mid-run failure, and no duplication on re-index.

Larger batches buy almost nothing (a further ~2% for 8x the rollback
granularity), so 64 is the shipped value. The remaining ~7.1 s is genuine
per-row SQLite and Python work — upserts, FTS indexing, and entity bookkeeping
— which is exactly the kind of loop a native rewrite *could* accelerate.

### Option B/C: the Rust traversal POC

At 100,000 nodes / 800,000 edges, depth-limited BFS, identical checksums:

| Metric | Rust CSR | Python list-of-lists | Ratio |
|---|---|---|---|
| Traversal p50 | 19.48 ms | 424.03 ms | **21.8x** |
| Traversal p95 | 36.23 ms | 465.58 ms | **12.9x** |
| Process wall p50 | 28.84 ms | 611.73 ms | 21.2x |
| Peak RSS p50 | 8,908 KB | 48,640 KB | **5.5x lower** |

## Verdict against the issue's proposed gates

The issue proposed: ≥1.5x on an important CPU-bound operation **or** ≥25% lower
non-model peak RSS, with no correctness regression, net of two runtimes.

| Gate | Met? | Evidence |
|---|---|---|
| ≥1.5x on an important CPU-bound op | **Yes, narrowly** | Rust traversal is 21.8x p50 faster, but only for a synthetic traversal primitive |
| ≥25% lower non-model peak RSS | **Yes, narrowly** | 5.5x on the POC (8.7 MiB vs 47.5 MiB), measured on a synthetic graph |
| No correctness regression | Yes | Identical checksums at all three sizes |

Both numeric gates pass. **That is not sufficient to justify the migration**, and
the recommendation is **not to port the core now**.

## Why the POC numbers do not transfer

1. **The POC's hot loop is not our hot loop.** 87% of indexing time is
   persistence, not traversal. Measured `graph_impact` is ~27 ms and `graph_path`
   ~29 ms on a 10k-entity index — already fast, and already dominated by SQL
   round trips and Python call overhead rather than adjacency traversal.
2. **The POC is synthetic.** A regular 800k-edge graph with uniform degree is the
   friendliest possible case for CSR. Real dependency graphs are sparser, more
   irregular, and mostly small.
3. **Most of the stack is already native.** tree-sitter, SQLite/FTS5, sqlite-vec,
   igraph and Leiden are compiled. The graph stage's CPU time exceeding its wall
   time proves native code is already doing parallel work there.
4. **Python overhead we removed ourselves.** Before comparing runtimes, we took
   the free 24.5%. Any Rust comparison should be against *this* Python, not the
   original.
5. **The cost side is unmeasured.** Porting 13 language adapters, the resolver,
   the MCP tool schemas and the daemon lifecycle is the expensive part, and the
   issue itself flags that a Rust EmbeddingGemma 2 backend is not established.
   Model weights do not shrink; PyTorch remains in the default configuration.

## Recommendation

**Maintain the Python core; do not migrate.**

The honest finding is that the obvious wins were already available in Python and
have now been taken. Re-run `scripts/benchmark_indexing_profile.py` after any
change to persistence and treat it as the regression gate.

Revisit only if a future measurement shows persistence *after* batching is
dominated by Python-side per-row loops rather than SQLite work, and only then
against a narrow Option B slice — a PyO3 module for one hot path — rather than a
full rewrite. The existing POC should be kept as the reference primitive and its
golden checksums should be preserved as a parity fixture for any future attempt.

## Limitations

- Generated synthetic corpus, not a large real monorepo; shapes and module sizes
  are uniform.
- Single machine, single run per configuration; no cross-machine comparison.
- No embedding or GPU stage measured — no cached EmbeddingGemma 2 weights.
- Windows and macOS were not measured here.