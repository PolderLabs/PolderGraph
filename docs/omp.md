# Oh My Pi integration

PolderGraph includes a native Oh My Pi (OMP) extension. It queries the local
`poldergraph` CLI and the repository's canonical `.poldergraph` index; it does
not maintain a second index. OMP bootstraps a structural index without blocking
on model downloads and retrieves context in offline mode; configure and warm a
local model explicitly with `poldergraph update` if semantic results are wanted.
OMP adds the
returned context to its model prompt, which is handled by the model provider
configured for that session.

## Install

Install OMP, then install this repository as an OMP plugin:

```bash
omp install github:PolderLabs/PolderGraph
```

That's the only setup command. The extension bootstraps the PolderGraph CLI
with `uv` when it is first needed, then creates or structurally refreshes the
repository index without loading an embedding model. The first task waits for
index setup before retrieving graph context. Later sessions reuse the
installation and index. `uv` must be installed; the initial package install
requires network access. After setup, indexing and retrieval run locally.

You can prewarm a repository before starting OMP by running:

```bash
poldergraph init
```

Restart OMP after installing the extension. For local development, clone this
repository and add the extension to `~/.omp/agent/config.yml`:

```yaml
extensions:
  - /absolute/path/to/PolderGraph/omp/index.ts
```

OMP's plugin installer installs the extension package. The extension installs
the Python runtime automatically when needed. If PolderGraph is already
installed, it reuses the executable on `PATH`.

## Behavior

On session start, the extension bootstraps the CLI if needed. Before each user
task, it initializes a missing index or structurally refreshes a stale one
without downloading a model, then uses a cheap local context plan. Social
messages skip repository retrieval and add no PolderGraph context; narrow symbol
lookups use a compact lexical pack; broader coding tasks use the configured
token budget with offline lexical and structural evidence. Successful OMP edit/write operations trigger
a background incremental refresh. If automatic setup fails, the agent receives
the error and continues with normal repository inspection; it retries
PolderGraph on a later task.

The model can also call these tools for focused queries:

- `poldergraph_search`
- `poldergraph_context`
- `poldergraph_explain`
- `poldergraph_path`
- `poldergraph_impact`
- `poldergraph_update`

Use `/poldergraph ui` to open the dashboard at `http://127.0.0.1:7432` and
`/poldergraph config show` to inspect settings. Set a basic value with
`/poldergraph config set ui.port 7433`. The `/poldergraph` command also accepts
CLI subcommands such as `status`, `search`, and `update`. The agent can call
`poldergraph_update`; updates are incremental and safe to repeat.

PolderGraph results are navigation evidence. The agent must inspect cited
source files, and semantic similarity alone does not establish a code
dependency.
