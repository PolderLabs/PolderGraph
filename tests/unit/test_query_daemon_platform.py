from __future__ import annotations

import socket

import pytest

from poldergraph.query_daemon import Daemon, ensure_daemon


def test_missing_unix_sockets_uses_in_process_fallback(tmp_path, monkeypatch):
    monkeypatch.delattr(socket, "AF_UNIX", raising=False)
    assert ensure_daemon(tmp_path) is False


def test_daemon_start_fails_with_actionable_platform_message(tmp_path, monkeypatch):
    monkeypatch.delattr(socket, "AF_UNIX", raising=False)
    with pytest.raises(RuntimeError, match="in-process query service"):
        Daemon(tmp_path).serve()
