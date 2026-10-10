# Memory evaluation: decision gates and cross-session task behavior

Covers [issue #22](https://github.com/PolderLabs/PolderGraph/issues/22). Both
benchmarks run offline with no model weights and no network:

```bash
python tests/benchmarks/benchmark_decision_gates.py    # write-gate comparison
python tests/benchmarks/benchmark_memory_tasks.py      # cross-session tasks
```

Both drive the real production paths — `capture_explicit_user_preferences` and
the Codex `UserPromptSubmit` hook — so the numbers describe behavior PolderGraph
actually has, not a reimplementation.

## Decision-gate dataset

`tests/benchmarks/gate_cases.py` holds a versioned, disclosed dataset
(`GATE_DATASET_VERSION = "1.0.0"`) of 15 real-shaped but synthetic and
anonymised statements: 6 durable preferences, 6 one-off or speculative
statements, and 3 deliberately ambiguous ones where a conservative gate should
abstain. No repository source, user prompt, or memory content from any real
project is included.

## Measured results

### Deterministic baseline (the shipped default, `provider = "disabled"`)

| Metric | Value |
|---|---|
| Cases | 15 |
| Stored | 3 |
| Precision | 1.000 |
| Recall | 0.500 |
| False-write rate | 0.000 |
| Abstention rate on ambiguous | 1.000 |
| Mean / p95 latency | 0.523 / 0.538 ms |
| Cold start | 6.765 ms |

This is the safety-relevant direction: **the deterministic gate never wrote a
statement it should not have**. Its cost is recall — only 3 of 6 durable
preferences were captured, because the local parser admits only explicit
first-person statements and relies on an explicit pattern list. Precision is
bought with missed durable notes.

### Laya and Jev (typesafe)

| Provider | Available | Reason |
|---|---|---|
| `laya` | no | `laya` package not importable (`ModuleNotFoundError`); no checkpoint cached |
| `typesafe` | no | `TYPESAFE_API_KEY` is not set; hosted decisions stay opt-in and fail closed |

**No figures are reported for either provider**, because neither can run in this
environment. Extrapolating them would be inventing evidence. The benchmark
probes availability on every run and reports the precise reason instead, so a
machine with a cached checkpoint or a credential automatically produces real
figures without code changes.

Privacy boundary, verified on this run: **0 network calls, 0 weight downloads.**
Hosted providers require an explicit credential and fail closed without one, and
no repository content leaves the machine.

### Retrieval-side relevance gate

| Metric | Value |
|---|---|
| Relevant queries answered | 1 of 3 |
| Irrelevant queries answered | 0 of 3 |
| Abstains on all irrelevant | yes |

Abstention on irrelevant queries is clean. Answering only 1 of 3 relevant
queries reflects the offline lexical/structural path with the semantic channel
disabled — paraphrased queries do not match without embeddings. That is a
configuration limit of this run, not a claim about semantic-enabled behavior.

## Cross-session task suite with a no-memory baseline

`benchmark_memory_tasks.py` runs four multi-session scenarios through the real
Codex hook. Each runs twice: the shipped default, and the **no-memory baseline**
where the capture step is disabled so retrieval still runs but nothing is ever
written.

| Scenario | Memory enabled | No-memory baseline |
|---|---|---|
| `durable_recall` | pass | fail |
| `correction_supersedes` | pass | fail |
| `irrelevant_abstention` | pass | pass |
| `not_persisted_without_user_origin` | pass | pass |
| **Task success rate** | **1.000 (5/5)** | **0.600 (3/5)** |

Persistent memory is worth **+0.40 task success** on this suite, and the entire
difference comes from the two scenarios that require cross-session carry-over:
recalling a preference stated in an earlier session, and recalling the
*corrected* preference while the superseded one stays absent. Both privacy
behaviors — irrelevant-query abstention and refusing to persist
agent-authored text — hold with or without memory.

## Limitations

- Synthetic scenarios with scripted expectations. This measures memory plumbing,
  not agent productivity or coding-task success.
- No agent model participates, so no claim about task completion by an LLM.
- The semantic channel is disabled; recall numbers are lexical-only.
- The dataset is small (15 gate cases, 4 task scenarios). Treat these as
  regression signals that guard behavior, not as performance estimates.
- Gate precision/recall describe the write decision only.