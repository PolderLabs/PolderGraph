"""Shared helpers for offline benchmarks.

Benchmarks must not inherit ambient filesystem state. PolderGraph resolves a
workspace root by walking up looking for project markers, so a stray file such
as ``/tmp/package.json`` would silently re-point a benchmark at an unrelated
directory and quietly invalidate its measurements.
"""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

ROOT_MARKERS = (
    ".git",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Gemfile",
    "composer.json",
    "CMakeLists.txt",
    ".poldergraph",
)


def has_marker_ancestor(directory: Path) -> bool:
    return any(
        (parent / marker).exists()
        for parent in (directory, *directory.parents)
        for marker in ROOT_MARKERS
    )


def marker_free_root() -> Path:
    """Return a directory whose ancestors contain no project marker files."""
    for base in (Path(tempfile.gettempdir()), Path("/var/tmp"), Path.home() / ".cache"):
        try:
            resolved = base.resolve()
        except OSError:
            continue
        if has_marker_ancestor(resolved):
            continue
        root = resolved / "poldergraph-benchmarks"
        root.mkdir(parents=True, exist_ok=True)
        return root
    raise RuntimeError("No marker-free temporary directory available for benchmarks.")


@contextmanager
def benchmark_workspace(prefix: str) -> Iterator[Path]:
    """A temporary directory that cannot be mistaken for another workspace."""
    root = marker_free_root()
    import shutil

    path = root / f"{prefix}{next(tempfile._get_candidate_names())}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)