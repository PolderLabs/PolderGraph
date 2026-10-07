"""Workspace: index directory layout, root registry and lifecycle."""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config.loader import LoadedConfig, load_config, write_config
from .config.models import Config
from .discovery.scanner import INDEX_DIR_NAME, detect_root, root_id_for
from .errors import CorruptIndexError, IndexMissingError
from .storage.schema import INDEX_FORMAT_VERSION, SCHEMA_VERSION
from .storage.sqlite import connect, current_schema_version, database_size_bytes, initialize

STATE_FILE = "state.json"
DB_FILE = "index.sqlite3"


@dataclass
class Workspace:
    """An opened PolderGraph index and the roots it covers."""

    root: Path
    index_dir: Path
    con: Any
    loaded: LoadedConfig
    roots: list[dict[str, Any]] = field(default_factory=list)

    @property
    def config(self) -> Config:
        return self.loaded.config

    @property
    def primary_root(self) -> Path:
        return self.root

    def root_id(self) -> str:
        return root_id_for(self.root)

    def path_for(self, relative: str) -> Path | None:
        """Resolve an index path to a real file, refusing traversal."""
        from .discovery.scanner import safe_join

        return safe_join(self.root, relative)

    def state(self) -> dict[str, Any]:
        return read_state(self.index_dir)

    def write_state(self, **updates: Any) -> None:
        write_state(self.index_dir, **updates)

    def close(self) -> None:
        try:
            self.con.close()
        except Exception:
            pass


def index_dir_for(root: Path) -> Path:
    return root / INDEX_DIR_NAME


def find_index_dir(start: Path | None = None) -> Path | None:
    """Locate an existing index by walking up from ``start``."""
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for directory in [current, *current.parents]:
        candidate = directory / INDEX_DIR_NAME
        if (candidate / DB_FILE).is_file():
            return candidate
    return None


def read_state(index_dir: Path) -> dict[str, Any]:
    path = index_dir / STATE_FILE
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_state(index_dir: Path, **updates: Any) -> None:
    """Merge updates into state.json atomically."""
    state = read_state(index_dir)
    state.update(updates)
    path = index_dir / STATE_FILE
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def create_index(root: Path, config: Config | None = None) -> Path:
    """Create the `.poldergraph/` layout for a root."""
    index_dir = index_dir_for(root)
    index_dir.mkdir(parents=True, exist_ok=True)
    (index_dir / "logs").mkdir(exist_ok=True)
    (index_dir / "cache").mkdir(exist_ok=True)
    (index_dir / "cache" / "model").mkdir(exist_ok=True)
    (index_dir / "cache" / "media").mkdir(exist_ok=True)
    if config is not None:
        write_config(config, index_dir)
    elif not (index_dir / "config.toml").is_file():
        write_config(Config(), index_dir)
    con = initialize(index_dir / DB_FILE)
    con.close()
    write_state(index_dir, created_at=time.time(), schema_version=SCHEMA_VERSION)
    return index_dir


def open_workspace(
    path: Path | None = None,
    *,
    require_index: bool = True,
    cli_overrides: dict[str, Any] | None = None,
) -> Workspace:
    """Open (or locate) the index covering a path."""
    if path is not None:
        given = path.resolve()
        index_dir = index_dir_for(given) if given.is_dir() else find_index_dir(given.parent)
        root = given if given.is_dir() else (index_dir.parent if index_dir else None)
        if index_dir is None or not (index_dir / DB_FILE).is_file():
            if require_index:
                raise IndexMissingError(
                    f"No PolderGraph index found at {given}.",
                    details={"path": str(given)},
                )
            index_dir = create_index(given)
            root = given
    else:
        index_dir = find_index_dir()
        if index_dir is None:
            detected = detect_root()
            index_dir = index_dir_for(detected)
            if not (index_dir / DB_FILE).is_file():
                if require_index:
                    raise IndexMissingError()
                create_index(detected)
            root = index_dir.parent
        else:
            root = index_dir.parent

    loaded = load_config(index_dir, cli_overrides=cli_overrides)
    try:
        con = initialize(index_dir / DB_FILE)
    except Exception as exc:
        raise CorruptIndexError(
            f"Cannot open index at {index_dir / DB_FILE}: {exc}",
            details={"index_dir": str(index_dir)},
        ) from exc

    version = current_schema_version(con)
    if version > SCHEMA_VERSION:
        con.close()
        raise CorruptIndexError(
            f"Index schema version {version} is newer than this build supports ({SCHEMA_VERSION}).",
            remediation="Upgrade PolderGraph, or run: poldergraph rebuild",
        )

    workspace = Workspace(root=root, index_dir=index_dir, con=con, loaded=loaded)
    workspace.roots = _read_roots(con)
    return workspace


def _read_roots(con: Any) -> list[dict[str, Any]]:
    rows = con.execute("SELECT root_id, path, name, is_primary FROM roots ORDER BY is_primary DESC, name").fetchall()
    return [dict(r) for r in rows]


def index_size_bytes(workspace: Workspace) -> int:
    return database_size_bytes(workspace.index_dir)


def remove_index(index_dir: Path) -> None:
    """Delete an index directory. Used only by an explicit rebuild."""
    if index_dir.exists():
        shutil.rmtree(index_dir)


def format_version() -> int:
    return INDEX_FORMAT_VERSION