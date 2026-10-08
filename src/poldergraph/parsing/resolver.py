"""Cross-file symbol resolution.

Rules the resolver must honor:
- a unique target produces a `resolved` edge
- several plausible targets produce `ambiguous` candidates, never a guess
- no local target leaves an unresolved reference recorded for context
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models.edge import Edge, EdgeType, Provenance, SourceLocation

#: Edge types whose reference name should prefer a qualified match.
QUALIFIED_EDGE_TYPES = frozenset({EdgeType.IMPORTS})


@dataclass
class FileIndex:
    """Everything the resolver knows about one parsed file."""

    root_id: str
    path: str
    language: str | None
    #: qualified_name -> entity id
    symbols: dict[str, str] = field(default_factory=dict)
    #: bare name -> entity ids (may hold several for overloads/duplicates)
    by_name: dict[str, list[str]] = field(default_factory=dict)
    #: exported qualified names
    exports: set[str] = field(default_factory=set)
    #: import alias -> module path
    import_aliases: dict[str, str] = field(default_factory=dict)
    #: module path -> file path, filled from imports across the workspace
    module_paths: dict[str, str] = field(default_factory=dict)
    #: symbol index -> entity id, so references can attach to their owner
    symbol_ids: dict[int, str] = field(default_factory=dict)


@dataclass
class ResolvedReference:
    edge: Edge
    source_path: str
    candidates: list[str] = field(default_factory=list)


class Resolver:
    """Resolve references to entity IDs across a workspace."""

    def __init__(self) -> None:
        self.files: dict[str, FileIndex] = {}
        #: module path -> file path across every parsed file
        self._module_index: dict[str, str] = {}
        self._export_index: dict[str, list[tuple[str, str]]] = {}
        #: language -> the same index, so a name never binds across languages.
        #: A JavaScript `Headers.delete()` must not resolve to a Python
        #: `def delete(...)`: the edge would be syntactically plausible and
        #: semantically false, which is worse for a consumer than no edge.
        self._export_index_by_language: dict[str, dict[str, list[tuple[str, str]]]] = {}
        #: entity id -> the file that declares it, so a resolved target's file
        #: scope can be reported accurately instead of guessed from its id.
        self._entity_path: dict[str, str] = {}

    # ------------------------------------------------------------ indexing

    def register_file(self, index: FileIndex) -> None:
        self.files[index.path] = index
        for entity_id in index.symbol_ids.values():
            self._entity_path[entity_id] = index.path
        for entity_id in index.by_name.values():
            for one in entity_id:
                self._entity_path.setdefault(one, index.path)
        for qualified, entity_id in index.symbols.items():
            self._export_index.setdefault(qualified, []).append((index.path, entity_id))
            bucket = self._export_index_by_language.setdefault(
                index.language or "", {}
            )
            bucket.setdefault(qualified, []).append((index.path, entity_id))
        for module in index.module_paths:
            self._module_index.setdefault(module, index.path)

    def index_module_path(self, module: str, path: str) -> None:
        self._module_index.setdefault(module, path)

    def register_module_paths(self, index: FileIndex) -> None:
        """Map import module paths onto the files that declare them."""
        for import_record in index.imports_raw if hasattr(index, "imports_raw") else []:
            module = import_record.module
            if module and module not in self._module_index:
                self._module_index[module] = index.path

    # ----------------------------------------------------------- resolution

    def _resolver_label(self, source_path: str, target_id: str) -> str:
        """Name the resolution scope that actually produced an edge.

        Most references resolve inside the file that makes them. Labelling those
        ``cross_file`` overstated the resolution's scope and made consumers
        distrust edges that were perfectly local. The comparison is made
        against the declaring file of the target entity, not its id.
        """
        target_path = self._entity_path.get(target_id)
        if target_path is None:
            return "cross_file"
        return "same_file" if target_path == source_path else "cross_file"

    def resolve(self, index: FileIndex, reference: Any) -> ResolvedReference | None:
        """Resolve one reference, returning an edge plus any candidates."""
        name = reference.name
        qualifier = reference.qualifier
        # `0` is a valid symbol index, so the lookup must not treat it as unset.
        symbol_index = reference.source_symbol_index
        if symbol_index is None:
            return None
        source_id = index.symbol_ids.get(symbol_index)
        if source_id is None:
            return None

        location = SourceLocation(
            path=index.path,
            line=reference.location.line,
            col=reference.location.col,
        )
        candidates = self._candidates(index, name, qualifier, reference.edge_type)

        if len(candidates) == 1:
            target = candidates[0]
            if target == source_id:
                # A self-reference carries no graph information; drop it here
                # rather than storing an edge whose endpoints are identical.
                return None
            return ResolvedReference(
                edge=Edge(
                    source_id=source_id,
                    target_id=target,
                    type=reference.edge_type,
                    provenance=Provenance.RESOLVED,
                    resolver=self._resolver_label(index.path, target),
                    source_location=location,
                    metadata={"reference": name},
                ),
                source_path=index.path,
            )

        if len(candidates) > 1:
            # Several plausible targets: preserve the ambiguity instead of
            # choosing one arbitrarily.
            distinct = [c for c in candidates if c != source_id]
            if len(distinct) == 1:
                return ResolvedReference(
                    edge=Edge(
                        source_id=source_id,
                        target_id=distinct[0],
                        type=reference.edge_type,
                        provenance=Provenance.RESOLVED,
                        resolver=self._resolver_label(index.path, distinct[0]),
                        source_location=location,
                        metadata={"reference": name},
                    ),
                    source_path=index.path,
                )
            return ResolvedReference(
                edge=Edge(
                    source_id=source_id,
                    target_id=source_id,
                    type=reference.edge_type,
                    provenance=Provenance.AMBIGUOUS,
                    resolver="cross_file",
                    source_location=location,
                    metadata={"reference": name, "candidates": distinct[:8]},
                ),
                source_path=index.path,
                candidates=distinct[:8],
            )

        return ResolvedReference(
            edge=Edge(
                source_id=source_id,
                target_id=source_id,
                type=reference.edge_type,
                provenance=Provenance.EXTRACTED,
                resolver="local",
                source_location=location,
                metadata={"reference": name, "unresolved": True},
            ),
            source_path=index.path,
        )

    def _candidates(
        self, index: FileIndex, name: str, qualifier: str | None, edge_type: str
    ) -> list[str]:
        """Find plausible targets, preferring the narrowest match."""
        out: list[str] = []

        if qualifier:
            # `module.symbol` / `Class.method` shapes.
            qualified = f"{qualifier}.{name}"
            if qualified in index.symbols:
                out.append(index.symbols[qualified])

            if qualifier in index.import_aliases:
                module = index.import_aliases[qualifier]
                target_index = self._index_for_module(index.path, module)
                if target_index is not None and _same_language(
                    index.language, target_index.language
                ):
                    if name in target_index.by_name:
                        out.extend(target_index.by_name[name])
                    qualified_module = f"{module}.{name}"
                    if qualified_module in target_index.symbols:
                        out.append(target_index.symbols[qualified_module])
                    pkg_prefix = _module_prefix(target_index.path)
                    if pkg_prefix and f"{pkg_prefix}.{name}" in target_index.symbols:
                        out.append(target_index.symbols[f"{pkg_prefix}.{name}"])

            # Qualified name in the same file.
            for qualified_name, entity_id in index.symbols.items():
                if qualified_name.endswith(f".{qualified}.{name}") or qualified_name == qualified:
                    out.append(entity_id)
            if out:
                return _dedupe(out)

        # Same-file qualified name first.
        if name in index.symbols:
            out.append(index.symbols[name])
        elif "." in name:
            if name in index.symbols:
                out.append(index.symbols[name])
            else:
                leaf = name.rsplit(".", 1)[-1]
                if leaf in index.by_name:
                    out.extend(index.by_name[leaf])
        elif name in index.by_name:
            out.extend(index.by_name[name])

        if out:
            return _dedupe(out)

        # Imported names: resolve through the import binding into the module.
        module = index.import_aliases.get(name)
        if module:
            target_index = self._index_for_module(index.path, module)
            if target_index is not None and _same_language(
                index.language, target_index.language
            ):
                if name in target_index.by_name:
                    out.extend(target_index.by_name[name])
                else:
                    leaf = module.rsplit(".", 1)[-1]
                    if leaf in target_index.by_name:
                        out.extend(target_index.by_name[leaf])
                    pkg_prefix = _module_prefix(target_index.path)
                    if pkg_prefix and f"{pkg_prefix}.{name}" in target_index.symbols:
                        out.append(target_index.symbols[f"{pkg_prefix}.{name}"])
                if out:
                    return _dedupe(out)

        # A bare name may still refer to something this module imports wholesale.
        for module in set(index.import_aliases.values()):
            target_index = self._index_for_module(index.path, module)
            if target_index is None or not _same_language(index.language, target_index.language):
                continue
            if name in target_index.by_name:
                out.extend(target_index.by_name[name])

        if out:
            return _dedupe(out)

        # Workspace-wide unique match, restricted to this file's language. An
        # unmatched name must not bind to a same-named symbol in an unrelated
        # language, and the unscoped fallback below only admits dialects that
        # are genuinely interchangeable.
        matches = self._export_index_by_language.get(index.language or "", {}).get(name)
        if matches:
            out.extend(entity_id for _, entity_id in matches)
            return _dedupe(out)

        # Dialect companions (TypeScript importing JavaScript, a C header into
        # a C++ file) have no separate bucket of their own, so they are
        # admitted only through the same compatibility check.
        for path, entity_id in self._export_index.get(name, ()):
            other = self.files.get(path)
            if other is not None and _same_language(index.language, other.language):
                out.append(entity_id)

        return _dedupe(out)

    def _index_for_module(self, importer_path: str, module: str) -> FileIndex | None:
        """Resolve an import module to the file index that declares it.

        Handles absolute dotted modules, relative modules (`from . import x`,
        `from .models import y`) and direct file paths.
        """
        candidates: list[str] = []

        if module.startswith("."):
            # Relative import: resolve against the importer's directory.
            base_dir = importer_path.rsplit("/", 1)[0] if "/" in importer_path else ""
            stripped = module.lstrip(".")
            up = len(module) - len(stripped)
            parts = base_dir.split("/") if base_dir else []
            for _ in range(up - 1):
                if parts:
                    parts.pop()
            relative = ".".join(p for p in parts if p)
            target_module = f"{relative}.{stripped}" if relative else stripped
            candidates.extend(_module_candidates(importer_path, target_module))
        else:
            candidates.extend(_module_candidates(importer_path, module))
            direct = self._module_index.get(module)
            if direct:
                candidates.append(direct)

        for candidate in candidates:
            index = self.files.get(candidate)
            if index is not None:
                return index
            # A package `__init__` resolves to its directory module.
            if candidate.endswith("/__init__") or candidate.endswith("\\__init__"):
                index = self.files.get(candidate.rsplit("/", 1)[0])
                if index is not None:
                    return index
        mapped = self._module_index.get(module)
        if mapped:
            return self.files.get(mapped)
        return None


def _module_candidates(importer_path: str, module: str) -> list[str]:
    """Turn a dotted module name into candidate file paths.

    Language module layout does not always match the on-disk path, so several
    spellings are tried rather than assuming one mapping.
    """
    if not module:
        return []
    importer_dir = importer_path.rsplit("/", 1)[0] if "/" in importer_path else ""
    parts = module.split(".")
    out: list[str] = []

    relative = "/".join(parts)
    if importer_dir:
        out.append(f"{importer_dir}/{relative}.py")
        out.append(f"{importer_dir}/{relative}/__init__.py")
    out.append(f"{relative}.py")
    out.append(f"{relative}/__init__.py")
    for extension in (".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java"):
        out.append(f"{relative}{extension}")
        if importer_dir:
            out.append(f"{importer_dir}/{relative}{extension}")
    return out


def _module_prefix(path: str) -> str | None:
    """Dotted prefix for a file's declaring package, if it has one."""
    if path.endswith("/__init__.py") or path == "__init__.py":
        return path.rsplit("/", 1)[0].replace("/", ".") if "/" in path else None
    return None


def _same_language(source: str | None, target: str | None) -> bool:
    """Whether a resolved target may legitimately live in that other language.

    An unknown language on either side is *not* a match. Permissive handling of
    ``None`` would reopen the exact cross-language leak this guard exists to
    close, so an unclassified file binds only to another unclassified one.

    The TypeScript/JavaScript and C-family dialects legitimately call into each
    other (a ``.ts`` file imports the ``.js`` module it compiles to; a ``.h``
    header declares what a ``.c``/``.cpp`` file defines), so those pairs count
    as one language.
    """
    if source is None or target is None:
        return source is None and target is None
    if source == target:
        return True
    return frozenset((source, target)) in _SHARED_DIALECT_GROUPS


#: Dialect pairs that are genuinely interchangeable at call sites.
_SHARED_DIALECT_GROUPS: frozenset[frozenset[str]] = frozenset(
    {
        frozenset({"typescript", "javascript"}),
        frozenset({"tsx", "javascript"}),
        frozenset({"c", "cpp"}),
        frozenset({"c", "csharp"}),
        frozenset({"cpp", "csharp"}),
    }
)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out