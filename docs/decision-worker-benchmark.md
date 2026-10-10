# Local decision worker: supervision and measured behavior

Covers [issue #34](https://github.com/PolderLabs/PolderGraph/issues/34). Everything
here is produced by an offline, repeatable script:

```bash
python scripts/benchmark_decision_worker.py --calls 20
```

The benchmark drives the real supervisor — process spawn, deadline enforcement,
resident-memory eviction, idle eviction and explicit close — through a local
stand-in child with the same serialization contract. It therefore needs no model
weights and no network.

## What was missing before

The supervisor enforced deadlines, offline-only mode, child reuse, idle eviction,
crash handling and explicit shutdown, but it had **no resource ceiling**: nothing
ever asked how much memory the child occupied, so a local decision model could grow
without bound and nothing in the status contract reported the operating limits.

## Added

| Area | Behavior |
|---|---|
| `max_rss_mb` | Optional resident-memory cap. Exceeding it stops the child and the next call starts a fresh one. An unmeasurable host never triggers eviction. |
| `max_state_tokens` | Optional bound on the state text handed to the model. Oversized requests are rejected before the model loads; `0` means unbounded. |
| Status contract | `status()` now reports `contract_version`, `deadline_ms`, `max_rss_mb`, `max_state_tokens`, `rss_bytes`, `rss_known`, `evictions`, `last_eviction`, `state_tokens` and `model_revision`, in both the idle and busy branches. Prompts and model inputs are never exposed. |

Configuration lives in `DecisionsConfig` (`max_rss_mb`, `max_state_tokens`) and is
pushed onto the shared worker by `decision_runtime.apply_supervision_limits()` on
both the single-call and batch decision paths. Supervision policy is deliberately
separate from decision *confidence*: an over-cap or oversized request degrades to
deterministic behavior instead of blocking a request.

Resident memory is measured portably **without adding a dependency**: `psutil` is
used only when the host already provides it, otherwise `/proc/<pid>/status` on
Linux, `ps` on macOS, and `GetProcessMemoryInfo` via `ctypes` on Windows. If no
path yields a value, the worker reports `rss_known: false` rather than guessing.

## Measured results

Linux x86_64, CPython 3.12.14, 20 warm calls:

| Measurement | Result |
|---|---|
| Cold start (spawn to first answer) | mean 90.5 ms, p50 91.3 ms, p95 92.3 ms (3 samples) |
| Warm latency, same loaded child | mean 0.082 ms, p50 0.071 ms, p95 0.143 ms, p99 0.149 ms |
| Resident memory while warm | 37,486,592 bytes (~35.8 MiB) |
| Hung child vs 500 ms deadline | returned `DecisionError` after 503.5 ms; child stopped |
| Memory-cap eviction | 2 evictions, `last_eviction: memory`, child replaced, state `warm` after restart |
| Idle eviction (0.2 s window) | child stopped and released |

The deadline row is the important one for the issue's blocking requirement: a hung
inference worker cannot hold a caller beyond its deadline, and the request path
falls back to deterministic evidence.

## Not measured here, and why

- **Cold model load, warm inference latency, VRAM/CPU footprint for Laya**: no Laya
  package and no cached checkpoint exist in this environment (`laya_package:
  not_installed`, `checkpoint_cached: false`). The script probes this and reports
  the result instead of extrapolating. No weights are downloaded automatically.
- **Hosted Jev latency and cost**: no `TYPESAFE_API_KEY` is present
  (`typesafe_api_key_present: false`). Hosted providers remain opt-in and
  fail closed.

Those figures require an explicit weight download or credential and are therefore
left to an environment that has them, rather than being guessed.

## Tests

`tests/unit/test_decision_worker_pressure.py` covers the cap, eviction and restart,
the "unmeasurable memory never evicts" degradation, invalid cap rejection, the
state-token bound on both single and batch paths, config push-through, and the
versioned status fields. None of them load a real model.