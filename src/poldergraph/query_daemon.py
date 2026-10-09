"""Persistent query daemon.

Every ``poldergraph search``/``context`` invocation that needs semantics pays
the full embedding-backend setup: importing torch, building the model, moving it
to the device and warming it up. Measured on a warm cache that is ~6.3 s, and an
agent issuing a dozen queries pays it a dozen times.

The daemon keeps one workspace, one model and one vector store resident, so
repeat queries cost milliseconds. Clients connect over a unix socket, fall back
to in-process execution when the daemon is not running, and can be started on
demand.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import suppress
from pathlib import Path
from typing import Any

#: Unix socket name, created inside the workspace index directory so a daemon
#: serves exactly one index.
SOCKET_NAME = "query.sock"

#: Seconds a client waits for a cold daemon before giving up. Deliberately
#: close to the real model-load time so a failed spawn falls back to in-process
#: execution quickly instead of stalling the agent.
START_TIMEOUT = 45.0

#: Seconds a request may run before the client gives up.
REQUEST_TIMEOUT = 120.0


def resolve_index_dir(root: Path | None) -> Path | None:
    """Return the index directory for a workspace root, or None if unindexed."""
    from .workspace import find_index_dir, index_dir_for

    candidate = Path(root) if root else Path.cwd()
    found = find_index_dir(candidate)
    if found is not None:
        return found
    # No index yet; the conventional location is still where one would live.
    expected = index_dir_for(candidate if candidate.is_dir() else candidate.parent)
    return expected if (expected / "index.sqlite3").is_file() else None


def socket_path(index_dir: Path) -> Path:
    index_dir = Path(index_dir)
    path = index_dir / SOCKET_NAME
    # macOS and Windows impose short local-socket path limits. Deep worktrees
    # can exceed them, so use a stable runtime path when the canonical path is
    # too long. The hash keeps each workspace on its own socket.
    if len(os.fsencode(path)) >= 100:
        runtime_dir = Path("/tmp") if Path("/tmp").is_dir() else Path(tempfile.gettempdir())
        user_id = getattr(os, "getuid", lambda: os.environ.get("USERNAME", "user"))()
        workspace_id = hashlib.sha256(os.fsencode(index_dir.resolve())).hexdigest()[:20]
        user_key = hashlib.sha256(str(user_id).encode()).hexdigest()[:8]
        path = runtime_dir / f"pg-{user_key}" / f"{workspace_id}.sock"
    return path


def is_running(index_dir: Path) -> bool:
    """True when a daemon is bound, has loaded its model, and answers."""
    if not hasattr(socket, "AF_UNIX"):
        return False
    path = socket_path(index_dir)
    if not path.exists():
        return False
    sock = _connect(index_dir, 1.0)
    if sock is None:
        return False
    try:
        payload = json.dumps({"command": "__ping__", "arguments": {}}).encode("utf-8")
        sock.sendall(len(payload).to_bytes(4, "big") + payload)
        header = _recv_exactly(sock, 4)
        if header is None:
            return False
        length = int.from_bytes(header, "big")
        return _recv_exactly(sock, length) is not None
    except OSError:
        return False
    finally:
        sock.close()


def _connect(index_dir: Path, timeout: float) -> socket.socket | None:
    if not hasattr(socket, "AF_UNIX"):
        return None
    path = socket_path(index_dir)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(str(path))
    except OSError:
        sock.close()
        return None
    return sock


def send_request(index_dir: Path, command: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
    """Send one request to a running daemon, or return None if unavailable."""
    sock = _connect(index_dir, REQUEST_TIMEOUT)
    if sock is None:
        return None
    try:
        payload = json.dumps({"command": command, "arguments": arguments}).encode("utf-8")
        sock.sendall(len(payload).to_bytes(4, "big") + payload)
        header = _recv_exactly(sock, 4)
        if header is None:
            return None
        length = int.from_bytes(header, "big")
        body = _recv_exactly(sock, length)
        if body is None:
            return None
        return json.loads(body.decode("utf-8"))
    except (OSError, ValueError):
        return None
    finally:
        sock.close()


def _named(arguments: dict[str, Any], service_key: str, client_key: str) -> Any:
    """Read a value that the CLI and the service call different things."""
    return arguments.get(service_key, arguments.get(client_key))


def _without(arguments: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {k: v for k, v in arguments.items() if k not in keys}


def _recv_exactly(sock: socket.socket, count: int) -> bytes | None:
    buffer = bytearray()
    while len(buffer) < count:
        chunk = sock.recv(count - len(buffer))
        if not chunk:
            return None
        buffer.extend(chunk)
    return bytes(buffer)


def ensure_daemon(root: Path, *, autostart: bool = True) -> bool:
    """Start the daemon for a workspace if it is not already running."""
    # Platforms without Unix domain sockets use the caller's in-process query
    # service; never spawn a daemon that cannot bind its transport.
    if not hasattr(socket, "AF_UNIX"):
        return False
    index_dir = resolve_index_dir(root)
    if index_dir is None:
        return False
    if is_running(index_dir):
        return True
    if not autostart or os.environ.get("POLDERGRAPH_NO_DAEMON"):
        return False

    path = socket_path(index_dir)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with suppress(OSError):
        path.parent.chmod(0o700)
    if path.exists():
        # A stale socket from a crashed daemon would block bind().
        with suppress(OSError):
            path.unlink()
    # Detach so the daemon outlives the client that started it.
    subprocess.Popen(
        [sys.executable, "-m", "poldergraph.query_daemon_main", str(root)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=os.name != "nt",
        env={**os.environ, "POLDERGRAPH_DAEMON": "1"},
    )
    deadline = time.monotonic() + START_TIMEOUT
    while time.monotonic() < deadline:
        if is_running(index_dir):
            return True
        time.sleep(0.05)
    return False


def stop_daemon(root: Path) -> bool:
    """Stop a running daemon for a workspace."""
    index_dir = resolve_index_dir(root)
    if index_dir is None:
        return False
    sock = _connect(index_dir, 2.0)
    if sock is None:
        return False
    try:
        payload = json.dumps({"command": "__shutdown__", "arguments": {}}).encode("utf-8")
        sock.sendall(len(payload).to_bytes(4, "big") + payload)
        _recv_exactly(sock, 4)
    except OSError:
        pass
    finally:
        sock.close()
    return True


class Daemon:
    """Serves retrieval commands for one workspace over a unix socket."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._workspace = None
        self._service = None
        self._server: socket.socket | None = None
        self._supervisor = None
        self._request_local = threading.local()
        self._read_connections: list[Any] = []
        self._read_connections_lock = threading.Lock()
        self._handlers: set[threading.Thread] = set()
        self._handlers_lock = threading.Lock()
        self._shutdown = threading.Event()

    def _ensure_loaded(self) -> Any:
        if self._service is not None:
            return self._service
        from .cli_support import build_service

        workspace, _repo, service = build_service(self.root, need_backend=True)
        # Load the embedding model now so the first client request is fast.
        backend = service.backend
        if backend is not None:
            with suppress(Exception):
                backend.model_info()
        self._workspace = workspace
        self._service = service
        from .indexing.supervisor import IndexSupervisor

        self._supervisor = IndexSupervisor(
            service.root,
            backend_provider=lambda: self._ensure_loaded().backend,
        )
        self._supervisor.start()
        return service

    def _service_for_thread(self) -> Any:
        """Give each concurrent client a SQLite connection and read snapshot."""
        base = self._ensure_loaded()
        service = getattr(self._request_local, "service", None)
        if service is not None:
            return service
        from .retrieval.service import QueryService
        from .storage.repository import Repository
        from .storage.sqlite import connect

        connection = connect(base.workspace_index() / "index.sqlite3", read_only=True)
        service = QueryService(
            Repository(connection),
            base.config,
            base.backend,
            root_id=base.root_id,
            workspace=base.workspace,
        )
        self._request_local.service = service
        with self._read_connections_lock:
            self._read_connections.append(connection)
        return service

    def close(self) -> None:
        """Close request-local readers and the resident workspace connection."""
        with self._read_connections_lock:
            connections, self._read_connections = self._read_connections, []
        for connection in connections:
            with suppress(Exception):
                connection.close()
        if self._workspace is not None:
            self._workspace.close()
            self._workspace = None

    def _release_thread_service(self) -> None:
        """Close the read connection owned by the current socket request."""
        service = getattr(self._request_local, "service", None)
        if service is None:
            return
        connection = service.repo.con
        with self._read_connections_lock:
            if connection in self._read_connections:
                self._read_connections.remove(connection)
        with suppress(Exception):
            connection.close()
        del self._request_local.service

    def handle(self, command: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute one request in a single committed SQLite read generation."""
        service = self._service_for_thread()
        connection = service.repo.con
        data_version_start = int(connection.execute("PRAGMA data_version").fetchone()[0])
        connection.execute("BEGIN")
        generation_start = service._index_generation()
        try:
            result = self._dispatch(command, arguments, service)
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        else:
            if connection.in_transaction:
                connection.execute("COMMIT")

        freshness = service.freshness()
        report = result.get("consistency_report") if isinstance(result, dict) else None
        if isinstance(report, dict):
            generation_end = freshness["generation"]
            changed = generation_start != generation_end
            database_changed = (
                int(connection.execute("PRAGMA data_version").fetchone()[0])
                != data_version_start
            )
            report["generation_start"] = generation_start
            report["generation_end"] = generation_end
            report["generation_changed"] = changed
            report["database_changed"] = database_changed
            report["structural_freshness"] = freshness["structural"]
            report["pending_changes"] = freshness["pending_changes"]
            report["stale_files"] = freshness["stale_files"]
            report["stale_files_truncated"] = freshness["stale_files_truncated"]
            report["stale_since"] = freshness["stale_since"]
            stale = not freshness["fresh"]
            if stale or changed or database_changed:
                report["status"] = (
                    "stale"
                    if stale
                    else "generation_changed"
                    if changed
                    else "database_changed"
                )
                report["source_read_required"] = True
                report["verified"] = False
            if report.get("mode") == "strict" and (stale or changed or database_changed):
                from .errors import IndexStaleError

                error = IndexStaleError(
                    "The index changed during this query.",
                    details={"freshness": freshness},
                )
                return {"ok": False, "error": error.to_dict()}
        if isinstance(result, dict) and isinstance(result.get("index"), dict):
            result["index"].update(freshness)
        return result

    def _dispatch(
        self, command: str, arguments: dict[str, Any], service: Any
    ) -> dict[str, Any]:
        """Dispatch a request while its read transaction is active."""
        from .errors import PolderGraphError

        try:
            if command == "search":
                from .retrieval.service import SearchFilters

                args = dict(arguments)
                # Filters cross a process boundary as plain dicts; rebuild them
                # so the service receives real SearchFilters objects.
                raw = args.pop("filters", None) or {}
                args["filters"] = SearchFilters(
                    kinds=list(raw.get("kinds") or []),
                    languages=list(raw.get("languages") or []),
                    roots=list(raw.get("roots") or []),
                    path_prefixes=list(raw.get("path_prefixes") or []),
                    provenances=list(raw.get("provenances") or []),
                )
                data = service.search(**args).to_dict()
                data["index"] = service.freshness()
                return data
            if command == "context":
                from .retrieval.service import SearchFilters

                args = dict(arguments)
                raw = args.pop("filters", None) or {}
                if raw:
                    args["filters"] = SearchFilters(
                        kinds=list(raw.get("kinds") or []),
                        languages=list(raw.get("languages") or []),
                        roots=list(raw.get("roots") or []),
                        path_prefixes=list(raw.get("path_prefixes") or []),
                    )
                result = service.context(**args)
                data = result.to_dict()
                # Memory recall and preference capture belong to context, so the
                # daemon runs them too; otherwise every client would redo the
                # embedding work this daemon exists to amortize.
                try:
                    from .memory import (
                        MemoryStore,
                        add_memories_to_context,
                    )

                    store = MemoryStore(service.root)
                    add_memories_to_context(
                        data, store, args.get("query", ""),
                        args.get("token_budget") or service.config.retrieval.default_context_tokens,
                        backend=service.backend,
                        decision_config=service.config.decisions,
                    )
                    from .retrieval.context import apply_evidence_cursor

                    apply_evidence_cursor(data, args.get("new_evidence_since"))
                    data["memories_learned"] = 0
                except Exception as exc:
                    data.setdefault("warnings", []).append(f"memory step skipped: {exc}")
                return data
            if command == "explain":
                return service.explain(
                    _named(arguments, "entity_ref", "entity"),
                    **_without(arguments, "entity", "entity_ref"),
                )
            if command == "related":
                return service.related(
                    _named(arguments, "entity_ref", "entity"),
                    **_without(arguments, "entity", "entity_ref"),
                )
            if command == "path":
                return service.path(
                    _named(arguments, "source_ref", "source"),
                    _named(arguments, "target_ref", "target"),
                    **_without(arguments, "source", "target"),
                )
            if command == "impact":
                return service.impact(
                    _named(arguments, "entity_ref", "entity"),
                    **_without(arguments, "entity", "entity_ref"),
                )
            if command.startswith("memory_"):
                return self._handle_memory(command[7:], arguments, service)
            if command == "status":
                return {
                    "counts": service.repo.counts(),
                    "freshness": service.freshness(),
                    "config": service.config.model_dump(),
                    "supervisor": (
                        self._supervisor.status() if self._supervisor else {"state": "stopped"}
                    ),
                }
        except (TypeError, ValueError) as exc:
            return {"ok": False, "error": {"code": "USAGE_ERROR", "message": str(exc)}}
        except PolderGraphError as exc:
            return {"ok": False, "error": exc.to_dict()}
        return {"ok": False, "error": {"code": "UNKNOWN_COMMAND", "message": f"Unknown command: {command}"}}

    def serve(self) -> None:
        """Accept connections until shutdown."""
        if not hasattr(socket, "AF_UNIX"):
            raise RuntimeError(
                "The query daemon requires Unix domain sockets on this platform; "
                "use the in-process query service instead."
            )
        from .workspace import index_dir_for

        index_dir = resolve_index_dir(self.root) or index_dir_for(self.root)
        index_dir.mkdir(parents=True, exist_ok=True)
        path = socket_path(index_dir)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with suppress(OSError):
            path.parent.chmod(0o700)
        if path.exists():
            path.unlink()

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(path))
        server.listen(16)
        server.settimeout(0.5)
        os.chmod(path, 0o600)
        self._server = server
        self._shutdown.clear()

        # Load the model before accepting connections. The socket is bound but
        # the client connect() would succeed, so readiness is signalled by the
        # daemon answering; ensure_daemon's poll below waits for a real reply.
        try:
            self._ensure_loaded()
            while True:
                try:
                    conn, _ = server.accept()
                except TimeoutError:
                    if self._shutdown.is_set():
                        break
                    continue
                except OSError:
                    break
                handler = threading.Thread(
                    target=self._serve_connection,
                    args=(conn,),
                    name="poldergraph-query-client",
                    daemon=True,
                )
                with self._handlers_lock:
                    self._handlers.add(handler)
                handler.start()
        finally:
            server.close()
            with self._handlers_lock:
                handlers = list(self._handlers)
            for handler in handlers:
                handler.join(timeout=REQUEST_TIMEOUT)
            if self._supervisor is not None:
                self._supervisor.stop()
            self.close()
            if path.exists():
                path.unlink()

    def _serve_connection(self, conn: socket.socket) -> None:
        try:
            with conn:
                self._serve_one(conn)
        finally:
            self._release_thread_service()
            with self._handlers_lock:
                self._handlers.discard(threading.current_thread())

    def _handle_memory(
        self, action: str, arguments: dict[str, Any], service: Any
    ) -> dict[str, Any]:
        """Serve a memory operation using the resident embedding backend.

        Memory search needs the same model the graph does, so serving it here
        removes the per-command model setup an agent would otherwise pay on
        every recall.
        """
        from .memory import MemoryStore

        store = MemoryStore(service.root)
        if action == "status":
            return store.status()
        if action == "search":
            results = store.search(
                arguments.get("query", ""),
                scope=arguments.get("scope", "all"),
                limit=int(arguments.get("limit", 10)),
                backend=service.backend,
            )
            return {"query": arguments.get("query", ""),
                    "scope": arguments.get("scope", "all"), "results": results}
        if action == "list":
            memories = store.list(
                scope=arguments.get("scope", "all"),
                limit=int(arguments.get("limit", 50)),
            )
            return {"scope": arguments.get("scope", "all"), "results": memories}
        if action == "add":
            created = store.add(
                arguments["content"],
                scope=arguments.get("scope", "user"),
                kind=arguments.get("kind", "fact"),
                tags=arguments.get("tags") or [],
                backend=service.backend,
            )
            return {"memory": created, "created": True}
        if action == "update":
            return {
                "memory": store.update(
                    arguments["id"],
                    content=arguments.get("content"),
                    kind=arguments.get("kind"),
                    tags=arguments.get("tags"),
                    backend=service.backend,
                ),
                "updated": True,
            }
        if action == "forget":
            return {"memory": store.forget(arguments["id"]), "deleted": True}
        if action == "repair":
            return store.repair_vectors(service.backend)
        return {"ok": False, "error": {"code": "UNKNOWN_COMMAND",
                                       "message": f"Unknown memory action: {action}"}}

    def _serve_one(self, conn: socket.socket) -> None:
        conn.settimeout(REQUEST_TIMEOUT)
        try:
            header = _recv_exactly(conn, 4)
            if header is None:
                return
            length = int.from_bytes(header, "big")
            body = _recv_exactly(conn, length)
            if body is None:
                return
            request = json.loads(body.decode("utf-8"))
            if request.get("command") == "__ping__":
                result = {"ok": True}
            elif request.get("command") == "__shutdown__":
                payload = json.dumps({"ok": True}).encode("utf-8")
                conn.sendall(len(payload).to_bytes(4, "big") + payload)
                self._shutdown.set()
                return
            else:
                result = self.handle(request["command"], request.get("arguments", {}))
        except Exception as exc:  # a bad request must not kill the daemon
            result = {"ok": False, "error": {"code": "DAEMON_ERROR", "message": str(exc)}}

        try:
            payload = json.dumps(result, default=str).encode("utf-8")
            conn.sendall(len(payload).to_bytes(4, "big") + payload)
        except OSError:
            pass
