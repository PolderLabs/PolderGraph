"""Optional Ollama embedding backend.

Used only when a compatible local Ollama endpoint is configured. Remote
embedding is opt-in via the privacy policy; this backend only ever talks to the
configured local host.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from ..errors import BackendUnavailableError
from .protocol import (
    DOCUMENT_TASK,
    QUERY_TASK,
    EmbeddingBackend,
    MediaRequest,
    ModelInfo,
    truncate_and_normalize,
)


class OllamaBackend(EmbeddingBackend):
    """Embed via a local Ollama server."""

    def __init__(
        self,
        *,
        host: str = "http://127.0.0.1:11434",
        model: str = "embeddinggemma",
        dimensions: int = 256,
        normalize: bool = True,
        offline: bool = False,
        timeout: float = 60.0,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.dimensions = dimensions
        self.normalize = normalize
        self.offline = offline
        self.timeout = timeout
        self._revision = "ollama"

    def capabilities(self) -> set[str]:
        """Ollama's embed endpoint is text-only here."""
        return {"text"}

    def model_info(self) -> ModelInfo:
        return ModelInfo(
            model_id=self.model,
            revision=self._revision,
            dimensions=self.dimensions,
            native_dimensions=self.dimensions,
            normalize=self.normalize,
            backend="ollama",
            prompt_query="task: search result | query: ",
            prompt_document="title: none | text: ",
        )

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.host}{path}"
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise BackendUnavailableError(
                f"Cannot reach the Ollama backend at {self.host}: {exc.reason}",
                remediation="Start Ollama, or set embedding.backend = \"native\" in config.",
            ) from exc
        except json.JSONDecodeError as exc:
            raise BackendUnavailableError(
                f"Ollama returned a malformed response: {exc}",
                remediation="Verify the configured Ollama model is an embedding model.",
            ) from exc

    def embed_texts(
        self, items: list[str], *, task: str = DOCUMENT_TASK, dimensions: int | None = None
    ) -> list[list[float]]:
        if not items:
            return []
        target = dimensions or self.dimensions
        prompt = "task: search result | query: " if task == QUERY_TASK else "title: none | text: "
        prepared = [f"{prompt}{text}" for text in items]
        payload = {"model": self.model, "prompt": prepared, "keep_alive": "5m"}
        response = self._post("/api/embed", payload)
        vectors = response.get("embeddings")
        if vectors is None and response.get("embedding") is not None:
            vectors = [response["embedding"]]
        if not vectors:
            raise BackendUnavailableError(
                "Ollama returned no embeddings.",
                remediation="Verify the model name and that it supports embeddings.",
            )
        return [
            truncate_and_normalize([float(x) for x in vector], target, normalize=self.normalize)
            for vector in vectors
        ]

    def embed_images(self, requests: list[MediaRequest], *, dimensions: int | None = None) -> list[list[float]]:
        """Ollama's text embed path does not accept images; caller must degrade."""
        return []

    def embed_audio(self, requests: list[MediaRequest], *, dimensions: int | None = None) -> list[list[float]]:
        return []

    def embed_video(self, requests: list[MediaRequest], *, dimensions: int | None = None) -> list[list[float]]:
        return []