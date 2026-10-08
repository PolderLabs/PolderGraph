"""Daemon entry point: ``python -m poldergraph.query_daemon <root>``."""

from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("usage: python -m poldergraph.query_daemon <repo-root>", file=sys.stderr)
        return 2
    root = Path(args[0]).expanduser().resolve()
    from .query_daemon import Daemon

    Daemon(root).serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())