# Rust graph traversal proof of concept

This disposable experiment compares a Python list-of-lists graph with a Rust
compressed sparse row (CSR) graph for depth-limited outgoing breadth-first
search. Both generate the same deterministic directed graph and traverse the
same seed nodes. Every sample compares the checksum and exits on any mismatch.

The timed traversal reuses one distance buffer in Rust and creates one per
query in Python, reflecting a compact native traversal loop against the current
idiomatic Python baseline. Internal traversal time excludes graph construction;
process wall time includes process startup and graph construction. Peak RSS is
read from Linux `/proc/self/status`, so RSS results are only reported on Linux.

Build and run without third-party Rust crates or network access:

```bash
cargo build --offline --release --manifest-path research/rust_graph_poc/Cargo.toml
python research/rust_graph_poc/benchmark.py --repeats 7
```

The experiment is not a PolderGraph backend, has no SQLite/parser/MCP parity,
and says nothing about embedding inference. Treat it as evidence about one
CPU-bound graph traversal primitive only.
