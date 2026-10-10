"""Local HTTP API for the dashboard.

A projection over the shared query service, not a second search implementation.
Binds to loopback by default and may only read files inside configured roots.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from pathlib import Path
from typing import Any

from ..config.models import Config
from ..errors import API_VERSION, PolderGraphError, UsageError, envelope, error_envelope
from ..memory import MemoryStore, memory_backend
from ..retrieval.service import QueryService, safe_read
from ..storage.repository import Repository
from ..storage.schema import SCHEMA_VERSION
from ..workspace import Workspace

#: Bundled dashboard assets, produced by the frontend build.
ASSET_DIR = Path(__file__).resolve().parent.parent / "web" / "dist"

#: Only loopback by default; binding elsewhere requires an explicit opt-in.
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


#: HTTP status for each command error code.
_ERROR_STATUS = {
    "USAGE_ERROR": 400,
    "INDEX_MISSING": 404,
    "INDEX_STALE": 409,
    "BACKEND_UNAVAILABLE": 503,
    "CORRUPT_INDEX": 500,
    "DOWNLOAD_DISABLED": 403,
    "UNSUPPORTED_BACKEND": 400,
    "MODEL_DOWNLOAD_FAILED": 502,
}


def create_app(workspace: Workspace, *, watch: bool = False, skip_backend: bool = False) -> Any:
    """Build the FastAPI application for a workspace."""
    try:
        from fastapi import FastAPI, Query, Request
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import FileResponse, JSONResponse
        from fastapi.staticfiles import StaticFiles
    except ImportError as exc:
        raise PolderGraphError(
            "FastAPI is not installed.",
            code="BACKEND_UNAVAILABLE",
            remediation="Install the API extra: uv pip install 'poldergraph[api]'",
        ) from exc

    # `from __future__ import annotations` turns handler annotations into
    # strings, and FastAPI resolves them against the *module* globals. Binding
    # these names here keeps endpoint signatures resolvable.
    globals()["Request"] = Request
    globals()["Query"] = Query
    globals()["FileResponse"] = FileResponse
    globals()["JSONResponse"] = JSONResponse

    config = workspace.config
    repo = Repository(workspace.con)
    backend = None if skip_backend else _build_backend(workspace)
    service = QueryService(
        repo, config, backend, root_id=workspace.root_id(), workspace=workspace
    )

    app = FastAPI(title="PolderGraph", version=API_VERSION, docs_url="/api/docs")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[f"http://{config.ui.host}:{config.ui.port}"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    def ok(command: str, data: Any) -> dict[str, Any]:
        return envelope(command=command, index=service.freshness(), data=data)

    def fail(command: str, error: PolderGraphError) -> JSONResponse:
        return JSONResponse(status_code=400, content=envelope(command=command, error=error))

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        counts = repo.counts()
        return ok(
            "status",
            {
                "root": str(workspace.root),
                "roots": [
                    {**root, "is_primary": bool(root["is_primary"])}
                    for root in repo.list_roots()
                ],
                "schema_version": SCHEMA_VERSION,
                "languages": sorted(
                    row[0]
                    for row in repo.con.execute(
                        "SELECT DISTINCT language FROM entities WHERE language IS NOT NULL"
                    ).fetchall()
                ),
                "fresh": service.freshness()["fresh"],
                "counts": counts,
                "model": config.embedding.model,
                "dimensions": config.index.dimensions,
                "communities": {
                    "structural": len(repo.communities("structural")),
                    "hybrid": len(repo.communities("hybrid")),
                },
                "capabilities": config.embedding.backend,
            },
        )

    @app.get("/api/graph/global")
    def graph_global(
        limit: int = Query(default=0, ge=0, le=50000),
        aggregate: str = Query(default="none"),
    ) -> dict[str, Any]:
        payload = build_global_graph(
            repo,
            config,
            root_id=workspace.root_id(),
            limit=limit or config.ui.global_graph_node_cap,
            aggregate=aggregate,
        )
        return ok("graph.global", payload)

    @app.get("/api/graph/neighborhood/{entity_id}")
    def graph_neighborhood(
        entity_id: str,
        depth: int = Query(default=2, ge=1, le=6),
        direction: str = Query(default="both"),
        structural_only: bool = Query(default=True),
        fanout: int = Query(default=0, ge=0, le=1000),
        kinds: str = Query(default=""),
        edge_types: str = Query(default=""),
    ) -> dict[str, Any]:
        from ..retrieval.structural import expand

        kind_list = [k for k in kinds.split(",") if k]
        edge_list = {e for e in edge_types.split(",") if e}

        expansion = expand(
            repo,
            [entity_id],
            hops=depth,
            fanout_cap=fanout or config.ui.neighborhood_fanout,
            total_cap=max(64, (fanout or config.ui.neighborhood_fanout) * depth * 4),
            edge_types=edge_list or None,
            include_semantic=not structural_only,
        )
        ids = [entity_id, *expansion.entity_ids]
        entities = repo.get_entities(ids)
        nodes = [_node(entity, repo) for entity in entities.values()]
        if kind_list:
            allowed = set(kind_list)
            nodes = [node for node in nodes if node["kind"] in allowed]
        return ok(
            "graph.neighborhood",
            {
                "nodes": nodes,
                "edges": [edge.to_dict() for edge in expansion.edges],
                "truncated": expansion.truncated,
            },
        )

    @app.get("/api/entity/{entity_id}")
    def entity(
        entity_id: str, consistency: str = Query(default="bounded")
    ) -> Any:
        try:
            return ok(
                "entity",
                service.explain(entity_id, semantic_limit=8, consistency=consistency),
            )
        except PolderGraphError as exc:
            return fail("entity", exc)

    @app.get("/api/search")
    def search(
        q: str = Query(...),
        limit: int = Query(default=20, ge=1, le=200),
        kinds: str = Query(default=""),
        languages: str = Query(default=""),
        paths: str = Query(default=""),
        include_semantic: bool = Query(default=True),
        include_structural_context: bool = Query(default=False),
        consistency: str = Query(default="bounded"),
        include_graph_context: bool = Query(default=False),
        graph_context_limit: int = Query(default=8, ge=1, le=24),
        graph_fanout: int = Query(default=10, ge=1, le=40),
    ) -> dict[str, Any]:
        from ..retrieval.service import SearchFilters

        filters = SearchFilters(
            kinds=[k for k in kinds.split(",") if k],
            languages=[item for item in languages.split(",") if item],
            path_prefixes=[p for p in paths.split(",") if p],
        )
        try:
            response = service.search(
                q,
                limit=limit,
                filters=filters,
                include_semantic=include_semantic,
                include_structural_context=include_structural_context,
                consistency=consistency,
            )
        except PolderGraphError as exc:
            return fail("search", exc)
        data = response.to_dict()
        if include_graph_context:
            from ..retrieval.structural import expand

            seeds = [
                result.entity_id
                for result in response.results[:graph_context_limit]
                if result.entity is not None
            ]
            expansion = expand(
                repo,
                seeds,
                hops=1,
                fanout_cap=graph_fanout,
                total_cap=graph_context_limit * graph_fanout,
            ) if seeds else None
            graph_ids = [*seeds, *(expansion.entity_ids if expansion else [])]
            entities = repo.get_entities(graph_ids)
            data["graph"] = {
                "nodes": [_node(entity, repo) for entity in entities.values()],
                "edges": [edge.to_dict() for edge in expansion.edges] if expansion else [],
                "truncated": bool(expansion and expansion.truncated),
                "aggregate": "none",
            }
        return ok("search", data)

    @app.get("/api/path")
    def path_route(
        from_: str = Query(..., alias="from"),
        to: str = Query(...),
        structural_only: bool = Query(default=True),
        include_semantic: bool = Query(default=False),
        consistency: str = Query(default="bounded"),
    ) -> Any:
        try:
            return ok(
                "path",
                service.path(
                    from_, to, structural_only=structural_only,
                    include_semantic=include_semantic, consistency=consistency,
                ),
            )
        except PolderGraphError as exc:
            return fail("path", exc)

    @app.get("/api/impact/{entity_id}")
    def impact_route(
        entity_id: str,
        max_depth: int = Query(default=3, ge=1, le=8),
        edge_types: str = Query(default=""),
        consistency: str = Query(default="bounded"),
    ) -> Any:
        try:
            return ok(
                "impact",
                service.impact(
                    entity_id,
                    max_depth=max_depth,
                    edge_types=[e for e in edge_types.split(",") if e] or None,
                    consistency=consistency,
                ),
            )
        except PolderGraphError as exc:
            return fail("impact", exc)

    @app.get("/api/communities")
    def communities(mode: str = Query(default="structural")) -> dict[str, Any]:
        if mode not in {"structural", "hybrid"}:
            mode = "structural"
        rows = repo.communities(mode)
        for row in rows:
            members = repo.con.execute(
                "SELECT entity_id FROM community_members WHERE community_id=? AND mode=? LIMIT 12",
                (row["community_id"], mode),
            ).fetchall()
            entities = repo.get_entities([member[0] for member in members])
            row["top_entities"] = [
                {"id": e.id, "name": e.qualified_name or e.name, "kind": e.kind}
                for e in entities.values()
            ]
        return ok("communities", {"mode": mode, "communities": rows})

    @app.post("/api/view/preferences")
    async def view_preferences(request: Request) -> dict[str, Any]:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        # Preferences are stored per workspace; the API only acknowledges them
        # because the dashboard also keeps a local copy.
        settings = _preferences_path(workspace)
        try:
            settings.parent.mkdir(parents=True, exist_ok=True)
            settings.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            pass
        return ok("view.preferences", payload)

# ------------------------------------------------------------ configuration

    #: Config sections the dashboard may read and write.
    CONFIG_SECTIONS = (
        "index",
        "embedding",
        "semantic_edges",
        "graph",
        "retrieval",
        "privacy",
        "decisions",
    )

    #: Never returned verbatim, so a secret cannot leave the machine by being
    #: displayed. Redacted rather than omitted so "unset" stays distinguishable.
    SECRET_FIELDS = ("api_key", "token", "password", "secret")

    def _redact(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: (
                    "***"
                    if any(marker in key.lower() for marker in SECRET_FIELDS)
                    else _redact(item)
                )
                for key, item in value.items()
            }
        return value

    def _config_payload() -> dict[str, Any]:
        config = workspace.config
        return {
            name: _redact(getattr(config, name).model_dump()) for name in CONFIG_SECTIONS
        }

    # A configuration mistake is the caller's, not the server's. Report it with
    # the same envelope as every other command error and a matching 4xx, so the
    # dashboard shows the message instead of a stack trace.
    @app.exception_handler(PolderGraphError)
    async def poldergraph_error_handler(request: Request, exc: PolderGraphError) -> Any:
        return JSONResponse(status_code=_ERROR_STATUS.get(exc.code, 400), content=error_envelope("error", exc))

    @app.get("/api/config")
    def read_config() -> dict[str, Any]:
        """Current workspace configuration, with anything secret redacted."""
        return ok("config.read", _config_payload())

    @app.put("/api/config")
    async def write_config(request: Request) -> dict[str, Any]:
        """Update configuration sections in place.

        Unknown sections and unknown fields are rejected rather than silently
        ignored, so a typo cannot look like it worked.
        """
        try:
            payload = await request.json()
        except Exception as exc:
            raise UsageError("Request body must be JSON.") from exc
        if not isinstance(payload, dict):
            raise UsageError("Configuration payload must be an object.")

        config = workspace.config
        applied: list[str] = []
        for name, values in payload.items():
            if name not in CONFIG_SECTIONS:
                raise UsageError(f"Unknown configuration section {name!r}.")
            if not isinstance(values, dict):
                raise UsageError(f"Section {name!r} must be an object.")
            section = getattr(config, name)
            unknown = [key for key in values if key not in section.model_dump()]
            if unknown:
                raise UsageError(
                    f"Unknown setting(s) in {name!r}: {', '.join(sorted(unknown))}."
                )
            merged = section.model_dump()
            merged.update(values)
            setattr(config, name, type(section)(**merged))
            applied.append(name)

        from ..config.loader import write_config as write_config_file

        write_config_file(config, workspace.index_dir)
        # The embedding model may have changed, so the cached service no longer
        # describes this workspace.
        service.invalidate_backend()
        return ok("config.write", {"applied": applied, "config": _config_payload()})

    def _model_cache_dir() -> Path:
        return (workspace.index_dir / "cache" / "model").resolve()

    def _model_is_cached() -> bool:
        directory = _model_cache_dir()
        if not directory.is_dir():
            return False
        needle = str(workspace.config.embedding.model).split("/")[-1].lower()
        return any(needle in child.name.lower() for child in directory.iterdir())

    def _workspace_vector_count() -> int:
        try:
            return int(workspace.con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0])
        except Exception:
            return 0

    @app.get("/api/models/status")
    def models_status() -> dict[str, Any]:
        """Which embedding model is configured and whether its weights are local."""
        config = workspace.config
        return ok(
            "models.status",
            {
                "backend": config.embedding.backend,
                "model": config.embedding.model,
                "dimensions": config.index.dimensions,
                "device": config.embedding.device,
                "allow_downloads": config.privacy.allow_model_downloads,
                "cache_dir": _model_cache_dir().as_posix(),
                "cached": _model_is_cached(),
                "vectors": _workspace_vector_count(),
            },
        )

    @app.post("/api/models/download")
    async def models_download() -> dict[str, Any]:
        """Fetch the configured embedding model into the local cache.

        Refuses when model downloads are switched off, so the setting the
        dashboard exposes is enforced rather than advisory.
        """
        config = workspace.config
        if not config.privacy.allow_model_downloads:
            raise PolderGraphError(
                "Model downloads are disabled for this workspace.",
                code="DOWNLOAD_DISABLED",
                remediation="Enable privacy.allow_model_downloads in Settings first.",
            )
        if config.embedding.backend != "native":
            raise PolderGraphError(
                "Only the native embedding backend downloads weights.",
                code="UNSUPPORTED_BACKEND",
                remediation="Set the embedding backend to 'native' first.",
            )

        from ..embedding.gemma import create_backend

        def load() -> tuple[str, int]:
            backend = create_backend(config, cache_dir=_model_cache_dir(), offline=False)
            info = backend.model_info()
            return info.model_id, info.dimensions

        try:
            model_id, dimensions = await asyncio.to_thread(load)
        except Exception as exc:
            raise PolderGraphError(
                f"Could not download the embedding model: {exc}",
                code="MODEL_DOWNLOAD_FAILED",
                remediation="Check the network connection and retry from Settings.",
            ) from exc
        return ok(
            "models.download",
            {
                "model": model_id,
                "dimensions": dimensions,
                "cached": _model_is_cached(),
            },
        )
    @app.get("/api/memory/status")
    def memory_status() -> dict[str, Any]:
        return ok("memory.status", MemoryStore(workspace.root).status())

    @app.get("/api/memory")
    def memory_list(
        scope: str = Query(default="all"),
        limit: int = Query(default=100, ge=1, le=100),
    ) -> Any:
        try:
            store = MemoryStore(workspace.root)
            return ok("memory.list", {"scope": scope, "results": store.list(scope=scope, limit=limit)})
        except PolderGraphError as exc:
            return fail("memory.list", exc)

    @app.get("/api/memory/search")
    def memory_search(
        q: str = Query(..., min_length=1),
        scope: str = Query(default="all"),
        limit: int = Query(default=30, ge=1, le=100),
        semantic: bool = Query(default=False),
    ) -> Any:
        try:
            store = MemoryStore(workspace.root)
            backend_for_memory = memory_backend() if semantic else None
            results = store.search(q, scope=scope, limit=limit, backend=backend_for_memory)
            from ..decision_runtime import decide_memory_relevance

            results, decision_info = decide_memory_relevance(
                q, results, workspace.config.decisions
            )
            data = {"query": q, "scope": scope, "results": results}
            if decision_info is not None:
                data["memory_decision"] = decision_info
            return ok(
                "memory.search",
                data,
            )
        except PolderGraphError as exc:
            return fail("memory.search", exc)

    @app.post("/api/memory")
    async def memory_add(request: Request) -> Any:
        try:
            payload = await request.json()
            result = MemoryStore(workspace.root).add(
                str(payload.get("content", "")),
                scope=payload.get("scope", "project"),
                kind=payload.get("kind", "fact"),
                tags=payload.get("tags", []),
            )
            return ok("memory.add", result)
        except PolderGraphError as exc:
            return fail("memory.add", exc)
        except (AttributeError, TypeError, ValueError) as exc:
            return fail("memory.add", UsageError(f"Invalid memory request: {exc}"))

    @app.post("/api/memory/{memory_id}/update")
    async def memory_update(memory_id: str, request: Request) -> Any:
        try:
            payload = await request.json()
            result = MemoryStore(workspace.root).update(
                memory_id,
                content=payload.get("content"),
                kind=payload.get("kind"),
                tags=payload.get("tags"),
            )
            return ok("memory.update", result)
        except PolderGraphError as exc:
            return fail("memory.update", exc)
        except (AttributeError, TypeError, ValueError) as exc:
            return fail("memory.update", UsageError(f"Invalid memory request: {exc}"))

    @app.get("/api/memory/{memory_id}/history")
    def memory_history(memory_id: str) -> Any:
        try:
            return ok(
                "memory.history",
                {"memory_id": memory_id, "versions": MemoryStore(workspace.root).history(memory_id)},
            )
        except PolderGraphError as exc:
            return fail("memory.history", exc)

    @app.post("/api/memory/{memory_id}/forget")
    def memory_forget(memory_id: str) -> Any:
        try:
            return ok("memory.forget", MemoryStore(workspace.root).forget(memory_id))
        except PolderGraphError as exc:
            return fail("memory.forget", exc)

    @app.get("/api/source")
    def source(
        path: str = Query(...),
        start_line: int = Query(default=1, ge=1),
        end_line: int = Query(default=0, ge=0),
    ) -> Any:
        """Return source text for an indexed path inside a configured root.

        Line numbers are 1-based and inclusive, matching every entity span the
        API reports, so a caller can pass an entity's ``start_line`` straight
        through and land on the declaration it names.
        """
        text = safe_read(workspace.root, path)
        if text is None:
            return fail(
                "source",
                UsageError(
                    f"Path '{path}' is not an indexed file inside a configured root.",
                    code="PATH_NOT_INDEXED",
                    remediation="Use a path exactly as returned by the API.",
                ),
            )
        lines = text.splitlines()
        start = min(max(1, start_line), max(1, len(lines)))
        end = min(len(lines), end_line) if end_line else min(len(lines), start + 399)
        end = max(start, end)
        return ok(
            "source",
            {
                "path": path,
                "start_line": start,
                "end_line": end,
                "content": "\n".join(lines[start - 1:end]),
            },
        )

    @app.get("/api/events")
    async def events(request: Request) -> Any:
        """Server-sent events for live index changes."""
        from sse_starlette.sse import EventSourceResponse

        async def generator():
            last_id = -1
            while True:
                if await request.is_disconnected():
                    break
                row = repo.con.execute(
                    "SELECT event_id, kind, entity_ids FROM change_events WHERE event_id > ? ORDER BY event_id LIMIT 50",
                    (last_id,),
                ).fetchall()
                if not row:
                    yield ": keepalive\n\n"
                    await asyncio.sleep(1.0)
                    continue
                for event in row:
                    last_id = event[0]
                    try:
                        ids = json.loads(event[2])
                    except json.JSONDecodeError:
                        ids = []
                    yield {
                        "event": "change",
                        "id": str(event[0]),
                        "data": json.dumps({"kind": event[1], "ids": ids}),
                    }
                await asyncio.sleep(0.5)

        return EventSourceResponse(generator())

    if ASSET_DIR.is_dir() and (ASSET_DIR / "index.html").is_file():
        assets = ASSET_DIR / "assets"
        if assets.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/{full_path:path}")
        def spa(full_path: str) -> Any:
            """Serve the dashboard SPA, falling back to index.html."""
            if full_path.startswith("api/"):
                return JSONResponse(status_code=404, content={"ok": False})
            candidate = (ASSET_DIR / full_path).resolve()
            try:
                candidate.relative_to(ASSET_DIR.resolve())
            except ValueError:
                return FileResponse(str(ASSET_DIR / "index.html"))
            if candidate.is_file():
                return FileResponse(str(candidate))
            return FileResponse(str(ASSET_DIR / "index.html"))

    return app


def _build_backend(workspace: Workspace) -> Any:
    from ..embedding.gemma import create_backend

    if workspace.config.embedding.backend == "none":
        return None
    try:
        return create_backend(workspace.config, cache_dir=None)
    except PolderGraphError:
        return None


def _preferences_path(workspace: Workspace) -> Path:
    return workspace.index_dir / "state" / "view-preferences.json"


def _node(entity: Any, repo: Repository) -> dict[str, Any]:
    """Render one node with the attributes the dashboard needs."""
    metrics = repo.metrics_for(entity.id)
    community = repo.community_of(entity.id, "structural")
    return {
        "id": entity.id,
        "label": entity.qualified_name or entity.name,
        "kind": entity.kind,
        "language": entity.language,
        "path": entity.path,
        "qualified_name": entity.qualified_name,
        "start_line": entity.start_line,
        "end_line": entity.end_line,
        "is_container": entity.is_container,
        "is_generated": entity.is_generated,
        "degree": metrics.get("degree", 0.0),
        "importance": metrics.get("pagerank", metrics.get("degree", 0.0)),
        "community": community.get("community_id") if community else None,
    }


def build_global_graph(
    repo: Repository,
    config: Config,
    *,
    root_id: str,
    limit: int = 3000,
    aggregate: str = "none",
) -> dict[str, Any]:
    """Build a bounded global graph payload for the dashboard.

    Large repositories must not send every node to the browser, so the result
    is capped and can be aggregated by directory or community.
    """
    from ..graph.metrics import graph_cache_key

    node_cap = min(limit, config.ui.global_graph_node_cap)
    edge_cap = config.ui.global_graph_edge_cap

    entities = repo.iter_entities(root_id=root_id)
    metrics = repo.metrics_map()
    if aggregate in {"directory", "community"} and len(entities) > node_cap:
        nodes, node_index = _aggregate_nodes(entities, aggregate, node_cap)
    else:
        ranked = sorted(
            entities,
            key=lambda e: metrics.get(e.id, {}).get("pagerank", metrics.get(e.id, {}).get("degree", 0.0)),
            reverse=True,
        )
        nodes = [_node(entity, repo) for entity in ranked[:node_cap]]
        node_index = {node["id"] for node in nodes}

    edges: list[dict[str, Any]] = []
    truncated = False
    for edge in repo.iter_edges(root_id=root_id):
        if edge.source_id in node_index and edge.target_id in node_index:
            edges.append(edge.to_dict())
            if len(edges) >= edge_cap:
                truncated = True
                break

    return {
        "nodes": nodes,
        "edges": edges,
        "truncated": truncated or len(entities) > node_cap,
        "aggregate": aggregate,
        "total_entities": len(entities),
        "cache_key": graph_cache_key(repo),
    }


def _aggregate_nodes(entities: list[Any], mode: str, cap: int) -> tuple[list[dict[str, Any]], set[str]]:
    """Group entities into meta-nodes by directory or community."""
    buckets: dict[str, list[Any]] = {}
    for entity in entities:
        if entity.kind in {"directory", "workspace", "repository"}:
            continue
        key = (
            "/".join(entity.path.split("/")[:-1]) or "."
            if mode == "directory"
            else (entity.kind if not entity.path else entity.path.split("/")[0])
        )
        buckets.setdefault(key, []).append(entity)

    nodes: list[dict[str, Any]] = []
    member_ids: set[str] = set()
    for key, members in sorted(buckets.items(), key=lambda pair: len(pair[1]), reverse=True):
        if len(nodes) >= cap:
            break
        meta_id = f"agg:{mode}:{key}"
        members = members[:200]
        member_ids.update(member.id for member in members)
        nodes.append(
            {
                "id": meta_id,
                "label": key,
                "kind": "aggregate",
                "aggregate_mode": mode,
                "size": len(members),
                "members": [member.id for member in members],
                "degree": float(len(members)),
                "importance": float(len(members)),
                "is_container": True,
                "is_generated": False,
                "language": None,
                "path": key,
                "start_line": None,
                "end_line": None,
                "community": None,
            }
        )
    return nodes, member_ids


def serve(workspace: Workspace, *, watch: bool = False) -> None:
    """Run the local dashboard server."""
    try:
        import uvicorn
    except ImportError as exc:
        raise PolderGraphError(
            "uvicorn is not installed.",
            code="BACKEND_UNAVAILABLE",
            remediation="Install the API extra: uv pip install 'poldergraph[api]'",
        ) from exc

    host = workspace.config.ui.host
    port = workspace.config.ui.port
    if host not in LOOPBACK_HOSTS:
        print(
            f"warning: binding to {host} exposes your repository index beyond this machine.",
            flush=True,
        )

    # Find a free port: try the configured port first, then scan forward.
    port = _find_free_port(host, port)

    app = create_app(workspace, watch=watch)

    if watch:
        import threading

        from ..indexing.watcher import run_watch

        threading.Thread(target=run_watch, args=(workspace.root,), daemon=True).start()

    url = f"http://{host}:{port}"
    print(f"PolderGraph dashboard: {url}", flush=True)
    if workspace.config.ui.open_browser:
        import webbrowser

        webbrowser.open(url)

    # Drive the server through its own lifecycle so Ctrl+C stops it cleanly.
    # `uvicorn.run` installs its own signal handling and reports an aborted
    # request as an ASGI error on the way out.
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    try:
        server.run()
    except KeyboardInterrupt:
        pass
    finally:
        with contextlib.suppress(Exception):
            server.should_exit = True
    print("Dashboard stopped.", flush=True)


def _find_free_port(host: str, preferred: int, *, max_attempts: int = 20) -> int:
    """Return the first available port starting from ``preferred``."""
    import socket

    for port in range(preferred, preferred + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((host, port))
                return port
        except OSError:
            continue
    raise PolderGraphError(
        f"Ports {preferred}-{preferred + max_attempts - 1} are all in use on {host}.",
        code="INDEX_LOCKED",
        remediation=f"Stop the process using port {preferred} or set ui.port in .poldergraph/config.toml",
    )
