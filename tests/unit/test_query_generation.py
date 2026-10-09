import subprocess
import sys

import pytest

import poldergraph.retrieval.service as retrieval_service
from poldergraph.errors import IndexStaleError
from poldergraph.retrieval.service import QueryService
from poldergraph.storage.repository import Repository
from poldergraph.storage.sqlite import connect, set_meta, writer_transaction


def test_query_service_pins_generation_and_marks_mid_query_commit(
    indexed_workspace, monkeypatch
):
    service = QueryService(
        Repository(indexed_workspace.con),
        indexed_workspace.config,
        root_id=indexed_workspace.root_id(),
        workspace=indexed_workspace,
    )
    original = service._apply_filters
    counter = iter(("concurrent-generation-a", "concurrent-generation-b"))

    def commit_during_query(results, filters):
        output = original(results, filters)
        writer_code = "\n".join(
            (
                "import sys",
                "from pathlib import Path",
                "from poldergraph.storage.sqlite import connect, set_meta, writer_transaction",
                "con = connect(Path(sys.argv[1]))",
                "with writer_transaction(con):",
                "    set_meta(con, 'index_generation', sys.argv[2])",
                "con.close()",
            )
        )
        subprocess.run(
            [
                sys.executable,
                "-c",
                writer_code,
                str(indexed_workspace.index_dir / "index.sqlite3"),
                next(counter),
            ],
            check=True,
        )
        return output

    monkeypatch.setattr(service, "_apply_filters", commit_during_query)

    bounded = service.search("AuthService", include_semantic=False).to_dict()
    assert bounded["consistency_report"]["status"] == "generation_changed"
    assert bounded["consistency_report"]["generation_changed"] is True
    assert bounded["consistency_report"]["source_read_required"] is True
    assert bounded["consistency_report"]["source_read_instruction"] == (
        "Read the listed source files directly before acting; this index evidence is not authoritative."
    )

    with pytest.raises(IndexStaleError):
        service.search("AuthService", include_semantic=False, consistency="strict")


def test_freshness_names_source_read_instruction_for_pending_file(indexed_workspace):
    service = QueryService(
        Repository(indexed_workspace.con),
        indexed_workspace.config,
        root_id=indexed_workspace.root_id(),
        workspace=indexed_workspace,
    )
    source = indexed_workspace.root / "pkg" / "auth.py"
    source.write_text(source.read_text() + "\n# changed\n")

    freshness = service.freshness()

    assert freshness["fresh"] is False
    assert freshness["stale_files"]
    assert freshness["source_read_required"] is True
    assert "Read the listed source files directly" in freshness["source_read_instruction"]


def test_search_cache_reuses_results_only_within_same_generation(
    indexed_workspace, monkeypatch
):
    service = QueryService(
        Repository(indexed_workspace.con),
        indexed_workspace.config,
        root_id=indexed_workspace.root_id(),
        workspace=indexed_workspace,
    )
    calls = 0

    def fake_semantic(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return [], None

    monkeypatch.setattr(retrieval_service, "semantic_candidates", fake_semantic)
    first = service.search("token behavior", include_semantic=True)
    second = service.search("token behavior", include_semantic=True)
    assert calls == 1
    assert first.consistency_report["status"] == second.consistency_report["status"] == "fresh"

    writer = connect(indexed_workspace.index_dir / "index.sqlite3")
    try:
        with writer_transaction(writer):
            set_meta(writer, "index_generation", "cache-invalidation-generation")
    finally:
        writer.close()

    service.search("token behavior", include_semantic=True)
    assert calls == 2
def test_git_revision_change_marks_index_stale(indexed_workspace):
    root = indexed_workspace.root
    source = root / "pkg" / "auth.py"
    commands = [
        ["git", "init", "-q", str(root)],
        ["git", "-C", str(root), "config", "user.name", "Test"],
        ["git", "-C", str(root), "config", "user.email", "test@example.invalid"],
        ["git", "-C", str(root), "add", "pkg/auth.py"],
        ["git", "-C", str(root), "commit", "-qm", "initial"],
    ]
    for command in commands:
        subprocess.run(command, check=True)

    from poldergraph.agents.bootstrap import ensure_workspace_ready

    source.write_text(source.read_text() + "\n# indexed baseline\n")
    subprocess.run(["git", "-C", str(root), "add", "pkg/auth.py"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", "indexed baseline"], check=True
    )
    ensure_workspace_ready(root)
    service = QueryService(
        Repository(indexed_workspace.con),
        indexed_workspace.config,
        root_id=indexed_workspace.root_id(),
        workspace=indexed_workspace,
    )
    assert service.freshness()["fresh"] is True

    source.write_text(source.read_text() + "\n# committed branch change\n")
    subprocess.run(["git", "-C", str(root), "add", "pkg/auth.py"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", "branch change"], check=True
    )

    freshness = service.freshness()
    assert freshness["revision_changed"] is True
    assert freshness["fresh"] is False
    assert freshness["source_read_required"] is True
    assert "pkg/auth.py" in freshness["stale_files"]
