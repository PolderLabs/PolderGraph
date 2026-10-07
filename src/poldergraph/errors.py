"""Error taxonomy, stable exit codes and the agent-friendly JSON envelope.

Exit codes are part of the public contract; agents branch on them.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any

#: Bumped when the shape of any --json payload changes incompatibly.
API_VERSION = 1


class ExitCode(IntEnum):
    """Stable process exit codes."""

    SUCCESS = 0
    USAGE = 2
    INDEX_MISSING = 3
    INDEX_STALE = 4
    BACKEND_UNAVAILABLE = 5
    LOCKED = 6
    CORRUPT = 7
    DEGRADED = 8


class ErrorCode(str):
    """String error codes embedded in the JSON envelope."""


class PolderGraphError(Exception):
    """Base class for all errors that map to a documented exit code."""

    exit_code: ExitCode = ExitCode.USAGE
    code: str = "ERROR"
    remediation: str | None = None

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        remediation: str | None = None,
        exit_code: ExitCode | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if remediation is not None:
            self.remediation = remediation
        if exit_code is not None:
            self.exit_code = exit_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "remediation": self.remediation,
            "details": self.details or None,
        }


class UsageError(PolderGraphError):
    exit_code = ExitCode.USAGE
    code = "USAGE_ERROR"
    remediation = "Check command arguments with: poldergraph --help"


class ConfigError(PolderGraphError):
    exit_code = ExitCode.USAGE
    code = "CONFIG_ERROR"
    remediation = "Run: poldergraph config show --effective"


class IndexMissingError(PolderGraphError):
    exit_code = ExitCode.INDEX_MISSING
    code = "INDEX_MISSING"
    remediation = "Run: poldergraph init"


class IndexStaleError(PolderGraphError):
    exit_code = ExitCode.INDEX_STALE
    code = "INDEX_STALE"
    remediation = "Run: poldergraph update --quiet"


class BackendUnavailableError(PolderGraphError):
    exit_code = ExitCode.BACKEND_UNAVAILABLE
    code = "BACKEND_UNAVAILABLE"
    remediation = "Run: poldergraph doctor"


class IndexLockedError(PolderGraphError):
    exit_code = ExitCode.LOCKED
    code = "INDEX_LOCKED"
    remediation = "Another poldergraph process is writing. Retry, or stop `poldergraph watch`."


class CorruptIndexError(PolderGraphError):
    exit_code = ExitCode.CORRUPT
    code = "INDEX_CORRUPT"
    remediation = "Run: poldergraph doctor, then poldergraph rebuild"


class DegradedError(PolderGraphError):
    """Raised when a command cannot represent partial capability in its JSON output."""

    exit_code = ExitCode.DEGRADED
    code = "DEGRADED"
    remediation = "Run: poldergraph doctor"


def envelope(
    *,
    command: str,
    data: Any = None,
    index: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    error: PolderGraphError | None = None,
) -> dict[str, Any]:
    """Build the canonical JSON envelope shared by CLI and MCP surfaces."""
    return {
        "ok": error is None,
        "api_version": API_VERSION,
        "command": command,
        "index": index,
        "data": data,
        "warnings": warnings or [],
        "error": error.to_dict() if error is not None else None,
    }


def error_envelope(
    command: str, error: PolderGraphError, *, warnings: list[str] | None = None
) -> dict[str, Any]:
    return envelope(command=command, error=error, warnings=warnings)
