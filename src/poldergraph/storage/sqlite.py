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
from contextlib import contextmanager, suppress
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
    if not read_only:
        _recover_wal(path, con)
    return con


def _recover_wal(path: Path, con: sqlite3.Connection) -> None:
    """Fold a carried-over write-ahead log back into the database.

    Copying or moving a repository while its index was open leaves a non-empty
    ``-wal`` and a ``-shm`` that no longer match this file. SQLite can then fail
    writes with "attempt to write a readonly database", which used to surface as
    an empty result set plus a vector-only warning. Checkpointing the log on open
    restores a consistent, writable index.
    """
    wal = Path(f"{path}-wal")
    try:
        if not wal.exists() or wal.stat().st_size == 0:
            return
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except sqlite3.DatabaseError:
        # Recovery is best-effort: a busy or locked database is still readable,
        # and any real problem must surface from the actual failing operation.
        return


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
        with suppress(sqlite3.DatabaseError):
            con.enable_load_extension(False)


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
    """Create or open an index database, migrating it to the current schema.

    The index-format stamp is deliberately *not* written here. This function
    runs on every workspace open, so stamping it would assert that the stored
    contents match the current build even when an older index was just opened
    untouched — permanently disarming the rebuild guard. A newly created
    database has no contents to be stale, so it records the current format;
    an existing one keeps its stamp until a run actually rewrites its files.
    """
    created = not path.exists()
    con = connect(path)
    migrate(con)
    if created:
        set_meta(con, "index_format_version", INDEX_FORMAT_VERSION)
    return con


class IndexLock:
    """Exclusive writer lock for one index directory.

    Uses an OS-level advisory lock so a crashed process releases the lock
    automatically instead of leaving a stale lock behind.
    """

    def __init__(
        self, index_dir: Path, *, timeout: float = 0.0, lock_name: str = "lock"
    ) -> None:
        self.path = index_dir / lock_name
        self.timeout = timeout
        self._fd: int | None = None
        self._windows_lock = False

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(str(self.path), os.O_CREAT | os.O_RDWR, 0o644)
        if os.name == "nt":  # pragma: no cover - exercised on Windows CI
            import msvcrt

            if os.fstat(self._fd).st_size == 0:
                # Initialize through append mode. Concurrent first-time
                # contenders may each append a marker, but they can never
                # write into byte zero after another contender has locked it.
                with open(self.path, "ab", buffering=0) as marker:
                    marker.write(b"\0")
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                if os.name == "nt":  # pragma: no cover - exercised on Windows CI
                    import msvcrt

                    os.lseek(self._fd, 0, os.SEEK_SET)
                    msvcrt.locking(self._fd, msvcrt.LK_NBLCK, 1)
                    self._windows_lock = True
                else:
                    import fcntl

                    fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
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
            if self._windows_lock:  # pragma: no cover - exercised on Windows CI
                import msvcrt

                os.lseek(self._fd, 0, os.SEEK_SET)
                msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._fd, fcntl.LOCK_UN)
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
        with suppress(OSError):
            total += candidate.stat().st_size
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
