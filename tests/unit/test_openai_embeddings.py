"""Remote embedding provider contracts and privacy gates."""

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


def test_cohere_provider_config_keeps_remote_access_opt_in():
    config = Config(embedding={"backend": "api", "api_provider": "cohere"})
    backend = create_backend(config, cache_dir=None)
    assert config.embedding.api_provider == "cohere"
    assert isinstance(backend, DisabledBackend)


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


def test_cohere_native_v2_embed_contract(monkeypatch):
    monkeypatch.setenv("COHERE_API_KEY", "cohere-test")
    vector = [1.0, *([0.0] * 255)]
    response = type("Response", (), {
        "__enter__": lambda self: self,
        "__exit__": lambda self, *args: None,
        "read": lambda self: json.dumps({"embeddings": {"float": [vector]}}).encode(),
    })()
    backend = OpenAICompatibleBackend(
        provider="cohere", dimensions=256, authorized=True, endpoint_authorized=True,
    )
    with patch("urllib.request.urlopen", return_value=response) as request:
        assert backend.embed_texts(["query"], task="query") == [vector]
    sent = json.loads(request.call_args.args[0].data)
    assert sent == {
        "model": "embed-v4.0",
        "texts": ["query"],
        "input_type": "search_query",
        "embedding_types": ["float"],
        "output_dimension": 256,
    }
    assert request.call_args.args[0].full_url == "https://api.cohere.com/v2/embed"
    assert request.call_args.args[0].headers["Authorization"] == "Bearer cohere-test"


def test_cohere_rejects_unsupported_dimensions():
    with pytest.raises(ValueError, match="supports output dimensions"):
        OpenAICompatibleBackend(provider="cohere", dimensions=2048)


@pytest.mark.parametrize(("provider", "cap"), [("cohere", 96), ("gemini", 100)])
def test_native_provider_batch_limits_are_enforced(provider, cap):
    backend = OpenAICompatibleBackend(provider=provider, dimensions=256, batch_size=128)
    assert backend.batch_size == cap


def test_gemini_uses_native_batched_embedding_contract(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")
    vector = [1.0, *([0.0] * 255)]
    response = type("Response", (), {
        "__enter__": lambda self: self,
        "__exit__": lambda self, *args: None,
        "read": lambda self: json.dumps({"embeddings": [{"values": vector}]}).encode(),
    })()
    backend = OpenAICompatibleBackend(
        provider="gemini", dimensions=256, authorized=True, endpoint_authorized=True,
    )
    with patch("urllib.request.urlopen", return_value=response) as request:
        assert backend.embed_texts(["query"], task="query") == [vector]
        assert backend.embed_texts(["document"], task="document") == [vector]
    query_body = json.loads(request.call_args_list[0].args[0].data)
    document_body = json.loads(request.call_args_list[1].args[0].data)
    assert query_body["requests"][0]["embedContentConfig"]["taskType"] == "CODE_RETRIEVAL_QUERY"
    assert document_body["requests"][0]["embedContentConfig"]["taskType"] == "RETRIEVAL_DOCUMENT"
    assert request.call_args.args[0].full_url.endswith(
        "/models/gemini-embedding-2:batchEmbedContents"
    )
    assert request.call_args.args[0].get_header("X-goog-api-key") == "gemini-test"


def test_jina_maps_query_and_document_task_fields(monkeypatch):
    monkeypatch.setenv("JINA_API_KEY", "jina-test")
    vector = [1.0, *([0.0] * 1023)]
    response = type("Response", (), {
        "__enter__": lambda self: self,
        "__exit__": lambda self, *args: None,
        "read": lambda self: json.dumps({"data": [{"index": 0, "embedding": vector}]}).encode(),
    })()
    backend = OpenAICompatibleBackend(
        provider="jina", dimensions=1024, authorized=True, endpoint_authorized=True,
    )
    with patch("urllib.request.urlopen", return_value=response) as request:
        assert backend.embed_texts(["document"], task="document") == [vector]
        assert backend.embed_texts(["query"], task="query") == [vector]
    document_sent = json.loads(request.call_args_list[0].args[0].data)
    sent = json.loads(request.call_args.args[0].data)
    assert document_sent["task"] == "retrieval.passage"
    assert sent == {
        "model": "jina-embeddings-v3",
        "input": ["query"],
        "task": "retrieval.query",
        "dimensions": 1024,
        "embedding_type": "float",
    }
    assert request.call_args.args[0].full_url == "https://api.jina.ai/v1/embeddings"
    assert request.call_args.args[0].headers["Authorization"] == "Bearer jina-test"


def test_jina_rejects_unsupported_v3_dimensions():
    with pytest.raises(ValueError, match="Jina jina-embeddings-v3"):
        OpenAICompatibleBackend(provider="jina", dimensions=1536)


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
