"""Rich progress display for init and update commands."""

from __future__ import annotations

import sys
import time
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# ANSI escape: dim + cyan for stage labels
_DIM = "\033[2m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_RESET = "\033[0m"
_BOLD = "\033[1m"
_CHECK = "✓"
_CROSS = "✗"
_DOT = "·"
_SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def _is_tty() -> bool:
    return sys.stderr.isatty()


class ProgressDisplay:
    """Multi-stage progress display for CLI commands.

    Shows a clean stage-by-stage progress with spinners, counts, and timing.
    Falls back to simple stderr output when not a TTY.
    """

    def __init__(self, *, json_mode: bool = False) -> None:
        self.json_mode = json_mode
        self.is_tty = _is_tty() and not json_mode
        self.stages: list[dict[str, Any]] = []
        self.current_stage = -1
        self.start_time = time.time()
        self._last_line = ""

    def add_stage(self, name: str, *, total: int = 0, detail: str = "") -> None:
        self.stages.append({"name": name, "total": total, "done": 0, "detail": detail, "start": None, "end": None, "status": "pending"})

    def start_stage(self, name: str, *, total: int = 0, detail: str = "") -> None:
        """Start or update a named stage."""
        for i, s in enumerate(self.stages):
            if s["name"] == name:
                self.current_stage = i
                s["status"] = "running"
                s["start"] = time.time()
                s["total"] = total
                s["detail"] = detail
                self._render()
                return
        self.add_stage(name, total=total, detail=detail)
        self.current_stage = len(self.stages) - 1
        self.stages[-1]["status"] = "running"
        self.stages[-1]["start"] = time.time()
        self._render()

    def update(self, done: int, *, total: int | None = None, detail: str = "") -> None:
        """Update progress for the current stage."""
        if self.current_stage < 0 or self.current_stage >= len(self.stages):
            return
        stage = self.stages[self.current_stage]
        stage["done"] = done
        if total is not None:
            stage["total"] = total
        if detail:
            stage["detail"] = detail
        self._render()

    def finish_stage(self, *, status: str = "done", detail: str = "") -> None:
        if self.current_stage < 0 or self.current_stage >= len(self.stages):
            return
        stage = self.stages[self.current_stage]
        stage["status"] = status
        stage["end"] = time.time()
        if detail:
            stage["detail"] = detail
        self._render()

    def warning(self, message: str) -> None:
        if self.is_tty:
            self._clear_line()
            sys.stderr.write(f"  {_YELLOW}⚠{_RESET} {message}\n")
            sys.stderr.flush()
        elif not self.json_mode:
            sys.stderr.write(f"warning: {message}\n")

    def error(self, message: str) -> None:
        if self.is_tty:
            self._clear_line()
            sys.stderr.write(f"  {_RED}✗{_RESET} {message}\n")
            sys.stderr.flush()
        elif not self.json_mode:
            sys.stderr.write(f"error: {message}\n", )

    def done(self) -> None:
        elapsed = time.time() - self.start_time
        if self.is_tty:
            self._render_final(elapsed)
        elif not self.json_mode:
            pass  # quiet

    def _render(self) -> None:
        if not self.is_tty or self.json_mode:
            return
        lines = []
        for stage in self.stages:
            name = stage["name"]
            status = stage["status"]
            done = stage["done"]
            total = stage["total"]
            detail = stage["detail"]
            elapsed = time.time() - stage["start"] if stage["start"] else 0

            if status == "pending":
                icon = f"{_DIM}○{_RESET}"
                line = f"  {icon} {name}"
            elif status == "running":
                idx = int(time.time() * 4) % len(_SPINNER)
                icon = f"{_CYAN}{_SPINNER[idx]}{_RESET}"
                if total > 0:
                    pct = int(100 * done / total) if total else 0
                    bar_width = 20
                    filled = int(bar_width * done / total) if total else 0
                    bar = f"[{'#'*filled}{'.'*(bar_width-filled)}]"
                    line = f"  {icon} {name}  {bar} {done}/{total}"
                else:
                    line = f"  {icon} {name}"
                if detail:
                    line += f"  {_DIM}{detail}{_RESET}"
            elif status == "done":
                icon = f"{_GREEN}{_CHECK}{_RESET}"
                elapsed_str = f"{elapsed:.1f}s" if elapsed > 0.5 else ""
                line = f"  {icon} {name}"
                if detail:
                    line += f"  {detail}"
                if elapsed_str:
                    line += f"  {_DIM}{elapsed_str}{_RESET}"
            elif status == "failed":
                icon = f"{_RED}{_CROSS}{_RESET}"
                line = f"  {icon} {name}"
                if detail:
                    line += f"  {_RED}{detail}{_RESET}"
            elif status == "skipped":
                icon = f"{_DIM}–{_RESET}"
                line = f"  {icon} {name}"
                if detail:
                    line += f"  {_DIM}{detail}{_RESET}"
            else:
                line = f"  ? {name}"
            lines.append(line)

        self._clear_line()
        output = "\n".join(lines)
        sys.stderr.write(output)
        sys.stderr.flush()
        self._last_line = output

    def _render_final(self, elapsed: float) -> None:
        self._clear_line()
        for stage in self.stages:
            name = stage["name"]
            status = stage["status"]
            detail = stage["detail"]
            stage_elapsed = (stage["end"] or time.time()) - stage["start"] if stage["start"] else 0

            if status == "done":
                icon = f"{_GREEN}{_CHECK}{_RESET}"
            elif status == "failed":
                icon = f"{_RED}{_CROSS}{_RESET}"
            elif status == "skipped":
                icon = f"{_DIM}–{_RESET}"
            else:
                icon = f"{_DIM}○{_RESET}"

            line = f"  {icon} {name}"
            if detail:
                line += f"  {detail}"
            if stage_elapsed > 0.5:
                line += f"  {_DIM}{stage_elapsed:.1f}s{_RESET}"
            sys.stderr.write(line + "\n")

        sys.stderr.write(f"\n  {_DIM}Total: {elapsed:.1f}s{_RESET}\n")
        sys.stderr.flush()

    def _clear_line(self) -> None:
        if self._last_line:
            n = len(self._last_line.split("\n"))
            sys.stderr.write(f"\033[{n}A\033[J")
            self._last_line = ""


class QuietProgress:
    """No-op progress for --quiet or --json mode."""

    def start_stage(self, *a: Any, **kw: Any) -> None: ...
    def update(self, *a: Any, **kw: Any) -> None: ...
    def finish_stage(self, *a: Any, **kw: Any) -> None: ...
    def warning(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...
    def done(self) -> None: ...