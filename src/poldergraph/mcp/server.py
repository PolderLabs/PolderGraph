"""MCP stdio server.

Tools invoke the same query service classes as the CLI and the dashboard; there
is no agent-only retrieval implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..errors import (
    PolderGraphError,
    envelope,
    error_envelope,
)
from ..storage.repository import Repository

#: Bounded output limits so a tool never floods an agent's context.
DEFAULT_RESULT_LIMIT = 25
MAX_RESULT_LIMIT = 100
MAX_BUDGET_TOKENS = 60_000


def _server_class() -> Any:
    """Resolve the MCP server class across SDK versions.

    The 1.x SDK exposes ``FastMCP``; 2.x renamed it to ``MCPServer`` while
    keeping the same ``@tool()`` decorator and stdio transport.
    """
    try:
        from mcp.server.mcpserver import MCPServer

        return MCPServer
    except ImportError:
        pass
    try:
        from mcp.server.fastmcp import FastMCP

        return FastMCP
    except ImportError as exc:
        raise PolderGraphError(
            "The MCP SDK is not installed.",
            code="BACKEND_UNAVAILABLE",
            remediation="Install it with: uv pip install mcp",
        ) from exc


def build_server(root: Path | None = None) -> Any:
    """Build the MCP server bound to a workspace."""
    server_class = _server_class()

    from ..cli_support import build_service

    server = server_class("poldergraph")

    class Session:
        """Lazily opened workspace, reused across tool calls.

        The embedding backend is attached on demand: `pg_status` must answer
        without paying model load, which is slow enough to look like a hang.
        """

        def __init__(self) -> None:
            self._workspace = None
            self._repo: Repository | None = None
            self._service = None

        def service(self, *, need_backend: bool = False) -> Any:
            if self._service is None:
                self._workspace, self._repo, self._service = build_service(root, need_backend=False)
            if need_backend and getattr(self._service, "backend", None) is None:
                from ..embedding.gemma import create_backend

                config = self._service.config
                if config.embedding.backend != "none":
                    try:
                        self._service.backend = create_backend(
                            config,
                            cache_dir=None,  # type: ignore[union-attr]
                        )
                    except Exception:
                        # Model load can fail for many reasons (disk, network,
                        # version). Degrade to lexical-only rather than failing
                        # the entire tool invocation.
                        self._service.backend = None
            return self._service

        def repo(self) -> Repository:
            self.service()
            assert self._repo is not None
            return self._repo

        def close(self) -> None:
            if self._workspace is not None:
                self._workspace.close()
            self._workspace = None
            self._service = None

    session = Session()

    def _envelope(command: str) -> dict[str, Any]:
        try:
            return envelope(command=command, index=session.service().freshness())
        except PolderGraphError as exc:
            return error_envelope(command, exc)

    def _clamp(value: int | None, default: int) -> int:
        if not value:
            return default
        return max(1, min(int(value), MAX_RESULT_LIMIT))

    # ------------------------------------------------------------- pg_status

    @server.tool()
    def pg_status() -> dict[str, Any]:
        """Report index existence, freshness, model, capabilities and counts."""
        from ..storage.schema import INDEX_FORMAT_VERSION, SCHEMA_VERSION
        from ..storage.sqlite import database_size_bytes, get_meta

        service = session.service()
        repo = session.repo()
        config = service.config
        payload = {
            "root": str(service_root(service)),
            "fresh": service.freshness()["fresh"],
            "counts": repo.counts(),
            "model": config.embedding.model,
            "dimensions": config.index.dimensions,
            "backend": config.embedding.backend,
            "schema_version": SCHEMA_VERSION,
            "index_format_version": INDEX_FORMAT_VERSION,
            "languages": sorted(
                row[0]
                for row in repo.con.execute(
                    "SELECT DISTINCT language FROM entities WHERE language IS NOT NULL"
                ).fetchall()
            ),
            "communities": {
                "structural": len(repo.communities("structural")),
                "hybrid": len(repo.communities("hybrid")),
            },
            "database_bytes": database_size_bytes(service.workspace_index()),
            "last_scan_at": get_meta(repo.con, "last_scan_at"),
        }
        return _envelope("pg_status") | {"data": payload}

    # ------------------------------------------------------------- pg_search

    @server.tool()
    def pg_search(
        query: str,
        limit: int = DEFAULT_RESULT_LIMIT,
        kinds: list[str] | None = None,
        languages: list[str] | None = None,
        roots: list[str] | None = None,
        paths: list[str] | None = None,
        include_semantic: bool = True,
        include_structural_context: bool = False,
        consistency: str = "bounded",
    ) -> dict[str, Any]:
        """Search the repository with hybrid ranking and score decomposition."""
        from ..retrieval.service import SearchFilters

        service = session.service()
        filters = SearchFilters(
            kinds=kinds or [],
            languages=languages or [],
            roots=roots or [],
            path_prefixes=paths or [],
        )

        def run() -> dict[str, Any]:
            response = service.search(
                query,
                limit=_clamp(limit, DEFAULT_RESULT_LIMIT),
                filters=filters,
                include_semantic=include_semantic,
                include_structural_context=include_structural_context,
                consistency=consistency,
            )
            return _envelope("pg_search") | {"data": response.to_dict(explain=True)}

        return _guard("pg_search", run)

    # ------------------------------------------------------------ pg_context

    @server.tool()
    def pg_context(
        query: str,
        token_budget: int = 6000,
        kinds: list[str] | None = None,
        languages: list[str] | None = None,
        consistency: str = "bounded",
    ) -> dict[str, Any]:
        """Return the canonical repository context pack for a task.

        This is the preferred first tool for broad repository questions.
        """
        from ..retrieval.context_plan import plan_context
        from ..retrieval.service import SearchFilters

        def run():
            budget = max(500, min(int(token_budget), MAX_BUDGET_TOKENS))
            plan = plan_context(query, budget)
            if plan.skipped:
                service = session.service(need_backend=False)
                result = service.context(
                    query, token_budget=budget, consistency=consistency
                ).to_dict()
                result["memories"] = []
                result["memories_learned"] = 0
                return _envelope("pg_context") | {"data": result}
            service = session.service(need_backend=True)
            filters = SearchFilters(kinds=kinds or [], languages=languages or [])
            result = service.context(
                query, token_budget=budget, filters=filters, consistency=consistency
            ).to_dict()
            from ..memory import (
                MemoryStore,
                add_memories_to_context,
            )

            memory_store = MemoryStore(service.root)
            add_memories_to_context(
                result, memory_store, query, budget, backend=service.backend,
                decision_config=service.config.decisions,
            )
            # Keep the field for older consumers while context remains read-only.
            result["memories_learned"] = 0
            return _envelope("pg_context") | {"data": result}

        return _guard("pg_context", run)

    # ------------------------------------------------------------ pg_entity

    @server.tool()
    def pg_entity(entity: str) -> dict[str, Any]:
        """Return entity details and a bounded neighborhood."""
        return _guard(
            "pg_entity",
            lambda: _envelope("pg_entity") | {"data": session.service().explain(entity)},
        )

    # -------------------------------------------------------------- pg_path

    @server.tool()
    def pg_path(
        source: str,
        target: str,
        structural_only: bool = True,
        include_semantic: bool = False,
        max_hops: int = 12,
    ) -> dict[str, Any]:
        """Find the relationship path between two entities."""
        service = session.service()
        return _guard(
            "pg_path",
            lambda: (
                _envelope("pg_path")
                | {
                    "data": service.path(
                        source,
                        target,
                        structural_only=structural_only,
                        include_semantic=include_semantic,
                        max_hops=max_hops,
                    )
                }
            ),
        )

    # ----------------------------------------------------------- pg_related

    @server.tool()
    def pg_related(entity: str, limit: int = 10) -> dict[str, Any]:
        """Return semantic neighbours with structural linkage made explicit."""
        service = session.service()
        return _guard(
            "pg_related",
            lambda: (
                _envelope("pg_related") | {"data": service.related(entity, limit=_clamp(limit, 10))}
            ),
        )

    # ------------------------------------------------------------ pg_impact

    @server.tool()
    def pg_impact(
        entity: str,
        max_depth: int = 3,
        edge_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Show what may be affected if this entity changes."""
        service = session.service()
        return _guard(
            "pg_impact",
            lambda: (
                _envelope("pg_impact")
                | {"data": service.impact(entity, max_depth=max_depth, edge_types=edge_types)}
            ),
        )

    # ---------------------------------------------------------- pg_update

    @server.tool()
    def pg_update() -> dict[str, Any]:
        """Incrementally refresh the index. Safe to invoke repeatedly."""
        from ..indexing.incremental import plan_update
        from ..indexing.pipeline import Indexer

        service = session.service(need_backend=True)
        workspace = service.workspace
        indexer = Indexer(workspace, backend=service.backend)
        discovered = indexer.discover()
        from ..indexing.incremental import embedding_space_fingerprint

        embedding_space_id = embedding_space_fingerprint(service.backend)
        plan = plan_update(
            session.repo(), discovered, root_id=workspace.root_id(),
            embedding_space_id=embedding_space_id,
        )
        stats = indexer.run(
            discovered, changed=plan.to_index, removed_paths=plan.removed,
            embedding_space_id=embedding_space_id,
        )
        return _envelope("pg_update") | {"data": {"plan": plan.summary(), "index": stats.to_dict()}}

    # ------------------------------------------------------- pg_find_tests

    @server.tool()
    def pg_find_tests(
        entity: str | None = None, query: str | None = None, limit: int = 25
    ) -> dict[str, Any]:
        """Return structurally or lexically linked tests for a symbol or file."""
        service = session.service()
        return _guard(
            "pg_find_tests",
            lambda: (
                _envelope("pg_find_tests")
                | {"data": service.find_tests(entity, query=query, limit=_clamp(limit, 25))}
            ),
        )

    # ------------------------------------------------------------- pg_memory

    @server.tool()
    def pg_memory_status() -> dict[str, Any]:
        """Show the shared memory location and current project/user memory counts."""
        from ..memory import MemoryStore

        return _guard(
            "pg_memory_status",
            lambda: envelope(
                command="pg_memory_status", data=MemoryStore(session.service().root).status()
            ),
        )

    @server.tool()
    def pg_memory_search(query: str, scope: str = "all", limit: int = 10) -> dict[str, Any]:
        """Retrieve project notes and user preferences with local vector and keyword RAG."""
        from ..memory import MemoryStore, memory_backend

        def run():
            service = session.service()
            store = MemoryStore(service.root)
            results = store.search(
                query,
                scope=scope,
                limit=_clamp(limit, 10),
                backend=memory_backend(service.backend),
            )
            from ..decision_runtime import decide_memory_relevance

            results, decision_info = decide_memory_relevance(
                query, results, service.config.decisions
            )
            data = {
                "query": query,
                "scope": scope,
                "results": results,
                "store": str(store.database),
            }
            if decision_info is not None:
                data["memory_decision"] = decision_info
            return envelope(
                command="pg_memory_search",
                data=data,
            )

        return _guard("pg_memory_search", run)

    @server.tool()
    def pg_memory_list(scope: str = "all", limit: int = 50) -> dict[str, Any]:
        """List user memories and current-project memories, without showing other projects."""
        from ..memory import MemoryStore

        def run():
            store = MemoryStore(session.service().root)
            return envelope(
                command="pg_memory_list",
                data={
                    "scope": scope,
                    "results": store.list(scope=scope, limit=_clamp(limit, 50)),
                    "store": str(store.database),
                },
            )

        return _guard("pg_memory_list", run)

    @server.tool()
    def pg_memory_add(
        content: str,
        scope: str = "project",
        kind: str = "fact",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Save durable project knowledge or a user preference for future tasks."""
        from ..memory import MemoryStore, memory_backend

        def run():
            service = session.service()
            store = MemoryStore(service.root)
            data = store.add(
                content,
                scope=scope,
                kind=kind,
                tags=tags,
                backend=memory_backend(service.backend),
            )
            warnings = [data["vector_warning"]] if data.get("vector_warning") else []
            return envelope(command="pg_memory_add", data=data, warnings=warnings)

        return _guard("pg_memory_add", run)

    @server.tool()
    def pg_memory_update(
        memory_id: str,
        content: str | None = None,
        kind: str | None = None,
        tags: list[str] | None = None,
        clear_tags: bool = False,
    ) -> dict[str, Any]:
        """Update a visible memory and refresh its local vector."""
        from ..memory import MemoryStore, memory_backend

        def run():
            service = session.service()
            data = MemoryStore(service.root).update(
                memory_id,
                content=content,
                kind=kind,
                tags=[] if clear_tags else tags,
                backend=memory_backend(service.backend),
            )
            warnings = [data["vector_warning"]] if data.get("vector_warning") else []
            return envelope(command="pg_memory_update", data=data, warnings=warnings)

        return _guard("pg_memory_update", run)

    @server.tool()
    def pg_memory_forget(memory_id: str) -> dict[str, Any]:
        """Permanently remove a user or current-project memory and its vectors."""
        from ..memory import MemoryStore

        return _guard(
            "pg_memory_forget",
            lambda: envelope(
                command="pg_memory_forget",
                data=MemoryStore(session.service().root).forget(memory_id),
            ),
        )

    server.poldergraph_session = session  # type: ignore[attr-defined]
    return server


def service_root(service: Any) -> Path:
    for attribute in ("root", "workspace"):
        value = getattr(service, attribute, None)
        if isinstance(value, Path):
            return value
    return Path.cwd()


def _guard(command: str, call: Any) -> Any:
    """Run a tool body, converting domain errors into structured envelopes.

    An MCP tool must answer with an actionable error envelope rather than
    raising: the agent sees the message and the remediation step, not a crash.
    """
    try:
        return call()
    except PolderGraphError as exc:
        return error_envelope(command, exc)


def run_server(root: Path | None = None) -> None:
    """Run the stdio MCP server until the client disconnects."""
    server = build_server(root)
    session = getattr(server, "poldergraph_session", None)
    try:
        server.run()
    finally:
        if session is not None:
            session.close()


def main() -> int:  # pragma: no cover - console helper
    run_server()
    return 0
