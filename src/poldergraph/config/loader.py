"""Configuration loading with explicit precedence and origin tracking."""

from __future__ import annotations

import json
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import platformdirs

from ..errors import ConfigError
from .models import ENV_PREFIX, Config


@dataclass
class LoadedConfig:
    """A resolved config plus the origin of every explicitly-set value."""

    config: Config
    workspace_config_path: Path | None = None
    user_config_path: Path | None = None
    origins: dict[str, str] = field(default_factory=dict)

    def origin_of(self, dotted: str) -> str:
        return self.origins.get(dotted, "default")

    def effective(self) -> dict[str, Any]:
        return self.config.to_toml_dict()


def user_config_path() -> Path:
    return Path(platformdirs.user_config_dir("poldergraph")) / "config.toml"


#: Config fields whose value is itself a mapping; they are leaves, not sections.
_LEAF_MAPPING_KEYS: frozenset[str] = frozenset({"weights", "kind_priors"})


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any], origin: str, origins: dict[str, str], prefix: str = "") -> dict[str, Any]:
    """Merge overlay into base, recording which origin supplied each leaf."""
    for key, value in overlay.items():
        dotted = f"{prefix}{key}"
        if isinstance(value, dict) and key not in _LEAF_MAPPING_KEYS:
            nested = base.get(key)
            if not isinstance(nested, dict):
                nested = {}
                base[key] = nested
            _deep_merge(nested, value, origin, origins, prefix=f"{dotted}.")
        else:
            base[key] = value
            origins[dotted] = origin
    return base


def _coerce_scalar(raw: str) -> Any:
    lowered = raw.strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def env_overrides(environ: dict[str, str] | None = None) -> dict[str, Any]:
    """Translate POLDERGRAPH_ env vars into a nested dict.

    ``POLDERGRAPH_EMBEDDING__DEVICE=cuda`` becomes ``{"embedding": {"device": "cuda"}}``.
    """
    environ = os.environ if environ is None else environ
    result: dict[str, Any] = {}
    for key, raw in environ.items():
        if not key.startswith(ENV_PREFIX):
            continue
        remainder = key[len(ENV_PREFIX) :].lower()
        if not remainder:
            continue
        parts = [p for p in remainder.split("__") if p]
        node = result
        for part in parts[:-1]:
            nxt = node.get(part)
            if not isinstance(nxt, dict):
                nxt = {}
                node[part] = nxt
            node = nxt
        node[parts[-1]] = _coerce_scalar(raw)
    return result


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            f"Invalid TOML in {path}: {exc}",
            remediation=f"Fix the syntax in {path} or delete the file to use defaults.",
        ) from exc
    except OSError as exc:
        raise ConfigError(
            f"Cannot read config {path}: {exc}", remediation="Check file permissions."
        ) from exc


def _apply_overrides(raw: dict[str, Any]) -> dict[str, Any]:
    """Apply CLI flag overrides onto a config-shaped dict."""
    cli = json.loads(os.environ.get("POLDERGRAPH_CLI_OVERRIDES", "{}"))
    return _deep_merge(raw, cli, "cli", {})


def load_config(
    index_dir: Path | None = None,
    *,
    environ: dict[str, str] | None = None,
    cli_overrides: dict[str, Any] | None = None,
    user_path: Path | None = None,
) -> LoadedConfig:
    """Resolve configuration from all sources and record value origins."""
    origins: dict[str, str] = {}
    raw: dict[str, Any] = {}

    upath = user_path if user_path is not None else user_config_path()
    loaded_user = False
    if upath.is_file():
        _deep_merge(raw, _read_toml(upath), "user", origins)
        loaded_user = True

    wpath = None
    if index_dir is not None:
        wpath = index_dir / "config.toml"
        if wpath.is_file():
            _deep_merge(raw, _read_toml(wpath), "workspace", origins)

    env = env_overrides(environ)
    if env:
        _deep_merge(raw, env, "env", origins)

    if cli_overrides:
        _deep_merge(raw, cli_overrides, "cli", origins)

    try:
        config = Config.model_validate(_apply_overrides(raw))
    except Exception as exc:
        raise ConfigError(
            f"Invalid configuration: {exc}",
            remediation="Run: poldergraph config show --effective",
        ) from exc

    return LoadedConfig(
        config=config,
        workspace_config_path=wpath if wpath and wpath.is_file() else None,
        user_config_path=upath if loaded_user else None,
        origins=origins,
    )


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(v) for v in value) + "]"
    if value is None:
        return '""'
    return f'"{value}"'


def _toml_table(name: str, data: dict[str, Any], lines: list[str]) -> None:
    """Emit a TOML table, recursing into nested mappings as sub-tables."""
    lines.append("")
    lines.append(f"[{name}]")
    for key, value in data.items():
        if isinstance(value, dict) or value is None:
            continue
        lines.append(f"{key} = {_toml_value(value)}")
    for key, value in data.items():
        if isinstance(value, dict):
            _toml_table(f"{name}.{key}", value, lines)


def write_config(config: Config, index_dir: Path) -> Path:
    """Write the documented config.toml shape (round-trips through load_config)."""
    path = index_dir / "config.toml"
    data = config.to_toml_dict()
    lines: list[str] = [f"version = {_toml_value(data['version'])}"]
    for section in (
        "index", "embedding", "semantic_edges", "graph", "retrieval", "ui", "privacy", "decisions"
    ):
        _toml_table(section, data[section], lines)
    if data.get("exclude"):
        lines.append("")
        lines.append(f"exclude = {_toml_value(data['exclude'])}")
    if data.get("include"):
        lines.append("")
        lines.append(f"include = {_toml_value(data['include'])}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
