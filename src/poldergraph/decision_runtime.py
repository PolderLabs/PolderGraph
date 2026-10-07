"""Conservative, shared integration of typed decisions into PolderGraph."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
from typing import Any

from .decisions import DecisionQuestion, choice, decide

logger = logging.getLogger(__name__)
_CACHE_TTL_SECONDS = 300.0
_CACHE_MAX_ITEMS = 512
_FAILURE_TTL_SECONDS = 15.0
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_FAILURES: dict[str, float] = {}
_CACHE_LOCK = threading.Lock()
_SENSITIVE_PATTERNS = (
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{16,}"),
    re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?"
        r"(?:-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|$)"
    ),
    re.compile(r"(?i)\b(?:password|passwd|api[_ -]?key|access[_ -]?token|secret)\s*[:=]\s*\S+"),
)


def _sanitize_text(value: str) -> str:
    for pattern in _SENSITIVE_PATTERNS:
        value = pattern.sub("[redacted]", value)
    return value


def _setting(config: Any, key: str, default: Any = None) -> Any:
    section = getattr(config, "decisions", None)
    if section is None:
        return default
    if isinstance(section, dict):
        return section.get(key, default)
    return getattr(section, key, default)


def provider_enabled(config: Any) -> bool:
    """Only an explicit configured provider enables model calls or data egress."""
    return _setting(config, "provider", "disabled") != "disabled"


def run_decision(
    state: str | dict[str, Any] | list[Any],
    questions: dict[str, DecisionQuestion],
    config: Any,
) -> dict[str, Any] | None:
    """Run a configured decision once, caching by content hash for five minutes.

    Raw state is never retained in the cache. Failures return ``None`` so callers
    preserve their deterministic behavior and never block retrieval or memory.
    """
    provider = _setting(config, "provider", "disabled")
    if provider == "disabled":
        return None
    model = _setting(config, "model")
    endpoint = _setting(config, "endpoint")
    timeout = float(_setting(config, "timeout", 3.0))
    canonical = json.dumps(
        {
            "state": state,
            "questions": {
                name: {
                    "type": question.type,
                    "instructions": question.instructions,
                    "options": dict(question.options),
                    "levels": list(question.levels),
                    "statement": question.statement,
                }
                for name, question in questions.items()
            },
            "provider": provider,
            "model": model,
            "endpoint": endpoint,
        },
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    now = time.monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(key)
        if cached and cached[0] > now:
            return json.loads(json.dumps(cached[1]))
        if cached:
            _CACHE.pop(key, None)
        failure_expiry = _FAILURES.get(key, 0.0)
        if failure_expiry > now:
            return None
        _FAILURES.pop(key, None)
    try:
        result = decide(
            state,
            questions,
            provider=provider,
            **({"model": model} if model else {}),
            **({"endpoint": endpoint} if endpoint else {}),
            timeout=timeout,
        )
    except Exception as exc:
        # Avoid logging error strings: provider errors can echo submitted state.
        logger.debug(
            "Typed decision unavailable (%s); using deterministic behavior", type(exc).__name__
        )
        with _CACHE_LOCK:
            if len(_FAILURES) >= _CACHE_MAX_ITEMS:
                oldest = min(_FAILURES, key=_FAILURES.get)
                _FAILURES.pop(oldest, None)
            _FAILURES[key] = now + _FAILURE_TTL_SECONDS
        return None
    with _CACHE_LOCK:
        if len(_CACHE) >= _CACHE_MAX_ITEMS:
            oldest = min(_CACHE, key=lambda item: _CACHE[item][0])
            _CACHE.pop(oldest, None)
        _CACHE[key] = (now + _CACHE_TTL_SECONDS, result)
    return json.loads(json.dumps(result))


def answer_confidence(answer: dict[str, Any], label: str | None = None) -> float | None:
    """Return confidence for a selected choice or the provider's top answer."""
    probabilities = answer.get("probabilities")
    if isinstance(probabilities, dict) and probabilities:
        if label is not None and isinstance(probabilities.get(label), (int, float)):
            return float(probabilities[label])
        numeric = [value for value in probabilities.values() if isinstance(value, (int, float))]
        if numeric:
            return max(float(value) for value in numeric)
    value = answer.get("confidence")
    if isinstance(value, (int, float)):
        return float(value)
    value = answer.get("probability")
    return float(value) if isinstance(value, (int, float)) else None


