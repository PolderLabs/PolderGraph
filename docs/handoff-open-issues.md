# PolderGraph handoff: remaining work

## Where to start

```sh
git switch main
git pull --ff-only origin main
```

The latest merged work is in PRs [#101–#107](https://github.com/PolderLabs/PolderGraph/pulls?q=is%3Apr+is%3Amerged). Recent changes cover daemon lifecycle, context and watcher benchmarks, monorepo/multi-root behavior, Codex memory correction, and a Rust CSR BFS research prototype. Issues #26 and #27 were closed. Five issues remain open:

## Open issues and next steps

- [#30 Context planner evaluation](https://github.com/PolderLabs/PolderGraph/issues/30): replace the expected-entity proxy with paired coding tasks. Measure task completion and answer grounding against a no-memory baseline and the adaptive planner.
- [#37 Typed decision plans](https://github.com/PolderLabs/PolderGraph/issues/37): connect the typed plans to real agent-event task fixtures and verify the resulting repository actions. Use #30's task-success evaluation as the outcome measure.
- [#22 Memory research and evaluation](https://github.com/PolderLabs/PolderGraph/issues/22): compare memory/decision strategies on cross-session tasks, including temporal updates and retrieval accuracy. Confirm model credentials and weights before planning external-model runs; the last environment lacked Laya weights.
- [#34 Local decision worker supervision](https://github.com/PolderLabs/PolderGraph/issues/34): finish the resource-pressure policy and benchmark cold/warm model runs for latency and RSS. The last environment lacked Laya weights, so model-backed measurements need an available checkpoint.
- [#39 Rust-native core evaluation](https://github.com/PolderLabs/PolderGraph/issues/39): profile actual indexing and query paths, then compare correctness and resource use on representative repositories. `research/rust_graph_poc/` currently demonstrates synthetic BFS only; treat it as a go/no-go experiment, not production parity.

Suggested sequence: #30 and #37 together, then #22; finish #34 when a model checkpoint is available; use real-path profiling to decide #39. Don’t claim broad performance gains from the isolated BFS result. No release has been made for these outstanding items.

## Verification context

The full suite had 396 passing tests before the later additions. Subsequent focused tests and CI for the merged changes passed across Linux, macOS, and Windows; the pinned OMP runtime smoke test also passed. Rerun the current full suite before preparing a release.
