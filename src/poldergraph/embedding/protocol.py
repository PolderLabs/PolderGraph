"""Embedding backend contracts.

Task roles follow EmbeddingGemma 2's documented prompt conventions: queries and
corpus text must be embedded with the correct, different roles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from ..errors import BackendUnavailableError

#: Corpus-side task prompt for EmbeddingGemma 2.
DOCUMENT_TASK = "document"
#: Query-side task prompt for EmbeddingGemma 2.
QUERY_TASK = "query"

#: Model default native output dimension before Matryoshka truncation.
NATIVE_DIMENSIONS = 768
SUPPORTED_DIMENSIONS: tuple[int, ...] = (128, 256, 512, 768)

#: Modality encoders are loaded lazily so a source-only repository never pays
#: the memory/startup cost of unused vision/audio encoders.
MODALITIES: tuple[str, ...] = ("text", "image", "audio", "video")


@dataclass
class ModelInfo:
    """Identity of the resolved embedding model, persisted with every vector."""

    model_id: str
    revision: str
    dimensions: int
    native_dimensions: int = NATIVE_DIMENSIONS
    normalize: bool = True
    backend: str = "native"
    prompt_query: str = ""
    prompt_document: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "revision": self.revision,
            "dimensions": self.dimensions,
            "native_dimensions": self.native_dimensions,
            "normalize": self.normalize,
            "backend": self.backend,
            "prompt_query": self.prompt_query,
            "prompt_document": self.prompt_document,
        }


@dataclass
class TextRequest:
    """A batch of text inputs with their task roles."""

    texts: list[str]
    task: str = DOCUMENT_TASK
    modality: str = "text"


@dataclass
class MediaRequest:
    """A media input with optional time ranges for audio/video segments."""

    path: Path
    modality: str
    start: float | None = None
    end: float | None = None
    label: str | None = None


@runtime_checkable
class EmbeddingBackend(Protocol):
    """The replaceable embedding interface."""

    def capabilities(self) -> set[str]:
        """Modality names this backend can currently encode."""
        ...

    def model_info(self) -> ModelInfo: ...

    def embed_texts(self, items: list[str], *, task: str, dimensions: int) -> list[list[float]]:
        ...

    def embed_images(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]:
        ...

    def embed_audio(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]:
        ...

    def embed_video(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]:
        ...


class DisabledBackend:
    """Backend used when semantics are explicitly disabled.

    Indexing still completes structurally; semantic capability is reported as
    unavailable rather than silently faked.
    """

    def __init__(self, reason: str = "disabled") -> None:
        self.reason = reason

    def capabilities(self) -> set[str]:
        return set()

    def model_info(self) -> ModelInfo:
        return ModelInfo(model_id="none", revision="none", dimensions=0, backend="none")

    def embed_texts(self, items: list[str], *, task: str, dimensions: int) -> list[list[float]]:
        raise BackendUnavailableError(
            f"Semantic embedding is unavailable: {self.reason}",
            remediation="Run: poldergraph doctor",
        )

    def embed_images(self, requests, *, dimensions):  # type: ignore[no-untyped-def]
        return []

    def embed_audio(self, requests, *, dimensions):  # type: ignore[no-untyped-def]
        return []

    def embed_video(self, requests, *, dimensions):  # type: ignore[no-untyped-def]
        return []


def truncate_and_normalize(vector: list[float], dimensions: int, *, normalize: bool = True) -> list[float]:
    """Matryoshka-truncate a vector to ``dimensions`` and re-normalize.

    Truncated vectors MUST be L2-normalized again before cosine similarity, or
    the stored distances no longer mean cosine.
    """
    if dimensions <= 0:
        raise ValueError("dimensions must be positive")
    truncated = vector[:dimensions]
    if len(truncated) < dimensions:
        # A backend that cannot reach the requested width is padded with zeros;
        # normalization below then keeps the result well defined.
        truncated = truncated + [0.0] * (dimensions - len(truncated))
    if not normalize:
        return truncated
    norm = sum(v * v for v in truncated) ** 0.5
    if norm <= 0.0:
        return truncated
    return [v / norm for v in truncated]


def batched(items: list[Any], size: int) -> list[list[Any]]:
    """Split a list into fixed-size batches."""
    if size <= 0:
        return [items] if items else []
    return [items[i : i + size] for i in range(0, len(items), size)]


def auto_batch_size(device: str, *, requested: int = 0) -> int:
    """Pick a batch size appropriate for the selected device."""
    if requested and requested > 0:
        return requested
    if device.startswith("cuda") or device.startswith("mps"):
        return 32
    return 8


def select_device(preference: str = "auto") -> str:
    """Resolve the compute device, reporting what was selected.

    CUDA is never required: CPU is always a valid fallback.
    """
    if preference and preference != "auto":
        return preference
    try:
        import torch
    except ImportError:
        return "cpu"
    try:
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    try:
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"