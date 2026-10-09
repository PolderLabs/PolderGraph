import pytest

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
        writer = connect(indexed_workspace.index_dir / "index.sqlite3")
        try:
            with writer_transaction(writer):
                set_meta(writer, "index_generation", next(counter))
        finally:
            writer.close()
        return output

    monkeypatch.setattr(service, "_apply_filters", commit_during_query)

    bounded = service.search("AuthService", include_semantic=False).to_dict()
    assert bounded["consistency_report"]["status"] == "generation_changed"
    assert bounded["consistency_report"]["generation_changed"] is True
    assert bounded["consistency_report"]["source_read_required"] is True

    with pytest.raises(IndexStaleError):
        service.search("AuthService", include_semantic=False, consistency="strict")
