"""Language adapter registry.

Strong adapters ship explicit semantic extraction; every other supported
grammar falls back to the baseline adapter.
"""

from __future__ import annotations

from typing import Any


def load_adapters() -> dict[str, Any]:
    """Instantiate every available strong adapter keyed by language."""
    adapters: dict[str, Any] = {}

    def register(cls: type, language: str) -> None:
        try:
            adapters[language] = cls()
        except Exception:  # pragma: no cover - an adapter must never break startup
            return

    from .markdown_adapter import MarkdownAdapter

    register(MarkdownAdapter, "markdown")

    from .python_adapter import PythonAdapter

    register(PythonAdapter, "python")

    try:
        from .javascript_adapter import JavaScriptAdapter

        register(JavaScriptAdapter, "javascript")
    except ImportError:
        pass
    try:
        from .javascript_adapter import JavaScriptAdapter

        register(JavaScriptAdapter, "jsx")
    except ImportError:
        pass
    try:
        from .typescript_adapter import TypeScriptAdapter

        register(TypeScriptAdapter, "typescript")
    except ImportError:
        pass
    try:
        from .typescript_adapter import TypeScriptAdapter

        register(TypeScriptAdapter, "tsx")
    except ImportError:
        pass

    from .c_like import load_c_like_adapters

    for language, adapter in load_c_like_adapters().items():
        adapters[language] = adapter

    return adapters


__all__ = ["load_adapters"]