"""Killable, persistent process for optional local decision inference."""

from __future__ import annotations

import atexit
import json
import math
import multiprocessing
import os
import subprocess
import sys
import threading
import time
from multiprocessing.connection import Connection
from typing import Any

from .decisions import DecisionError, DecisionQuestion
from .retrieval.context import estimate_tokens

_IDLE_SECONDS = 300.0
#: Versioned shape of the worker status contract reported by ``status()``.
STATUS_CONTRACT_VERSION = 1

_PSUTIL: Any = None
_PSUTIL_LOOKED_UP = False


def _load_psutil() -> Any:
    """Return psutil when the host already has it; never a required dependency."""
    global _PSUTIL, _PSUTIL_LOOKED_UP
    if not _PSUTIL_LOOKED_UP:
        _PSUTIL_LOOKED_UP = True
        try:
            import psutil  # optional, intentionally not a project dependency

            _PSUTIL = psutil
        except Exception:
            _PSUTIL = None
    return _PSUTIL


def _procfs_rss_bytes(pid: int) -> int | None:
    """Read ``VmRSS`` from ``/proc/<pid>/status`` (Linux)."""
    try:
        with open(f"/proc/{pid}/status", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        return None
    return None


def _ps_rss_bytes(pid: int) -> int | None:
    """Read resident memory from ``ps`` (macOS and any POSIX host without procfs)."""
    completed = subprocess.run(
        ["ps", "-o", "rss=", "-p", str(pid)],
        capture_output=True,
        text=True,
        timeout=1.0,
        check=False,
    )
    return int(completed.stdout.strip()) * 1024


def _windows_rss_bytes(pid: int) -> int | None:
    """Read resident memory through ``GetProcessMemoryInfo`` (Windows)."""
    import ctypes
    from ctypes import wintypes

    class _Counters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # noqa: F821 - Windows only
    psapi = ctypes.WinDLL("psapi", use_last_error=True)  # noqa: F821 - Windows only
    handle = kernel32.OpenProcess(0x1000 | 0x0010, False, pid)
    if not handle:
        return None
    try:
        counters = _Counters()
        counters.cb = ctypes.sizeof(_Counters)
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return None
        return int(counters.WorkingSetSize)
    finally:
        kernel32.CloseHandle(handle)


def rss_bytes(pid: int | None) -> int | None:
    """Return a child's resident memory in bytes, or None when unavailable.

    Every platform path is guarded so importing this module on any OS succeeds
    and an unmeasurable host degrades to "unknown" instead of failing.
    """
    if pid is None or pid <= 0:
        return None
    psutil = _load_psutil()
    if psutil is not None:
        try:
            return int(psutil.Process(pid).memory_info().rss)
        except Exception:
            return None
    try:
        if os.name == "nt":
            return _windows_rss_bytes(pid)
        if sys.platform.startswith("darwin"):
            return _ps_rss_bytes(pid)
        return _procfs_rss_bytes(pid)
    except Exception:
        return None


def _validate_max_rss_mb(value: float | None) -> float | None:
    """Validate an optional resident-memory cap in megabytes."""
    if value is None:
        return None
    if not math.isfinite(float(value)) or float(value) <= 0:
        raise ValueError("max_rss_mb must be greater than zero")
    return float(value)


def _state_token_estimate(state: Any) -> int:
    """Estimate tokens for any supported state shape.

    ``state`` may be text, a mapping or a sequence of messages, so non-text
    states are measured through their canonical JSON form rather than being
    counted as a single opaque element.
    """
    if isinstance(state, str):
        return estimate_tokens(state)
    try:
        canonical = json.dumps(state, sort_keys=True, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        canonical = str(state)
    return estimate_tokens(canonical)


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

    def __init__(
        self,
        *,
        worker_main: Any = _worker_main,
        idle_seconds: float = _IDLE_SECONDS,
        max_rss_mb: float | None = None,
        max_state_tokens: int = 0,
    ) -> None:
        if not math.isfinite(idle_seconds) or idle_seconds <= 0:
            raise ValueError("idle_seconds must be greater than zero")
        self._context = multiprocessing.get_context("spawn")
        self._worker_main = worker_main
        self._idle_seconds = float(idle_seconds)
        self._lock = threading.RLock()
        self._process: multiprocessing.Process | None = None
        self._connection: Connection | None = None
        self._offline_only = False
        self._timer: threading.Timer | None = None
        self._last_used = 0.0
        self._model_loaded = False
        self._max_rss_mb = _validate_max_rss_mb(max_rss_mb)
        self._max_state_tokens = int(max_state_tokens or 0)
        self._deadline_ms: int | None = None
        self._model_revision: str | None = None
        self._state_tokens: int | None = None
        self._evictions = 0
        self._last_eviction: str | None = None

    def set_limits(
        self, *, max_rss_mb: float | None = None, max_state_tokens: int | None = None
    ) -> None:
        """Apply runtime supervision limits from configuration."""
        with self._lock:
            self._max_rss_mb = _validate_max_rss_mb(max_rss_mb)
            if max_state_tokens is not None:
                self._max_state_tokens = max(0, int(max_state_tokens))

    def _start(self, offline_only: bool) -> None:
        parent, child = self._context.Pipe(duplex=True)
        process = self._context.Process(target=self._worker_main, args=(child, offline_only), daemon=True)
        process.start()
        child.close()
        self._process, self._connection = process, parent
        self._offline_only = offline_only
        self._model_loaded = False

    def _stop_locked(self, *, force: bool = False) -> None:
        if self._timer:
            self._timer.cancel()
            self._timer = None
        connection, process = self._connection, self._process
        self._connection = None
        self._process = None
        self._model_loaded = False
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

    def _evicted_for_memory(self, process: multiprocessing.Process) -> bool:
        """Stop the child when its resident set exceeds the configured cap.

        Runs under ``self._lock``. An unmeasurable host returns False so an
        unknown footprint never triggers an eviction.
        """
        if self._max_rss_mb is None or not process.is_alive():
            return False
        rss = rss_bytes(process.pid)
        if rss is None:
            return False
        if rss <= self._max_rss_mb * 1024 * 1024:
            return False
        self._stop_locked(force=True)
        self._evictions += 1
        self._last_eviction = "memory"
        return True

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
                self._idle_seconds, self._evict_if_idle, (process, self._last_used)
            )
            self._timer.daemon = True
            self._timer.start()

    def _call(self, operation: str, payload: Any, *, timeout: float, offline_only: bool) -> Any:
        if timeout <= 0:
            raise DecisionError("timeout must be greater than zero.")
        deadline = time.monotonic() + timeout
        self._deadline_ms = int(round(timeout * 1000))
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not self._lock.acquire(timeout=remaining):
            raise DecisionError("Local decision deadline exceeded while waiting for the worker.")
        try:
            if self._process is None or not self._process.is_alive() or self._offline_only != offline_only:
                self._stop_locked()
                self._start(offline_only)
            elif self._evicted_for_memory(self._process):
                # Over the resident-memory cap: restart cleanly on the next call
                # rather than serving inference from a pressured process.
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
                self._model_loaded = False
                raise DecisionError(f"Local decision worker failed ({result}).")
            self._model_loaded = True
            return result
        finally:
            self._lock.release()

    def decide(
        self, state: Any, questions: dict[str, DecisionQuestion], *, model: str | None,
        timeout: float, offline_only: bool = False,
    ) -> dict[str, Any]:
        self._record_state(state, model)
        return self._call("single", (state, questions, model), timeout=timeout, offline_only=offline_only)

    def decide_batch(
        self, states: list[Any], questions: dict[str, DecisionQuestion], *, model: str | None,
        batch_size: int = 8, timeout: float = 3.0, offline_only: bool = False,
    ) -> list[dict[str, Any]]:
        largest = max((_state_token_estimate(item) for item in states), default=0)
        self._record_token_count(largest, model)
        return self._call(
            "batch", (states, questions, model, batch_size),
            timeout=timeout, offline_only=offline_only,
        )

    def _record_token_count(self, tokens: int, model: str | None) -> None:
        """Track the state bound and reject requests beyond a configured cap."""
        self._state_tokens = int(tokens)
        self._model_revision = model
        if self._max_state_tokens and tokens > self._max_state_tokens:
            raise DecisionError(
                "Local decision state exceeds the configured max_state_tokens bound "
                f"({tokens} > {self._max_state_tokens})."
            )

    def _record_state(self, state: Any, model: str | None) -> None:
        self._record_token_count(_state_token_estimate(state), model)

    def close(self) -> None:
        with self._lock:
            self._stop_locked()

    def status(self) -> dict[str, Any]:
        """Return local worker health without exposing prompts or model inputs."""
        if not self._lock.acquire(blocking=False):
            process = self._process
            return {
                "state": "busy",
                "pid": process.pid if process and process.is_alive() else None,
                "model_loaded": None,
                "offline_only": None,
                "idle_seconds": None,
                "idle_timeout_seconds": self._idle_seconds,
                "contract_version": STATUS_CONTRACT_VERSION,
                "deadline_ms": self._deadline_ms,
                "max_state_tokens": self._max_state_tokens or None,
                "max_rss_mb": self._max_rss_mb,
                "rss_bytes": None,
                "rss_known": False,
                "evictions": self._evictions,
                "last_eviction": self._last_eviction,
                "state_tokens": self._state_tokens,
                "model_revision": self._model_revision,
            }
        try:
            process = self._process
            alive = bool(process and process.is_alive())
            if not alive and process is not None:
                self._stop_locked(force=True)
                process = None
            return {
                "state": "warm" if alive and self._model_loaded else "running" if alive else "stopped",
                "pid": process.pid if alive and process else None,
                "model_loaded": bool(alive and self._model_loaded),
                "offline_only": self._offline_only if alive else None,
                "idle_seconds": (
                    round(max(0.0, time.monotonic() - self._last_used), 3)
                    if alive and self._last_used
                    else None
                ),
                "idle_timeout_seconds": self._idle_seconds,
                "contract_version": STATUS_CONTRACT_VERSION,
                "deadline_ms": self._deadline_ms,
                "max_state_tokens": self._max_state_tokens or None,
                "max_rss_mb": self._max_rss_mb,
                "rss_bytes": rss_bytes(process.pid) if alive and process else None,
                "rss_known": alive and process is not None and rss_bytes(process.pid) is not None,
                "evictions": self._evictions,
                "last_eviction": self._last_eviction,
                "state_tokens": self._state_tokens,
                "model_revision": self._model_revision,
            }
        finally:
            self._lock.release()


local_decision_worker = LocalDecisionWorker()
atexit.register(local_decision_worker.close)
