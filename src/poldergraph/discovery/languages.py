"""Language and file-type detection."""

from __future__ import annotations

from pathlib import PurePosixPath

#: Strong adapters ship explicit semantic extraction for these languages.
STRONG_LANGUAGES: frozenset[str] = frozenset(
    {
        "typescript",
        "tsx",
        "javascript",
        "jsx",
        "python",
        "rust",
        "go",
        "java",
        "c",
        "cpp",
        "csharp",
        "kotlin",
        "swift",
    }
)

#: Grammars available for baseline indexing without a strong resolver.
BASELINE_LANGUAGES: frozenset[str] = frozenset(
    {
        "ruby",
        "php",
        "scala",
        "perl",
        "lua",
        "haskell",
        "elixir",
        "erlang",
        "ocaml",
        "zig",
        "dart",
        "groovy",
        "objective_c",
        "r",
        "julia",
        "shell",
        "sql",
        "vue",
        "svelte",
        "astro",
    }
)

#: Maps PolderGraph language keys to tree-sitter-language-pack grammar names.
GRAMMAR_NAMES: dict[str, str] = {
    "typescript": "typescript",
    "tsx": "tsx",
    "javascript": "javascript",
    "jsx": "javascript",
    "python": "python",
    "rust": "rust",
    "go": "go",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "csharp": "csharp",
    "kotlin": "kotlin",
    "swift": "swift",
    "markdown": "markdown",
    "ruby": "ruby",
    "php": "php",
    "scala": "scala",
    "perl": "perl",
    "lua": "lua",
    "haskell": "haskell",
    "elixir": "elixir",
    "erlang": "erlang",
    "ocaml": "ocaml",
    "zig": "zig",
    "dart": "dart",
    "groovy": "groovy",
    "objective_c": "objc",
    "r": "r",
    "julia": "julia",
    "shell": "bash",
    "sql": "sql",
    "vue": "vue",
    "svelte": "svelte",
    "astro": "astro",
    "json": "json",
    "yaml": "yaml",
    "toml": "toml",
    "html": "html",
    "css": "css",
}

EXTENSION_MAP: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".ts": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "jsx",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".hxx": "cpp",
    ".cs": "csharp",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".swift": "swift",
    ".rb": "ruby",
    ".php": "php",
    ".scala": "scala",
    ".sc": "scala",
    ".pl": "perl",
    ".pm": "perl",
    ".lua": "lua",
    ".hs": "haskell",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".ml": "ocaml",
    ".zig": "zig",
    ".dart": "dart",
    ".groovy": "groovy",
    ".m": "objective_c",
    ".mm": "objective_c",
    ".r": "r",
    ".jl": "julia",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".sql": "sql",
    ".vue": "vue",
    ".svelte": "svelte",
    ".astro": "astro",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "css",
    ".md": "markdown",
    ".markdown": "markdown",
    ".mdx": "markdown",
    ".txt": "text",
    ".rst": "text",
    ".pdf": "pdf",
}

FILENAME_MAP: dict[str, str] = {
    "dockerfile": "dockerfile",
    "makefile": "makefile",
    "cmakelists.txt": "cmake",
}

IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff", ".svg", ".ico"}
)
AUDIO_EXTENSIONS: frozenset[str] = frozenset(
    {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus", ".wma"}
)
VIDEO_EXTENSIONS: frozenset[str] = frozenset(
    {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".mpg", ".mpeg", ".wmv"}
)

DOCUMENT_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".txt", ".rst", ".md", ".markdown"})


def language_for_path(path: str) -> str | None:
    """Detect the language for a path, honouring special filenames first."""
    pure = PurePosixPath(path.replace("\\", "/"))
    lowered = pure.name.lower()
    if lowered in FILENAME_MAP:
        return FILENAME_MAP[lowered]
    suffix = pure.suffix.lower()
    return EXTENSION_MAP.get(suffix)


def grammar_for(language: str | None) -> str | None:
    """Map a PolderGraph language key to its tree-sitter grammar name."""
    if not language:
        return None
    return GRAMMAR_NAMES.get(language)


def is_strong_language(language: str | None) -> bool:
    return language in STRONG_LANGUAGES


def is_media_path(path: str) -> bool:
    suffix = PurePosixPath(path.replace("\\", "/")).suffix.lower()
    return suffix in IMAGE_EXTENSIONS or suffix in AUDIO_EXTENSIONS or suffix in VIDEO_EXTENSIONS


def is_image_path(path: str) -> bool:
    return PurePosixPath(path.replace("\\", "/")).suffix.lower() in IMAGE_EXTENSIONS


def is_audio_path(path: str) -> bool:
    return PurePosixPath(path.replace("\\", "/")).suffix.lower() in AUDIO_EXTENSIONS


def is_video_path(path: str) -> bool:
    return PurePosixPath(path.replace("\\", "/")).suffix.lower() in VIDEO_EXTENSIONS


def is_document_path(path: str) -> bool:
    """Documents and media that produce their own entity kinds."""
    suffix = PurePosixPath(path.replace("\\", "/")).suffix.lower()
    return suffix in DOCUMENT_EXTENSIONS or suffix in IMAGE_EXTENSIONS or is_media_path(path)