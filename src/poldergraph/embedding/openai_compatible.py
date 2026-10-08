"""OpenAI-compatible remote text embeddings with explicit privacy gating."""

from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.error
import urllib.request
from typing import Any

from ..errors import BackendUnavailableError
from .protocol import DOCUMENT_TASK, EmbeddingBackend, MediaRequest, ModelInfo


class OpenAICompatibleBackend(EmbeddingBackend):
    """Small OpenAI embeddings API client; compatible endpoints can be configured."""

    def __init__(self, *, endpoint: str, model: str, dimensions: int, normalize: bool = True,
                 timeout: float = 30.0, offline: bool = False, authorized: bool = False,
                 endpoint_authorized: bool = False) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.model = model
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
            model_id=f"api:{self.model}:{self._endpoint_id}", revision="api-v1",
            dimensions=self.dimensions, native_dimensions=self.dimensions,
            normalize=self.normalize, backend="api",
        )

    def _request(self, texts: list[str]) -> list[list[float]]:
        if self.offline or not self.authorized or not self.endpoint_authorized:
            raise BackendUnavailableError(
                "Remote embedding is disabled by the privacy policy.",
                remediation="Enable privacy.allow_remote_embedding in trusted user config or environment.",
            )
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise BackendUnavailableError("OPENAI_API_KEY is required for API embeddings.")
        payload = json.dumps({"model": self.model, "input": texts, "dimensions": self.dimensions}).encode()
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
            output.extend(self._request(items[start:start + 64]))
            if on_batch:
                on_batch(len(output), len(items))
        return output

    def embed_images(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]: return []
    def embed_audio(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]: return []
    def embed_video(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]: return []
