"""CLI helpers: workspace/service construction and output rendering."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .config.models import Config
from .errors import (
    API_VERSION,
    ExitCode,
    PolderGraphError,
    envelope,
)
from .storage.repository import Repository
from .storage.vectors import backend_name, create_vector_store
from .workspace import Workspace, open_workspace


def emit_json(payload: dict[str, Any]) -> None:
    """Write a JSON document to stdout, one compact object."""
    sys.stdout.write(json.dumps(payload, separators=(",", ":"), default=str) + "\n")
    sys.stdout.flush()


def emit_error(command: str, error: PolderGraphError, *, warnings: list[str] | None = None) -> int:
    payload = envelope(command=command, error=error, warnings=warnings)
    emit_json(payload)
    return int(error.exit_code)


def build_service(
    path: Path | None,
    *,
    require_index: bool = True,
    need_backend: bool = False,
    offline: bool = False,
    cli_overrides: dict[str, Any] | None = None,
) -> tuple[Workspace, Repository, Any]:
    """Open a workspace and build the shared query service."""
    from .embedding.gemma import create_backend
    from .retrieval.service import QueryService

    workspace = open_workspace(path, require_index=require_index, cli_overrides=cli_overrides)
    repo = Repository(workspace.con)
    backend = None
    if need_backend and workspace.config.embedding.backend != "none":
        backend = create_backend(
            workspace.config,
            cache_dir=workspace.index_dir / "cache" / "model",
            offline=offline,
        )
    service = QueryService(
        repo, workspace.config, backend, root_id=workspace.root_id(), workspace=workspace
    )
    return workspace, repo, service


def freshness_payload(service: Any) -> dict[str, Any]:
    return service.freshness()


def model_payload(service: Any) -> dict[str, Any]:
    """Model metadata for the JSON index block."""
    backend = getattr(service, "backend", None)
    if backend is None or not backend.capabilities():
        return {"model": None, "dimensions": None, "revision": None}
    try:
        info = backend.model_info()
    except Exception:
        return {"model": None, "dimensions": None, "revision": None}
    return {
        "model": info.model_id,
        "dimensions": info.dimensions,
        "revision": info.revision,
        "backend": info.backend,
    }


def vector_backend_name(workspace: Workspace) -> str:
    store = create_vector_store(
        workspace.con,
        dimensions=workspace.config.index.dimensions,
        model_id=workspace.config.embedding.model,
    )
    return backend_name(store)


def table(rows: list[list[str]], headers: list[str]) -> str:
    """Render a simple aligned text table."""
    if not rows:
        return ""
    widths = [len(h) for h in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(str(cell)))
    lines = ["  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)).rstrip()]
    lines.append("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        lines.append("  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)).rstrip())
    return "\n".join(lines)


def entity_line(entity: Any, *, extra: str = "") -> str:
    location = ""
    if entity.path:
        location = f"{entity.path}:{entity.start_line + 1}" if entity.start_line is not None else entity.path
    name = entity.qualified_name or entity.name
    suffix = f"  {extra}" if extra else ""
    return f"{name}  [{entity.kind}]  {location}{suffix}"


def truncate(text: str, limit: int = 400) -> str:
    if not text:
        return ""
    return text if len(text) <= limit else text[: limit - 1] + "…"


__all__ = [
    "API_VERSION",
    "Config",
    "ExitCode",
    "build_service",
    "emit_error",
    "emit_json",
    "entity_line",
    "freshness_payload",
    "model_payload",
    "table",
    "truncate",
    "vector_backend_name",
]