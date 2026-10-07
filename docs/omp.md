# Oh My Pi integration

PolderGraph includes a native Oh My Pi (OMP) extension. It queries the local
`poldergraph` CLI and the repository's canonical `.poldergraph` index; it does
not maintain a second index or make separate network requests. OMP adds the
returned context to its model prompt, which is handled by the model provider
configured for that session.

## Install

Install PolderGraph and OMP, then install this repository as an OMP plugin:

```bash
uv tool install --from "git+https://github.com/PolderLabs/PolderGraph.git" "poldergraph[all]"
omp install github:PolderLabs/PolderGraph
```

Inside each repository you want indexed, run:

```bash
poldergraph init
```

Restart OMP after installing the extension. For local development, clone this
repository and add the extension to `~/.omp/agent/config.yml`:

```yaml
extensions:
  - /absolute/path/to/PolderGraph/omp/index.ts
```

The extension requires the `poldergraph` executable on `PATH`. Install the
Python package separately as shown above; OMP's plugin installer installs the
extension package, not its Python runtime.

## Behavior

Before each user task, the extension checks index status, incrementally updates
a stale index, then obtains a 3,000-token `poldergraph context` pack and adds it
to that request's system context. If PolderGraph is not installed, the
repository has not been initialized, or a command fails, OMP continues without
the automatic context. The extension never initializes an index implicitly:
first-time indexing downloads the local embedding model and should be an
explicit user action (`poldergraph init`).

The model can also call these tools for focused queries:

- `poldergraph_search`
- `poldergraph_context`
- `poldergraph_explain`
- `poldergraph_path`
- `poldergraph_impact`
- `poldergraph_update`

The `/poldergraph` command accepts a CLI subcommand such as `/poldergraph
status` or `/poldergraph update`. After substantial edits, the agent can call
`poldergraph_update`; updates are incremental and safe to repeat.

PolderGraph results are navigation evidence. The agent must inspect cited
source files, and semantic similarity alone does not establish a code
dependency.
