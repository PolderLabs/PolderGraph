"""Regression coverage for stable CLI error payloads."""

import pytest

from poldergraph.errors import ExitCode, IndexMissingError
from poldergraph import workspace


def test_open_workspace_without_an_index_raises_actionable_error(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(workspace, "find_index_dir", lambda: None)
    monkeypatch.setattr(workspace, "detect_root", lambda: tmp_path)

    with pytest.raises(IndexMissingError, match=f"No PolderGraph index found for {tmp_path}") as exc_info:
        workspace.open_workspace()

    assert exc_info.value.exit_code == ExitCode.INDEX_MISSING
    assert exc_info.value.to_dict()["remediation"] == "Run: poldergraph init"
    assert exc_info.value.details["path"] == str(tmp_path)
