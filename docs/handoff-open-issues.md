# PolderGraph handoff: state as of v0.10.0

## Where to start

```sh
git switch main
git pull --ff-only origin main
```

## Status

**No issues are open.** The five issues listed below were resolved and closed,
and their work shipped in [v0.10.0](https://github.com/PolderLabs/PolderGraph/releases/tag/v0.10.0).

| Issue | Resolution |
|---|---|
| [#30 Context planner](https://github.com/PolderLabs/PolderGraph/issues/30) | Budget-matched planner evaluation plus `why_selected` per lane. Change-impact phrasings now select structural and test lanes. |
| [#37 Typed decision plans](https://github.com/PolderLabs/PolderGraph/issues/37) | Hook re-entry no longer duplicates injected context; the capability matrix advertises only host events the extension truly wires; source-grounded task fixtures added. |
| [#22 Memory evaluation](https://github.com/PolderLabs/PolderGraph/issues/22) | Disclosed decision-gate dataset and cross-session suite with a no-memory baseline (1.000 vs 0.600). Jev/Laya reported unavailable rather than estimated. |
| [#34 Decision worker](https://github.com/PolderLabs/PolderGraph/issues/34) | Resident-memory pressure eviction, state-token bound, and a complete versioned status contract. |
| [#39 Rust core](https://github.com/PolderLabs/PolderGraph/issues/39) | Segmented profiling, a 24.4% indexing win from batched SQLite writes, and a **maintain the Python core** verdict. |

Evidence and full measurements live in
[decision worker](decision-worker-benchmark.md),
[context planner](benchmark-methodology.md#context-planner-benchmark),
[memory evaluation](memory-evaluation.md) and
[Rust core evaluation](rust-core-evaluation.md).

## Still worth doing

These are not open issues; they are the honest gaps the shipped work could not
close in this environment.

- **Laya checkpoint measurements.** Cold-load time, warm inference latency and
  CPU/GPU footprint still need a cached `laya-typed-decisions` checkpoint. The
  benchmarks probe for one on every run and emit real figures automatically when
  it exists, so no code change is needed — only the weights.
- **Hosted Jev comparison.** Needs an explicit `TYPESAFE_API_KEY`. It remains
  opt-in and fail-closed; no repository content leaves the machine by default.
- **Model-judged grounding.** All grounding numbers are expected-entity
  coverage. A paired coding-agent benchmark with an independent judge is a
  separate, larger study and is not claimed anywhere in the docs.
- **Larger and cross-platform indexing measurements.** Profiling used a
  generated corpus on one Linux machine; Windows and macOS numbers were not
  taken.

## Verification context

The suite is at **430 passing tests** on `main`. CI runs the Python suite, the
MCP server contract, the decision worker, batched-persistence atomicity, test
isolation, the daemon watcher, and the OMP extension tests (including the
re-entry dedup test) across Linux, macOS and Windows, plus the OMP runtime smoke
test. The full suite is green on `main` at v0.10.0.

Note: `tests/omp/runtime_smoke.mjs` requires the pinned OMP runtime from CI
(`@oh-my-pi/pi-coding-agent@18.8.7`). It fails locally against an older OMP
build, and it reproduces that way on unmodified `main`, so it is a version
mismatch rather than a regression.
