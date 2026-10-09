"""In-process lifecycle wrapper for one workspace's live index watcher."""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any


class IndexSupervisor:
    """Start and stop one debounced watcher without blocking its host process."""

    def __init__(
        self, root: Path, *, backend_provider: Any = None, reconcile_interval: float | None = None
    ) -> None:
        if reconcile_interval is not None and reconcile_interval <= 0:
            raise ValueError("reconcile_interval must be greater than zero")
        self.root = root.resolve()
        self.backend_provider = backend_provider
        self.reconcile_interval = reconcile_interval
        self._stop = threading.Event()
        self._started = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._status = "stopped"
        self._error: str | None = None

    def start(self, *, wait_seconds: float = 2.0) -> dict[str, Any]:
        """Start supervision once; return promptly if it is already running."""
        if os.environ.get("POLDERGRAPH_NO_WATCHER"):
            with self._lock:
                self._status = "disabled"
            return self.status()
        with self._lock:
            if self._thread and self._thread.is_alive():
                return {"state": self._status, "error": self._error}
            self._stop.clear()
            self._started.clear()
            self._status = "starting"
            self._error = None
            self._thread = threading.Thread(
                target=self._run,
                name=f"poldergraph-watcher-{self.root.name}",
                daemon=True,
            )
            self._thread.start()
        self._started.wait(max(0.0, wait_seconds))
        return self.status()

    def stop(self, *, timeout: float = 30.0) -> dict[str, Any]:
        """Request an orderly watcher stop and wait for its polling interval."""
        self._stop.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(max(0.0, timeout))
        with self._lock:
            if not thread or not thread.is_alive():
                self._status = "stopped"
        return self.status()

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {"state": self._status, "error": self._error}

    def _run(self) -> None:
        from ..errors import IndexLockedError
        from .watcher import run_watch

        try:
            run_watch(
                self.root,
                stop_event=self._stop,
                backend_provider=self.backend_provider,
                reconcile_interval=self.reconcile_interval,
                on_started=self._on_started,
            )
        except IndexLockedError:
            with self._lock:
                self._status = "supervised_elsewhere"
                self._error = None
                self._started.set()
        except Exception as exc:
            with self._lock:
                self._status = "degraded"
                self._error = type(exc).__name__
                self._started.set()
        else:
            with self._lock:
                self._status = "stopped"

    def _on_started(self) -> None:
        with self._lock:
            self._status = "running"
            self._started.set()
