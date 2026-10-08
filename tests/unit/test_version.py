"""Version consistency.

The shipped version is asserted from two places — the package attribute and
the project metadata — because a release whose code reports the wrong version
makes `poldergraph upgrade` offer itself forever.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import poldergraph

ROOT = Path(__file__).resolve().parents[2]


def _pyproject_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


class TestVersion:
    def test_package_attribute_matches_pyproject(self):
        assert poldergraph.__version__ == _pyproject_version()

    def test_version_is_semantic(self):
        parts = poldergraph.__version__.split(".")
        assert len(parts) == 3, poldergraph.__version__
        assert all(part.isdigit() for part in parts), poldergraph.__version__

    def test_cli_reports_the_package_version(self):
        from typer.testing import CliRunner

        from poldergraph.cli import app

        result = CliRunner().invoke(app, ["--version"])
        assert result.exit_code == 0
        assert poldergraph.__version__ in result.output