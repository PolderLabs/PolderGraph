"""Progress display for long-running indexing commands.

A full `poldergraph init` spends most of its time embedding vectors, which can
take tens of seconds with no output. That reads as a hang, so progress is
reported continuously and rendered differently depending on where it goes:

* an interactive terminal gets an in-place, redrawn view
* a pipe or log file gets periodic timestamped lines, so `poldergraph init |
  tee log.txt` still shows movement
* `--json` stays silent, because the envelope is the output
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

#: Minimum gap between rendered updates, so a fast loop cannot flood a terminal.
MIN_INTERVAL = 0.1

#: Minimum gap between lines when writing to a pipe or file.
PLAIN_INTERVAL = 2.0

_DIM = "\033[2m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_BOLD = "\033[1m"
_RESET = "\033[0m"
_CHECK = "✓"
_DOT = "·"
_SPINNER = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


def _stream_is_tty(stream: Any) -> bool:
    try:
        return bool(stream.isatty())
    except Exception:
        return False


class ProgressDisplay:
    """Stage-based progress for indexing commands."""

    def __init__(self, *, json_mode: bool = False, stream: Any = None) -> None:
        self.json_mode = json_mode
        self.stream = stream if stream is not None else sys.stderr
        self.is_tty = _stream_is_tty(self.stream) and not json_mode
        self.is_plain = not self.is_tty and not json_mode
        self.stages: list[dict[str, Any]] = []
        self.current = -1
        self.started = time.monotonic()
        self._last_render = 0.0
        self._last_plain = 0.0
        self._frame = 0

    # ------------------------------------------------------------- plumbing

    @property
    def enabled(self) -> bool:
        return not self.json_mode

    def _find(self, name: str) -> int:
        for index, stage in enumerate(self.stages):
            if stage["name"] == name:
                return index
        return -1

    def _stage(self, name: str) -> dict[str, Any]:
        index = self._find(name)
        if index >= 0:
            return self.stages[index]
        self.stages.append(
            {"name": name, "done": 0, "total": 0, "detail": "",
             "start": None, "end": None, "status": "pending"}
        )
        return self.stages[-1]

    # --------------------------------------------------------------- events

    def add_stage(self, name: str, *, total: int = 0, detail: str = "") -> None:
        if not self.enabled:
            return
        stage = self._stage(name)
        if total:
            stage["total"] = total
        if detail:
            stage["detail"] = detail

    def start_stage(self, name: str, *, total: int = 0, detail: str = "") -> None:
        if not self.enabled:
            return
        stage = self._stage(name)
        stage["status"] = "running"
        stage["start"] = time.monotonic()
        if total:
            stage["total"] = total
        if detail:
            stage["detail"] = detail
        self.current = self._find(name)
        self._render(force=True)

    def update(self, done: int, *, total: int | None = None, detail: str = "") -> None:
        """Report incremental progress on the current stage."""
        if not self.enabled or self.current < 0:
            return
        stage = self.stages[self.current]
        stage["done"] = done
        if total is not None:
            stage["total"] = total
        if detail:
            stage["detail"] = detail
        self._render()

    def finish_stage(
        self, *, status: str = "done", detail: str = "", name: str | None = None
    ) -> None:
        """Complete a stage.

        Pass ``name`` to close a specific stage. Without it the currently
        active stage is closed, which is what sequential callers want.
        """
        if not self.enabled:
            return
        index = self._find(name) if name else self.current
        if index < 0 or index >= len(self.stages):
            return
        stage = self.stages[index]
        stage["status"] = status
        stage["end"] = time.monotonic()
        if total_of(stage):
            stage["done"] = stage["total"]
        if detail:
            stage["detail"] = detail
        if index == self.current:
            self.current = -1
        self._render(force=True)
        # A completed stage is terminal: report it immediately rather than
        # letting the throttle swallow it until the next tick.
        if self.is_plain:
            took = (stage["end"] or 0) - (stage["start"] or 0)
            bits = []
            if total_of(stage):
                bits.append(f"{stage['done']}/{stage['total']}")
            bits.append(f"{took:.1f}s")
            extra = f"  {stage['detail']}" if stage["detail"] else ""
            self._last_plain = time.monotonic()
            self.stream.write(
                f"{_DIM}{time.strftime('%H:%M:%S')}{_RESET} "
                f"done {_stage_label(stage)} ({', '.join(bits)}){extra}\n"
            )
            self.stream.flush()

    def note(self, message: str) -> None:
        """Emit a standalone message that is not tied to a stage."""
        if not self.enabled:
            return
        if self.is_tty:
            self._clear()
            self.stream.write(f"  {_DIM}{_DOT}{_RESET} {message}\n")
            self.stream.flush()
        elif self.is_plain:
            self._write_plain(message)

    def warning(self, message: str) -> None:
        self._emit(f"{_YELLOW}warning{_RESET}: {message}" if self.is_tty else f"warning: {message}")

    def error(self, message: str) -> None:
        self._emit(f"{_RED}error{_RESET}: {message}" if self.is_tty else f"error: {message}")

    def _emit(self, text: str) -> None:
        if not self.enabled:
            return
        if self.is_tty:
            self._clear()
        self.stream.write(f"{text}\n")
        self.stream.flush()

    # ------------------------------------------------------------ rendering

    def _render(self, *, force: bool = False) -> None:
        if not self.enabled:
            return
        if self.is_tty:
            now = time.monotonic()
            if not force and now - self._last_render < MIN_INTERVAL:
                return
            self._last_render = now
            self._draw()
        elif self.is_plain:
            self._write_plain(self._plain_line())

    def _draw(self) -> None:
        self._clear()
        self.stream.write(f"{_BOLD}PolderGraph{_RESET} {_DIM}indexing{_RESET}\n")
        for stage in self.stages:
            self.stream.write("  " + self._stage_line(stage) + "\n")
        self.stream.write(
            f"  {_DIM}elapsed {time.monotonic() - self.started:5.1f}s{_RESET}\n"
        )
        self.stream.flush()

    def _stage_line(self, stage: dict[str, Any]) -> str:
        name = stage["name"]
        status = stage["status"]
        done = stage["done"]
        total = stage["total"]
        detail = stage["detail"]

        if status == "pending":
            return f"{_DIM}{_DOT} {name}{_RESET}"
        if status == "skipped":
            suffix = f"  {_DIM}{detail}{_RESET}" if detail else ""
            return f"{_DIM}– {name}{_RESET}{suffix}"
        if status in {"done", "failed"}:
            took = (stage["end"] or time.monotonic()) - (stage["start"] or time.monotonic())
            mark = f"{_GREEN}{_CHECK}{_RESET}" if status == "done" else f"{_RED}x{_RESET}"
            bits = []
            if total:
                bits.append(f"{done}/{total}")
            if took >= 0.5:
                bits.append(f"{took:.1f}s")
            tail = f"  {_DIM}{'  '.join(bits)}{_RESET}" if bits else ""
            extra = f"  {detail}" if detail else ""
            return f"{mark} {name}{extra}{tail}"
        # running
        self._frame += 1
        spinner = _SPINNER[self._frame % len(_SPINNER)]
        icon = f"{_CYAN}{spinner}{_RESET}"
        if total:
            width = 22
            fraction = min(1.0, done / total) if total else 0.0
            filled = int(width * fraction)
            bar = f"[{'█' * filled}{_DIM}{'░' * (width - filled)}{_RESET}]"
            pct = f"{fraction * 100:5.1f}%"
            body = f"{bar} {pct}  {done}/{total}"
        else:
            body = _DIM + (_SPINNER[self._frame % len(_SPINNER)]) + _RESET
        extra = f"  {_DIM}{detail}{_RESET}" if detail else ""
        return f"{icon} {name}  {body}{extra}"

    def _plain_line(self) -> str:
        if self.current < 0 or self.current >= len(self.stages):
            return ""
        stage = self.stages[self.current]
        total = stage["total"]
        detail = f" {stage['detail']}" if stage["detail"] else ""
        if total:
            return f"[{self.current + 1}/{len(self.stages)}] {stage['name']} {stage['done']}/{total}{detail}"
        return f"[{self.current + 1}/{len(self.stages)}] {stage['name']}{detail}"

    def _write_plain(self, text: str) -> None:
        if not text:
            return
        now = time.monotonic()
        if now - self._last_plain < PLAIN_INTERVAL:
            return
        self._last_plain = now
        self.stream.write(
            f"{_DIM}{time.strftime('%H:%M:%S')}{_RESET} {text}\n"
        )
        self.stream.flush()

    def _clear(self) -> None:
        if not self.is_tty:
            return
        lines = len(self.stages) + 2
        self.stream.write(f"\033[{lines}A\033[J")
        self.stream.flush()

    # --------------------------------------------------------------- finish

    def done(self) -> None:
        if not self.enabled:
            return
        elapsed = time.monotonic() - self.started
        if self.is_tty:
            self._clear()
            self.stream.write(f"{_BOLD}Done{_RESET} in {elapsed:.1f}s\n\n")
            self.stream.flush()
        elif self.is_plain:
            # Individual stages already reported as they finished.
            self.stream.write(
                f"{_DIM}{time.strftime('%H:%M:%S')}{_RESET} complete in {elapsed:.1f}s\n"
            )
            self.stream.flush()


def total_of(stage: dict[str, Any]) -> int:
    return int(stage.get("total") or 0)


def _stage_label(stage: dict[str, Any]) -> str:
    """Lower-case label used in plain output lines."""
    name = str(stage.get("name", ""))
    return name[0].lower() + name[1:] if name else ""


class QuietProgress:
    """No-op progress used for `--quiet`, `--json`, and MACHINE_READABLE paths."""

    def add_stage(self, *a: Any, **kw: Any) -> None: ...

    def start_stage(self, *a: Any, **kw: Any) -> None: ...

    def update(self, *a: Any, **kw: Any) -> None: ...

    def finish_stage(self, *a: Any, **kw: Any) -> None: ...

    def note(self, *a: Any, **kw: Any) -> None: ...

    def warning(self, *a: Any, **kw: Any) -> None: ...

    def error(self, *a: Any, **kw: Any) -> None: ...

    def done(self, *a: Any, **kw: Any) -> None: ...

    def _find(self, name: str) -> int:
        """No stages are recorded, so a lookup always reports "not present"."""
        return -1


def make_progress(*, json_mode: bool = False, quiet: bool = False) -> ProgressDisplay | QuietProgress:
    """Build the right progress sink for the current invocation."""
    if json_mode or quiet:
        return QuietProgress()
    return ProgressDisplay(json_mode=json_mode)