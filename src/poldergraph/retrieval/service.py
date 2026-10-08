"""The shared query service.

CLI, MCP and the dashboard all call this. There is deliberately no second
implementation of search for any surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..decision_runtime import decide_query_route, provider_enabled
from ..embedding.protocol import EmbeddingBackend
from ..errors import UsageError
from ..graph.metrics import importance_map
from ..models.edge import Edge
from ..models.entity import Entity
from ..storage.repository import Repository
from ..storage.sqlite import get_meta
from .context import ContextResult, pack_context
from .context_plan import plan_context
from .lexical import Candidate, exact_matches, lexical_candidates
from .rerank import RankedResult, dedupe_results, detect_intent, fuse
from .semantic import neighbors_of, semantic_candidates
from .structural import PathResult, expand, find_path, find_tests, impact


@dataclass
class SearchFilters:
    """Filters shared by search, context and MCP tools."""

    kinds: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    roots: list[str] = field(default_factory=list)
    path_prefixes: list[str] = field(default_factory=list)
    provenances: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not any((self.kinds, self.languages, self.roots, self.path_prefixes, self.provenances))


@dataclass
class SearchResponse:
    """Ranked results plus the evidence behind them."""

    query: str
    intent: str
    results: list[RankedResult]
    degraded: list[str] = field(default_factory=list)
    truncated: bool = False
    routing: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, *, explain: bool = False) -> dict[str, Any]:
        return {
            "query": self.query,
            "intent": self.intent,
            "results": [
                {
                    "id": result.entity_id,
                    "label": result.entity.qualified_name or result.entity.name if result.entity else None,
                    "name": result.entity.qualified_name or result.entity.name if result.entity else None,
                    "kind": result.entity.kind if result.entity else None,
                    "path": result.entity.path if result.entity else None,
                    "qualified_name": result.entity.qualified_name if result.entity else None,
                    "language": result.entity.language if result.entity else None,
                    "start_line": result.entity.start_line if result.entity else None,
                    "end_line": result.entity.end_line if result.entity else None,
                    "score": round(result.score, 6),
                    "evidence": _primary_evidence(result),
                    "why_included": (
                        result.graph_provenance.get("why_included")
                        if result.graph_provenance
                        else None
                    ),
                    "graph_provenance": result.graph_provenance,
                    "index_generation": (
                        result.graph_provenance.get("index_generation")
                        if result.graph_provenance
                        else None
                    ),
                    "score_features": {
                        key: round(value, 6) for key, value in result.features.items()
                    },
                    **({"explain": result.explain()} if explain else {}),
                }
                for result in self.results
            ],
            "degraded": self.degraded,
            "truncated": self.truncated,
            "routing": self.routing,
        }


def _primary_evidence(result: RankedResult) -> str:
    """Badge showing the strongest evidence channel for a result."""
    for channel in ("exact_name", "exact_path", "lexical", "semantic", "graph_expanded"):
        if result.features.get(channel):
            return {
                "exact_name": "exact",
                "exact_path": "exact",
                "lexical": "lexical",
                "semantic": "semantic",
                "graph_expanded": "graph-expanded",
            }[channel]
    if result.features.get("graph_expansion"):
        return "graph-expanded"
    return "lexical"


class QueryService:
    """Read-mostly retrieval over the canonical index."""

    def __init__(
        self,
        repo: Repository,
        config: Any,
        backend: EmbeddingBackend | None = None,
        *,
        root_id: str | None = None,
        workspace: Any = None,
    ) -> None:
        self.repo = repo
        self.config = config
        self.backend = backend
        self.root_id = root_id
        self.workspace = workspace
        self.root = workspace.root if workspace is not None else None
        self._communities: dict[str, str] | None = None
        self._communities_token: tuple[Any, ...] | None = None

    def workspace_index(self) -> Any:
        """Index directory, used for size reporting."""
        from pathlib import Path

        from ..workspace import find_index_dir

        if self.workspace is not None:
            return self.workspace.index_dir
        return find_index_dir(self.root) or Path.cwd() / ".poldergraph"

    # ---------------------------------------------------------------- search

    def search(
        self,
        query: str,
        *,
        limit: int = 20,
        filters: SearchFilters | None = None,
        include_semantic: bool = True,
        include_structural_context: bool = False,
    ) -> SearchResponse:
        """Run hybrid retrieval across the independent evidence channels."""
        filters = filters or SearchFilters()
        baseline_intent = detect_intent(query)
        degraded: list[str] = []

        candidates: dict[str, Candidate] = {}

        def absorb(found: list[Candidate]) -> None:
            for candidate in found:
                existing = candidates.get(candidate.entity_id)
                if existing is None:
                    candidates[candidate.entity_id] = candidate
                    continue
                for key, value in candidate.features.items():
                    existing.features[key] = max(existing.features.get(key, 0.0), value)
                existing.channels |= candidate.channels
                if candidate.graph_provenance:
                    existing.graph_provenance = candidate.graph_provenance

        # Exact channel has the highest priority and is never scored away.
        exact = exact_matches(self.repo, query, root_id=self.root_id)
        absorb(exact)
        # Lexical channel.
        lexical = lexical_candidates(
            self.repo,
            query,
            limit=self.config.retrieval.lexical_candidates,
            kinds=filters.kinds or None,
            languages=filters.languages or None,
            root_id=self.root_id,
            path_prefixes=filters.path_prefixes or None,
        )
        absorb(lexical)

        # Exact identifiers and high-coverage lexical matches use the fast path.
        # Configured decision models see only ambiguous natural-language queries.
        strong_lexical = any(candidate.score >= 0.8 for candidate in lexical)
        route = None
        decision_eligible = (
            baseline_intent.value == "semantic"
            and not exact
            and not strong_lexical
            and provider_enabled(self.config)
        )
        if decision_eligible:
            route = decide_query_route(query, baseline_intent.value, self.config)
        intent_value = (route or {}).get("intent", {}).get("value", baseline_intent.value)
        retrieval_plan = (route or {}).get("retrieval", {}).get("value")
        effective_semantic = include_semantic
        effective_structural = include_structural_context
        if retrieval_plan == "lexical":
            effective_semantic = False
        elif retrieval_plan == "graph":
            effective_structural = True
        decision_status = (route or {}).get("status")
        if decision_status is None:
            decision_status = "fallback" if decision_eligible else (
                "fast_path" if provider_enabled(self.config) else "disabled"
            )
        route_confidence = {
            key: answer["confidence"]
            for key in ("intent", "retrieval")
            if route and isinstance((answer := route.get(key)), dict) and "confidence" in answer
        }
        routing = {
            "intent": intent_value,
            "strategy": "graph" if effective_structural else "hybrid" if effective_semantic else "lexical",
            "decision_plan": retrieval_plan,
            "source": "decision" if route and ("intent" in route or "retrieval" in route) else "deterministic",
            "provider": (route or {}).get("provider")
            or (self.config.decisions.provider if provider_enabled(self.config) else None),
            "model": (route or {}).get("model"),
            "decision_status": decision_status,
            "confidence": route_confidence,
        }
        # Semantic channel.
        semantic_degraded = None
        if effective_semantic:
            semantic, semantic_degraded = semantic_candidates(
                self.repo,
                query,
                self.backend,
                limit=self.config.retrieval.semantic_candidates,
                root_id=self.root_id,
                kinds=filters.kinds or None,
            )
            if semantic_degraded:
                degraded.append(semantic_degraded)
            absorb(semantic)

        candidate_list = list(candidates.values())

        expansion_ids: set[str] = set()
        expansion_truncated = False
        if effective_structural and candidate_list:
            seeds = [c.entity_id for c in candidate_list[:10]]
            expansion = expand(
                self.repo,
                seeds,
                hops=self.config.retrieval.graph_hops,
                total_cap=self.config.retrieval.max_graph_candidates,
                fanout_cap=self.config.retrieval.max_expansion_fanout,
                provenances=set(filters.provenances) if filters.provenances else None,
            )
            expansion_ids = set(expansion.entity_ids)
            expansion_truncated = expansion.truncated
            generation = self._index_generation()
            provenance_factor = {
                "extracted": 1.0,
                "resolved": 0.85,
                "manual": 0.8,
                "inferred": 0.55,
                "ambiguous": 0.3,
                "semantic": 0.0,
            }
            for entity_id in expansion.entity_ids:
                entity = self.repo.get_entity(entity_id)
                if entity is None or (self.root_id and entity.root_id != self.root_id):
                    continue
                path = expansion.path_to(entity_id)
                edge_path = [
                    {
                        "from": source_id,
                        "to": target_id,
                        **edge.to_dict(),
                    }
                    for source_id, target_id, edge in path
                ]
                confidence = 1.0
                for _source_id, _target_id, edge in path:
                    confidence *= max(
                        0.0,
                        min(
                            1.0,
                            float(edge.confidence)
                            * provenance_factor.get(str(edge.provenance), 0.5),
                        ),
                    )
                distance = max(1, expansion.distances.get(entity_id, 1))
                existing = candidates.get(entity_id)
                if existing is None:
                    existing = Candidate(entity_id=entity_id, entity=entity)
                    candidates[entity_id] = existing
                existing.features["graph_expansion"] = max(
                    existing.features.get("graph_expansion", 0.0), confidence / distance
                )
                existing.channels.add("graph")
                existing.entity = entity
                existing.graph_provenance = {
                    "seed_id": expansion.seed_ids.get(entity_id),
                    "distance": distance,
                    "edge_types": [step["type"] for step in edge_path],
                    "provenances": [step["provenance"] for step in edge_path],
                    "confidence": round(confidence, 6),
                    "path": edge_path,
                    "truncated": expansion.truncated,
                    "index_generation": generation,
                    "why_included": "reachable through bounded structural graph expansion",
                }

        ranked = fuse(
            list(candidates.values()),
            self.repo,
            self.config,
            query=query,
            structural_expansion_ids=expansion_ids,
            communities=self._community_map(),
            metrics=self.repo.metrics_map(),
        )
        ranked = dedupe_results(ranked)

        truncated = expansion_truncated
        if len(ranked) > limit * 3:
            truncated = True
        filtered = self._apply_filters(ranked, filters)
        return SearchResponse(
            query=query,
            intent=str(intent_value),
            results=filtered[:limit],
            degraded=degraded,
            truncated=truncated,
            routing=routing,
        )

    def _index_generation(self) -> str:
        """Return a stable identifier for the currently indexed scan generation."""
        format_version = get_meta(self.repo.con, "index_format_version") or "unknown"
        last_scan = get_meta(self.repo.con, "last_scan_at") or "unknown"
        return f"{format_version}:{last_scan}"

    def _apply_filters(self, results: list[RankedResult], filters: SearchFilters) -> list[RankedResult]:
        out: list[RankedResult] = []
        for result in results:
            entity = result.entity
            if entity is None:
                continue
            if filters.kinds and entity.kind not in filters.kinds:
                continue
            if filters.languages and (entity.language or "") not in filters.languages:
                continue
            if filters.roots and entity.root_id not in filters.roots:
                continue
            if filters.path_prefixes and not any(
                entity.path and entity.path.startswith(prefix) for prefix in filters.path_prefixes
            ):
                continue
            if filters.provenances and result.graph_provenance and not set(
                result.graph_provenance.get("provenances", [])
            ).intersection(filters.provenances):
                continue
            out.append(result)
        return out

    # --------------------------------------------------------------- explain

    def explain(self, entity_ref: str, *, semantic_limit: int = 10) -> dict[str, Any]:
        """Return identity, ownership, relations, neighbors and metrics."""
        entity = self.resolve_entity(entity_ref)
        if entity is None:
            raise UsageError(
                f"No entity matches '{entity_ref}'.",
                code="ENTITY_NOT_FOUND",
                remediation="Run: poldergraph search \"<term>\" --json to find candidates.",
            )

        inbound = self.repo.get_edges(entity.id, direction="inbound", limit=200)
        outbound = self.repo.get_edges(entity.id, direction="outbound", limit=200)
        metrics = self.repo.metrics_for(entity.id)
        communities = {
            mode: self.repo.community_of(entity.id, mode)
            for mode in ("structural", "hybrid")
        }
        neighbors = neighbors_of(
            self.repo, entity.id, self.backend, limit=semantic_limit, root_id=self.root_id
        )
        parent = self.repo.get_entity(entity.parent_id) if entity.parent_id else None
        excerpt = self.source_excerpt(entity)

        return {
            "entity": entity.to_dict(),
            "parent": parent.to_dict() if parent else None,
            "inbound": [self._describe_edge(edge, entity.id) for edge in inbound],
            "outbound": [self._describe_edge(edge, entity.id) for edge in outbound],
            "semantic_neighbors": [
                {
                    "entity": self._entity_ref(neighbor["entity"]),
                    "similarity": round(neighbor["similarity"], 6),
                    "modality": neighbor["modality"],
                }
                for neighbor in neighbors
            ],
            "communities": communities,
            "metrics": metrics,
            "excerpt": excerpt,
            "unresolved": self.repo.unresolved_for(entity.id),
        }

    def _describe_edge(self, edge: Edge, entity_id: str) -> dict[str, Any]:
        """Describe an edge relative to the entity being explained.

        Uses the `source`/`target`/`entity` field names the dashboard expects.
        """
        other_id = edge.target_id if edge.source_id == entity_id else edge.source_id
        other = self.repo.get_entity(other_id)
        return {
            **edge.to_dict(),
            "entity": self._entity_ref(other) if other else None,
        }

    # ------------------------------------------------------------- structure

    def _entity_ref(self, entity: Entity) -> dict[str, Any]:
        """Compact entity reference used by dashboard relation lists."""
        return {
            "id": entity.id,
            "label": entity.qualified_name or entity.name,
            "kind": entity.kind,
            "path": entity.path,
            "qualified_name": entity.qualified_name,
            "language": entity.language,
        }

    def path(
        self,
        source_ref: str,
        target_ref: str,
        *,
        structural_only: bool = True,
        include_semantic: bool = False,
        max_hops: int = 12,
    ) -> dict[str, Any]:
        """Compute a path between two resolvable entities."""
        source = self.resolve_entity(source_ref)
        target = self.resolve_entity(target_ref)
        if source is None:
            raise UsageError(
                f"No entity matches source '{source_ref}'.",
                code="ENTITY_NOT_FOUND",
                remediation="Run: poldergraph search \"<term>\" --json",
            )
        if target is None:
            raise UsageError(
                f"No entity matches target '{target_ref}'.",
                code="ENTITY_NOT_FOUND",
                remediation="Run: poldergraph search \"<term>\" --json",
            )
        result = find_path(
            self.repo,
            source.id,
            target.id,
            structural_only=structural_only,
            include_semantic=include_semantic,
            max_hops=max_hops,
        )
        return self._path_to_dict(result, source, target)

    def _path_to_dict(self, result: PathResult, source: Entity, target: Entity) -> dict[str, Any]:
        entities = self.repo.get_entities(result.nodes)
        return {
            "found": result.found,
            "reason": result.reason,
            "hops": result.hops,
            "from": source.to_dict(),
            "to": target.to_dict(),
            "nodes": [entities[node_id].to_dict() for node_id in result.nodes if node_id in entities],
            "edges": [edge.to_dict() for edge in result.edges],
        }

    def impact(self, entity_ref: str, *, max_depth: int = 3, edge_types: list[str] | None = None) -> dict[str, Any]:
        """Reverse-dependency impact for an entity or path."""
        entity = self.resolve_entity(entity_ref)
        if entity is None:
            raise UsageError(
                f"No entity matches '{entity_ref}'.",
                code="ENTITY_NOT_FOUND",
                remediation="Run: poldergraph search \"<term>\" --json",
            )
        result = impact(
            self.repo,
            entity.id,
            max_depth=max_depth,
            edge_types=set(edge_types) if edge_types else None,
        )
        payload = result.to_dict(self.repo)
        payload["entity"] = entity.to_dict()
        return payload

    def related(self, entity_ref: str, *, limit: int = 10) -> dict[str, Any]:
        """Semantic neighbours, annotated with structural linkage."""
        entity = self.resolve_entity(entity_ref)
        if entity is None:
            raise UsageError(
                f"No entity matches '{entity_ref}'.",
                code="ENTITY_NOT_FOUND",
                remediation="Run: poldergraph search \"<term>\" --json",
            )
        neighbors = neighbors_of(self.repo, entity.id, self.backend, limit=limit, root_id=self.root_id)
        out = []
        for neighbor in neighbors:
            other = neighbor["entity"]
            edges = self.repo.all_edges_between(entity.id, other.id)
            out.append(
                {
                    "entity": other.to_dict(),
                    "similarity": round(neighbor["similarity"], 6),
                    "structurally_connected": bool(edges),
                    "structural_edges": [
                        {"type": edge.type, "provenance": str(edge.provenance)} for edge in edges
                    ],
                }
            )
        return {"entity": entity.to_dict(), "related": out}

    def find_tests(self, entity_ref: str | None = None, *, query: str | None = None, limit: int = 25) -> dict[str, Any]:
        """Find structurally or lexically linked tests."""
        if entity_ref:
            entity = self.resolve_entity(entity_ref)
            if entity is None:
                raise UsageError(
                    f"No entity matches '{entity_ref}'.",
                    code="ENTITY_NOT_FOUND",
                    remediation="Run: poldergraph search \"<term>\" --json",
                )
            ids = [entity.id]
        elif query:
            response = self.search(query, limit=10)
            ids = [result.entity_id for result in response.results]
        else:
            raise UsageError(
                "Provide an entity reference or a query.",
                code="USAGE_ERROR",
                remediation="Usage: pg_find_tests(entity=...) or pg_find_tests(query=...)",
            )
        test_ids = find_tests(self.repo, ids, limit=limit)
        entities = self.repo.get_entities(test_ids)
        return {
            "tests": [entities[test_id].to_dict() for test_id in test_ids if test_id in entities],
            "truncated": len(test_ids) >= limit,
        }

    # --------------------------------------------------------------- context

    def context(
        self,
        query: str,
        *,
        token_budget: int | None = None,
        filters: SearchFilters | None = None,
    ) -> ContextResult:
        """Build the canonical agent context pack."""
        budget = token_budget or self.config.retrieval.default_context_tokens
        plan = plan_context(query, budget)
        if plan.skipped:
            roots = self.repo.list_roots()
            freshness = self.freshness()
            return ContextResult(
                query=query,
                index={
                    "root": roots[0]["path"] if roots else ".",
                    **freshness,
                    "context_skipped": True,
                },
                plan=plan,
            )
        budget = plan.budget
        response = self.search(
            query,
            limit=30,
            filters=filters,
            include_semantic="semantic" in plan.lanes,
            include_structural_context="structural" in plan.lanes,
        )
        roots = self.repo.list_roots()
        result = pack_context(
            self,
            query,
            response,
            token_budget=budget,
            root=roots[0]["path"] if roots else ".",
            freshness=self.freshness(),
            degraded=response.degraded,
        )
        result.plan = plan
        return result

    # ------------------------------------------------------------- utilities

    def resolve_entity(self, reference: str) -> Entity | None:
        """Resolve a stable ID, qualified name, bare name or path."""
        reference = reference.strip()
        if not reference:
            return None
        entity = self.repo.get_entity(reference)
        if entity is not None:
            return entity
        for candidate in exact_matches(self.repo, reference, root_id=self.root_id, limit=5):
            if candidate.entity is not None:
                return candidate.entity
        return None

    def source_excerpt(self, entity: Entity, *, max_chars: int = 2400) -> str | None:
        """Read the entity's source text through the path-safety guard."""
        root = self.root or Path_cwd()
        if not entity.path:
            return None
        resolved = safe_read(root, entity.path)
        if resolved is None or entity.start_line is None:
            return None
        lines = resolved.splitlines()
        # Entity lines are 1-based for display; list indices are 0-based.
        start = max(0, entity.start_line - 1)
        end = (
            min(len(lines), entity.end_line)
            if entity.end_line is not None
            else min(len(lines), start + 60)
        )
        return "\n".join(lines[start:end])[:max_chars]

    def _community_map(self) -> dict[str, str]:
        if self._communities is None or self._communities_token != self._graph_token():
            self._communities = self.repo.community_map("structural")
            self._communities_token = self._graph_token()
        return self._communities

    def _graph_token(self) -> tuple[Any, ...]:
        """Cheap fingerprint that changes whenever the graph is recomputed.

        A resident query daemon serves many requests, so any cache derived from
        the graph must be invalidated when `poldergraph update` rewrites it —
        otherwise agents keep scoring against stale communities.
        """
        from ..storage.sqlite import get_meta

        return (get_meta(self.repo.con, "graph_computed_at"),)

    def importance(self) -> dict[str, float]:
        return importance_map(self.repo)

    def freshness(self) -> dict[str, Any]:
        """Report whether the index reflects the current source tree."""
        state = get_meta(self.repo.con, "last_scan_at")
        last_scan = float(state) if state else 0.0
        drift = self._pending_changes()
        head = get_meta(self.repo.con, "indexed_head")
        fresh = drift == 0
        return {
            "fresh": fresh,
            "generation": self._index_generation(),
            "revision": head,
            "structural": "fresh" if fresh else "stale",
            # The index does not yet track per-file embedding completion as a
            # committed generation, so callers must not infer semantic freshness.
            "semantic": "unknown",
            "last_scan_at": int(last_scan) if last_scan else None,
            "pending_changes": drift,
            "indexed_head": head,
            "stale_since": int(last_scan) if drift and last_scan else None,
            "source_read_required": not fresh,
        }

    def _pending_changes(self) -> int:
        """Count source files whose state drifted from the indexed snapshot.

        Uses size and mtime as a cheap first filter; only a file whose metadata
        moved is re-hashed, so the freshness check stays interactive.

        Walking only the indexed rows made every brand-new file invisible, so
        `status` reported `fresh: true` for a tree containing an untracked file
        that `poldergraph update` would immediately pick up. Freshness has to
        see both directions: indexed files that moved, and files on disk that
        the index has never seen.
        """
        from pathlib import Path

        # Source paths in the index are relative to the indexed workspace, not
        # the process working directory. This matters for callers that open a
        # workspace by an explicit path (for example MCP clients).
        root = self.root or Path.cwd()
        pending = 0
        try:
            records = self.repo.all_files(self.root_id)
        except Exception:
            return 0
        seen: set[str] = set()
        for record in records:
            path = root / record["path"]
            seen.add(record["path"])
            try:
                stat_result = path.stat()
            except OSError:
                pending += 1
                continue
            if stat_result.st_size != record["size"]:
                pending += 1
                continue
            mtime_ns = stat_result.st_mtime_ns
            if record["mtime_ns"] and mtime_ns != record["mtime_ns"]:
                pending += 1
        return pending + self._unindexed_files(root, seen)

    def _unindexed_files(self, root: Path, seen: set[str]) -> int:
        """Count indexable files on disk that the index has never seen.

        An untracked file is exactly the case a human most needs warned about,
        because retrieval will answer as if it were not there.
        """
        try:
            files = self._discovery(root).scan().files
        except OSError:
            return 0
        return sum(1 for f in files if f.path not in seen)

    def _discovery(self, root: Path) -> Any:
        """Build a discovery pass using the workspace's configured ignore rules."""
        from ..discovery.scanner import Discovery

        index_config = getattr(getattr(self.config, "index", None), "__dict__", {})
        include = index_config.get("include")
        exclude = index_config.get("exclude")
        return Discovery(
            root,
            include=list(include) if include else None,
            exclude=list(exclude) if exclude else None,
            follow_symlinks=bool(index_config.get("follow_symlinks", False)),
            include_generated=bool(index_config.get("include_generated", False)),
            include_media=bool(index_config.get("include_media", True)),
            max_file_bytes=int(index_config.get("max_file_bytes", 5_000_000)),
            max_roots=int(index_config.get("max_roots", 64)),
        )


