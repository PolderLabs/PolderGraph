"""Media segmentation for audio and video.

Long media is split into bounded overlapping windows so no single encoder input
exceeds model/runtime limits, and each segment persists its time range so a
search hit can link to the exact segment.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..discovery.languages import is_audio_path, is_image_path, is_video_path


@dataclass
class MediaSegment:
    """A bounded time window within a media file."""

    ordinal: int
    start: float
    end: float

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class MediaInfo:
    """Probed metadata for a media file."""

    duration: float
    kind: str
    exists: bool = True


def probe_media(path: Path) -> MediaInfo | None:
    """Read duration and kind without decoding the whole file."""
    if is_audio_path(str(path)):
        return _probe_audio(path)
    if is_video_path(str(path)):
        return _probe_video(path)
    if is_image_path(str(path)):
        return MediaInfo(duration=0.0, kind="image")
    return None


def _probe_audio(path: Path) -> MediaInfo | None:
    try:
        import soundfile as sf

        info = sf.info(str(path))
        return MediaInfo(duration=float(info.frames) / float(info.samplerate or 1), kind="audio")
    except Exception:
        duration = _probe_with_ffprobe(path)
        return MediaInfo(duration=duration, kind="audio") if duration is not None else None


def _probe_video(path: Path) -> MediaInfo | None:
    duration = _probe_with_ffprobe(path)
    return MediaInfo(duration=duration, kind="video") if duration is not None else None


def _probe_with_ffprobe(path: Path) -> float | None:
    """Use ffprobe when available; never builds a shell string from repo content."""
    import shutil
    import subprocess

    binary = shutil.which("ffprobe")
    if binary is None:
        return None
    try:
        completed = subprocess.run(
            [
                binary,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    try:
        return float(completed.stdout.decode("utf-8", errors="replace").strip())
    except ValueError:
        return None


def segment_media(
    duration: float,
    *,
    window: float = 30.0,
    overlap: float = 5.0,
    max_segments: int = 400,
) -> list[MediaSegment]:
    """Split a duration into bounded overlapping windows.

    Overlap prevents a phrase straddling a boundary from being lost. Segment
    count is capped so a pathological duration cannot explode the index.
    """
    if duration <= 0:
        return []
    window = max(1.0, window)
    overlap = min(max(0.0, overlap), window - 1.0)
    stride = window - overlap

    segments: list[MediaSegment] = []
    start = 0.0
    ordinal = 0
    while start < duration and len(segments) < max_segments:
        end = min(duration, start + window)
        segments.append(MediaSegment(ordinal=ordinal, start=start, end=end))
        ordinal += 1
        if end >= duration:
            break
        start += stride
    return segments


def sample_video_times(
    duration: float, *, samples: int = 8, max_segments: int = 400
) -> list[MediaSegment]:
    """Deterministic temporal sampling for video.

    Uniform samples keep the result reproducible for a given file, unlike
    content-dependent keyframe detection.
    """
    if duration <= 0:
        return []
    samples = max(1, min(samples, max_segments))
    step = duration / samples
    return [
        MediaSegment(ordinal=i, start=i * step, end=min(duration, (i + 1) * step))
        for i in range(samples)
    ]


def image_dimensions(path: Path) -> tuple[int, int] | None:
    """Read image dimensions for stored metadata."""
    try:
        from PIL import Image

        with Image.open(path) as image:
            return int(image.width), int(image.height)
    except Exception:
        return None