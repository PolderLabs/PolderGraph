"""Guard the tmp_path isolation that keeps workspace-root detection honest.

`poldergraph.discovery.scanner.detect_root` walks up looking for project markers.
If a marker file sits in a shared temporary directory, every `tmp_path` created
under it silently resolves to that directory's workspace instead of the test's own
directory, which produces confusing, environment-dependent failures.
"""

from __future__ import annotations

from pathlib import Path

from conftest import _has_marker_ancestor, _isolated_tmp_root


def test_marker_inside_the_base_directory_is_detected(tmp_path: Path):
    # A marker that is a sibling of the isolated root, i.e. an ancestor of any
    # directory created beneath it, must disqualify that base directory.
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    root = tmp_path / "poldergraph-pytest"

    assert _has_marker_ancestor(root) is True


def test_marker_further_up_the_chain_is_detected(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    root = tmp_path / "nested" / "poldergraph-pytest"

    assert _has_marker_ancestor(root) is True


def test_clean_directory_is_accepted(tmp_path: Path):
    (tmp_path / "source.py").write_text("value = 1\n", encoding="utf-8")
    root = tmp_path / "poldergraph-pytest"

    assert _has_marker_ancestor(root) is False


def test_isolated_tmp_root_is_itself_marker_free():
    root = _isolated_tmp_root()

    assert root.is_dir()
    assert _has_marker_ancestor(root) is False