def Path_cwd() -> Any:
    """Current working directory as a Path."""
    from pathlib import Path

    return Path.cwd()


def safe_read(root: Any, relative: str) -> str | None:
    """Read a repository file, refusing traversal and symlink escapes."""
    from ..discovery.scanner import safe_join

    target = safe_join(root, relative)
    if target is None or not target.is_file():
        return None
    try:
        return target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def neighborhood(
    repo: Repository,
    entity_id: str,
    *,
    depth: int = 2,
    direction: str = "both",
    fanout: int = 60,
    structural_only: bool = True,
) -> dict[str, Any]:
    """Bounded neighborhood for the dashboard's local graph view."""
    result = expand(
        repo,
        [entity_id],
        hops=depth,
        fanout_cap=fanout,
        total_cap=max(1, fanout) * max(1, depth) * 3,
        include_semantic=not structural_only,
    )
    ids = [entity_id, *result.entity_ids]
    entities = repo.get_entities(ids)
    return {
        "nodes": [_node(entity) for entity in entities.values()],
        "edges": [edge.to_dict() for edge in result.edges],
        "truncated": result.truncated,
    }


def _node(entity: Entity) -> dict[str, Any]:
    return {
        "id": entity.id,
        "label": entity.qualified_name or entity.name,
        "kind": entity.kind,
        "language": entity.language,
        "path": entity.path,
        "start_line": entity.start_line,
        "end_line": entity.end_line,
    }
