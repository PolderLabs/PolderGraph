"""Context packing under a hard token budget.

The pack maximizes distinct useful evidence rather than concatenating top-K
chunks: exact entry points, short definitions, critical neighbors, then
lower-confidence semantic context.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..errors import API_VERSION, UsageError
from .context_plan import ContextPlan

if TYPE_CHECKING:
    from .service import QueryService

#: Small documented allowance for JSON framing outside the content budget.
FRAMING_ENVELOPE_TOKENS = 120

#: Characters per token for the conservative fallback estimator.
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Conservative deterministic token estimate.

    Uses the configured tokenizer when one is available, otherwise a
    characters-per-token approximation that over-estimates rather than
    under-estimates, so the budget is never silently exceeded.
    """
    if not text:
        return 0
    return max(1, (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN)


@dataclass
class ContextResult:
    """The canonical agent context document."""

    query: str
    index: dict[str, Any]
    entities: list[dict[str, Any]] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    snippets: list[dict[str, Any]] = field(default_factory=list)
    paths: list[dict[str, Any]] = field(default_factory=list)
    relevant_tests: list[dict[str, Any]] = field(default_factory=list)
    communities: list[dict[str, Any]] = field(default_factory=list)
    unresolved: list[dict[str, Any]] = field(default_factory=list)
    retrieval: dict[str, bool] = field(default_factory=dict)
    routing: dict[str, Any] = field(default_factory=dict)
    plan: ContextPlan | None = None
    consistency: str = "bounded"
    consistency_report: dict[str, Any] = field(default_factory=dict)
    token_estimate: int = 0
    truncated: bool = False
    evidence_cursor: str | None = None
    new_evidence_count: int = 0
    evidence_cursor_truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_version": API_VERSION,
            "query": self.query,
            "index": self.index,
            "entities": self.entities,
            "relationships": self.relationships,
            "snippets": self.snippets,
            "paths": self.paths,
            "relevant_tests": self.relevant_tests,
            "communities": self.communities,
            "unresolved": self.unresolved,
            "retrieval": self.retrieval,
            "routing": self.routing,
            "plan": self.plan.to_dict() if self.plan else None,
            "consistency": self.consistency,
            "consistency_report": self.consistency_report,
            "token_estimate": self.token_estimate,
            "truncated": self.truncated,
            "evidence_cursor": self.evidence_cursor,
            "new_evidence_count": self.new_evidence_count,
            "evidence_cursor_truncated": self.evidence_cursor_truncated,
        }


_CURSOR_FIELDS = (
    "entities",
    "relationships",
    "snippets",
    "paths",
    "relevant_tests",
    "communities",
    "unresolved",
    "memories",
)
_CURSOR_KEY_LIMIT = 512
_CURSOR_TOKEN_LIMIT = 16_384


def apply_evidence_cursor(result: ContextResult | dict[str, Any], cursor: str | None) -> None:
    """Remove already-delivered evidence and return a bounded cumulative cursor.

    The cursor contains only opaque SHA-256 evidence IDs, never source text or
    prompts. Changed snippets receive new IDs, so edits can be sent again.
    """
    prior = _decode_evidence_cursor(cursor)
    prior_set = set(prior)
    current_keys: list[str] = []
    new_count = 0
    for field_name in _CURSOR_FIELDS:
        items = (
            result.get(field_name, [])
            if isinstance(result, dict)
            else getattr(result, field_name, [])
        )
        fresh_items: list[dict[str, Any]] = []
        for item in items:
            key = _evidence_key(field_name, item)
            current_keys.append(key)
            if key not in prior_set:
                fresh_items.append(item)
                new_count += 1
        if cursor is not None:
            if isinstance(result, dict):
                if field_name in result:
                    result[field_name] = fresh_items
            elif hasattr(result, field_name):
                setattr(result, field_name, fresh_items)

    combined = list(dict.fromkeys((*prior, *current_keys)))
    truncated = len(combined) > _CURSOR_KEY_LIMIT
    combined = combined[-_CURSOR_KEY_LIMIT:]
    encoded = base64.urlsafe_b64encode(
        json.dumps({"v": 1, "keys": combined}, separators=(",", ":")).encode("ascii")
    ).decode("ascii").rstrip("=")
    if isinstance(result, dict):
        result["evidence_cursor"] = encoded
        result["evidence_cursor_truncated"] = truncated
        result["new_evidence_count"] = new_count if cursor is not None else len(current_keys)
    else:
        result.evidence_cursor = encoded
        result.evidence_cursor_truncated = truncated
        result.new_evidence_count = new_count if cursor is not None else len(current_keys)
    if cursor is not None:
        evidence = {
            name: (
                result.get(name, []) if isinstance(result, dict) else getattr(result, name, [])
            )
            for name in _CURSOR_FIELDS
        }
        token_estimate = estimate_tokens(json.dumps(evidence, ensure_ascii=False))
        if isinstance(result, dict):
            result["token_estimate"] = token_estimate
        else:
            result.token_estimate = token_estimate


def _evidence_key(field_name: str, item: dict[str, Any]) -> str:
    stable = {key: value for key, value in item.items() if key not in {"score", "matched_terms"}}
    payload = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{field_name}\0{payload}".encode()).hexdigest()


