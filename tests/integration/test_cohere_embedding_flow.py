"""End-to-end contract for Cohere embeddings during indexing and search."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from poldergraph.config.models import Config
from poldergraph.embedding.gemma import create_backend
from poldergraph.indexing.pipeline import Indexer
from poldergraph.retrieval.service import QueryService
from poldergraph.storage.repository import Repository
from poldergraph.workspace import create_index, open_workspace


def test_cohere_vectors_flow_from_indexing_into_semantic_search(
    sample_repo: Path, monkeypatch,
) -> None:
    monkeypatch.setenv("COHERE_API_KEY", "test-key")
    config = Config.model_validate({
        "embedding": {"backend": "api", "api_provider": "cohere"},
        "index": {"dimensions": 256},
    })
    create_index(sample_repo, config)
    workspace = open_workspace(sample_repo)
    # These are runtime trust signals, deliberately not workspace-configurable.
    workspace.config.embedding.remote_authorized = True
    workspace.config.embedding.endpoint_authorized = True
    calls: list[dict[str, object]] = []

    class Response:
        def __init__(self, payload: dict[str, object]) -> None:
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self) -> bytes:
            texts = self.payload["texts"]
            assert isinstance(texts, list)
            return json.dumps({"embeddings": {"float": [[1.0, *([0.0] * 255)] for _ in texts]}}).encode()

    def fake_urlopen(request, timeout):
        assert timeout > 0
        payload = json.loads(request.data)
        calls.append(payload)
        return Response(payload)

    try:
        backend = create_backend(workspace.config)
        indexer = Indexer(workspace, backend=backend)
        indexer.ensure_root()
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            stats = indexer.run(indexer.discover())
            assert stats.embeddings_written > 0
            service = QueryService(
                Repository(workspace.con), workspace.config, backend,
                root_id=workspace.root_id(), workspace=workspace,
            )
            response = service.search("describe authentication", include_semantic=True)
        assert response.degraded == []
        assert any(call["input_type"] == "search_document" for call in calls)
        assert any(call["input_type"] == "search_query" for call in calls)
        assert any("semantic" in result.channels for result in response.results)
    finally:
        workspace.close()
