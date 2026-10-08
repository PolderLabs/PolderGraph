"""PolderGraph command-line interface.

Every query/status command supports `--json` with a stable, versioned envelope,
and exits with the documented codes so agents can branch on them.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Optional

import typer

from . import __version__
from .cli_support import (
    build_service,
    emit_error,
    emit_json,
    entity_line,
    freshness_payload,
    model_payload,
    table,
    truncate,
)
from .config.models import Config
from .errors import (
    API_VERSION,
    ExitCode,
    PolderGraphError,
    UsageError,
    envelope,
)
from .workspace import create_index, open_workspace

app = typer.Typer(
    name="poldergraph",
    help="Fully local, zero-cloud code intelligence graph.",
    add_completion=False,
    no_args_is_help=True,
)
memory_app = typer.Typer(
    help="Remember project knowledge and user preferences across coding agents.",
    no_args_is_help=True,
)
app.add_typer(memory_app, name="memory")

DimensionOption = typer.Option(
    256, "--dimensions", help="Embedding dimensions: 128, 256, 512 or 768."
)


def _overrides(**kwargs: Any) -> dict[str, Any]:
    """Build config overrides from explicit CLI flags only."""
    overrides: dict[str, Any] = {}
    if kwargs.get("dimensions"):
        overrides.setdefault("index", {})["dimensions"] = kwargs["dimensions"]
    if kwargs.get("backend"):
        overrides.setdefault("embedding", {})["backend"] = kwargs["backend"]
    if kwargs.get("media") is not None:
        overrides.setdefault("index", {})["include_media"] = kwargs["media"]
    if kwargs.get("port"):
        overrides.setdefault("ui", {})["port"] = kwargs["port"]
    if kwargs.get("host"):
        overrides.setdefault("ui", {})["host"] = kwargs["host"]
    if kwargs.get("open_browser") is not None:
        overrides.setdefault("ui", {})["open_browser"] = kwargs["open_browser"]
    return overrides


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"poldergraph {__version__}")
        raise typer.Exit(0)


@app.callback()
def main_callback(
    version: bool = typer.Option(False, "--version", callback=_version_callback, is_eager=True),
) -> None:
    """PolderGraph: local code intelligence for developers and coding agents."""


# --------------------------------------------------------------------- init


@app.command()
def init(
    path: Optional[Path] = typer.Argument(None, help="Repository or workspace root."),
    force: bool = typer.Option(False, "--force", help="Discard an existing index and rebuild."),
    no_agent: bool = typer.Option(False, "--no-agent", help="Skip agent instruction generation."),
    dimensions: int = typer.Option(256, "--dimensions", help="Embedding dimensions."),
    embedding_backend: str = typer.Option(
        "native", "--embedding-backend", help="native or ollama."
    ),
    media: bool = typer.Option(True, "--include-media/--no-media", help="Index media files."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Create the index and run complete indexing."""
    from .progress import ProgressDisplay, QuietProgress

    command = "init"
    p = QuietProgress() if (json_output or not sys.stderr.isatty()) else ProgressDisplay()
    try:
        overrides = _overrides(dimensions=dimensions, backend=embedding_backend, media=media)
        root = (path or Path.cwd()).resolve()
        if root.is_file():
            root = root.parent

        p.start_stage("Setting up index directory")
        index_existed = (root / ".poldergraph" / "index.sqlite3").exists()
        if force and index_existed:
            from .workspace import remove_index
            remove_index(root / ".poldergraph")
            p.finish_stage(detail="existing index removed")

        config = Config()
        create_index(root, config)
        p.finish_stage(detail=str(root / ".poldergraph"))

        from .agents.setup import setup_agent_guidance
        from .embedding.gemma import create_backend
        from .graph import run_graph_stage
        from .indexing.pipeline import Indexer
        from .storage.repository import Repository

        workspace = open_workspace(root, require_index=False, cli_overrides=overrides)
        repo = Repository(workspace.con)
        backend = None
        degraded: list[str] = []

        if workspace.config.embedding.backend != "none":
            p.start_stage("Loading embedding model")
            try:
                backend = create_backend(workspace.config, cache_dir=None)
                info = backend.model_info()
                p.finish_stage(detail=f"{info.model_id} @ {info.dimensions}d on {_device_label(backend)}")
            except PolderGraphError as exc:
                degraded.append(exc.message)
                backend = None
                p.finish_stage(status="skipped", detail=str(exc.message)[:80])
        else:
            p.add_stage("Embedding model")
            p.finish_stage(status="skipped", detail="disabled in config")

        p.start_stage("Discovering files")
        indexer = Indexer(workspace, backend=backend)
        indexer.ensure_root()
        discovered = indexer.discover()
        p.finish_stage(detail=f"{len(discovered)} files found")

        p.start_stage("Parsing and indexing")
        stats = indexer.run(discovered)
        p.finish_stage(
            detail=f"{stats.entities_written} entities, {stats.edges_written} edges, "
            f"{stats.embeddings_written} embeddings"
        )

        p.start_stage("Building graph")
        graph = run_graph_stage(workspace, workspace.config, repo, backend)
        communities = sum(len(c.memberships) for c in graph.communities)
        semantic = graph.semantic_edges.created
        p.finish_stage(detail=f"{communities} communities, {semantic} semantic edges")

        _ensure_gitignore(root)
        agent_result = None
        if not no_agent:
            p.start_stage("Writing agent guidance")
            agent_result = setup_agent_guidance(root, workspace.config)
            written = ", ".join(agent_result.get("written", [])) or "nothing"
            p.finish_stage(detail=written)

        p.done()

        payload = envelope(
            command=command,
            index={"root": str(root), "fresh": True, **model_payload_for(workspace)},
            data={
                "index": stats.to_dict(),
                "graph": graph.to_dict(),
                "counts": repo.counts(),
                "agent": agent_result,
                "degraded": degraded + stats.degraded,
            },
            warnings=degraded + stats.degraded,
        )
        if json_output:
            emit_json(payload)
        else:
            _print_init_summary(root, stats, graph, repo, agent_result, degraded + stats.degraded)
        workspace.close()
    except PolderGraphError as exc:
        p.error(exc.message)
        if exc.remediation:
            typer.secho(f"  -> {exc.remediation}", fg=typer.colors.YELLOW, err=True)
        if json_output:
            emit_error(command, exc)
        raise typer.Exit(int(exc.exit_code))


def _device_label(backend: Any) -> str:
    """Short label for the device an embedding backend selected."""
    info = backend.model_info()
    device = getattr(backend, "device", None) or "unknown"
    return f"{device}"


