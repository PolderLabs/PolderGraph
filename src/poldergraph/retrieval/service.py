"""The shared query service.

CLI, MCP and the dashboard all call this. There is deliberately no second
implementation of search for any surface.
"""

from __future__ import annotations

import subprocess
import threading
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Literal

from ..decision_runtime import decide_query_route, provider_enabled
from ..embedding.protocol import EmbeddingBackend
from ..errors import IndexStaleError, UsageError
from ..graph.metrics import importance_map
from ..models.edge import Edge
from ..models.entity import Entity
from ..storage.repository import Repository
from ..storage.sqlite import get_meta
from .context import ContextResult, apply_evidence_cursor, estimate_tokens, pack_context
from .context_plan import plan_context
from .lexical import Candidate, exact_matches, lexical_candidates
from .rerank import RankedResult, dedupe_results, detect_intent, fuse
from .semantic import neighbors_of, semantic_candidates
from .structural import PathResult, expand, find_path, find_tests, impact

STRICT_FRESHNESS_HASH_BYTE_LIMIT = 64 * 1024 * 1024
SOURCE_READ_INSTRUCTION = (
    "Read the listed source files directly before acting; this index evidence is not authoritative."
)


def _active_diff_paths(root: Path | None) -> list[str]:
    """Return a bounded local Git worktree path sample for task planning."""
    if root is None:
        return []
    try:
        result = subprocess.run(
            [
                "git", "-C", str(root), "status", "--porcelain=v1", "-z",
                "--untracked-files=all", "--", ".", ":!.poldergraph",
            ],
            capture_output=True,
            text=True,
            timeout=0.25,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    paths: set[str] = set()
    for entry in result.stdout.split("\0"):
        if len(entry) < 4 or entry[2] != " ":
            continue
        path = entry[3:].replace("\\", "/")
        if not path or any(part in {".git", ".poldergraph", "node_modules"} for part in path.split("/")):
            continue
        paths.add(path)
        if len(paths) >= 256:
            break
    return sorted(paths)


def _read_generation(method: Any) -> Any:
    """Run nested query operations against one serialized SQLite snapshot."""

    @wraps(method)
    def wrapped(self: QueryService, *args: Any, **kwargs: Any) -> Any:
        with self._snapshot_lock:
            connection = self.repo.con
            depth = getattr(self._snapshot_local, "depth", 0)
            owns_transaction = depth == 0 and not connection.in_transaction
            if owns_transaction:
                connection.execute("BEGIN")
                data_version = int(connection.execute("PRAGMA data_version").fetchone()[0])
                generation_start = self._index_generation()
                self._snapshot_local.data_version = data_version
                self._snapshot_local.generation = generation_start
            self._snapshot_local.depth = depth + 1
            try:
                result = method(self, *args, **kwargs)
            except BaseException:
                self._snapshot_local.depth = depth
                if owns_transaction and connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
            self._snapshot_local.depth = depth
            if not owns_transaction:
                return result

            connection.execute("COMMIT")
            generation_end = self._index_generation()
            data_version_end = int(connection.execute("PRAGMA data_version").fetchone()[0])
            freshness = self.freshness()
            generation_changed = generation_start != generation_end
            database_changed = data_version != data_version_end
            changed = generation_changed or database_changed
            freshness.update(
                {
                    "generation_start": generation_start,
                    "generation_end": generation_end,
                    "generation_changed": generation_changed,
                    "database_changed": database_changed,
                }
            )
            report = getattr(result, "consistency_report", None)
            if report is None and isinstance(result, dict):
                report = result.get("consistency_report")
            stale = not freshness["fresh"]
            if isinstance(report, dict):
                report.update(
                    {
                        "generation_start": generation_start,
                        "generation_end": generation_end,
                        "generation_changed": generation_changed,
                        "database_changed": database_changed,
                        "structural_freshness": freshness["structural"],
                        "pending_changes": freshness["pending_changes"],
                        "stale_files": freshness["stale_files"],
                        "stale_files_truncated": freshness["stale_files_truncated"],
                        "stale_since": freshness["stale_since"],
                    }
                )
                if stale or changed:
                    report["status"] = "stale" if stale else "generation_changed"
                    report["source_read_required"] = True
                    report["source_read_instruction"] = SOURCE_READ_INSTRUCTION
                    report["verified"] = False
            if kwargs.get("consistency", "bounded") == "strict" and (stale or changed):
                raise IndexStaleError(
                    "The index changed during this query.",
                    details={"freshness": freshness},
                )
            if isinstance(result, dict) and isinstance(result.get("index"), dict):
                result["index"].update(freshness)
            return result

    return wrapped


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
    consistency: str = "bounded"
    consistency_report: dict[str, Any] = field(default_factory=dict)

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
            "consistency": self.consistency,
            "consistency_report": self.consistency_report,
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
        self._freshness_directories: dict[str, int] | None = None
        self._freshness_directory_generation: str | None = None
        self._snapshot_lock = threading.RLock()
        self._snapshot_local = threading.local()
        self._search_cache: OrderedDict[tuple[Any, ...], SearchResponse] = OrderedDict()
        self._search_cache_limit = 64

    def workspace_index(self) -> Any:
        """Index directory, used for size reporting."""
        from pathlib import Path

        from ..workspace import find_index_dir

        if self.workspace is not None:
            return self.workspace.index_dir
        return find_index_dir(self.root) or Path.cwd() / ".poldergraph"

    # ---------------------------------------------------------------- search

    @_read_generation
    def search(
        self,
        query: str,
        *,
        limit: int = 20,
        filters: SearchFilters | None = None,
        include_semantic: bool = True,
        include_structural_context: bool = False,
        consistency: Literal["strict", "bounded", "best_effort"] = "bounded",
    ) -> SearchResponse:
        """Run hybrid retrieval across the independent evidence channels."""
        snapshot = self._start_consistency(consistency)
        filters = filters or SearchFilters()
        # Decision-enabled searches first check deterministic fast paths, which
        # may change independently of a prior ambiguous-query route.
        cache_key = None
        if not provider_enabled(self.config):
            cache_key = self._search_cache_key(
                query, limit, filters, include_semantic, include_structural_context
            )
            cached = self._search_cache.get(cache_key)
            if cached is not None:
                self._search_cache.move_to_end(cache_key)
                response = deepcopy(cached)
                response.consistency = consistency
                response.consistency_report = self._finish_consistency(consistency, snapshot)
                return response
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
        response = SearchResponse(
            query=query,
            intent=str(intent_value),
            results=filtered[:limit],
            degraded=degraded,
            truncated=truncated,
            routing=routing,
            consistency=consistency,
        )
        response.consistency_report = self._finish_consistency(consistency, snapshot)
        if cache_key is not None:
            self._search_cache[cache_key] = deepcopy(response)
            self._search_cache.move_to_end(cache_key)
            while len(self._search_cache) > self._search_cache_limit:
                self._search_cache.popitem(last=False)
        return response

    def _search_cache_key(
        self,
        query: str,
        limit: int,
        filters: SearchFilters,
        include_semantic: bool,
        include_structural_context: bool,
    ) -> tuple[Any, ...]:
        """Key deterministic candidate/ranking work to every retrieval input."""
        retrieval = self.config.retrieval
        settings = (
            retrieval.lexical_candidates,
            retrieval.semantic_candidates,
            retrieval.graph_hops,
            retrieval.max_graph_candidates,
            retrieval.max_expansion_fanout,
            tuple(sorted(retrieval.weights.items())),
            tuple(sorted(retrieval.kind_priors.items())),
        )
        backend = None
        if self.backend is not None:
            try:
                info = self.backend.model_info()
                backend = (info.model_id, info.revision, info.dimensions, info.backend)
            except Exception:
                backend = (type(self.backend).__qualname__,)
        decisions = self.config.decisions
        decision_settings = (
            decisions.provider,
            decisions.model,
            decisions.endpoint,
            decisions.confidence_threshold,
            provider_enabled(self.config),
        )
        return (
            self._index_generation(),
            self.root_id,
            query,
            limit,
            tuple(sorted(filters.kinds)),
            tuple(sorted(filters.languages)),
            tuple(sorted(filters.roots)),
            tuple(sorted(filters.path_prefixes)),
            tuple(sorted(filters.provenances)),
            include_semantic,
            include_structural_context,
            settings,
            backend,
            decision_settings,
        )

    def _index_generation(self) -> str:
        """Return a stable identifier for the currently indexed scan generation."""
        generation = get_meta(self.repo.con, "index_generation")
        if generation:
            return generation
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

    @_read_generation
    def explain(
        self,
        entity_ref: str,
        *,
        semantic_limit: int = 10,
        consistency: Literal["strict", "bounded", "best_effort"] = "bounded",
    ) -> dict[str, Any]:
        """Return identity, ownership, relations, neighbors and metrics."""
        snapshot = self._start_consistency(consistency)
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

        result = {
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
        result["consistency_report"] = self._finish_consistency(consistency, snapshot)
        return result

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

    @_read_generation
    def path(
        self,
        source_ref: str,
        target_ref: str,
        *,
        structural_only: bool = True,
        include_semantic: bool = False,
        max_hops: int = 12,
        consistency: Literal["strict", "bounded", "best_effort"] = "bounded",
    ) -> dict[str, Any]:
        """Compute a path between two resolvable entities."""
        snapshot = self._start_consistency(consistency)
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
        payload = self._path_to_dict(result, source, target)
        payload["consistency_report"] = self._finish_consistency(consistency, snapshot)
        return payload

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

    @_read_generation
    def impact(
        self,
        entity_ref: str,
        *,
        max_depth: int = 3,
        edge_types: list[str] | None = None,
        consistency: Literal["strict", "bounded", "best_effort"] = "bounded",
    ) -> dict[str, Any]:
        """Reverse-dependency impact for an entity or path."""
        snapshot = self._start_consistency(consistency)
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
        payload["consistency_report"] = self._finish_consistency(consistency, snapshot)
        return payload

    @_read_generation
    def related(
        self,
        entity_ref: str,
        *,
        limit: int = 10,
        consistency: Literal["strict", "bounded", "best_effort"] = "bounded",
    ) -> dict[str, Any]:
        """Semantic neighbours, annotated with structural linkage."""
        snapshot = self._start_consistency(consistency)
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
        result = {"entity": entity.to_dict(), "related": out}
        result["consistency_report"] = self._finish_consistency(consistency, snapshot)
        return result

    @_read_generation
    def find_tests(
        self,
        entity_ref: str | None = None,
        *,
        query: str | None = None,
        limit: int = 25,
        consistency: Literal["strict", "bounded", "best_effort"] = "bounded",
    ) -> dict[str, Any]:
        """Find structurally or lexically linked tests."""
        snapshot = self._start_consistency(consistency)
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
            response = self.search(query, limit=10, consistency=consistency)
            ids = [result.entity_id for result in response.results]
        else:
            raise UsageError(
                "Provide an entity reference or a query.",
                code="USAGE_ERROR",
                remediation="Usage: pg_find_tests(entity=...) or pg_find_tests(query=...)",
            )
        test_ids = find_tests(self.repo, ids, limit=limit)
        entities = self.repo.get_entities(test_ids)
        result = {
            "tests": [entities[test_id].to_dict() for test_id in test_ids if test_id in entities],
            "truncated": len(test_ids) >= limit,
        }
        result["consistency_report"] = self._finish_consistency(consistency, snapshot)
        return result

    # --------------------------------------------------------------- context

    @_read_generation
    def context(
        self,
        query: str,
        *,
        token_budget: int | None = None,
        filters: SearchFilters | None = None,
        consistency: Literal["strict", "bounded", "best_effort"] = "bounded",
        new_evidence_since: str | None = None,
    ) -> ContextResult:
        """Build the canonical agent context pack."""
        snapshot = self._start_consistency(consistency)
        budget = token_budget or self.config.retrieval.default_context_tokens
        plan = plan_context(query, budget)
        if plan.skipped:
            roots = self.repo.list_roots()
            freshness = self.freshness(verify_content=False)
            result = ContextResult(
                query=query,
                index={
                    "root": roots[0]["path"] if roots else ".",
                    **freshness,
                    "context_skipped": True,
                },
                plan=plan,
                consistency=consistency,
            )
            apply_evidence_cursor(result, new_evidence_since)
            result.consistency_report = self._finish_consistency(consistency, snapshot)
            return result
        # Feed known source drift into task planning. These paths are disclosed
        # as needing a source read: the indexed graph cannot safely stand in
        # for edits that have not yet been indexed.
        _pending, changed_paths, _truncated, _error = self._pending_change_details()
        if self.root is not None:
            changed_paths = sorted(set(changed_paths) | set(_active_diff_paths(self.root)))[:256]
        if changed_paths:
            plan = plan_context(query, budget, changed_paths=changed_paths)
        budget = plan.budget
        response = self.search(
            query,
            limit=30,
            filters=filters,
            include_semantic="semantic" in plan.lanes,
            include_structural_context="structural" in plan.lanes,
            consistency=consistency,
        )
        if "changed_files" in plan.lanes and plan.changed_paths:
            focused_paths = list(plan.changed_paths[:8])
            focused_filters = SearchFilters(
                kinds=list(filters.kinds) if filters else [],
                languages=list(filters.languages) if filters else [],
                roots=list(filters.roots) if filters else [],
                path_prefixes=focused_paths,
                provenances=list(filters.provenances) if filters else [],
            )
            changed_response = self.search(
                " ".join(focused_paths),
                limit=24,
                filters=focused_filters,
                include_semantic=False,
                consistency=consistency,
            )
            merged: dict[str, RankedResult] = {}
            for candidate in (*changed_response.results, *response.results):
                merged.setdefault(candidate.entity_id, candidate)
            response.results = list(merged.values())[:54]
            response.truncated = response.truncated or changed_response.truncated
            response.degraded.extend(changed_response.degraded)
        roots = self.repo.list_roots()
        freshness = self.freshness(verify_content=False)
        result = pack_context(
            self,
            query,
            response,
            token_budget=budget,
            root=roots[0]["path"] if roots else ".",
            freshness=freshness,
            degraded=response.degraded,
        )
        result.plan = plan
        result.consistency = consistency
        result.consistency_report = self._finish_consistency(consistency, snapshot)
        if "tests" in plan.lanes and result.entities:
            self._add_relevant_test_evidence(result, budget)
        apply_evidence_cursor(result, new_evidence_since)
        return result

    def _add_relevant_test_evidence(self, result: ContextResult, budget: int) -> None:
        """Add a few linked tests inside the existing context token budget."""
        entity_ids = [item["id"] for item in result.entities[:8] if item.get("id")]
        if not entity_ids:
            return
        test_ids = find_tests(self.repo, entity_ids, limit=8)
        if not test_ids:
            return
        links: dict[str, list[str]] = {test_id: [] for test_id in test_ids}
        for row in self.repo.con.execute(
            "SELECT source_id, target_id FROM edges WHERE type='tests'"
        ).fetchall():
            source, target = row[0], row[1]
            if source in links and target in entity_ids:
                links[source].append(target)
            elif target in links and source in entity_ids:
                links[target].append(source)
        content_budget = max(0, budget - 120)
        for test_id in test_ids:
            entity = self.repo.get_entity(test_id)
            if entity is None or not entity.path:
                continue
            connected = links[test_id]
            evidence = "structural_test_edge" if connected else "lexical_test_file_match"
            excerpt = self.source_excerpt(entity, max_chars=800)
            payload = {
                "id": entity.id,
                "name": entity.qualified_name or entity.name,
                "path": entity.path,
                "start_line": entity.start_line,
                "end_line": entity.end_line,
                "evidence": evidence,
                "linked_entity_ids": connected,
                "content": excerpt,
            }
            cost = estimate_tokens(str(payload))
            if result.token_estimate + cost > content_budget:
                result.truncated = True
                continue
            result.relevant_tests.append(payload)
            result.token_estimate += cost

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

    def freshness(self, *, verify_content: bool = False) -> dict[str, Any]:
        """Report whether the index reflects the current source tree."""
        state = get_meta(self.repo.con, "last_scan_at")
        last_scan = float(state) if state else 0.0
        drift, stale_files, truncated, check_error = self._pending_change_details(
            verify_content=verify_content
        )
        head = get_meta(self.repo.con, "indexed_head")
        try:
            from ..indexing.pipeline import git_state

            _branch, current_head = git_state(self.root or Path.cwd())
        except Exception:
            current_head = None
        revision_changed = bool(head and current_head and head != current_head)
        fresh = drift == 0 and check_error is None and not revision_changed
        return {
            "fresh": fresh,
            "generation": self._index_generation(),
            "revision": head,
            "current_revision": current_head,
            "revision_changed": revision_changed,
            "structural": "fresh" if fresh else "stale",
            # The index does not yet track per-file embedding completion as a
            # committed generation, so callers must not infer semantic freshness.
            "semantic": "unknown",
            "last_scan_at": int(last_scan) if last_scan else None,
            "pending_changes": drift,
            "stale_files": stale_files,
            "stale_files_truncated": truncated,
            "freshness_error": check_error,
            "indexed_head": head,
            "stale_since": int(last_scan) if (drift or revision_changed) and last_scan else None,
            "source_read_required": not fresh,
            "source_read_instruction": SOURCE_READ_INSTRUCTION if not fresh else None,
        }

    def _require_fresh(self) -> None:
        freshness = self.freshness(verify_content=True)
        if not freshness["fresh"]:
            self._raise_stale(freshness)

    def _start_consistency(
        self, consistency: Literal["strict", "bounded", "best_effort"]
    ) -> dict[str, Any]:
        if consistency not in {"strict", "bounded", "best_effort"}:
            raise UsageError("Consistency must be strict, bounded, or best_effort.")
        generation = self._index_generation()
        data_version = int(self.repo.con.execute("PRAGMA data_version").fetchone()[0])
        connection_changes = int(self.repo.con.total_changes)
        if consistency == "strict":
            self._require_fresh()
        return {
            "generation": generation,
            "root_id": self.root_id,
            "data_version": data_version,
            "connection_changes": connection_changes,
        }

    def _finish_consistency(
        self,
        consistency: Literal["strict", "bounded", "best_effort"],
        snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        end_generation = self._index_generation()
        start_generation = str(snapshot["generation"])
        generation_changed = start_generation != end_generation
        end_data_version = int(self.repo.con.execute("PRAGMA data_version").fetchone()[0])
        database_changed = int(snapshot["data_version"]) != end_data_version
        connection_changed = int(snapshot["connection_changes"]) != int(self.repo.con.total_changes)
        # Bounded reads still inspect file revisions after retrieval. This is
        # the edit-to-index race barrier: a source edit that has not reached
        # SQLite must be disclosed even when no generation changed.
        freshness = self.freshness(verify_content=consistency == "strict")
        stale_during_query = not freshness["fresh"]
        if consistency == "strict" and (
            generation_changed or database_changed or connection_changed or stale_during_query
        ):
            freshness.update(
                generation_start=start_generation,
                generation_end=end_generation,
                generation_changed=generation_changed,
                database_changed=database_changed,
                connection_changed=connection_changed,
            )
            self._raise_stale(freshness)
        changed = generation_changed or database_changed or connection_changed
        return {
            "mode": consistency,
            "root_id": snapshot["root_id"],
            "generation_start": start_generation,
            "generation_end": end_generation,
            "generation_changed": generation_changed,
            "database_changed": database_changed,
            "connection_changed": connection_changed,
            "revision": freshness["revision"],
            "current_revision": freshness["current_revision"],
            "revision_changed": freshness["revision_changed"],
            "structural_freshness": freshness["structural"],
            "semantic_freshness": freshness["semantic"],
            "pending_changes": freshness["pending_changes"],
            "stale_files": freshness["stale_files"],
            "stale_files_truncated": freshness["stale_files_truncated"],
            "stale_since": freshness["stale_since"],
            "verified": consistency == "strict" and not changed and not stale_during_query,
            "status": (
                "stale" if stale_during_query
                else "generation_changed" if changed
                else "verified" if consistency == "strict" else "fresh"
            ),
            "source_read_required": stale_during_query or changed,
            "source_read_instruction": (
                SOURCE_READ_INSTRUCTION if stale_during_query or changed else None
            ),
        }

    @staticmethod
    def _raise_stale(freshness: dict[str, Any]) -> None:
        raise IndexStaleError(
            "The index is stale or could not be verified; strict consistency cannot return repository evidence.",
            details={"freshness": freshness},
        )

    def _pending_change_details(
        self, *, verify_content: bool = False
    ) -> tuple[int, list[str], bool, str | None]:
        """Return pending count and a bounded sample of stale workspace paths.

        Reconcile indexed and newly discovered paths so stale results name
        their source files when possible.
        """

        # Source paths in the index are relative to the indexed workspace, not
        # the process working directory. This matters for callers that open a
        # workspace by an explicit path (for example MCP clients).
        root = self.root or Path.cwd()
        try:
            records = self.repo.all_files(self.root_id)
        except Exception as exc:
            return 0, [], False, f"Could not read indexed file revisions ({type(exc).__name__})."
        seen: set[str] = set()
        stale_paths: list[str] = []
        pending = 0
        hashed_bytes = 0
        reconciliation_required = False

        def mark_stale(path: str) -> None:
            nonlocal pending
            pending += 1
            if len(stale_paths) < 100:
                stale_paths.append(path)

        for record in records:
            path = root / record["path"]
            seen.add(record["path"])
            try:
                stat_result = path.stat()
            except OSError:
                mark_stale(record["path"])
                continue
            if stat_result.st_size != record["size"]:
                mark_stale(record["path"])
                continue
            mtime_ns = stat_result.st_mtime_ns
            metadata_changed = stat_result.st_size != record["size"] or (
                bool(record["mtime_ns"]) and mtime_ns != record["mtime_ns"]
            )
            if metadata_changed:
                if Path(record["path"]).name in {
                    ".gitignore",
                    ".ignore",
                    ".poldergraphignore",
                }:
                    reconciliation_required = True
                mark_stale(record["path"])
                continue
            if verify_content:
                from ..discovery.scanner import safe_join
                from ..models.entity import content_hash

                hashed_bytes += stat_result.st_size
                if hashed_bytes > STRICT_FRESHNESS_HASH_BYTE_LIMIT:
                    return (
                        pending,
                        stale_paths,
                        pending > len(stale_paths),
                        "Strict freshness verification exceeded its 64 MiB read budget.",
                    )
                safe_path = safe_join(root, record["path"])
                try:
                    digest = content_hash(safe_path.read_bytes()) if safe_path else ""
                except OSError:
                    digest = ""
                if not digest or digest != record["content_hash"]:
                    mark_stale(record["path"])
        generation = self._index_generation()
        cached_directories = self._freshness_directories
        if (
            cached_directories is not None
            and self._freshness_directory_generation == generation
        ):
            directories_unchanged = True
            for relative, expected_mtime in cached_directories.items():
                directory = root / relative if relative else root
                try:
                    if directory.stat().st_mtime_ns != expected_mtime:
                        directories_unchanged = False
                        break
                except OSError:
                    directories_unchanged = False
                    break
            if directories_unchanged and not reconciliation_required:
                # File edits/deletions were checked above. Unchanged directory
                # mtimes prove there are no new or renamed entries, avoiding a
                # full ignore-aware tree walk on the common query path.
                return pending, stale_paths, pending > len(stale_paths), None
        try:
            discovered = self._discovery(root).scan()
        except OSError as exc:
            return pending, stale_paths, pending > len(stale_paths), (
                f"Could not reconcile workspace files ({type(exc).__name__})."
            )
        self._freshness_directories = dict(discovered.directories)
        self._freshness_directory_generation = generation
        for item in discovered.files:
            if item.path not in seen:
                mark_stale(item.path)
        return pending, stale_paths, pending > len(stale_paths), None

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
