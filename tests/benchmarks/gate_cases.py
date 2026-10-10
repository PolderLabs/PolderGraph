"""Versioned memory decision-gate dataset.

Real-shaped but synthetic and anonymised statements. No repository source, user
prompt, or memory content from any real project is included.

``expected_store`` is the ground truth a correct gate must reach. The gate must
only ever reject on high confidence, so the safety-critical error is a false
write (expected_store=True but the gate rejected it); false rejections of
durable notes are tracked separately.
"""

from __future__ import annotations

from typing import Any

# Bumped whenever the dataset changes so results stay comparable.
GATE_DATASET_VERSION = "1.0.0"

# Durable preferences: expected_store=True.
DURABLE: list[str] = [
    "I prefer pytest fixtures over unittest setUp methods in this repository.",
    "I always want type annotations on public functions.",
    "Use ruff for linting and formatting in this project, not flake8.",
    "I prefer small focused pull requests with a single concern each.",
    "Always run the linter before committing Python changes.",
    "I want database migrations reviewed before they are applied.",
]

# One-off, temporary, or speculative statements: expected_store=False.
EPIHEREMERAL: list[str] = [
    "Fix the failing test on line 42 of this file right now.",
    "What is the capital of France?",
    "Tell me a joke about programmers.",
    "The build is broken right now, can you look at it?",
    "I wonder if we should probably maybe use a queue someday.",
    "Please print the contents of this file for me.",
]

# Ambiguous statements where a conservative gate should abstain rather than write.
AMBIGUOUS: list[str] = [
    "The caching layer feels slow lately.",
    "Maybe we should index that column.",
    "Something about the config seems off.",
]


def gate_cases() -> list[dict[str, Any]]:
    """Return the disclosed, versioned gate evaluation dataset."""
    cases: list[dict[str, Any]] = []
    for text in DURABLE:
        cases.append({"id": f"durable-{len(cases)}", "text": text, "expected_store": True, "class": "durable"})
    for text in EPIHEREMERAL:
        cases.append({"id": f"ephemeral-{len(cases)}", "text": text, "expected_store": False, "class": "ephemeral"})
    for text in AMBIGUOUS:
        cases.append({"id": f"ambiguous-{len(cases)}", "text": text, "expected_store": None, "class": "ambiguous"})
    return cases


def retrieval_cases() -> list[dict[str, Any]]:
    """Recall/abstention pairs for the retrieval-side relevance gate."""
    return [
        {"id": "relevant-0", "query": "how do I run the linter", "relevant": True},
        {"id": "relevant-1", "query": "what testing style does this project use", "relevant": True},
        {"id": "relevant-2", "query": "pull request conventions", "relevant": True},
        {"id": "irrelevant-0", "query": "banana bread recipe", "relevant": False},
        {"id": "irrelevant-1", "query": "best hiking boots", "relevant": False},
        {"id": "irrelevant-2", "query": "who won the world series", "relevant": False},
    ]