def model_payload_for(workspace: Any) -> dict[str, Any]:
    from .storage.sqlite import get_meta

    return {
        "model": workspace.config.embedding.model,
        "dimensions": workspace.config.index.dimensions,
        "backend": workspace.config.embedding.backend,
        "indexed_head": get_meta(workspace.con, "indexed_head"),
    }


def _print_init_summary(
    root: Path, stats: Any, graph: Any, repo: Any, agent: Any, degraded: list[str]
) -> None:
    typer.echo(f"Indexed {root}")
    typer.echo(f"  files      {stats.files_indexed} (+{stats.files_removed} removed)")
    typer.echo(f"  entities   {stats.entities_written}")
    typer.echo(f"  edges      {stats.edges_written}")
    typer.echo(f"  embeddings {stats.embeddings_written} ({stats.embeddings_reused} reused)")
    typer.echo(
        f"  communities {sum(len(c.memberships) for c in graph.communities)} (structural + hybrid)"
    )
    if stats.unresolved:
        typer.echo(f"  unresolved references {stats.unresolved}")
    for warning in degraded:
        typer.secho(f"  warning: {warning}", fg=typer.colors.YELLOW)
    if agent and agent.get("written"):
        typer.echo(f"  agent guidance: {', '.join(agent['written'])}")
    typer.echo("")
    typer.echo("Next:")
    typer.echo("  poldergraph ui")
    typer.echo('  poldergraph search "where is authorization checked?"')
    typer.echo('  poldergraph context "how does login work?" --json')


def _ensure_gitignore(root: Path) -> None:
    """Add only a minimal idempotent `.poldergraph/` entry."""
    gitignore = root / ".gitignore"
    entry = ".poldergraph/"
    try:
        existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    except OSError:
        return
    if entry in existing.split():
        return
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    try:
        with gitignore.open("a", encoding="utf-8") as handle:
            handle.write(f"{prefix}{entry}\n")
    except OSError:
        pass


# ------------------------------------------------------------------- update


@app.command()
def update(
    path: Optional[Path] = typer.Argument(None, help="Repository or workspace root."),
    quiet: bool = typer.Option(False, "--quiet", help="Print nothing on success."),
    force: bool = typer.Option(False, "--force", help="Re-verify hashes for every file."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
    offline: bool = typer.Option(False, "--offline", help="Forbid network access."),
) -> None:
    """Incrementally update the index."""
    from .progress import ProgressDisplay, QuietProgress

    command = "update"
    p = QuietProgress() if (json_output or quiet or not sys.stderr.isatty()) else ProgressDisplay()
    workspace = None
    try:
        from .embedding.gemma import create_backend
        from .graph import run_graph_stage
        from .indexing.incremental import plan_update
        from .indexing.pipeline import Indexer
        from .storage.repository import Repository

        p.start_stage("Opening index")
        workspace, repo, _ = build_service(path, offline=offline)
        p.finish_stage(detail=str(workspace.index_dir))

        indexer = Indexer(workspace, backend=None)
        if workspace.config.embedding.backend != "none":
            p.start_stage("Loading embedding model")
            try:
                indexer.backend = create_backend(workspace.config, cache_dir=None, offline=offline)
                info = indexer.backend.model_info()
                p.finish_stage(detail=f"{info.model_id} @ {info.dimensions}d on {_device_label(indexer.backend)}")
            except PolderGraphError as exc:
                indexer.backend = None
                if not quiet and not json_output:
                    p.warning(exc.message)
                p.finish_stage(status="skipped", detail=str(exc.message)[:80])

        p.start_stage("Scanning for changes")
        discovered = indexer.discover()
        plan = plan_update(repo, discovered, root_id=workspace.root_id(), force=force)
        changed = len(plan.to_index)
        unchanged = len(plan.unchanged)
        removed = len(plan.removed)
        p.finish_stage(detail=f"{changed} changed, {unchanged} unchanged, {removed} removed")

        if not plan.has_work:
            p.done()
            payload = envelope(
                command=command,
                index={"fresh": True, **model_payload_for(workspace)},
                data={"plan": plan.summary(), "index": {"changed": 0}, "graph": {}},
            )
            if json_output:
                emit_json(payload)
            elif not quiet:
                typer.echo("Nothing to update.")
            workspace.close()
            return

        if changed > 0:
            p.start_stage("Parsing and indexing")
            stats = indexer.run(discovered, changed=plan.to_index, removed_paths=plan.removed)
            stats.files_skipped = unchanged
            p.finish_stage(
                detail=f"{stats.entities_written} entities, {stats.edges_written} edges, "
                f"{stats.embeddings_written} embeddings"
            )
        else:
            stats = indexer.run(discovered, changed=[], removed_paths=plan.removed)
            stats.files_skipped = unchanged

        p.start_stage("Building graph")
        graph = run_graph_stage(workspace, workspace.config, repo, indexer.backend)
        communities = sum(len(c.memberships) for c in graph.communities)
        semantic = graph.semantic_edges.created
        p.finish_stage(detail=f"{communities} communities, {semantic} semantic edges")

        p.done()

        payload = envelope(
            command=command,
            index={"fresh": True, **model_payload_for(workspace)},
            data={"plan": plan.summary(), "index": stats.to_dict(), "graph": graph.to_dict()},
            warnings=stats.degraded,
        )
        if json_output:
            emit_json(payload)
        elif not quiet:
            typer.echo(
                f"Updated: {stats.files_indexed} indexed, "
                f"{stats.files_skipped} unchanged, {stats.files_removed} removed, "
                f"{stats.entities_written} entities, {stats.edges_written} edges"
            )
            for warning in stats.degraded:
                p.warning(warning)
    except PolderGraphError as exc:
        if json_output:
            emit_error(command, exc)
        elif not quiet:
            typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code))
    finally:
        if workspace:
            workspace.close()


# ------------------------------------------------------------------- watch


@app.command()
def watch(
    path: Optional[Path] = typer.Argument(None, help="Repository or workspace root."),
) -> None:
    """Continuously update the index as files change."""
    from .indexing.watcher import run_watch

    run_watch(path)


# ------------------------------------------------------------------ status


