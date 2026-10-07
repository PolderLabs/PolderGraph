"""Reproducible benchmark corpus used by the retrieval harness."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

MANIFEST = Path(__file__).parent / "corpus_manifest.json"

#: A small, realistic multi-module repository with predictable answers.
CORPUS_FILES: dict[str, str] = {
    "README.md": (
        "# Corpus\n\nA benchmark repository.\n\n## Authentication\n\n"
        "Sessions are validated by AuthService.\n\n## Billing\n\nInvoices live in billing.\n"
    ),
    "auth.py": (
        '"""Authentication."""\n'
        "\n"
        "from models import Session, User\n"
        "\n"
        "\n"
        "class AuthService:\n"
        '    """Validate session tokens."""\n'
        "\n"
        "    def validate_session(self, token: str) -> Session:\n"
        '        """Check that a token maps to a live session."""\n'
        "        user = UserRepository.find_user(token)\n"
        "        if user is None:\n"
        "            raise ValueError(\"invalid token\")\n"
        "        return Session(token, user)\n"
        "\n"
        "    def refresh(self, token: str) -> Session:\n"
        '        """Issue a fresh session."""\n'
        "        return self.validate_session(token)\n"
        "\n"
        "\n"
        "class UserRepository:\n"
        '    """Look up users."""\n'
        "\n"
        "    def find_user(self, token: str):\n"
        "        return USERS.get(token)\n"
        "\n"
        "\n"
        "USERS = {}\n"
    ),
    "models.py": (
        '"""Domain models."""\n'
        "\n"
        "\n"
        "class Session:\n"
        '    """A user session."""\n'
        "\n"
        "    def __init__(self, token, user):\n"
        "        self.token = token\n"
        "        self.user = user\n"
        "\n"
        "\n"
        "class Invoice:\n"
        '    """A billing invoice."""\n'
        "\n"
        "    def total(self):\n"
        "        return 0\n"
    ),
    "billing.py": (
        '"""Billing."""\n'
        "\n"
        "from models import Invoice\n"
        "\n"
        "\n"
        "class BillingService:\n"
        '    """Create and total invoices."""\n'
        "\n"
        "    def create_invoice(self, user) -> Invoice:\n"
        "        return Invoice()\n"
    ),
    "test_auth.py": (
        "from auth import AuthService\n"
        "\n"
        "\n"
        "def test_validate_session():\n"
        '    assert AuthService().validate_session("x")\n'
    ),
}


def build_corpus(destination: Path) -> Path:
    """Materialize the benchmark corpus at ``destination``."""
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for relative, content in CORPUS_FILES.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return destination


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def cases() -> list[dict]:
    return load_manifest()["cases"]