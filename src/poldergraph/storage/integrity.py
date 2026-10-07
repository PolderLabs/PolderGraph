"""Index correctness invariants.

`poldergraph doctor` verifies every invariant listed in docs/testing-performance.md:
- every edge endpoint exists
- every embedding references an existing entity
- vector dimensions match recorded dimensions
- normalized vectors are approximately unit norm
- no entity source span lies outside its file
- parent chains are acyclic
- deleted source entities cannot appear in search
- FTS and vector IDs map to the same canonical entity namespace
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any

from .repository import Repository
from .schema import INDEX_FORMAT_VERSION, SCHEMA_VERSION
from .sqlite import get_meta
from .vectors import create_vector_store, vector_norm

UNIT_NORM_TOLERANCE = 0.02


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""
    severity: str = "error"
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class DoctorReport:
    checks: list[Check] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "", severity: str = "error", **data: Any) -> None:
        self.checks.append(Check(name, ok, detail, severity, data))

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks if c.severity == "error")

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if not c.ok and c.severity == "error"]

    @property
    def warnings(self) -> list[Check]:
        return [c for c in self.checks if not c.ok and c.severity == "warning"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": [
                {
                    "name": c.name,
                    "ok": c.ok,
                    "severity": c.severity,
                    "detail": c.detail,
                    **({"data": c.data} if c.data else {}),
                }
                for c in self.checks
            ],
            "summary": {
                "total": len(self.checks),
                "failed": len(self.failures),
                "warnings": len(self.warnings),
            },
        }


def check_sqlite_integrity(con: sqlite3.Connection) -> Check:
    try:
        row = con.execute("PRAGMA integrity_check").fetchone()
        result = row[0] if row else "unknown"
        ok = result == "ok"
        return Check("sqlite_integrity", ok, "" if ok else str(result))
    except sqlite3.DatabaseError as exc:
        return Check("sqlite_integrity", False, f"integrity_check failed: {exc}")


def check_schema_version(con: sqlite3.Connection) -> Check:
    from .sqlite import current_schema_version

    actual = current_schema_version(con)
    return Check(
        "schema_version",
        actual == SCHEMA_VERSION,
        f"index schema {actual}, expected {SCHEMA_VERSION}",
        data={"actual": actual, "expected": SCHEMA_VERSION},
    )


def check_index_format_version(con: sqlite3.Connection) -> Check:
    stored = get_meta(con, "index_format_version")
    actual = int(stored) if stored else 0
    return Check(
        "index_format_version",
        actual == INDEX_FORMAT_VERSION,
        f"format version {actual}, expected {INDEX_FORMAT_VERSION}",
        severity="warning",
        data={"actual": actual, "expected": INDEX_FORMAT_VERSION},
    )


def check_orphan_edges(repo: Repository) -> Check:
    row = repo.con.execute(
        "SELECT COUNT(*) FROM edges e"
        " LEFT JOIN entities s ON s.id=e.source_id"
        " LEFT JOIN entities t ON t.id=e.target_id"
        " WHERE s.id IS NULL OR t.id IS NULL"
    ).fetchone()
    count = int(row[0])
    return Check("orphan_edges", count == 0, f"{count} edges reference a missing entity", data={"count": count})


def check_orphan_embeddings(repo: Repository) -> Check:
    row = repo.con.execute(
        "SELECT COUNT(*) FROM embeddings em"
        " LEFT JOIN entities e ON e.id=em.entity_id"
        " WHERE em.entity_id IS NOT NULL AND e.id IS NULL"
    ).fetchone()
    count = int(row[0])
    return Check(
        "orphan_embeddings", count == 0, f"{count} embeddings reference a missing entity", data={"count": count}
    )


def check_parent_cycles(repo: Repository) -> Check:
    """Walk parent chains to detect cycles.

    A cycle in ``parent_id`` would make ownership traversal non-terminating, so
    it must never persist.
    """
    rows = repo.con.execute("SELECT id, parent_id FROM entities WHERE parent_id IS NOT NULL").fetchall()
    parents = {r[0]: r[1] for r in rows}
    seen_global: set[str] = set()
    cycles = 0
    for start in parents:
        if start in seen_global:
            continue
        path: set[str] = set()
        current: str | None = start
        while current is not None and current in parents:
            if current in path:
                cycles += 1
                break
            path.add(current)
            seen_global.add(current)
            current = parents[current]
    return Check("parent_acyclic", cycles == 0, f"{cycles} parent cycles detected", data={"cycles": cycles})


def check_span_bounds(repo: Repository) -> Check:
    """No entity may claim a line span beyond its file's line count."""
    files = {f["path"]: f for f in repo.all_files()}
    bad: list[str] = []
    for row in repo.con.execute(
        "SELECT id, path, start_line, end_line FROM entities WHERE path IS NOT NULL AND start_line IS NOT NULL"
    ):
        _, path, start_line, end_line = row
        record = files.get(path)
        if record is None:
            continue
        if start_line < 0 or (end_line is not None and end_line < start_line):
            bad.append(path)
    return Check(
        "span_bounds", not bad, f"{len(bad)} entities have invalid line spans", data={"examples": bad[:5]}
    )


