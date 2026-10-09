"""Killable, persistent process for optional local decision inference."""

from __future__ import annotations

import atexit
import multiprocessing
import threading
import time
from multiprocessing.connection import Connection
from typing import Any

from .decisions import DecisionError, DecisionQuestion

_IDLE_SECONDS = 300.0


def _worker_main(connection: Connection, offline_only: bool) -> None:
    """Serve serialized local Laya requests; model initialization stays in child."""
    if offline_only:
        import os

        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
    while True:
        try:
            message = connection.recv()
        except EOFError:
            return
        if message is None:
            return
        operation, payload = message
        try:
            from . import decisions

            if operation == "single":
                state, questions, model = payload
                result = decisions._decide_laya(state, questions, model=model)
            else:
                states, questions, model, batch_size = payload
                result = decisions._decide_laya_batch(
                    states, questions, model=model, batch_size=batch_size
                )
            connection.send((True, result))
        except BaseException as exc:
            # Do not send exception messages: providers may echo submitted text.
            connection.send((False, type(exc).__name__))


class LocalDecisionWorker:
    """Serialize Laya inference in a reusable process with killable deadlines."""

    def __init__(self, *, worker_main: Any = _worker_main) -> None:
        self._context = multiprocessing.get_context("spawn")
        self._worker_main = worker_main
        self._lock = threading.RLock()
        self._process: multiprocessing.Process | None = None
        self._connection: Connection | None = None
        self._offline_only = False
        self._timer: threading.Timer | None = None
        self._last_used = 0.0

    def _start(self, offline_only: bool) -> None:
        parent, child = self._context.Pipe(duplex=True)
        process = self._context.Process(target=self._worker_main, args=(child, offline_only), daemon=True)
        process.start()
        child.close()
        self._process, self._connection = process, parent
        self._offline_only = offline_only

    def _stop_locked(self, *, force: bool = False) -> None:
        if self._timer:
            self._timer.cancel()
            self._timer = None
        connection, process = self._connection, self._process
        self._connection = None
        self._process = None
        if connection is not None:
            try:
                connection.send(None)
                connection.close()
            except (BrokenPipeError, OSError):
                pass
        if process is not None:
            if force and process.is_alive():
                process.terminate()
                process.join(timeout=0.05)
                if process.is_alive():
                    process.kill()
                    process.join(timeout=0.05)
            else:
                process.join(timeout=0.2)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=1.0)

    def _evict_if_idle(self, expected: multiprocessing.Process, scheduled_at: float) -> None:
        with self._lock:
            if self._process is expected and self._last_used <= scheduled_at:
                self._stop_locked()

    def _arm_idle_eviction(self) -> None:
        if self._timer:
            self._timer.cancel()
        process = self._process
        if process is not None:
            self._last_used = time.monotonic()
            self._timer = threading.Timer(
                _IDLE_SECONDS, self._evict_if_idle, (process, self._last_used)
            )
            self._timer.daemon = True
            self._timer.start()

    def _call(self, operation: str, payload: Any, *, timeout: float, offline_only: bool) -> Any:
        if timeout <= 0:
            raise DecisionError("timeout must be greater than zero.")
        deadline = time.monotonic() + timeout
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not self._lock.acquire(timeout=remaining):
            raise DecisionError("Local decision deadline exceeded while waiting for the worker.")
        try:
            if self._process is None or not self._process.is_alive() or self._offline_only != offline_only:
                self._stop_locked()
                self._start(offline_only)
            connection = self._connection
            process = self._process
            if connection is None or process is None:
                raise DecisionError("Local decision worker is unavailable.")
            try:
                connection.send((operation, payload))
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not connection.poll(remaining):
                    self._stop_locked(force=True)
                    raise DecisionError("Local decision deadline exceeded.")
                ok, result = connection.recv()
            except (EOFError, BrokenPipeError, OSError) as exc:
                self._stop_locked(force=True)
                raise DecisionError("Local decision worker exited unexpectedly.") from exc
            self._arm_idle_eviction()
            if not ok:
                raise DecisionError(f"Local decision worker failed ({result}).")
            return result
        finally:
            self._lock.release()

    def decide(
        self, state: Any, questions: dict[str, DecisionQuestion], *, model: str | None,
        timeout: float, offline_only: bool = False,
    ) -> dict[str, Any]:
        return self._call("single", (state, questions, model), timeout=timeout, offline_only=offline_only)

    def decide_batch(
        self, states: list[Any], questions: dict[str, DecisionQuestion], *, model: str | None,
        batch_size: int = 8, timeout: float = 3.0, offline_only: bool = False,
    ) -> list[dict[str, Any]]:
        return self._call(
            "batch", (states, questions, model, batch_size),
            timeout=timeout, offline_only=offline_only,
        )

    def close(self) -> None:
        with self._lock:
            self._stop_locked()


local_decision_worker = LocalDecisionWorker()
atexit.register(local_decision_worker.close)