@app.command()
def status(
    path: Optional[Path] = typer.Argument(None, help="Repository or workspace root."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Show roots, versions, counts, model and language capability."""
    command = "status"
    workspace = None
    try:
        workspace, repo, service = build_service(path, need_backend=False)
        counts = repo.counts()
        from .parsing.engine import ParseEngine
        from .storage.schema import INDEX_FORMAT_VERSION, SCHEMA_VERSION
        from .storage.sqlite import database_size_bytes, get_meta

        capabilities = ParseEngine().capabilities()
        config = workspace.config
        payload = envelope(
            command=command,
            index={"root": str(workspace.root), "fresh": service.freshness()["fresh"]},
            data={
                "roots": repo.list_roots(),
                "versions": {
                    "schema": SCHEMA_VERSION,
                    "index_format": INDEX_FORMAT_VERSION,
                    "stored_format": get_meta(workspace.con, "index_format_version"),
                },
                "counts": counts,
                "embedding": {
                    "backend": config.embedding.backend,
                    "model": config.embedding.model,
                    "dimensions": config.index.dimensions,
                    "normalize": config.embedding.normalize,
                    "device": config.embedding.device,
                },
                "embeddings": repo.embedding_counts(),
                "languages": [
                    {
                        "language": info.language,
                        "available": info.available,
                        "strong": info.strong,
                        "resolves_imports": info.resolves_imports,
                        "detail": info.detail,
                    }
                    for info in capabilities
                ],
                "communities": {
                    "structural": len(repo.communities("structural")),
                    "hybrid": len(repo.communities("hybrid")),
                },
                "database_bytes": database_size_bytes(workspace.index_dir),
                "last_scan_at": get_meta(workspace.con, "last_scan_at"),
                "freshness": service.freshness(),
            },
        )
        if json_output:
            emit_json(payload)
        else:
            _print_status(workspace, counts, capabilities, config, payload)
    except PolderGraphError as exc:
        if json_output:
            emit_error(command, exc)
        else:
            typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code))
    finally:
        if workspace:
            workspace.close()


def _print_status(
    workspace: Any, counts: dict, capabilities: list, config: Config, payload: dict
) -> None:
    data = payload["data"]
    typer.echo(f"root        {workspace.root}")
    typer.echo(
        f"versions    schema {data['versions']['schema']}, "
        f"format {data['versions']['index_format']}"
    )
    freshness = data["freshness"]
    state = "fresh" if freshness["fresh"] else f"stale ({freshness['pending_changes']} pending)"
    typer.echo(f"freshness   {state}")
    typer.echo("")
    typer.echo(
        table(
            [
                ["files", str(counts["files"])],
                ["entities", str(counts["entities"])],
                ["edges", str(counts["edges"])],
                ["embeddings", str(counts["embeddings"])],
                ["unresolved", str(counts["unresolved"])],
                ["communities", str(counts["communities"])],
                ["database", _human_bytes(data["database_bytes"])],
            ],
            ["metric", "value"],
        )
    )
    typer.echo("")
    typer.echo(
        f"embedding   {config.embedding.model} @ {config.index.dimensions}d "
        f"({config.embedding.backend}, device={config.embedding.device})"
    )
    strong = [c.language for c in capabilities if c.strong and c.available]
    baseline = [c.language for c in capabilities if not c.strong and c.available]
    typer.echo(f"strong      {', '.join(sorted(strong)) or 'none'}")
    typer.echo(f"baseline    {', '.join(sorted(baseline)) or 'none'}")


def _human_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


# ------------------------------------------------------------------ search


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query."),
    path: Optional[Path] = typer.Option(None, "--path", help="Restrict to a path prefix."),
    limit: int = typer.Option(20, "--limit", help="Maximum results."),
    kind: list[str] = typer.Option([], "--kind", help="Filter by entity kind (repeatable)."),
    language: list[str] = typer.Option([], "--language", help="Filter by language (repeatable)."),
    semantic: bool = typer.Option(True, "--semantic/--no-semantic", help="Use semantic retrieval."),
    structural_context: bool = typer.Option(
        False, "--structural-context", help="Expand around strong candidates."
    ),
    explain_score: bool = typer.Option(False, "--explain-score", help="Show score breakdown."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
    root: Optional[Path] = typer.Argument(None, help="Repository root."),
) -> None:
    """Hybrid search over exact, lexical, semantic and structural evidence."""
    command = "search"
    workspace = None
    try:
        from .retrieval.service import SearchFilters

        workspace, repo, service = build_service(root, need_backend=semantic)
        filters = SearchFilters(kinds=list(kind), languages=list(language))
        if path:
            filters.path_prefixes = [str(path)]
        response = service.search(
            query,
            limit=limit,
            filters=filters,
            include_semantic=semantic,
            include_structural_context=structural_context,
        )
        payload = envelope(
            command=command,
            index=freshness_payload(service),
            data=response.to_dict(explain=explain_score),
            warnings=response.degraded,
        )
        if json_output:
            emit_json(payload)
        else:
            if not response.results:
                typer.echo("No matches.")
            rows = []
            for item in (
                response.data_dict_rows()
                if hasattr(response, "data_dict_rows")
                else payload["data"]["results"]
            ):
                rows.append(
                    [
                        f"{item['score']:.3f}",
                        item.get("name") or item["id"][:16],
                        item.get("kind") or "",
                        item.get("path") or "",
                        item.get("evidence") or "",
                    ]
                )
            typer.echo(table(rows, ["score", "name", "kind", "path", "evidence"]))
            if explain_score:
                typer.echo("")
                for item in payload["data"]["results"][:3]:
                    typer.echo(f"  {item.get('name')}")
                    for name, value in item["explain"]["contributions"].items():
                        typer.echo(f"    {name:<20} {value:+.4f}")
            for warning in response.degraded:
                typer.secho(f"warning: {warning}", fg=typer.colors.YELLOW)
    except PolderGraphError as exc:
        if json_output:
            emit_error(command, exc)
        else:
            typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code))
    finally:
        if workspace:
            workspace.close()


# ----------------------------------------------------------------- explain


@app.command()
def explain(
    entity: str = typer.Argument(..., help="Entity ID, qualified name or path."),
    root: Optional[Path] = typer.Option(None, "--root", help="Repository root."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Show identity, ownership, relations, neighbors and metrics for an entity."""
    command = "explain"
    workspace = None
    try:
        workspace, repo, service = build_service(root, need_backend=True)
        data = service.explain(entity)
        payload = envelope(command=command, index=freshness_payload(service), data=data)
        if json_output:
            emit_json(payload)
        else:
            _print_explain(data)
    except PolderGraphError as exc:
        if json_output:
            emit_error(command, exc)
        else:
            typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code))
    finally:
        if workspace:
            workspace.close()


