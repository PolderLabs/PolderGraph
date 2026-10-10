# End-to-end user test findings (v0.10.0)

A hands-on run of the shipped release the way a new user and a coding agent would
use it. Method: install from the published v0.10.0 wheel, index a real
multi-module repository, then exercise the CLI, MCP server, query daemon,
memory, dashboard and the Codex/OMP agent hooks. Corpus for the main runs:
PolderGraph itself (215 files, ~3.5k entities), plus a small fixture repo.

Environment: Linux x86_64, CPython 3.12.14. EmbeddingGemma 2 weights were
cached locally.

## Summary

Seven confirmed issues. Two are release-blocking for the documented install and
automatic-agent paths.

| # | Severity | Issue |
|---|---|---|
| 1 | **P1 — release-blocking** | `scripts/install.sh` cannot install v0.10.0 |
| 2 | **P1** | `--offline` disables the local embedding model, so agents get no semantic or memory recall |
| 3 | P2 | A copied/stale index makes every query silently return zero results |
| 4 | P2 | `search` hard-fails when the `semantic` extra is missing, with remediation that cannot help |
| 5 | P3 | MCP `serverInfo.version` is an empty string |
| 6 | P3 | `status.counts.unresolved` exceeds the entity count and is dominated by external method calls |
| 7 | P3 | Dashboard surfaces a raw backend error with no remediation |

---

## 1. `scripts/install.sh` cannot install the release (P1)

`sh scripts/install.sh` — the documented primary install path — fails:

```
FileNotFoundError: Forced include not found:
  .../PolderLabs-PolderGraph-41a1ab6/web/dist
```

**Cause.** `pyproject.toml` force-includes `web/dist` into the wheel, but
`web/.gitignore` excludes `dist`, so the GitHub **source tarball never contains
it**. The release workflow builds the dashboard first, which is why the attached
wheel is fine — but any source-tarball install cannot build. This affects every
release, not just v0.10.0.

**Impact.** The advertised one-line installer is broken. Users who install from
the tarball get a build error; only the attached wheel works.

**Verified working.** The attached wheel installs and runs cleanly:

```sh
curl -fsSLO https://github.com/PolderLabs/PolderGraph/releases/download/v0.10.0/poldergraph-0.10.0-py3-none-any.whl
uv pip install "poldergraph[api,vectors,communities] @ ./poldergraph-0.10.0-py3-none-any.whl"
poldergraph --version   # -> poldergraph 0.10.0
```

All five dashboard assets are present in the published wheel.

**Suggested fix.** Make `install.sh` prefer the published wheel, and/or stop
force-including `web/dist` from a path that does not exist in the sdist (for
example, ship a placeholder or build assets during install).

---

## 2. `--offline` disables the local model, so agents lose memory and semantic recall (P1)

**Minimal reproduction** (repo with a stored user preference):

```sh
poldergraph context "How should you summarize work for me?" --offline --json
#   -> memories: 0   entities: 8
poldergraph context "How should you summarize work for me?" --json
#   -> memories: 3   entities: 9
```

The same preference is found either way when queried directly:

```sh
poldergraph memory search "How should you summarize work for me?" --scope user --json
#   -> 3 results, semantic_score 0.798
```

**Cause.** `cli.py:1177` maps `--offline` to `need_backend=not offline`, so
`--offline` disables the embedding backend entirely — including the **local**
EmbeddingGemma model. It does not merely block network access.

**Impact.** Both agent integrations hardcode `--offline`:

- `src/poldergraph/agents/codex_hook.py:168`
- `omp/index.ts:226`

