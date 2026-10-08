"""Incremental update planning.

mtime is only a fast-change hint; the content hash is authoritative. A file whose
normalized semantic input is unchanged keeps its existing vector even when its
bytes changed, so formatting churn never forces re-embedding.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from ..discovery.scanner import DiscoveredFile
from ..embedding.representation import normalize_representation
from ..storage.repository import Repository
from ..storage.schema import INDEX_FORMAT_VERSION


@dataclass
class UpdatePlan:
    """What an incremental run must do."""

    added: list[DiscoveredFile] = field(default_factory=list)
    changed: list[DiscoveredFile] = field(default_factory=list)
    unchanged: list[DiscoveredFile] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    stale_format: bool = False
    embedding_space_changed: bool = False

    @property
    def to_index(self) -> list[DiscoveredFile]:
        return [*self.added, *self.changed]

    @property
    def has_work(self) -> bool:
        return bool(
            self.added or self.changed or self.removed or self.stale_format
            or self.embedding_space_changed
        )

    def summary(self) -> dict[str, Any]:
        return {
            "added": len(self.added),
            "changed": len(self.changed),
            "unchanged": len(self.unchanged),
            "removed": len(self.removed),
            "stale_format": self.stale_format,
            "embedding_space_changed": self.embedding_space_changed,
        }


def plan_update(
    repo: Repository,
    discovered: list[DiscoveredFile],
    *,
    root_id: str,
    verify_hashes: bool = True,
    force: bool = False,
    embedding_space_id: str | None = None,
) -> UpdatePlan:
    """Compare the filesystem against the index and plan the work."""
    plan = UpdatePlan()
    # An index written by an older format version stores representations this
    # build no longer produces (0-based spans, cross-language edges).
    # Re-parsing only files whose hashes moved would leave the rest wrong
    # forever, so a format change forces a full re-verify. This lives here
    # rather than in one caller so the CLI, the watcher and MCP updates all
    # get it.
    if not index_format_current(repo):
        plan.stale_format = True
        force = True
    if embedding_space_id is not None:
        from ..storage.sqlite import get_meta

        plan.embedding_space_changed = (
            get_meta(repo.con, "embedding_space_id") != embedding_space_id
        )
        force = force or plan.embedding_space_changed
    known = {record["path"]: record for record in repo.all_files(root_id)}

    for file in discovered:
        record = known.get(file.path)
        if record is None:
            plan.added.append(file)
            continue
        if force:
            plan.changed.append(file)
            continue
        # Fast path: size and mtime unchanged means the file almost certainly
        # did not change. `verify_hashes` re-reads the bytes to be certain.
        if (
            record["size"] == file.size
            and record["mtime_ns"] == file.mtime_ns
            and record["content_hash"]
            and not verify_hashes
        ):
            plan.unchanged.append(file)
            continue
        digest = _hash_file(file)
        if digest == record["content_hash"]:
            plan.unchanged.append(file)
            continue
        plan.changed.append(file)

    discovered_paths = {file.path for file in discovered}
    for path in known:
        if path not in discovered_paths:
            plan.removed.append(path)

    return plan


def _hash_file(file: DiscoveredFile) -> str:
    from ..models.entity import content_hash

    try:
        return content_hash(file.abs_path.read_bytes())
    except OSError:
        return ""


def embedding_space_fingerprint(backend: Any) -> str | None:
    """Return a stable, secret-free identity for all vector-space settings."""
    if backend is None or not backend.capabilities():
        return None
    info = backend.model_info()
    from ..embedding.representation import REPRESENTATION_VERSION

    identity = {
        "backend": info.backend,
        "model_id": info.model_id,
        "revision": info.revision,
        "dimensions": info.dimensions,
        "normalize": info.normalize,
        "prompt_query": info.prompt_query,
        "prompt_document": info.prompt_document,
        "representation_version": REPRESENTATION_VERSION,
        "task_policy": ["document", "query"],
    }
    raw = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def semantic_input_changed(old_hash: str | None, new_text: str) -> bool:
    """True when the normalized embedding input differs from the stored hash."""
    from ..models.entity import semantic_hash

    return semantic_hash(normalize_representation(new_text)) != old_hash


def index_format_current(repo: Repository) -> bool:
    from ..storage.sqlite import get_meta

    stored = get_meta(repo.con, "index_format_version")
    return stored is not None and int(stored) == INDEX_FORMAT_VERSION