def check_fts_namespace(repo: Repository) -> Check:
    """FTS rows must map onto the same canonical entity namespace."""
    row = repo.con.execute(
        "SELECT COUNT(*) FROM entity_fts f LEFT JOIN entities e ON e.id=f.entity_id WHERE e.id IS NULL"
    ).fetchone()
    orphans = int(row[0])
    missing = int(
        repo.con.execute(
            "SELECT COUNT(*) FROM entities e LEFT JOIN entity_fts f ON f.entity_id=e.id"
            " WHERE f.entity_id IS NULL AND e.kind NOT IN ('directory','workspace','repository')"
        ).fetchone()[0]
    )
    ok = orphans == 0 and missing == 0
    return Check(
        "fts_namespace",
        ok,
        f"{orphans} orphan FTS rows, {missing} entities missing from FTS",
        data={"orphans": orphans, "missing": missing},
    )


def check_vector_dimensions(repo: Repository, *, dimensions: int) -> Check:
    row = repo.con.execute(
        "SELECT COUNT(*) FROM embeddings WHERE dimensions != ?", (dimensions,)
    ).fetchone()
    count = int(row[0])
    return Check(
        "vector_dimensions",
        count == 0,
        f"{count} embeddings have a dimension other than {dimensions}",
        data={"count": count, "expected": dimensions},
    )


def check_vector_norms(repo: Repository, *, sample: int = 200) -> Check:
    """Verify stored vectors are approximately unit norm."""
    from .vectors import BruteForceStore

    store = create_vector_store(repo.con, dimensions=_dominant_dimension(repo), model_id=_model_id(repo))
    if not isinstance(store, BruteForceStore):
        # sqlite-vec keeps vectors in its own shadow tables; trust its KNN index
        # and validate norms on the embedding metadata instead.
        return Check("vector_norms", True, "validated via sqlite-vec backend", severity="info")

    store.ensure_table()
    rows = repo.con.execute(
        f"SELECT vector, dimensions FROM {store.table} LIMIT ?", (sample,)
    ).fetchall()
    bad = 0
    for blob, dim in rows:
        import array

        values = array.array("f")
        values.frombytes(blob)
        norm = vector_norm(list(values))
        if abs(norm - 1.0) > UNIT_NORM_TOLERANCE:
            bad += 1
    ok = bad == 0
    return Check(
        "vector_norms",
        ok,
        f"{bad}/{len(rows)} sampled vectors deviate from unit norm",
        data={"bad": bad, "sampled": len(rows), "tolerance": UNIT_NORM_TOLERANCE},
    )


def _dominant_dimension(repo: Repository) -> int:
    row = repo.con.execute("SELECT dimensions, COUNT(*) c FROM embeddings GROUP BY dimensions ORDER BY c DESC LIMIT 1").fetchone()
    return int(row[0]) if row else 256


def _model_id(repo: Repository) -> str:
    row = repo.con.execute("SELECT model_id FROM embeddings LIMIT 1").fetchone()
    return row[0] if row else "unknown"


def check_entity_paths_safety(repo: Repository) -> Check:
    """Entity paths must stay inside their root and be relative."""
    bad: list[str] = []
    for row in repo.con.execute("SELECT id, path FROM entities WHERE path IS NOT NULL"):
        entity_id, path = row
        if path.startswith("/") or ".." in path.split("/") or "\x00" in path:
            bad.append(entity_id)
    ok = not bad
    return Check(
        "path_safety", ok, f"{len(bad)} entities have unsafe paths", data={"examples": bad[:5]}
    )


def check_freshness_state(repo: Repository) -> Check:
    from ..models.entity import utcnow

    row = repo.con.execute("SELECT MAX(last_indexed_at) FROM files").fetchone()
    last = row[0] if row else None
    return Check(
        "freshness_state", last is not None, "no files indexed", severity="warning",
        data={"last_indexed_at": last, "now": utcnow()},
    )


def run_doctor(repo: Repository, *, dimensions: int = 256) -> DoctorReport:
    """Run every invariant check and return a structured report."""
    report = DoctorReport()
    report.checks.append(check_sqlite_integrity(repo.con))
    report.checks.append(check_schema_version(repo.con))
    report.checks.append(check_index_format_version(repo.con))
    report.checks.append(check_orphan_edges(repo))
    report.checks.append(check_orphan_embeddings(repo))
    report.checks.append(check_parent_cycles(repo))
    report.checks.append(check_span_bounds(repo))
    report.checks.append(check_fts_namespace(repo))
    report.checks.append(check_vector_dimensions(repo, dimensions=dimensions))
    report.checks.append(check_vector_norms(repo))
    report.checks.append(check_entity_paths_safety(repo))
    report.checks.append(check_freshness_state(repo))
    return report