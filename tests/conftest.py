"""Shared pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "fixtures"))


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