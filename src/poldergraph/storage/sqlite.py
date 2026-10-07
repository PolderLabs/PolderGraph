"""SQLite connection management: WAL policy, migrations and writer locking.

Concurrency model:
- exactly one writer per index, guarded by an OS-level lock file
- unlimited concurrent readers via WAL mode
- migrations take an exclusive lock so a schema change cannot race a writer
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ..errors import CorruptIndexError, IndexLockedError
from .schema import INDEX_FORMAT_VERSION, MIGRATIONS, SCHEMA_VERSION

BUSY_TIMEOUT_MS = 10_000


def connect(path: Path, *, read_only: bool = False) -> sqlite3.Connection:
    """Open a tuned SQLite connection with WAL and foreign keys enabled."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if read_only and path.exists():
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=BUSY_TIMEOUT_MS / 1000)
    else:
        con = sqlite3.connect(
            str(path),
            timeout=BUSY_TIMEOUT_MS / 1000,
            isolation_level=None,
            # The dashboard serves requests on a thread pool, so the connection
            # is shared across worker threads. WAL mode makes concurrent reads
            # safe; writes are still serialized by the index writer lock.
            check_same_thread=False,
        )

    con.row_factory = sqlite3.Row
    cur = con.cursor()
    if not read_only:
        try:
            cur.execute("PRAGMA journal_mode=WAL")
        except sqlite3.DatabaseError as exc:  # pragma: no cover - unusual filesystems
            raise CorruptIndexError(f"Cannot enable WAL journal mode: {exc}") from exc
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    cur.execute("PRAGMA synchronous=NORMAL")
    cur.execute("PRAGMA temp_store=MEMORY")
    cur.execute("PRAGMA cache_size=-32000")
    cur.close()
    return con


def load_vec_extension(con: sqlite3.Connection) -> bool:
    """Load sqlite-vec when available. Returns False if the extension is missing."""
    try:
        import sqlite_vec
    except ImportError:
        return False
    try:
        con.enable_load_extension(True)
        sqlite_vec.load(con)
        return bool(con.execute("select vec_version()").fetchone()[0])
    except (sqlite3.DatabaseError, AttributeError):
        return False
    finally:
        try:
            con.enable_load_extension(False)
        except sqlite3.DatabaseError:  # pragma: no cover
            pass


def current_schema_version(con: sqlite3.Connection) -> int:
    row = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='meta'"
    ).fetchone()
    if row is None:
        return 0
    row = con.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    return int(row[0]) if row else 0


def get_meta(con: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    try:
        row = con.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    except sqlite3.OperationalError:
        return default
    return row[0] if row else default


def set_meta(con: sqlite3.Connection, key: str, value: Any) -> None:
    con.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )


def migrate(con: sqlite3.Connection, *, force: bool = False) -> int:
    """Apply pending migrations transactionally. Idempotent via version guard."""
    version = current_schema_version(con)
    if version > SCHEMA_VERSION:
        raise CorruptIndexError(
            f"Index schema version {version} is newer than supported version {SCHEMA_VERSION}.",
            remediation="Upgrade PolderGraph, or run: poldergraph rebuild",
        )
    if version == SCHEMA_VERSION and not force:
        return version

    for target, statements in MIGRATIONS:
        if target <= version:
            continue
        con.execute("BEGIN IMMEDIATE")
        try:
            for statement in statements:
                con.execute(statement)
            con.execute(
                "INSERT INTO meta(key, value) VALUES('schema_version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(target),),
            )
            con.commit()
        except Exception:
            con.rollback()
            raise
        version = target
    return version


def initialize(path: Path) -> sqlite3.Connection:
    """Create or open an index database, migrating it to the current schema."""
    con = connect(path)
    migrate(con)
    set_meta(con, "index_format_version", INDEX_FORMAT_VERSION)
    return con


class IndexLock:
    """Exclusive writer lock for one index directory.

    Uses an OS-level advisory lock so a crashed process releases the lock
    automatically instead of leaving a stale lock behind.
    """

    def __init__(self, index_dir: Path, *, timeout: float = 0.0) -> None:
        self.path = index_dir / "lock"
        self.timeout = timeout
        self._fd: int | None = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(str(self.path), os.O_CREAT | os.O_RDWR, 0o644)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                import fcntl

                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except ImportError:  # pragma: no cover - Windows
                return
            except OSError:
                if time.monotonic() >= deadline:
                    os.close(self._fd)
                    self._fd = None
                    raise IndexLockedError(
                        "The PolderGraph index is locked by another process.",
                        details={"lock_path": str(self.path)},
                    ) from None
                time.sleep(0.05)

    def release(self) -> None:
        if self._fd is None:
            return
        try:
            import fcntl

            fcntl.flock(self._fd, fcntl.LOCK_UN)
        except ImportError:  # pragma: no cover - Windows
            pass
        finally:
            os.close(self._fd)
            self._fd = None

    def __enter__(self) -> IndexLock:
        self.acquire()
        return self

    def __exit__(self, *exc: object) -> None:
        self.release()


@contextmanager
def writer_transaction(con: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run a batch of writes in one IMMEDIATE transaction.

    A failed batch rolls back completely, so an interrupted indexing run cannot
    leave a logically inconsistent graph.
    """
    con.execute("BEGIN IMMEDIATE")
    try:
        yield con
    except Exception:
        con.rollback()
        raise
    else:
        con.commit()


def index_paths(index_dir: Path) -> tuple[Path, Path]:
    """Return (database, wal) paths for an index directory."""
    return index_dir / "index.sqlite3", index_dir / "index.sqlite3-wal"


def database_size_bytes(index_dir: Path) -> int:
    db, wal = index_paths(index_dir)
    total = 0
    for candidate in (db, wal, db.with_suffix(".sqlite3-shm")):
        try:
            total += candidate.stat().st_size
        except OSError:
            pass
    return total


def record_change_event(
    con: sqlite3.Connection, kind: str, entity_ids: list[str] | None = None
) -> int:
    """Append a change event for the dashboard live-update stream."""
    payload = json.dumps(entity_ids or [], separators=(",", ":"))
    cur = con.execute(
        "INSERT INTO change_events(kind, entity_ids, created_at) VALUES(?, ?, ?)",
        (kind, payload, int(time.time())),
    )
    return int(cur.lastrowid or 0)


def prune_change_events(con: sqlite3.Connection, keep: int = 500) -> None:
    """Keep the change log bounded."""
    con.execute(
        "DELETE FROM change_events WHERE event_id <= "
        "(SELECT MAX(event_id) - ? FROM change_events)",
        (keep,),
    )