def decide_query_route(query: str, baseline_intent: str, config: Any) -> dict[str, Any] | None:
    """Select a bounded retrieval plan for ambiguous natural-language queries."""
    if not provider_enabled(config):
        return None
    intents = {
        "exact_symbol": "A specific code identifier, symbol, or path is requested.",
        "where": "Find where a behavior, validation, or feature is implemented.",
        "how_reaches": "Trace a call, data, or control flow through graph relationships.",
        "architecture": "Explain modules, architecture, or subsystem structure.",
        "change_impact": "Find likely impact, affected components, or safe change context.",
        "tests": "Find tests, specs, or test coverage for behavior.",
        "semantic": "Find conceptually related implementation or documentation.",
    }
    questions = {
        "intent": choice(
            "intent", "Choose the user's primary repository question intent.", intents
        ),
        "retrieval": choice(
            "retrieval",
            "Choose the cheapest retrieval that is likely to answer accurately. Prefer graph for call/data flow or impact, lexical for a precise name/location, and hybrid for concepts or broad explanations.",
            {
                "lexical": "Exact names or locations should be found by lexical and exact matching only.",
                "hybrid": "Combine exact, lexical, and semantic evidence for concepts or broad questions.",
                "graph": "Add bounded structural neighborhood expansion to lexical and semantic evidence.",
            },
        ),
    }
    result = run_decision(
        {"query": _sanitize_text(query[:4000]), "baseline_intent": baseline_intent},
        questions,
        config,
    )
    if not result:
        return {"status": "fallback", "provider": _setting(config, "provider")}
    threshold = float(_setting(config, "confidence_threshold", 0.9))
    answers = result.get("answers", {})
    chosen: dict[str, Any] = {}
    for key, allowed in (("intent", intents), ("retrieval", {"lexical", "hybrid", "graph"})):
        answer = answers.get(key, {})
        label = answer.get("choice")
        confidence = answer_confidence(answer, label)
        if label in allowed and confidence is not None and confidence >= threshold:
            chosen[key] = {"value": label, "confidence": confidence}
    if not chosen:
        return {
            "status": "abstained",
            "provider": result.get("provider"),
            "model": result.get("model"),
        }
    return {
        "status": "applied",
        "provider": result.get("provider"),
        "model": result.get("model"),
        **chosen,
    }


def decide_memory_relevance(
    query: str,
    memories: list[dict[str, Any]],
    config: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Remove only weak memory matches the decision model confidently rejects."""
    if not memories or not provider_enabled(config):
        return memories, None
    candidates = [
        memory
        for memory in memories
        if float(memory.get("lexical_score", 0.0)) < 0.8
        and (memory.get("semantic_score") is None or float(memory["semantic_score"]) < 0.85)
    ][:8]
    if not candidates:
        return memories, None
    questions = {
        f"relevant_{index}": DecisionQuestion(
            name=f"relevant_{index}",
            type="predicate",
            statement=(
                f"Memory {index} is directly relevant to the query and would improve "
                "an agent's answer without introducing unrelated or stale context."
            ),
            instructions="Judge relevance to the query using only the supplied memory text.",
        )
        for index, _memory in enumerate(candidates)
    }
    state = {
        "query": _sanitize_text(query[:2000]),
        "memories": [
            {
                "kind": memory["kind"],
                "content": _sanitize_text(str(memory["content"])[:1200]),
                "matched_terms": memory.get("matched_terms", []),
            }
            for memory in candidates
        ],
    }
    result = run_decision(state, questions, config)
    if not result:
        return memories, {"status": "fallback"}
    threshold = float(_setting(config, "confidence_threshold", 0.9))
    rejected: set[str] = set()
    confidences: dict[str, float] = {}
    for index, memory in enumerate(candidates):
        answer = result.get("answers", {}).get(f"relevant_{index}", {})
        probability = answer.get("probability")
        if isinstance(probability, (int, float)):
            confidences[memory["id"]] = float(probability)
            if probability <= 1.0 - threshold:
                rejected.add(memory["id"])
    if not confidences:
        return memories, {"status": "fallback"}
    filtered = [memory for memory in memories if memory["id"] not in rejected]
    return filtered, {
        "status": "applied",
        "provider": result.get("provider"),
        "model": result.get("model"),
        "filtered": len(rejected),
        "evaluated": len(confidences),
        "confidence_threshold": threshold,
    }


def rejected_memory_candidates(candidates: list[str], config: Any) -> set[int]:
    """Batch candidate gates and return only high-confidence rejection indices."""
    if not candidates or not provider_enabled(config):
        return set()
    threshold = float(_setting(config, "confidence_threshold", 0.9))
    rejected: set[int] = set()
    # Decision APIs answer all questions against one state in a single pass.
    for offset in range(0, len(candidates), 8):
        batch = candidates[offset : offset + 8]
        questions = {
            f"capture_{index}": choice(
                f"capture_{index}",
                "Should this explicit first-person user preference be saved for future coding tasks? Reject one-off instructions, temporary state, speculation, and statements with unclear ownership.",
                {
                    "store": "Explicit, durable preference or personal fact useful across future tasks.",
                    "reject": "One-off, temporary, inferred, unclear, or not useful as durable memory.",
                },
            )
            for index in range(len(batch))
        }
        result = run_decision(
            {"candidate_memories": [_sanitize_text(item[:1600]) for item in batch]},
            questions,
            config,
        )
        if not result:
            continue
        answers = result.get("answers", {})
        for index in range(len(batch)):
            answer = answers.get(f"capture_{index}", {})
            label = answer.get("choice")
            confidence = answer_confidence(answer, label)
            if label == "reject" and confidence is not None and confidence >= threshold:
                rejected.add(offset + index)
    return rejected


__all__ = [
    "answer_confidence",
    "decide_memory_relevance",
    "decide_query_route",
    "provider_enabled",
    "rejected_memory_candidates",
    "run_decision",
]
