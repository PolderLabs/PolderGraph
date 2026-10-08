"""OpenAI-compatible provider validation and privacy gates."""

import json
from email.message import Message
from io import BytesIO
from unittest.mock import patch

import pytest

from poldergraph.config.loader import load_config
from poldergraph.config.models import Config
from poldergraph.embedding.gemma import create_backend
from poldergraph.embedding.openai_compatible import OpenAICompatibleBackend
from poldergraph.embedding.protocol import DisabledBackend
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


def test_backend_factory_disables_api_without_trusted_consent():
    config = Config.model_validate({"embedding": {"backend": "api"}})
    assert isinstance(create_backend(config), DisabledBackend)


def test_provider_rejects_plain_http_non_loopback_endpoint():
    with pytest.raises(BackendUnavailableError, match="HTTPS"):
        OpenAICompatibleBackend(
            endpoint="http://example.test/v1", model="x", dimensions=2,
            authorized=True, endpoint_authorized=True,
        )


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


def test_voyage_uses_provider_specific_auth_and_task_contract(monkeypatch):
    monkeypatch.setenv("VOYAGE_API_KEY", "voyage-test")
    backend = OpenAICompatibleBackend(
        provider="voyage", dimensions=2, authorized=True, endpoint_authorized=True,
    )
    response = type("Response", (), {
        "__enter__": lambda self: self,
        "__exit__": lambda self, *args: None,
        "read": lambda self: b'{"data":[{"index":0,"embedding":[3,4]}]}',
    })()
    with patch("urllib.request.urlopen", return_value=response) as request:
        assert backend.embed_texts(["query"], task="query") == [[0.6, 0.8]]
    sent = json.loads(request.call_args.args[0].data)
    assert sent["input_type"] == "query"
    assert sent["output_dimension"] == 2
    assert sent["model"] == "voyage-3.5"
    assert request.call_args.args[0].full_url == "https://api.voyageai.com/v1/embeddings"


def test_provider_rejects_duplicate_vector_indexes(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    backend = OpenAICompatibleBackend(
        endpoint="https://example.test/v1", model="x", dimensions=2,
        authorized=True, endpoint_authorized=True,
    )
    response = type("Response", (), {
        "__enter__": lambda self: self,
        "__exit__": lambda self, *args: None,
        "read": lambda self: b'{"data":[{"index":0,"embedding":[1,0]},{"index":0,"embedding":[0,1]}]}',
    })()
    with patch("urllib.request.urlopen", return_value=response), pytest.raises(BackendUnavailableError, match="indexes"):
        backend.embed_texts(["a", "b"])


def test_provider_retries_rate_limit_with_retry_after(monkeypatch):
    from urllib.error import HTTPError

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    headers = Message()
    headers["Retry-After"] = "0"
    limited = HTTPError("https://example.test/v1/embeddings", 429, "limited", headers, BytesIO())
    response = type("Response", (), {
        "__enter__": lambda self: self,
        "__exit__": lambda self, *args: None,
        "read": lambda self: b'{"data":[{"index":0,"embedding":[1,0]}]}',
    })()
    backend = OpenAICompatibleBackend(
        endpoint="https://example.test/v1", model="x", dimensions=2,
        authorized=True, endpoint_authorized=True, retries=1,
    )
    with (
        patch("poldergraph.embedding.openai_compatible.time.sleep") as sleep,
        patch("urllib.request.urlopen", side_effect=[limited, response]) as request,
    ):
        assert backend.embed_texts(["a"]) == [[1.0, 0.0]]
    assert request.call_count == 2
    assert sleep.call_count == 1


def test_provider_batches_to_configured_limit(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    backend = OpenAICompatibleBackend(
        endpoint="https://example.test/v1", model="x", dimensions=2,
        authorized=True, endpoint_authorized=True, batch_size=1,
    )
    def response(*args, **kwargs):
        return type("Response", (), {
            "__enter__": lambda self: self,
            "__exit__": lambda self, *items: None,
            "read": lambda self: b'{"data":[{"index":0,"embedding":[1,0]}]}',
        })()
    with patch("urllib.request.urlopen", side_effect=response) as request:
        vectors = backend.embed_texts(["a", "b"])
    assert vectors == [[1.0, 0.0], [1.0, 0.0]]
    assert request.call_count == 2