def _decode_evidence_cursor(cursor: str | None) -> list[str]:
    if cursor is None:
        return []
    if not isinstance(cursor, str) or len(cursor) > _CURSOR_TOKEN_LIMIT:
        raise UsageError("The evidence cursor is invalid or too large; omit it to reset context history.")
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UsageError("The evidence cursor is malformed; omit it to reset context history.") from exc
    keys = payload.get("keys") if isinstance(payload, dict) and payload.get("v") == 1 else None
    if (
        not isinstance(keys, list)
        or len(keys) > _CURSOR_KEY_LIMIT
        or any(not isinstance(key, str) or re.fullmatch(r"[0-9a-f]{64}", key) is None for key in keys)
    ):
        raise UsageError("The evidence cursor has an unsupported version or content; omit it to reset context history.")
    return list(dict.fromkeys(keys))


def pack_context(
    service: QueryService,
    query: str,
    response: Any,
    *,
    token_budget: int,
    root: str,
    freshness: dict[str, Any],
    degraded: list[str] | None = None,
) -> ContextResult:
    """Assemble a context pack within the token budget.

    Selection order prefers distinct evidence: exact matches, then
    high-centrality definitions, then implementation excerpts.
    """
    repo = service.repo
    budget = max(0, token_budget - FRAMING_ENVELOPE_TOKENS)
    spent = 0
    truncated = False

    model = None
    if service.backend is not None and service.backend.capabilities():
        try:
            model = service.backend.model_info()
        except Exception:
            model = None

    index_info = {
        "root": root,
        "head": freshness.get("indexed_head"),
        "fresh": freshness.get("fresh", True),
        "pending_changes": freshness.get("pending_changes", 0),
        "model": model.model_id if model else None,
        "revision": model.revision if model else None,
        "dimensions": model.dimensions if model else None,
    }

    result = ContextResult(
        query=query,
        index=index_info,
        retrieval={
            "semantic": any(r.features.get("semantic") for r in response.results),
            "lexical": any(r.features.get("lexical") for r in response.results),
            "structural": True,
        },
        routing=dict(getattr(response, "routing", {})),
    )

    seen_spans: set[tuple[str | None, int | None, int | None]] = set()
    relationships_seen: set[tuple[str, str, str]] = set()

    for ranked in response.results:
        entity = ranked.entity
        if entity is None:
            continue

        entity_payload = {
            "id": entity.id,
            "kind": entity.kind,
            "name": entity.qualified_name or entity.name,
            "path": entity.path,
            "language": entity.language,
            "start_line": entity.start_line,
            "end_line": entity.end_line,
            "signature": entity.signature,
            "community": (repo.community_of(entity.id, "structural") or {}).get("community_id"),
        }
        entity_cost = estimate_tokens(str(entity_payload))
        if spent + entity_cost > budget:
            truncated = True
            continue
        result.entities.append(entity_payload)
        spent += entity_cost

        # Relationships: strongest structural evidence first.
        for edge in repo.get_edges(entity.id, direction="outbound", limit=6):
            if edge.type not in {"calls", "imports", "inherits", "implements", "overrides", "constructs"}:
                continue
            key = (edge.source_id, edge.target_id, edge.type)
            if key in relationships_seen:
                continue
            relationships_seen.add(key)
            other = repo.get_entity(edge.target_id)
            if other is None:
                continue
            payload = {
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "target_name": other.qualified_name or other.name,
                "type": edge.type,
                "provenance": str(edge.provenance),
                "confidence": round(edge.confidence, 4),
                "line": edge.source_location.line,
            }
            cost = estimate_tokens(str(payload))
            if spent + cost > budget:
                truncated = True
                break
            result.relationships.append(payload)
            spent += cost

        # Snippets: source text for the highest-value symbols only.
        if entity.start_line is None or entity.kind in {"file", "document"}:
            continue
        span_key = (entity.path, entity.start_line, entity.end_line)
        if span_key in seen_spans:
            continue
        excerpt = service.source_excerpt(entity, max_chars=1200)
        if not excerpt:
            continue
        seen_spans.add(span_key)
        snippet = {
            "id": entity.id,
            "name": entity.qualified_name or entity.name,
            "path": entity.path,
            "start_line": entity.start_line,
            "end_line": entity.end_line,
            "content": excerpt,
        }
        cost = estimate_tokens(excerpt)
        if spent + cost > budget:
            truncated = True
            continue
        result.snippets.append(snippet)
        spent += cost

        if spent >= budget:
            truncated = True
            break

    # Communities for the packed entities.
    for payload in result.entities[:12]:
        community = repo.community_of(payload["id"], "structural")
        if community and community not in result.communities:
            result.communities.append(community)

    # Unresolved references are honesty signals; include a bounded sample.
    for payload in result.entities[:20]:
        for record in repo.unresolved_for(payload["id"])[:2]:
            result.unresolved.append(
                {
                    "id": payload["id"],
                    "name": record["name"],
                    "line": record["line"],
                    "reason": "no unique structural target",
                    "candidates": len(json_loads(record["candidates"])),
                }
            )

    result.token_estimate = spent
    result.truncated = truncated
    return result


def json_loads(value: str) -> list[Any]:
    import json

    try:
        return json.loads(value or "[]")
    except json.JSONDecodeError:
        return []


def dedupe_snippets(snippets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop nested spans whose text is contained in an already-picked span."""
    kept: list[dict[str, Any]] = []
    for snippet in sorted(
        snippets,
        key=lambda item: (item.get("start_line") or 0, -(item.get("end_line") or 0)),
    ):
        content = snippet.get("content") or ""
        if any(content and content in (existing.get("content") or "") for existing in kept):
            continue
        kept.append(snippet)
    return kept