def _print_explain(data: dict) -> None:
    entity = data["entity"]
    typer.echo(f"{entity['qualified_name'] or entity['name']}  [{entity['kind']}]")
    if entity["path"]:
        location = entity["path"]
        if entity["start_line"] is not None:
            location += f":{entity['start_line'] + 1}"
        typer.echo(f"  {location}")
    if entity.get("signature"):
        typer.echo(f"  {entity['signature']}")
    if entity.get("docstring"):
        typer.echo(f"  {truncate(entity['docstring'], 200)}")
    if data.get("parent"):
        parent = data["parent"]
        typer.echo(f"  owner: {parent['qualified_name'] or parent['name']}")
    if data["outbound"]:
        typer.echo("")
        typer.echo("outbound")
        for edge in data["outbound"][:15]:
            other = edge.get("other") or {}
            name = other.get("qualified_name") or other.get("name") or edge["target_id"][:12]
            typer.echo(f"  {edge['type']:<14} {name}  [{edge['provenance']}]")
    if data["inbound"]:
        typer.echo("")
        typer.echo("inbound")
        for edge in data["inbound"][:15]:
            other = edge.get("other") or {}
            name = other.get("qualified_name") or other.get("name") or edge["source_id"][:12]
            typer.echo(f"  {edge['type']:<14} {name}  [{edge['provenance']}]")
    if data["semantic_neighbors"]:
        typer.echo("")
        typer.echo("semantic neighbours (not structural)")
        for neighbor in data["semantic_neighbors"][:8]:
            typer.echo(
                f"  {neighbor['similarity']:.3f}  {neighbor['entity']['qualified_name'] or neighbor['entity']['name']}"
            )
    if data["metrics"]:
        typer.echo("")
        typer.echo("metrics  " + "  ".join(f"{k}={v:.4f}" for k, v in data["metrics"].items()))
    if data.get("excerpt"):
        typer.echo("")
        typer.echo(truncate(data["excerpt"], 1200))


# ------------------------------------------------------------------ related


@app.command()
def related(
    entity: str = typer.Argument(..., help="Entity ID, qualified name or path."),
    limit: int = typer.Option(10, "--limit", help="Maximum neighbours."),
    root: Optional[Path] = typer.Option(None, "--root", help="Repository root."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Semantic neighbours with structural linkage made explicit."""
    command = "related"
    workspace = None
    try:
        workspace, repo, service = build_service(root, need_backend=True)
        data = service.related(entity, limit=limit)
        payload = envelope(command=command, index=freshness_payload(service), data=data)
        if json_output:
            emit_json(payload)
        else:
            for item in data["related"]:
                marker = "linked" if item["structurally_connected"] else "unlinked"
                typer.echo(
                    f"{item['similarity']:.3f}  {item['entity']['qualified_name'] or item['entity']['name']}  ({marker})"
                )
    except PolderGraphError as exc:
        if json_output:
            emit_error(command, exc)
        else:
            typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code))
    finally:
        if workspace:
            workspace.close()


# -------------------------------------------------------------------- path


@app.command()
def path(
    source: str = typer.Argument(..., help="Source entity."),
    target: str = typer.Argument(..., help="Target entity."),
    structural_only: bool = typer.Option(
        True, "--structural-only/--include-semantic", help="Edge classes to traverse."
    ),
    max_hops: int = typer.Option(12, "--max-hops", help="Maximum path length."),
    root: Optional[Path] = typer.Option(None, "--root", help="Repository root."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Find the relationship path between two entities."""
    command = "path"
    workspace = None
    try:
        workspace, repo, service = build_service(root, need_backend=False)
        data = service.path(
            source,
            target,
            structural_only=structural_only,
            include_semantic=not structural_only,
            max_hops=max_hops,
        )
        payload = envelope(command=command, index=freshness_payload(service), data=data)
        if json_output:
            emit_json(payload)
        else:
            if not data["found"]:
                typer.echo(f"No path found: {data.get('reason')}")
                raise typer.Exit(0)
            typer.echo(f"{data['hops']} hops")
            for index, node in enumerate(data["nodes"]):
                prefix = "  " * index
                typer.echo(f"{prefix}{node['qualified_name'] or node['name']}  [{node['kind']}]")
                if index < len(data["edges"]):
                    edge = data["edges"][index]
                    typer.echo(f"{prefix}  -{edge['type']}-> [{edge['provenance']}]")
    except PolderGraphError as exc:
        if json_output:
            emit_error(command, exc)
        else:
            typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code))
    finally:
        if workspace:
            workspace.close()


# ------------------------------------------------------------------ impact


