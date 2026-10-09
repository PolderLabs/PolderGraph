"""Remote text embedding APIs with explicit privacy gating."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlsplit

from ..errors import BackendUnavailableError
from .protocol import DOCUMENT_TASK, EmbeddingBackend, MediaRequest, ModelInfo


class OpenAICompatibleBackend(EmbeddingBackend):
    """Provider adapters for OpenAI-compatible APIs and Cohere's native v2 API."""

    def __init__(self, *, provider: str = "openai", endpoint: str | None = None,
                 model: str | None = None, dimensions: int, normalize: bool = True,
                 timeout: float = 30.0, offline: bool = False, authorized: bool = False,
                 endpoint_authorized: bool = False, retries: int = 2,
                 batch_size: int = 64) -> None:
        if provider not in {"openai", "voyage", "cohere"}:
            raise ValueError(f"Unsupported API embedding provider: {provider}")
        self.provider = provider
        self.endpoint = (endpoint or {
            "openai": "https://api.openai.com/v1",
            "voyage": "https://api.voyageai.com/v1",
            "cohere": "https://api.cohere.com/v2",
        }[provider]).rstrip("/")
        parsed_endpoint = urlsplit(self.endpoint)
        local_http = parsed_endpoint.hostname in {"localhost", "127.0.0.1", "::1"}
        if (
            not parsed_endpoint.hostname
            or parsed_endpoint.username
            or parsed_endpoint.password
            or parsed_endpoint.query
            or parsed_endpoint.fragment
            or (parsed_endpoint.scheme != "https" and not (local_http and parsed_endpoint.scheme == "http"))
        ):
            raise BackendUnavailableError(
                "Embedding API endpoint must use HTTPS (HTTP is allowed only for loopback endpoints)."
            )
        self.model = model or {
            "openai": "text-embedding-3-small",
            "voyage": "voyage-3.5",
            "cohere": "embed-v4.0",
        }[provider]
        if provider == "cohere" and dimensions not in {256, 512, 1024, 1536}:
            raise ValueError("Cohere embed-v4.0 supports output dimensions 256, 512, 1024, and 1536.")
        self.dimensions = dimensions
        self.normalize = normalize
        self.timeout = timeout
        self.retries = max(0, min(5, retries))
        self.batch_size = max(1, min(128, batch_size))
        self.offline = offline
        self.authorized = authorized
        self.endpoint_authorized = endpoint_authorized
        self._endpoint_id = hashlib.sha256(self.endpoint.encode()).hexdigest()[:12]

    def capabilities(self) -> set[str]:
        return {"text"}

    def model_info(self) -> ModelInfo:
        return ModelInfo(
            model_id=f"api:{self.provider}:{self.model}:{self._endpoint_id}", revision="api-v1",
            dimensions=self.dimensions, native_dimensions=self.dimensions,
            normalize=self.normalize, backend="api",
        )

    def _request(self, texts: list[str], task: str) -> list[list[float]]:
        if self.offline or not self.authorized or not self.endpoint_authorized:
            raise BackendUnavailableError(
                "Remote embedding is disabled by the privacy policy.",
                remediation="Enable privacy.allow_remote_embedding in trusted user config or environment.",
            )
        key_name = {
            "openai": "OPENAI_API_KEY",
            "voyage": "VOYAGE_API_KEY",
            "cohere": "COHERE_API_KEY",
        }[self.provider]
        key = os.environ.get(key_name)
        if not key:
            raise BackendUnavailableError(f"{key_name} is required for API embeddings.")
        payload_data: dict[str, Any] = {"model": self.model, "input": texts}
        request_url = f"{self.endpoint}/embeddings"
        if self.provider == "openai":
            payload_data["dimensions"] = self.dimensions
        elif self.provider == "voyage":
            payload_data["input_type"] = "query" if task == "query" else "document"
            payload_data["output_dimension"] = self.dimensions
        else:
            payload_data = {
                "model": self.model,
                "texts": texts,
                "input_type": "search_query" if task == "query" else "search_document",
                "embedding_types": ["float"],
                "output_dimension": self.dimensions,
            }
            request_url = f"{self.endpoint}/embed"
        payload = json.dumps(payload_data).encode()
        req = urllib.request.Request(
            request_url, data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, method="POST",
        )
        body = None
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    body = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt >= self.retries:
                    raise BackendUnavailableError(
                        f"Embedding API request failed with HTTP {exc.code}."
                    ) from exc
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    delay = min(15.0, max(0.0, float(retry_after))) if retry_after else 0.0
                except ValueError:
                    delay = 0.0
                delay = max(delay, min(8.0, 0.5 * (2 ** attempt) + random.uniform(0, 0.2)))
                time.sleep(delay)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                if attempt >= self.retries:
                    raise BackendUnavailableError(
                        f"Embedding API request failed: {type(exc).__name__}."
                    ) from exc
                time.sleep(min(8.0, 0.5 * (2 ** attempt) + random.uniform(0, 0.2)))
        if body is None:
            raise BackendUnavailableError("Embedding API request did not produce a response.")
        try:
            if self.provider == "cohere":
                embeddings = body.get("embeddings")
                data = embeddings.get("float") if isinstance(embeddings, dict) else None
                if not isinstance(data, list) or len(data) != len(texts):
                    raise BackendUnavailableError(
                        "Cohere returned an unexpected number of vectors."
                    )
                vectors = [[float(value) for value in vector] for vector in data]
            else:
                data = body.get("data")
                if not isinstance(data, list) or len(data) != len(texts):
                    raise BackendUnavailableError("Embedding API returned an unexpected number of vectors.")
                indexes = [int(item["index"]) for item in data]
                if sorted(indexes) != list(range(len(texts))):
                    raise BackendUnavailableError("Embedding API returned invalid vector indexes.")
                data = sorted(data, key=lambda item: int(item["index"]))
                vectors = [[float(v) for v in item["embedding"]] for item in data]
        except (KeyError, TypeError, ValueError) as exc:
            raise BackendUnavailableError("Embedding API returned malformed vectors.") from exc
        for vector in vectors:
            if len(vector) != self.dimensions or not all(math.isfinite(v) for v in vector):
                raise BackendUnavailableError("Embedding API vector width or values are invalid.")
            if self.normalize:
                norm = math.sqrt(sum(v * v for v in vector))
                if norm:
                    vector[:] = [v / norm for v in vector]
        return vectors

    def embed_texts(self, items: list[str], *, task: str = DOCUMENT_TASK,
                    dimensions: int | None = None, on_batch: Any = None) -> list[list[float]]:
        if not items:
            return []
        target = dimensions or self.dimensions
        if target != self.dimensions:
            raise BackendUnavailableError("Requested dimensions differ from the configured API vector width.")
        output: list[list[float]] = []
        for start in range(0, len(items), self.batch_size):
            output.extend(self._request(items[start:start + self.batch_size], task))
            if on_batch:
                on_batch(len(output), len(items))
        return output

    def embed_images(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]: return []
    def embed_audio(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]: return []
    def embed_video(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]: return []
