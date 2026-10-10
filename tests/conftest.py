"""Shared pytest fixtures."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "fixtures"))

# Mirrors poldergraph.discovery.scanner.detect_root. A workspace root is found by
# walking up from the start directory, so a stray project marker in a shared
# temporary directory (for example /tmp/package.json) would capture every
# pytest tmp_path and silently re-point the tests at the wrong workspace root.
_ROOT_MARKERS = (
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


def _has_marker_ancestor(directory: Path) -> bool:
    """True when ``directory`` or any parent is a directory a workspace root could resolve to."""
    return any(
        (parent / marker).exists()
        for parent in (directory, *directory.parents)
        for marker in _ROOT_MARKERS
    )


def _isolated_tmp_root() -> Path:
    """A temp directory whose ancestors contain no project marker files."""
    candidates = [Path(tempfile.gettempdir()), Path("/var/tmp"), Path.home() / ".cache"]
    for base in candidates:
        try:
            resolved = base.resolve()
            if not _has_marker_ancestor(resolved):
                root = resolved / "poldergraph-pytest"
                root.mkdir(parents=True, exist_ok=True)
                return root
        except OSError:
            continue
    raise RuntimeError("No marker-free temporary directory available for isolated tests.")


def pytest_configure(config: pytest.Config) -> None:
    """Keep tmp_path out of any directory that could be mistaken for a workspace root."""
    root = _isolated_tmp_root()
    tempfile.tempdir = str(root)
    os.environ["TMPDIR"] = str(root)


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    """A small multi-file repository with cross-file references."""
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "auth.py").write_text(
        "from .models import Session\n"
        "\n"
        "class AuthService:\n"
        '    """Validate session tokens."""\n'
        "    def validate_session(self, token: str) -> Session:\n"
        '        """Check a token is valid."""\n'
        "        return Session(token)\n"
        "\n"
        "    def refresh(self, token):\n"
        "        return self.validate_session(token)\n"
    )
    (tmp_path / "pkg" / "models.py").write_text(
        "class Session:\n"
        '    """A user session."""\n'
        "    def __init__(self, token):\n"
        "        self.token = token\n"
    )
    (tmp_path / "pkg" / "__init__.py").write_text("from .auth import AuthService\n")
    (tmp_path / "test_auth.py").write_text(
        "from pkg.auth import AuthService\n"
        "\n"
        "def test_validate_session():\n"
        '    assert AuthService().validate_session("x")\n'
    )
    (tmp_path / "README.md").write_text("# Sample\n\nIntro.\n\n## Usage\n\nCall it.\n")
    return tmp_path


@pytest.fixture()
def indexed_workspace(sample_repo: Path):
    """A workspace with a structural-only index (no model download)."""
    from poldergraph.config.models import Config
    from poldergraph.graph import run_graph_stage
    from poldergraph.indexing.pipeline import Indexer
    from poldergraph.storage.repository import Repository
    from poldergraph.workspace import create_index, open_workspace

    create_index(sample_repo, Config())
    workspace = open_workspace(sample_repo)
    indexer = Indexer(workspace, backend=None)
    indexer.ensure_root()
    indexer.run(indexer.discover())
    run_graph_stage(workspace, workspace.config, Repository(workspace.con), None)
    yield workspace
    workspace.close()