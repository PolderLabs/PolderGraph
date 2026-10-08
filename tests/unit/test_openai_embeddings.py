"""OpenAI-compatible provider validation and privacy gates."""

import json
from unittest.mock import patch

import pytest

from poldergraph.config.loader import load_config
from poldergraph.embedding.openai_compatible import OpenAICompatibleBackend
from poldergraph.errors import BackendUnavailableError


def test_workspace_cannot_grant_remote_embedding_consent(tmp_path):
    (tmp_path / "config.toml").write_text(
        '[privacy]\nallow_remote_embedding = true\n[embedding]\nbackend = "api"\n', encoding="utf-8"
    )
    loaded = load_config(tmp_path, environ={}, user_path=tmp_path / "no-user.toml")
    assert loaded.config.embedding.remote_authorized is False


def test_trusted_environment_can_grant_remote_embedding_consent(tmp_path):
    loaded = load_config(
        tmp_path, environ={"POLDERGRAPH_PRIVACY__ALLOW_REMOTE_EMBEDDING": "true"},
        user_path=tmp_path / "no-user.toml",
    )
    assert loaded.config.embedding.remote_authorized is True


def test_provider_fails_closed_without_consent():
    backend = OpenAICompatibleBackend(endpoint="https://api.openai.com/v1", model="x", dimensions=2)
    with pytest.raises(BackendUnavailableError, match="privacy policy"):
        backend.embed_texts(["private source"])


def test_provider_sends_api_payload_and_normalizes_vectors(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    backend = OpenAICompatibleBackend(
        endpoint="https://example.test/v1", model="x", dimensions=2,
        authorized=True, endpoint_authorized=True,
    )
    response = type("Response", (), {
        "__enter__": lambda self: self,
        "__exit__": lambda self, *args: None,
        "read": lambda self: json.dumps({"data": [
            {"index": 1, "embedding": [0, 2]}, {"index": 0, "embedding": [3, 4]},
        ]}).encode(),
    })()
    with patch("urllib.request.urlopen", return_value=response) as request:
        vectors = backend.embed_texts(["a", "b"])
    assert vectors == [[0.6, 0.8], [0.0, 1.0]]
    assert "test-key" not in request.call_args.args[0].full_url


def test_provider_rejects_wrong_vector_width(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    backend = OpenAICompatibleBackend(
        endpoint="https://example.test/v1", model="x", dimensions=2,
        authorized=True, endpoint_authorized=True,
    )
    response = type("Response", (), {
        "__enter__": lambda self: self,
        "__exit__": lambda self, *args: None,
        "read": lambda self: b'{"data":[{"index":0,"embedding":[1]}]}',
    })()
    with patch("urllib.request.urlopen", return_value=response), pytest.raises(BackendUnavailableError, match="width"):
        backend.embed_texts(["a"])
