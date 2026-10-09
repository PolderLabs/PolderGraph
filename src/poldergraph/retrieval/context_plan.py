"""Cheap deterministic planning for automatic repository context."""

from __future__ import annotations

import re
from dataclasses import dataclass

_SOCIAL = re.compile(
    r"^(?:hi|hello|hey|good (?:morning|afternoon|evening)|thanks|thank you|"
    r"how are you\??|who are you\??|tell me a joke|what(?:'s| is) the weather\??)[.! ]*$",
    re.IGNORECASE,
)
_NARROW = re.compile(
    r"\b(where|find|locate|show|open|definition|signature|symbol|file|function|class)\b",
    re.IGNORECASE,
)
_BROAD = re.compile(
    r"\b(refactor|debug|architecture|overview|impact|tests?|explain|trace|flow|"
    r"change|modify|implement|feature|bug|error|failure|failing)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ContextPlan:
    """An inspectable local plan for one context request."""

    intent: str
    budget: int
    skipped: bool
    reason: str
    lanes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "intent": self.intent,
            "budget": self.budget,
            "skipped": self.skipped,
            "reason": self.reason,
            "lanes": list(self.lanes),
        }


def plan_context(query: str, budget: int) -> ContextPlan:
    """Select a cheap context policy without initializing embedding backends."""
    text = query.strip()
    normalized_budget = max(0, int(budget))
    if not text or _SOCIAL.fullmatch(text):
        return ContextPlan(
            intent="none",
            budget=0,
            skipped=True,
            reason="No repository evidence is needed for this message.",
            lanes=(),
        )
    if _NARROW.search(text) and len(text.split()) <= 12 and not _BROAD.search(text):
        return ContextPlan(
            intent="locate",
            budget=min(normalized_budget, 1000),
            skipped=False,
            reason="Narrow lookup: use compact exact and lexical evidence.",
            lanes=("exact", "lexical"),
        )
    intent = "modify" if re.search(r"\b(refactor|change|modify|implement|fix)\b", text, re.I) else (
        "debug" if re.search(r"\b(debug|error|failure|failing|bug)\b", text, re.I) else (
            "test" if re.search(r"\b(test|tests|coverage)\b", text, re.I) else (
                "architecture"
                if re.search(r"\b(architecture|overview|design|structure)\b", text, re.I)
                else "explain"
            )
        )
    )
    lanes = ("exact", "lexical", "semantic")
    if intent in {"modify", "debug", "test", "architecture"}:
        lanes = (*lanes, "structural", "tests")
    recommended_budget = {
        "explain": 1800,
        "test": 2400,
        "modify": 3000,
        "debug": 3200,
        "architecture": 4200,
    }[intent]
    if len(text.split()) > 30:
        recommended_budget = min(6000, recommended_budget + 600)
    effective_budget = min(normalized_budget, recommended_budget)
    return ContextPlan(
        intent=intent,
        budget=effective_budget,
        skipped=False,
        reason=(
            f"{intent.title()} task: use a {effective_budget}-token budget and "
            "retrieve bounded evidence for the selected lanes."
        ),
        lanes=lanes,
    )