@app.command()
def impact(
    target: str = typer.Argument(..., help="Entity ID, qualified name or path."),
    max_depth: int = typer.Option(3, "--max-depth", help="Reverse dependency depth."),
    edge_type: list[str] = typer.Option(
        [], "--edge-type", help="Restrict edge classes (repeatable)."
    ),
    root: Optional[Path] = typer.Option(None, "--root", help="Repository root."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Show what may be affected if this entity changes."""
    command = "impact"
    workspace = None
    try:
        workspace, repo, service = build_service(root, need_backend=False)
        data = service.impact(target, max_depth=max_depth, edge_types=list(edge_type) or None)
        payload = envelope(command=command, index=freshness_payload(service), data=data)
        if json_output:
            emit_json(payload)
        else:
            entity = data["entity"]
            typer.echo(f"Impact of {entity['qualified_name'] or entity['name']}")
            for label in ("direct", "transitive", "tests", "docs"):
                items = data[label]
                if items:
                    typer.echo("")
                    typer.echo(f"{label} ({len(items)})")
                    for item in items[:20]:
                        typer.echo(f"  {item['name']}  {item['path'] or ''}")
    except PolderGraphError as exc:
        if json_output:
            emit_error(command, exc)
        else:
            typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code))
    finally:
        if workspace:
            workspace.close()


# ----------------------------------------------------------------- context


@app.command()
def context(
    query: str = typer.Argument(..., help="Question or task description."),
    budget: int = typer.Option(6000, "--budget", help="Token budget for the context pack."),
    root: Optional[Path] = typer.Option(None, "--root", help="Repository root."),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Machine-readable output."),
) -> None:
    """Agent-optimized repository context under a token budget."""
    command = "context"
    workspace = None
    try:
        workspace, repo, service = build_service(root, need_backend=True)
        result = service.context(query, token_budget=budget)
        data = result.to_dict()
        from .memory import MemoryStore, add_memories_to_context, capture_explicit_user_preferences

        memory_store = MemoryStore(service.root)
        captured = capture_explicit_user_preferences(
            memory_store, query, backend=service.backend, decision_config=service.config.decisions
        )
        add_memories_to_context(
            data, memory_store, query, budget, backend=service.backend,
            decision_config=service.config.decisions,
        )
        data["memories_learned"] = len(captured)
        payload = envelope(command=command, index=freshness_payload(service), data=data)
        if json_output:
            emit_json(payload)
        else:
            typer.echo(
                f"{len(data['entities'])} entities, {len(data['snippets'])} snippets, "
                f"{len(data['memories'])} memories, ~{data['token_estimate']} tokens"
            )
            for entity in data["entities"]:
                typer.echo(entity_line(_Simple(entity)))
    except PolderGraphError as exc:
        if json_output:
            emit_error(command, exc)
        else:
            typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code))
    finally:
        if workspace:
            workspace.close()


# --------------------------------------------------------------- agent memory


def _memory_backend_or_none():
    from .memory import memory_backend

    try:
        return memory_backend()
    except Exception:
        return None


def _memory_emit(command: str, data: dict[str, Any], json_output: bool, text: str) -> None:
    if json_output:
        emit_json(envelope(command=f"memory.{command}", data=data))
    else:
        typer.echo(text)


def _memory_guard(command: str, json_output: bool, call: Any) -> None:
    try:
        data, message = call()
        _memory_emit(command, data, json_output, message)
    except PolderGraphError as exc:
        if json_output:
            emit_error(f"memory.{command}", exc)
        else:
            typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code)) from exc


@memory_app.command("status")
def memory_status(
    root: Path | None = typer.Option(None, "--root", help="Current project root."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Show the shared memory store and current project scope."""
    from .memory import MemoryStore

    store = MemoryStore(root)

    def run():
        data = store.status()
        return data, (
            f"Memory store: {data['store']}\n"
            f"User memories: {data['user_memories']}  Project memories: {data['project_memories']}\n"
            f"Current project: {data['current_project']}"
        )

    _memory_guard("status", json_output, run)


@memory_app.command("add")
def memory_add(
    content: str = typer.Argument(..., help="A durable fact, preference, decision, or workflow."),
    scope: str = typer.Option("project", "--scope", help="Project-specific or user-wide memory."),
    kind: str = typer.Option(
        "fact", "--kind", help="fact, preference, decision, workflow, or reference."
    ),
    tag: list[str] = typer.Option([], "--tag", help="Searchable tag (repeatable)."),
    root: Path | None = typer.Option(
        None, "--root", help="Project root for project-scoped memory."
    ),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Save a memory in the central per-user store, shared across projects."""
    from .memory import MemoryStore

    store = MemoryStore(root)

    def run():
        data = store.add(
            content, scope=scope, kind=kind, tags=tag, backend=_memory_backend_or_none()
        )
        return data, f"Saved {data['scope']} memory {data['id']} ({data['kind']})."

    _memory_guard("add", json_output, run)


@memory_app.command("search")
def memory_search(
    query: str = typer.Argument(..., help="Question or terms to match against memories."),
    scope: str = typer.Option(
        "all", "--scope", help="Search project, user, or all visible memories."
    ),
    limit: int = typer.Option(10, "--limit", min=1, max=100, help="Maximum results."),
    lexical_only: bool = typer.Option(False, "--lexical-only", help="Skip local vector search."),
    root: Path | None = typer.Option(None, "--root", help="Current project root."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Find relevant project notes and user preferences with hybrid RAG."""
    from .memory import MemoryStore

    store = MemoryStore(root)

    def run():
        from .config.loader import load_config
        from .workspace import find_index_dir

        results = store.search(
            query,
            scope=scope,
            limit=limit,
            backend=None if lexical_only else _memory_backend_or_none(),
        )
        from .decision_runtime import decide_memory_relevance

        decision_config = load_config(find_index_dir(store.root)).config.decisions
        results, decision_info = decide_memory_relevance(query, results, decision_config)
        data = {"query": query, "scope": scope, "results": results, "store": str(store.database)}
        if decision_info is not None:
            data["memory_decision"] = decision_info
        lines = [
            f"{item['id']}  [{item['scope']} · {item['kind']} · {item['retrieval']} · {item['score']:.2f}]\n"
            f"  {item['content']}"
            for item in results
        ]
        return data, "\n".join(lines) if lines else "No matching memories."

    _memory_guard("search", json_output, run)


@memory_app.command("list")
def memory_list(
    scope: str = typer.Option(
        "all", "--scope", help="List project, user, or all visible memories."
    ),
    limit: int = typer.Option(50, "--limit", min=1, max=100, help="Maximum results."),
    root: Path | None = typer.Option(None, "--root", help="Current project root."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """List memories available to the current project."""
    from .memory import MemoryStore

    store = MemoryStore(root)

    def run():
        results = store.list(scope=scope, limit=limit)
        data = {"scope": scope, "results": results, "store": str(store.database)}
        lines = [
            f"{item['id']}  [{item['scope']} · {item['kind']}]\n  {item['content']}"
            for item in results
        ]
        return data, "\n".join(lines) if lines else "No memories saved yet."

    _memory_guard("list", json_output, run)


@memory_app.command("update")
def memory_update(
    memory_id: str = typer.Argument(..., help="Memory ID."),
    content: str | None = typer.Option(None, "--content", help="Replace the memory text."),
    kind: str | None = typer.Option(None, "--kind", help="Change the memory kind."),
    tag: list[str] | None = typer.Option(None, "--tag", help="Replace tags (repeatable)."),
    clear_tags: bool = typer.Option(False, "--clear-tags", help="Remove all tags."),
    root: Path | None = typer.Option(None, "--root", help="Current project root."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Update a memory visible to this project."""
    from .memory import MemoryStore

    store = MemoryStore(root)

    def run():
        if clear_tags and tag is not None:
            raise UsageError("Use --clear-tags or --tag, not both.")
        data = store.update(
            memory_id,
            content=content,
            kind=kind,
            tags=[] if clear_tags else tag,
            backend=_memory_backend_or_none(),
        )
        return data, f"Updated memory {memory_id}."

    _memory_guard("update", json_output, run)


@memory_app.command("forget")
def memory_forget(
    memory_id: str = typer.Argument(..., help="Memory ID."),
    root: Path | None = typer.Option(None, "--root", help="Current project root."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Permanently remove a project or user memory from the central store."""
    from .memory import MemoryStore

    store = MemoryStore(root)

    def run():
        data = store.forget(memory_id)
        return data, f"Forgot memory {memory_id}."

    _memory_guard("forget", json_output, run)


class _Simple:
    """Adapter so `entity_line` can render a context payload entry."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.qualified_name = payload.get("name")
        self.name = payload.get("name")
        self.kind = payload.get("kind")
        self.path = payload.get("path")
        self.start_line = payload.get("start_line")


# ---------------------------------------------------------------------- ui


@app.command()
def ui(
    host: Optional[str] = typer.Option(None, "--host", help="Bind address (default 127.0.0.1)."),
    port: Optional[int] = typer.Option(None, "--port", help="Port (default 7432)."),
    no_open: bool = typer.Option(False, "--no-open", help="Do not open a browser."),
    watch: bool = typer.Option(False, "--watch", help="Also run the file watcher."),
    path: Optional[Path] = typer.Argument(None, help="Repository root."),
) -> None:
    """Start the local dashboard."""
    from .api.server import serve

    command = "ui"
    workspace = None
    try:
        overrides: dict[str, Any] = {}
        if host:
            overrides.setdefault("ui", {})["host"] = host
        if port:
            overrides.setdefault("ui", {})["port"] = port
        if no_open:
            overrides.setdefault("ui", {})["open_browser"] = False
        workspace = open_workspace(path, cli_overrides=overrides or None)
        serve(workspace, watch=watch)
    except PolderGraphError as exc:
        typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        if exc.remediation:
            typer.secho(f"  -> {exc.remediation}", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(int(exc.exit_code))
    except KeyboardInterrupt:
        typer.echo("")
    finally:
        if workspace:
            workspace.close()


# --------------------------------------------------------------------- mcp


@app.command()
def mcp(
    path: Optional[Path] = typer.Argument(None, help="Repository root."),
) -> None:
    """Start the stdio MCP server."""
    from .mcp.server import run_server

    run_server(path)


# ------------------------------------------------------------- setup-agent


@app.command("setup")
def setup(
    agent: list[str] = typer.Option(
        [], "--agent", help="Set up one named agent integration (repeatable)."
    ),
    all_agents: bool = typer.Option(
        False, "--all", help="Set up every supported agent integration."
    ),
    skip_init: bool = typer.Option(
        False, "--skip-init", help="Skip running poldergraph init after setup."
    ),
) -> None:
    """Global setup wizard: configure embedding backend, agents, and user settings.

    Runs from any directory. Writes user-level config (~/.config/poldergraph/).
    Per-repo indexing is handled by 'poldergraph init'.
    """
    import sys as _sys

    import click

    from .agents.setup import AGENT_ADAPTERS, detect_installed_agents, setup_agent_guidance
    from .config.loader import user_config_path, write_config
    from .config.models import Config
    from .embedding.protocol import SUPPORTED_DIMENSIONS, select_device

    is_tty = _sys.stdin.isatty()
    supported_agents = [adapter.name for adapter in AGENT_ADAPTERS]
    cwd = Path.cwd().resolve()

    typer.echo()
    typer.secho("  ┌──────────────────────────────────────────────┐", fg=typer.colors.CYAN)
    typer.secho("  │        PolderGraph Setup Wizard               │", fg=typer.colors.CYAN)
    typer.secho("  └──────────────────────────────────────────────┘", fg=typer.colors.CYAN)
    typer.echo()

    # --- Step 1: Embedding backend ---
    typer.secho("  ── Step 1: Embedding Backend ──", fg=typer.colors.YELLOW)
    typer.echo("  PolderGraph uses EmbeddingGemma 2 for semantic search.")
    typer.echo("  The model is ~2 GB and downloads once to your local cache.")
    typer.echo()

    _VALID_BACKENDS = {"native", "ollama", "none"}
    _VALID_DEVICES = {"auto", "cpu", "cuda", "mps"}
    _VALID_DIMS = {"128", "256", "512", "768"}

    if not is_tty:
        backend_choice = "native"
        device_choice = "auto"
        dims_choice = 256
    else:
        backend_choice = typer.prompt(
            "  Embedding backend (native/ollama/none)", default="native"
        ).strip().lower()
        if backend_choice not in _VALID_BACKENDS:
            typer.secho(f"  Invalid choice '{backend_choice}', using 'native'", fg=typer.colors.RED)
            backend_choice = "native"
        device_choice = "auto"
        dims_choice = 256
        if backend_choice == "native":
            device_choice = typer.prompt(
                "  Compute device (auto/cpu/cuda/mps)", default="auto"
            ).strip().lower()
            if device_choice not in _VALID_DEVICES:
                device_choice = "auto"
            resolved = select_device(device_choice)
            typer.echo(f"  → Will use: {resolved}")
            dims_str = typer.prompt(
                "  Embedding dimensions (128/256/512/768)", default="256"
            ).strip()
            if dims_str in _VALID_DIMS:
                dims_choice = int(dims_str)
            else:
                typer.echo(f"  Invalid dimensions '{dims_str}', using 256")
                dims_choice = 256
        elif backend_choice == "ollama":
            typer.echo("  Make sure Ollama is running locally with an embedding model.")
            typer.echo("  Default: http://127.0.0.1:11434 / embeddinggemma")
        elif backend_choice == "none":
            typer.echo("  Semantic search disabled. Only lexical and structural retrieval available.")

    typer.echo()

    # --- Step 2: Agent detection ---
    typer.secho("  ── Step 2: Agent Integrations ──", fg=typer.colors.YELLOW)
    detected = detect_installed_agents(cwd)
    if detected:
        typer.echo(f"  Detected: {', '.join(detected)}")
    else:
        typer.echo("  No coding agents detected on this machine.")
    typer.echo(f"  Supported: {', '.join(supported_agents)}")

    selected_agents: list[str] = []
    if all_agents:
        selected_agents = supported_agents
    elif agent:
        invalid = [name for name in agent if name not in supported_agents]
        if invalid:
            raise typer.BadParameter(
                f"Unknown agent(s): {', '.join(invalid)}. Choose from: {', '.join(supported_agents)}"
            )
        selected_agents = list(dict.fromkeys(agent))
    elif is_tty:
        default = ",".join(detected) if detected else "none"
        answer = typer.prompt(
            "  Choose integrations (comma-separated, 'all', or 'none')",
            default=default,
        ).strip().lower()
        if answer in {"", "none"}:
            selected_agents = []
        elif answer == "all":
            selected_agents = supported_agents
        else:
            selected_agents = list(
                dict.fromkeys(part.strip() for part in answer.split(",") if part.strip())
            )
            invalid = [name for name in selected_agents if name not in supported_agents]
            if invalid:
                raise typer.BadParameter(f"Unknown agent(s): {', '.join(invalid)}.")
    typer.echo()

    # --- Step 3: Dashboard config ---
    typer.secho("  ── Step 3: Dashboard ──", fg=typer.colors.YELLOW)
    default_port = 7432
    if is_tty:
        port_answer = typer.prompt("  Dashboard port", default=str(default_port))
        try:
            default_port = int(port_answer)
        except ValueError:
            default_port = 7432
    typer.echo(f"  Dashboard will run at http://127.0.0.1:{default_port}")
    typer.echo()

    # --- Step 4: Write user-level config ---
    typer.secho("  ── Step 4: Writing Configuration ──", fg=typer.colors.YELLOW)
    config = Config()
    config.embedding.backend = backend_choice  # type: ignore[assignment]
    config.embedding.device = device_choice
    config.index.dimensions = dims_choice
    config.ui.port = default_port

    config_path = user_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    write_config(config, config_path.parent)
    typer.echo(f"  Config written to {config_path}")

    # --- Step 5: Agent instructions (in current directory if it's a repo) ---
    typer.echo()
    typer.secho("  ── Step 5: Agent Instructions ──", fg=typer.colors.YELLOW)
    result = setup_agent_guidance(cwd, config, targets=selected_agents)
    typer.echo(f"  Wrote: {', '.join(result['written']) or 'nothing'}")
    if result["skipped"]:
        typer.echo(f"  Skipped: {', '.join(result['skipped'])}")

    # --- Step 6: Index suggestion ---
    typer.echo()
    typer.secho("  ── Step 6: Next Steps ──", fg=typer.colors.YELLOW)
    if skip_init:
        typer.echo("  Skipped (--skip-init). Run 'poldergraph init' when ready.")
    elif is_tty:
        run_init = typer.confirm("  Run 'poldergraph init' in this directory now?", default=True)
        if run_init:
            typer.echo("  Initializing index...")
            typer.echo()
            init(target=cwd, force=False, no_agent=True, dimensions=dims_choice,
                 embedding_backend=backend_choice, media=True, json_output=False)
        else:
            typer.echo("  Skipped. Run 'poldergraph init' when ready.")
    else:
        typer.echo("  Non-interactive mode: run 'poldergraph init' separately.")

    # --- Done ---
    typer.echo()
    typer.secho("  ── Setup Complete ──", fg=typer.colors.GREEN)
    typer.echo(f"  Config:  {config_path}")
    typer.echo(f"  Agents:  {', '.join(selected_agents) or 'none (AGENTS.md only)'}")
    typer.echo(f"  Dashboard: http://127.0.0.1:{default_port}")
    typer.echo()
    typer.echo("  Next steps:")
    typer.echo("    poldergraph init       Index the current repository")
    typer.echo("    poldergraph ui         Open the dashboard")
    typer.echo("    poldergraph mcp        Start the MCP server")
    typer.echo("    poldergraph status     Check index health")
    typer.echo()


@app.command("setup-agent")
def setup_agent(
    target: Optional[Path] = typer.Argument(None, help="Repository root."),
    all_agents: bool = typer.Option(
        False, "--all", help="Update every supported agent integration."
    ),
    agent: list[str] = typer.Option([], "--agent", help="Target one agent adapter (repeatable)."),
    print_config: bool = typer.Option(
        False, "--print-mcp-config", help="Print MCP server configuration."
    ),
    hooks: bool = typer.Option(False, "--hooks", help="Explicitly allow installing git hooks."),
) -> None:
    """Install or update agent instructions and MCP configuration."""
    from .agents.setup import setup_agent_guidance

    root = (target or Path.cwd()).resolve()
    try:
        workspace = open_workspace(root)
        config = workspace.config
    except PolderGraphError:
        config = Config()

    if print_config:
        from .agents.setup import mcp_config_snippet

        typer.echo(mcp_config_snippet(root))
        return

    result = setup_agent_guidance(
        root, config, all_agents=all_agents, targets=list(agent) or None, hooks=hooks
    )
    typer.echo(f"Wrote: {', '.join(result['written']) or 'nothing'}")
    if result["skipped"]:
        typer.echo(f"Skipped: {', '.join(result['skipped'])}")


# ------------------------------------------------------------------ doctor


@app.command()
def doctor(
    path: Optional[Path] = typer.Argument(None, help="Repository root."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
    fix: bool = typer.Option(False, "--fix", help="Attempt to repair recoverable problems."),
) -> None:
    """Verify index integrity, schema, backend and vector health."""
    command = "doctor"
    workspace = None
    try:
        from .storage.integrity import run_doctor
        from .storage.sqlite import database_size_bytes

        workspace, repo, _ = build_service(path, need_backend=False)
        report = run_doctor(repo, dimensions=workspace.config.index.dimensions)
        report.add(
            "vector_backend",
            True,
            f"sqlite-vec {database_size_bytes(workspace.index_dir)} index bytes",
        )
        data = report.to_dict()
        payload = envelope(
            command=command,
            index={"fresh": True},
            data=data,
            warnings=[f"{c.name}: {c.detail}" for c in report.warnings],
        )
        if json_output:
            emit_json(payload)
        else:
            for check in data["checks"]:
                mark = (
                    "ok  "
                    if check["ok"]
                    else ("WARN" if check["severity"] == "warning" else "FAIL")
                )
                color = (
                    typer.colors.GREEN
                    if check["ok"]
                    else (
                        typer.colors.YELLOW if check["severity"] == "warning" else typer.colors.RED
                    )
                )
                typer.secho(f"{mark}  {check['name']}  {check['detail']}", fg=color)
            typer.echo("")
            typer.echo("healthy" if data["ok"] else "problems detected")
        if not data["ok"]:
            raise typer.Exit(int(ExitCode.CORRUPT))
    except PolderGraphError as exc:
        if json_output:
            emit_error(command, exc)
        else:
            typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code))
    finally:
        if workspace:
            workspace.close()


# ------------------------------------------------------------------ rebuild


@app.command()
def rebuild(
    path: Optional[Path] = typer.Argument(None, help="Repository root."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Rebuild the index in a replacement database and swap it atomically."""
    command = "rebuild"
    root = (path or Path.cwd()).resolve()
    try:
        from .rebuild import rebuild_index

        result = rebuild_index(root)
        payload = envelope(command=command, data=result)
        if json_output:
            emit_json(payload)
        else:
            typer.echo(
                f"Rebuilt {result['root']}: {result['files_indexed']} files, "
                f"{result['entities_written']} entities, {result['edges_written']} edges"
            )
    except PolderGraphError as exc:
        if json_output:
            emit_error(command, exc)
        else:
            typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code))


# ----------------------------------------------------------------- upgrade


@app.command()
def upgrade(
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
    check_only: bool = typer.Option(False, "--check", help="Only check for updates, do not install."),
    pre: bool = typer.Option(False, "--pre", help="Include pre-release versions."),
) -> None:
    """Check for and install the latest PolderGraph release."""
    import subprocess

    command = "upgrade"
    try:
        from urllib.request import Request, urlopen

        api = "https://api.github.com/repos/PolderLabs/PolderGraph/releases/latest"
        req = Request(api, headers={"Accept": "application/vnd.github+json"})
        try:
            with urlopen(req, timeout=15) as resp:
                release = json.loads(resp.read().decode())
        except Exception as exc:
            raise PolderGraphError(
                f"Cannot check for updates: {exc}",
                code="BACKEND_UNAVAILABLE",
                remediation="Check your internet connection and try again.",
            ) from exc

        latest = release.get("tag_name", "").lstrip("v")
        current = __version__

        def _parse(v: str) -> tuple[int, ...]:
            return tuple(int(x) for x in v.split(".") if x.isdigit())

        update_available = _parse(latest) > _parse(current) if latest else False
        prerelease = release.get("prerelease", False)

        payload: dict[str, Any] = {
            "current": current,
            "latest": latest,
            "update_available": update_available,
            "prerelease": prerelease,
            "release_url": release.get("html_url", ""),
            "published_at": release.get("published_at", ""),
        }

        if json_output:
            emit_json(envelope(command=command, data=payload))
        else:
            typer.echo(f"Current version: {current}")
            typer.echo(f"Latest version:  {latest}" + (" (pre-release)" if prerelease else ""))
            if update_available:
                typer.secho(f"  Update available: v{current} → v{latest}", fg=typer.colors.GREEN)
            else:
                typer.secho("  Already up to date.", fg=typer.colors.GREEN)

        if not update_available or check_only:
            if json_output:
                pass
            return

        if json_output:
            pass
        else:
            typer.echo(f"\nInstalling PolderGraph {latest}...")

        # Determine the install source. Always use the git source with [all]
        # extras — wheel URLs don't support extras syntax with uv tool install.
        source = f"poldergraph[all] @ git+https://github.com/PolderLabs/PolderGraph.git@v{latest}"

        uv_cmd = ["uv", "tool", "install", "--force", "--upgrade", source]
        result = subprocess.run(uv_cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            if json_output:
                payload["installed"] = True
                payload["source"] = source
                emit_json(envelope(command=command, data=payload))
            else:
                typer.secho(f"  ✓ Installed v{latest}", fg=typer.colors.GREEN)
                typer.echo("  Restart your shell if the poldergraph command is not on PATH.")
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or "uv install failed"
            if json_output:
                payload["installed"] = False
                payload["error"] = error_msg
                emit_json(envelope(command=command, data=payload))
            else:
                typer.secho(f"  ✗ Install failed: {error_msg}", fg=typer.colors.RED)
            raise typer.Exit(1)

    except PolderGraphError as exc:
        if json_output:
            emit_error(command, exc)
        else:
            typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code))


# ------------------------------------------------------------------- config


config_app = typer.Typer(help="Inspect and modify configuration.")
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show(
    path: Optional[Path] = typer.Argument(None, help="Repository root."),
    effective: bool = typer.Option(False, "--effective", help="Show merged values and origins."),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Print configuration values."""
    command = "config show"
    workspace = None
    try:
        from .config.loader import load_config
        from .workspace import find_index_dir

        index_dir = (find_index_dir(path) if path else find_index_dir()) or (
            (path or Path.cwd()).resolve() / ".poldergraph"
        )
        loaded = load_config(index_dir)
        data = {
            "config": loaded.effective(),
            "origins": {key: loaded.origin_of(key) for key in loaded.effective().get("index", {})},
            "workspace_config": str(loaded.workspace_config_path)
            if loaded.workspace_config_path
            else None,
            "user_config": str(loaded.user_config_path) if loaded.user_config_path else None,
        }
        payload = envelope(command=command, data=data)
        if json_output:
            emit_json(payload)
        else:
            typer.echo(json.dumps(data["config"], indent=2))
            if effective:
                typer.echo("")
                typer.echo("origins")
                for key, origin in sorted(data["origins"].items()):
                    typer.echo(f"  {key:<28} {origin}")
    except PolderGraphError as exc:
        if json_output:
            emit_error(command, exc)
        else:
            typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code))
    finally:
        if workspace:
            workspace.close()


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Dotted key, e.g. index.dimensions."),
    value: str = typer.Argument(..., help="New value."),
    path: Optional[Path] = typer.Argument(None, help="Repository root."),
) -> None:
    """Set one configuration value in the workspace config."""
    command = "config set"
    try:
        from .config.loader import load_config, write_config
        from .workspace import find_index_dir

        index_dir = find_index_dir(path) or (path or Path.cwd()).resolve() / ".poldergraph"
        index_dir.mkdir(parents=True, exist_ok=True)
        loaded = load_config(index_dir)
        config = loaded.config
        section, _, field = key.partition(".")
        if not field:
            raise UsageError(f"Key must be dotted, e.g. index.dimensions (got '{key}').")
        target = getattr(config, section, None)
        if target is None:
            raise UsageError(f"Unknown config section '{section}'.")
        if not hasattr(target, field):
            raise UsageError(f"Unknown config key '{key}'.")
        current = getattr(target, field)
        try:
            coerced: Any = value
            if isinstance(current, bool):
                coerced = value.lower() in {"1", "true", "yes", "on"}
            elif isinstance(current, int):
                coerced = int(value)
            elif isinstance(current, float):
                coerced = float(value)
        except ValueError:
            raise UsageError(f"Cannot parse '{value}' for {key}.") from None
        setattr(target, field, coerced)
        config = config.model_validate(config.model_dump())
        write_config(config, index_dir)
        typer.echo(f"{key} = {getattr(target, field)}")
    except PolderGraphError as exc:
        typer.secho(f"error: {exc.message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(int(exc.exit_code))


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    main()
