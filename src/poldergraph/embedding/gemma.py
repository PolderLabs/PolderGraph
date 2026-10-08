"""Canonical native EmbeddingGemma 2 backend.

Uses sentence-transformers/Transformers locally. Non-text modality encoders are
loaded lazily: indexing a source-only repository must not pay their cost.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

# CRITICAL: Set HF_HUB_OFFLINE *before* importing anything from huggingface_hub.
# The hub module caches the env var state at import time, so importing
# huggingface_hub.constants (which triggers the cache read) before setting
# the flag means the flag is ignored for that process lifetime.
#
# We check the default cache directory directly (without importing huggingface_hub)
# to see if the model is already downloaded.
_HF_HUB_CACHE = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface") / "hub")
_default_model_id = "google/embeddinggemma-2"
_model_cache_dir = _HF_HUB_CACHE / f"models--{_default_model_id.replace('/', '--')}"
if _model_cache_dir.is_dir() and any(_model_cache_dir.iterdir()):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

#: Representation length, in characters, that a full batch is tuned for.
#: Peak attention memory scales with batch * len^2, so this is the reference
#: point for sizing a bucket. Calibrated from measurements on a 5.7 GB GPU.
REFERENCE_CHARS = 600

from ..errors import BackendUnavailableError
from .protocol import (
    DOCUMENT_TASK,
    MODALITIES,
    NATIVE_DIMENSIONS,
    QUERY_TASK,
    SUPPORTED_DIMENSIONS,
    EmbeddingBackend,
    MediaRequest,
    ModelInfo,
    auto_batch_size,
    select_device,
    truncate_and_normalize,
)


class NativeGemmaBackend(EmbeddingBackend):
    """Local EmbeddingGemma 2 inference."""

    def __init__(
        self,
        *,
        model_id: str = "google/embeddinggemma-2",
        device: str = "auto",
        batch_size: int = 0,
        normalize: bool = True,
        dimensions: int = 256,
        revision: str | None = None,
        offline: bool = False,
        cache_dir: Path | None = None,
        max_tokens: int = 2048,
    ) -> None:
        self.model_id = model_id
        self.device = select_device(device)
        self.batch_size = auto_batch_size(self.device, requested=batch_size)
        self.normalize = normalize
        self.dimensions = dimensions
        self.requested_revision = revision
        self.offline = offline
        # Only set cache_dir when explicitly requested; the default HuggingFace
        # cache (~/.cache/huggingface/hub/) is shared across workspaces and
        # avoids re-downloading the model for each new index.
        self.cache_dir = cache_dir
        self.max_tokens = max_tokens
        self._model: Any = None
        self._revision: str | None = revision
        self._prompts: dict[str, str] = {}
        self._loaded_modalities: set[str] = {"text"}
        self._force_cpu: bool = False
        #: Current encode batch size; lowered automatically if the device OOMs.
        self._batch_size: int = self.batch_size

    # -------------------------------------------------------------- loading

    def _ensure_loaded(self) -> Any:
        if self._model is not None:
            return self._model
        if self.offline:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise BackendUnavailableError(
                "sentence-transformers is not installed.",
                remediation="Install the semantic extra: uv pip install 'poldergraph[semantic]'",
            ) from exc

        kwargs: dict[str, Any] = {"trust_remote_code": True, "device": "cpu" if self._force_cpu else self.device}
        if self.requested_revision:
            kwargs["revision"] = self.requested_revision
        if self.cache_dir:
            kwargs["cache_folder"] = str(self.cache_dir)

        try:
            model = SentenceTransformer(self.model_id, **kwargs)
        except Exception as exc:
            hint = ""
            if self.offline:
                hint = (
                    " Offline mode forbids downloads; warm the cache first with "
                    "`poldergraph init` while online."
                )
            raise BackendUnavailableError(
                f"Cannot load embedding model '{self.model_id}': {exc}.{hint}",
                remediation="Run: poldergraph doctor",
            ) from exc

        # Bound sequence length so a large source file cannot blow up memory.
        try:
            model.max_seq_length = min(getattr(model, "max_seq_length", 512) or 512, self.max_tokens)
        except Exception:
            pass
        self._model = model
        self._revision = self._resolve_revision(model)
        self._prompts = dict(getattr(model, "prompts", {}) or {})

        # Warm-up: run one tiny forward pass to trigger CPU JIT compilation.
        # Without this, the first real embedding call pays a ~14-second penalty
        # for one-time graph compilation, which looks like a hang.
        try:
            prompt = self._prompts.get(QUERY_TASK, "")
            model.encode(
                [f"{prompt}warmup"],
                batch_size=1,
                prompt_name=QUERY_TASK if QUERY_TASK in self._prompts else None,
                convert_to_numpy=True,
                normalize_embeddings=False,
                show_progress_bar=False,
            )
        except Exception:
            pass  # warm-up failure is never fatal

        return model

    def _resolve_revision(self, model: Any) -> str:
        """Record the resolved model revision so stale vectors can be invalidated."""
        if self.requested_revision:
            return self.requested_revision
        for candidate in (getattr(model, "model_card_data", None), getattr(model, "_model_card", None)):
            revision = getattr(candidate, "revision", None) or getattr(candidate, "sha", None)
            if revision:
                return str(revision)
        try:
            from huggingface_hub import HfApi

            info = HfApi().model_info(self.model_id)
            return str(info.sha)
        except Exception:
            # Fall back to a hash of the local module set: still stable per install.
            return "local:" + hashlib.sha256(
                (getattr(model, "_target_modules", None) and str(type(model)) or str(type(model))).encode()
            ).hexdigest()[:16]

    # ---------------------------------------------------------- capabilities

    def capabilities(self) -> set[str]:
        """Report loaded encoders; multimodal encoders appear only once loaded."""
        return set(self._loaded_modalities)

    def model_info(self) -> ModelInfo:
        self._ensure_loaded()
        return ModelInfo(
            model_id=self.model_id,
            revision=self._revision or "unknown",
            dimensions=self.dimensions,
            native_dimensions=NATIVE_DIMENSIONS,
            normalize=self.normalize,
            backend="native",
            prompt_query=self._prompts.get(QUERY_TASK, ""),
            prompt_document=self._prompts.get(DOCUMENT_TASK, ""),
        )

    # ----------------------------------------------------------------- text

    def _apply_prompt(self, text: str, task: str) -> str:
        """Prefix text with the model's documented role prompt for this task."""
        prompt = self._prompts.get(task)
        if not prompt:
            return text
        return f"{prompt}{text}"

    def embed_texts(
        self,
        items: list[str],
        *,
        task: str = DOCUMENT_TASK,
        dimensions: int | None = None,
        on_batch: Any = None,
    ) -> list[list[float]]:
        if not items:
            return []
        model = self._ensure_loaded()
        target = dimensions or self.dimensions

        # Clear CUDA cache before large embedding batches. On small GPUs the
        # warm-up pass and earlier operations fill the allocator cache, and
        # without a clear the first large encode hits OOM even though the
        # model fits.
        using_cuda = "cuda" in str(getattr(model, "device", ""))
        if using_cuda:
            try:
                import torch
                torch.cuda.empty_cache()
            except Exception:
                pass

        prepared = [self._apply_prompt(text, task) for text in items]
        prompt_name = task if task in self._prompts else None

        # Group by length so short representations batch together and long ones
        # never inflate the batch. Attention cost scales with
        # (batch x sequence length)^2, so mixing a 4000-token body with 400
        # short ones wastes most of the device.
        vectors = self._encode_by_length(
            model, prepared, prompt_name=prompt_name, target=target, on_batch=on_batch
        )

        return vectors

    def _encode_by_length(
        self,
        model: Any,
        prepared: list[str],
        *,
        prompt_name: str | None,
        target: int,
        on_batch: Any = None,
    ) -> list[list[float]]:
        """Encode in length-sorted buckets whose size adapts to content length.

        Attention memory scales with (batch x sequence length)^2, so a fixed
        batch count is either wasteful for short texts or fatal for long ones.
        Measured on a 5.7 GB GPU: 600-char texts allow a batch of 64, while
        2000-char texts in the same batch demand >10 GB. Each bucket therefore
        derives its own size from the lengths it actually contains, and shrinks
        on OOM before giving up.
        """
        order = sorted(range(len(prepared)), key=lambda i: len(prepared[i]))
        out: list[list[float]] = [[] for _ in prepared]
        max_batch = self._bucket_size()
        encoded = 0

        i = 0
        while i < len(order):
            # Grow the bucket while the texts stay similar in length, so short
            # representations batch aggressively and long ones stay small.
            first_len = len(prepared[order[i]])
            j = i + 1
            while j < len(order) and len(prepared[order[j]]) <= first_len * 2:
                j += 1
            window = order[i:j]
            bucket = self._length_bucket(window, prepared, max_batch)
            while window:
                chunk, window = window[:bucket], window[bucket:]
                try:
                    vectors = self._encode_once(
                        model,
                        [prepared[k] for k in chunk],
                        prompt_name=prompt_name,
                        batch_size=len(chunk),
                    )
                except Exception as exc:
                    if not self._is_out_of_memory(exc):
                        raise BackendUnavailableError(
                            f"Embedding failed: {exc}",
                            remediation="Run: poldergraph doctor",
                        ) from exc
                    self._release_device_memory()
                    if bucket > 1:
                        bucket = max(1, bucket // 2)
                        max_batch = min(max_batch, bucket)
                        continue
                    # Even a single text does not fit: use CPU from here on.
                    self._force_cpu = True
                    self._model = None
                    self._release_device_memory()
                    model = self._ensure_loaded()
                    continue
                for slot, vector in zip(chunk, vectors):
                    out[slot] = truncate_and_normalize(
                        [float(x) for x in vector], target, normalize=self.normalize
                    )
                if on_batch is not None:
                    encoded += len(chunk)
                    on_batch(encoded, len(prepared))
            i = j
        return out

    @staticmethod
    def _length_bucket(window: list[int], prepared: list[str], max_batch: int) -> int:
        """Pick a batch size for texts of the given lengths.

        Peak attention memory grows roughly with batch * len^2, so the budget
        for a bucket is the batch size that a mid-length text can afford.
        """
        longest = max((len(prepared[k]) for k in window), default=0)
        if longest <= 0:
            return max_batch
        # A short text can share a large batch; a long one needs few neighbours.
        scaled = int(max_batch * (REFERENCE_CHARS / longest) ** 2)
        return max(1, min(max_batch, scaled))

    def _encode_once(
        self,
        model: Any,
        texts: list[str],
        *,
        prompt_name: str | None,
        batch_size: int,
    ) -> Any:
        return model.encode(
            texts,
            batch_size=batch_size,
            prompt_name=prompt_name,
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=False,
        )

    @staticmethod
    def _is_out_of_memory(exc: Exception) -> bool:
        text = str(exc).lower()
        return "out of memory" in text or "cuda" in text or isinstance(exc, MemoryError)

    @staticmethod
    def _release_device_memory() -> None:
        try:
            import gc

            import torch

            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def _bucket_size(self) -> int:
        """Batch size for the next encode, bounded by the configured maximum."""
        return max(1, min(getattr(self, "_batch_size", self.batch_size), self.batch_size))

    def embed_query(self, text: str, *, dimensions: int | None = None) -> list[float]:
        """Embed a search query with the query role."""
        return self.embed_texts([text], task=QUERY_TASK, dimensions=dimensions)[0]

    # ------------------------------------------------------------ multimodal

    def _load_multimodal(self) -> Any:
        model = self._ensure_loaded()
        self._loaded_modalities.update({"image", "audio", "video"})
        return model

    def embed_images(self, requests: list[MediaRequest], *, dimensions: int | None = None) -> list[list[float]]:
        if not requests:
            return []
        try:
            from PIL import Image
        except ImportError as exc:
            raise BackendUnavailableError(
                "Pillow is required for image embeddings.",
                remediation="Install: uv pip install 'poldergraph[semantic]'",
            ) from exc
        model = self._load_multimodal()
        images = []
        for request in requests:
            try:
                images.append(Image.open(request.path).convert("RGB"))
            except Exception:
                images.append(Image.new("RGB", (224, 224)))
        vectors = self._encode_multimodal(model, images, dimensions)
        self._loaded_modalities.add("image")
        return vectors

    def embed_audio(self, requests: list[MediaRequest], *, dimensions: int | None = None) -> list[list[float]]:
        if not requests:
            return []
        try:
            import soundfile as sf
        except ImportError as exc:
            raise BackendUnavailableError(
                "soundfile is required for audio embeddings.",
                remediation="Install: uv pip install 'poldergraph[semantic]'",
            ) from exc
        model = self._load_multimodal()
        audio_list = []
        for request in requests:
            try:
                data, rate = sf.read(str(request.path))
                if request.start is not None and request.end is not None:
                    # Segment rather than decoding an entire long file.
                    data = data[int(request.start * rate) : int(request.end * rate)]
                audio_list.append(data)
            except Exception:
                audio_list.append(None)
        vectors = self._encode_multimodal(model, audio_list, dimensions, audio=True)
        self._loaded_modalities.add("audio")
        return vectors

    def embed_video(self, requests: list[MediaRequest], *, dimensions: int | None = None) -> list[list[float]]:
        if not requests:
            return []
        model = self._load_multimodal()
        frames: list[Any] = []
        for request in requests:
            try:
                frames.extend(_sample_video_frames(request))
            except Exception:
                frames.append(None)
        vectors = self._encode_multimodal(model, frames, dimensions)
        self._loaded_modalities.add("video")
        return vectors

    def _encode_multimodal(
        self, model: Any, items: list[Any], dimensions: int | None, *, audio: bool = False
    ) -> list[list[float]]:
        """Encode media inputs through the model's multimodal projection."""
        target = dimensions or self.dimensions
        processor = getattr(model, "_first_module", lambda: None)()
        processor = getattr(processor, "processor", None)
        try:
            outputs = model.encode(
                items,
                batch_size=self.batch_size,
                convert_to_numpy=True,
                normalize_embeddings=False,
                show_progress_bar=False,
            )
            return [
                truncate_and_normalize([float(x) for x in vector], target, normalize=self.normalize)
                for vector in outputs
            ]
        except Exception as exc:
            raise BackendUnavailableError(
                f"Multimodal embedding failed: {exc}",
                remediation="Reindex with --no-media to skip media, or check the model cache.",
            ) from exc


def _sample_video_frames(request: MediaRequest, *, max_frames: int = 8) -> list[Any]:
    """Deterministically sample frames from a video segment using ffmpeg if present."""
    import subprocess

    args = [
        "ffmpeg", "-v", "error",
    ]
    if request.start is not None:
        args.extend(["-ss", str(request.start)])
    args.extend(["-i", str(request.path)])
    if request.end is not None and request.start is not None:
        args.extend(["-t", str(request.end - request.start)])
    args.extend(["-vf", f"fps=1/{_segment_seconds(request) or 30}", "-frames:v", str(max_frames), "-f", "image2pipe", "-vcodec", "png", "-"])
    completed = subprocess.run(args, capture_output=True, timeout=60, check=False)
    if completed.returncode != 0 or not completed.stdout:
        return [None]
    from PIL import Image
    import io

    stream = io.BytesIO(completed.stdout)
    images: list[Any] = []
    while True:
        try:
            images.append(Image.open(stream).convert("RGB"))
        except Exception:
            break
    return images or [None]


def _segment_seconds(request: MediaRequest) -> float | None:
    if request.start is None or request.end is None:
        return None
    return max(0.1, request.end - request.start)


def create_backend(config: Any, *, cache_dir: Path | None = None, offline: bool = False) -> Any:
    """Build the configured embedding backend."""
    backend_name = getattr(config.embedding, "backend", "native")
    if backend_name == "none":
        from .protocol import DisabledBackend

        return DisabledBackend("configured backend = none")

    if backend_name == "ollama":
        from .ollama import OllamaBackend

        if config.index.dimensions not in SUPPORTED_DIMENSIONS:
            raise BackendUnavailableError(
                f"Ollama embeddings support configured dimensions {SUPPORTED_DIMENSIONS}; got {config.index.dimensions}."
            )

        return OllamaBackend(
            host=config.embedding.ollama_host,
            model=config.embedding.ollama_model,
            dimensions=config.index.dimensions,
            normalize=config.embedding.normalize,
            offline=offline,
        )

    if backend_name == "api":
        from .openai_compatible import OpenAICompatibleBackend

        return OpenAICompatibleBackend(
            provider=config.embedding.api_provider,
            endpoint=config.embedding.api_endpoint,
            model=config.embedding.api_model,
            dimensions=config.index.dimensions,
            normalize=config.embedding.normalize,
            timeout=config.embedding.api_timeout,
            offline=offline,
            authorized=config.embedding.remote_authorized,
            endpoint_authorized=config.embedding.endpoint_authorized,
        )

    if backend_name != "native":
        from .protocol import DisabledBackend

        return DisabledBackend(f"unknown backend '{backend_name}'")

    if config.index.dimensions not in SUPPORTED_DIMENSIONS:
        raise BackendUnavailableError(
            f"Native EmbeddingGemma supports dimensions {SUPPORTED_DIMENSIONS}; got {config.index.dimensions}."
        )

    return NativeGemmaBackend(
        model_id=config.embedding.model,
        device=config.embedding.device,
        batch_size=config.embedding.batch_size,
        normalize=config.embedding.normalize,
        dimensions=config.index.dimensions,
        revision=config.embedding.revision,
        offline=offline,
        cache_dir=cache_dir,
        max_tokens=config.embedding.max_tokens,
    )