so an agent prompt that paraphrases the user's question retrieves **no memories
at all** and no semantic neighbours. Observed across a real four-session Codex
flow: the preference was stored correctly and recalled only for prompts that
reused the same words. A paraphrased question ("How should you summarize work
for me?" vs stored "I prefer terse bullet points in summaries.") recalled
nothing, and the injected context contained zero occurrences of the preference
text.

This contradicts both the CLI help ("Do not download models or call hosted
providers") and `docs/cli-reference.md` ("forbid network access"), and it
undercuts the README claim that "Relevant user preferences and project notes are
already included above".

**This also overstates our own benchmark.** `benchmark_memory_tasks.py` reports
1.000 cross-session task success, but its recall prompts deliberately share
wording with the stored preference ("Do I prefer concise or detailed
explanations?" vs "I prefer concise explanations."), so it exercises the lexical
path only and cannot observe this defect. That benchmark needs paraphrased
prompts before its number can be trusted for real use.

**Suggested fix.** `--offline` should suppress downloads and remote calls while
still using the local model; if a mode with no model at all is wanted, give it a
separate, explicitly named flag.

---

## 3. Copied or stale index silently returns zero results (P2)

Copying a repository containing a live `.poldergraph/` directory (backup, moving
a checkout, cloning a repo that carries an index) produced, on six consecutive
runs:

```json
{"results": [], "degraded": ["vector search failed: attempt to write a readonly database"]}
```

The same query returned 5 results later, once the WAL had settled. Lexical and
structural results also disappeared, not just vectors, because the whole SQLite
connection was unusable — yet the only signal names the *vector* channel, and
there is no remediation hint.

**Impact.** A user whose query returns nothing will conclude their code has no
matches, rather than that their index directory was copied while in use.

**Suggested fix.** Detect a stale `-wal`/`-shm` or unwritable database up front,
report it as an explicit, actionable condition, and checkpoint rather than
degrading silently.

---

## 4. `search` hard-fails without the `semantic` extra (P2)

Installing `poldergraph[api,vectors,communities]` (no `semantic`) and running a
structural-only index:

```json
{"ok": false, "error": {"code": "BACKEND_UNAVAILABLE",
 "message": "sentence-transformers is not installed.",
 "remediation": "Install the semantic extra: uv pip install 'poldergraph[semantic]'"}}
```

**Impact.** `poldergraph search`, `explain` and friends fail outright rather than
serving the lexical/structural evidence the index actually contains. On an index
built with `init --no-embed` there are no vectors at all, so the suggested
remediation would not change the result.

`install.sh` uses `poldergraph[all]`, so the default install is unaffected; this
bites users who install a subset or deliberately index without embeddings.

---

## 5. MCP `serverInfo.version` is empty (P3)

The handshake returns:

```json
{"serverInfo": {"name": "poldergraph", "version": ""}}
```

The package defines `__version__ = "0.10.0"`. Clients that display server
version show nothing, and it makes the MCP surface harder to identify in logs.

---

## 6. `unresolved` count is larger than the entity count (P3)

On the PolderGraph repo: **3,515 entities, 4,404 unresolved refs**, grouped as
`calls` 2,766 / `accepts_type` 1,064 / `constructs` 274 / `references` 142. The
top unresolved names are `execute`, `echo`, `field`, `fetchone`, `dumps`,
`child_by_field_name` — i.e. methods on external objects (`con.execute`,
tree-sitter's `child_by_field_name`), which can never resolve locally.

**Impact.** `poldergraph status` reports a number larger than the entity total,
which reads as a broken index to an agent or a new user. There is no way to
distinguish "we failed to link our own symbol" from "this is a third-party call".

**Suggested fix.** Classify unresolved refs (external/third-party vs
intra-project) so the headline number is meaningful.

---

## 7. Dashboard shows a raw backend error (P3)

With the backend unavailable the dashboard displays the bare string
`sentence-transformers is not installed.` in the corner. The CLI and MCP wrap
this in a `BACKEND_UNAVAILABLE` envelope with remediation text; the dashboard
does not, and gives no hint what to do. The graph itself still rendered
correctly (7 canvases, clusters, labels, legend and controls all worked).

---

## What worked correctly

Recording these so the fixes above do not regress them.

- **First run.** `poldergraph init` on a real repo: 215 files, 3,548 entities,
  9,930 edges in **2.28 s**, zero parse errors.
- **Incremental update.** Editing one file then `poldergraph update`:
  `added/changed 1, unchanged 215`, 2 entities written, **0.064 s**. A no-op
  update correctly reports `unchanged: 215` and indexes nothing.
- **Daemon.** Cold query 5.4 s → warm query **0.197 s** (~27x), with the daemon
  reporting itself running.
- **Memory lifecycle.** Add → update → recall keeps a correct supersession chain
  with temporal bounds, and recall returns only the current version.
- **MCP.** 16 tools advertised and all exercised: `pg_status`, `pg_context`,
  `pg_search`, `pg_impact`, `pg_find_tests`, and the six `pg_memory_*` tools.
  Machine-readable envelopes throughout.
- **Evidence cursor dedup.** A second `pg_context` with `new_evidence_since`
  returned `new_evidence_count: 0`, and `why_selected` was present on the plan.
- **Codex hook.** `setup-agent --agent codex --hooks` writes
  `.codex/hooks.json`; real `UserPromptSubmit` events injected ~13–14k of
  grounded context and captured trusted preferences correctly.
- **Dashboard.** Real graph rendered with clusters, labels, legend, node kinds,
  size/edge/ring controls, search box and the Memory tab; memory list and save
  form both worked.

## Not verified here

- Windows and macOS (Linux only).
- OMP end-to-end against the pinned 18.8.7 runtime: local OMP is 18.8.6, and
  `tests/omp/runtime_smoke.mjs` fails on unmodified `main` with that mismatch, so
  a local failure would not be informative. The extension's TypeScript tests do
  pass, and issue 2 was confirmed in the shared `context --offline` path both
  hooks use.
- A real model-backed decision run (no Laya checkpoint present).