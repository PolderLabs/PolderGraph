# Troubleshooting

## Index is stale

Run `poldergraph update --quiet` to refresh the index. This is safe to run repeatedly.

## Model download fails

Check network connectivity and available disk space (~2GB required). Use `--offline` to forbid network access and use cached models only.

## sqlite-vec unavailable

Install the vector extra: `uv pip install 'poldergraph[vectors]'`

If sqlite-vec still fails, PolderGraph falls back to a brute-force vector backend for small indexes. This is explicitly slower but correct.

## Index is locked

Another `poldergraph` process (possibly `watch`) is writing. Wait or stop the other process. The lock is released automatically when the writing process exits.

## Query daemon uses old settings or does not restart

The query daemon checks the effective configuration before reuse. A change to
workspace or user settings causes the next daemon-backed query or
`poldergraph daemon start` to replace the warm process. `poldergraph daemon stop`
waits for the socket to be removed; if it times out, check
`poldergraph daemon status` and retry after active queries finish.

The local socket accepts request frames up to 8 MiB and serves at most 16
clients at once. Extra clients are closed promptly, and incomplete frame headers
or bodies time out after five seconds.

## Corrupt index

Run `poldergraph doctor` to diagnose. Run `poldergraph rebuild` to create a replacement index atomically. The existing index is preserved as a backup until the new one passes integrity checks.

## Slow semantic search

- Reduce `index.dimensions` (256 is the default; try 128)
- Use `device = "auto"` to select the best available accelerator
- For large indexes, the brute-force vector fallback is slow; install sqlite-vec

## Dashboard shows no graph

- Check that `poldergraph init` or `poldergraph update` has completed
- Check that the API server is running (default `http://127.0.0.1:7432`)
- Check browser console for errors

## Cross-file resolution misses imports

PolderGraph resolves imports through module path heuristics. If your project uses unusual import patterns (e.g., path aliases, monorepo symlinks), the resolver may not find the target. Check `poldergraph explain <entity>` for unresolved references.

## Adding a new language

1. Add the language key to `STRONG_LANGUAGES` in `poldergraph/discovery/languages.py`
2. Add the extension mapping in `EXTENSION_MAP`
3. Create a language adapter in `poldergraph/parsing/languages/`
4. Register it in `poldergraph/parsing/languages/__init__.py`
5. Add parser fixtures in `tests/fixtures/parser_samples.py`
6. Run the parser tests to verify

## Adding an embedding backend

1. Implement the `EmbeddingBackend` protocol in a new module under `poldergraph/embedding/`
2. Register it in `poldergraph/embedding/gemma.py::create_backend`
3. Add configuration options to `config.models.EmbeddingConfig`
4. Add tests that verify vector correctness

## Token budget exceeded

The context pack uses a conservative token estimator. If you need precise control, set `--budget` to the exact limit. The pack prefers distinct evidence over completeness.
