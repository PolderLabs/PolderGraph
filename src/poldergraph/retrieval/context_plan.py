"""Cheap deterministic planning for automatic repository context."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

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
    changed_paths: tuple[str, ...] = ()
    why_selected: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "intent": self.intent,
            "budget": self.budget,
            "skipped": self.skipped,
            "reason": self.reason,
            "lanes": list(self.lanes),
            "why_selected": dict(self.why_selected),
            "changed_paths": list(self.changed_paths),
            "changed_paths_source_read_required": bool(self.changed_paths),
        }


_LANE_REASONS: dict[str, str] = {
    "exact": "Exact symbol and path matches for the named entities.",
    "lexical": "Keyword matches over indexed source text.",
    "semantic": "Semantic neighbours of the query; inferred, not structural fact.",
    "structural": "Callers, callees and typed edges resolved from source.",
    "tests": "Tests linked to the affected code.",
    "changed_files": "Files changed in the working tree for this request.",
}


def _why_selected(lanes: tuple[str, ...]) -> dict[str, str]:
    """Explain, per lane, why it was chosen for this task.

    Structural and semantic lanes stay explicitly distinguishable so an agent
    never reads an inferred neighbour as a proven dependency.
    """
    return {lane: _LANE_REASONS[lane] for lane in lanes if lane in _LANE_REASONS}


def plan_context(
    query: str, budget: int, *, changed_paths: tuple[str, ...] | list[str] = ()
) -> ContextPlan:
    """Select a cheap context policy without initializing embedding backends."""
    text = query.strip()
    normalized_budget = max(0, int(budget))
    # Stable ordering and a small cap keep plans deterministic and bounded.
    changed = tuple(sorted(set(changed_paths))[:32])
    if not text or _SOCIAL.fullmatch(text):
        return ContextPlan(
            intent="none",
            budget=0,
            skipped=True,
            reason="No repository evidence is needed for this message.",
            lanes=(),
            changed_paths=(),
            why_selected={},
        )
    if _NARROW.search(text) and len(text.split()) <= 12 and not _BROAD.search(text):
        return ContextPlan(
            intent="locate",
            budget=min(normalized_budget, 1000),
            skipped=False,
            reason="Narrow lookup: use compact exact and lexical evidence.",
            lanes=("exact", "lexical"),
            changed_paths=changed,
            why_selected=_why_selected(("exact", "lexical")),
        )
    intent = "modify" if re.search(
        r"\b(refactor|change|changes|modify|implement|fix|impact|break|breaks|breaking|"
        r"ripple|regress\w*|affect\w*|consequence\w*)\b",
        text,
        re.I,
    ) else (
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
    if changed and intent in {"modify", "debug", "test"}:
        lanes = (*lanes, "changed_files")
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
        changed_paths=changed,
        why_selected=_why_selected(lanes),
    )
