"""OpenAI-compatible remote text embeddings with explicit privacy gating."""

from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlsplit

from ..errors import BackendUnavailableError
from .protocol import DOCUMENT_TASK, EmbeddingBackend, MediaRequest, ModelInfo


class OpenAICompatibleBackend(EmbeddingBackend):
    """Small OpenAI embeddings API client; compatible endpoints can be configured."""

    def __init__(self, *, provider: str = "openai", endpoint: str | None = None,
                 model: str | None = None, dimensions: int, normalize: bool = True,
                 timeout: float = 30.0, offline: bool = False, authorized: bool = False,
                 endpoint_authorized: bool = False) -> None:
        if provider not in {"openai", "voyage"}:
            raise ValueError(f"Unsupported API embedding provider: {provider}")
        self.provider = provider
        self.endpoint = (endpoint or {
            "openai": "https://api.openai.com/v1",
            "voyage": "https://api.voyageai.com/v1",
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
        self.model = model or {"openai": "text-embedding-3-small", "voyage": "voyage-3.5"}[provider]
        self.dimensions = dimensions
        self.normalize = normalize
        self.timeout = timeout
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
        key_name = {"openai": "OPENAI_API_KEY", "voyage": "VOYAGE_API_KEY"}[self.provider]
        key = os.environ.get(key_name)
        if not key:
            raise BackendUnavailableError(f"{key_name} is required for API embeddings.")
        payload_data: dict[str, Any] = {"model": self.model, "input": texts}
        if self.provider == "openai":
            payload_data["dimensions"] = self.dimensions
        else:
            payload_data["input_type"] = "query" if task == "query" else "document"
            payload_data["output_dimension"] = self.dimensions
        payload = json.dumps(payload_data).encode()
        req = urllib.request.Request(
            f"{self.endpoint}/embeddings", data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise BackendUnavailableError(f"Embedding API request failed: {type(exc).__name__}.") from exc
        data = body.get("data")
        if not isinstance(data, list) or len(data) != len(texts):
            raise BackendUnavailableError("Embedding API returned an unexpected number of vectors.")
        try:
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
        for start in range(0, len(items), 64):
            output.extend(self._request(items[start:start + 64], task))
            if on_batch:
                on_batch(len(output), len(items))
        return output

    def embed_images(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]: return []
    def embed_audio(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]: return []
    def embed_video(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]: return []
