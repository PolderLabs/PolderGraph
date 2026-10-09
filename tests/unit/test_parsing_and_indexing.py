"""Parser fixture tests and indexing behaviour tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from parser_samples import SAMPLES

from poldergraph.parsing.engine import ParseEngine


@pytest.fixture(scope="module")
def engine() -> ParseEngine:
    return ParseEngine()


class TestLanguageAdapters:
    @pytest.mark.parametrize("language", sorted(SAMPLES))
    def test_adapter_produces_symbols(self, engine: ParseEngine, language: str):
        """A supported language must never silently index nothing."""
        path, source = SAMPLES[language]
        result = engine.parse(source, language, path)
        assert result.symbols, f"{language} produced no symbols"

    @pytest.mark.parametrize("language", sorted(SAMPLES))
    def test_symbols_have_usable_identity(self, engine: ParseEngine, language: str):
        path, source = SAMPLES[language]
        result = engine.parse(source, language, path)
        for symbol in result.symbols:
            assert symbol.name
            assert symbol.qualified_name
            # A declarator blob leaked into the name would poison every ID.
            assert "(" not in symbol.name, f"{language}: bad name {symbol.name!r}"
            assert "::" not in symbol.name, f"{language}: bad name {symbol.name!r}"
            assert symbol.end_line >= symbol.start_line

    @pytest.mark.parametrize("language", sorted(SAMPLES))
    def test_no_duplicate_qualified_names(self, engine: ParseEngine, language: str):
        path, source = SAMPLES[language]
        names = [s.qualified_name for s in engine.parse(source, language, path).symbols]
        assert len(names) == len(set(names)), f"{language} produced duplicate symbols"

    @pytest.mark.parametrize("language", sorted(SAMPLES))
    def test_invalid_syntax_does_not_raise(self, engine: ParseEngine, language: str):
        """Half-written editor buffers must still be indexable."""
        path, source = SAMPLES[language]
        truncated = source[: len(source) // 2]
        result = engine.parse(truncated, language, path)
        assert isinstance(result.symbols, list)


class TestStoredLineNumbers:
    """Stored spans must be the lines an editor shows.

    Tree-sitter counts lines from zero. Adapters copy those coordinates
    straight into the model, so every stored span was one line short — a defect
    that survives spot-checking, because a tool that reads line N and an editor
    that shows line N both land on *some* real text.
    """

    @pytest.mark.parametrize("language", sorted(SAMPLES))
    def test_symbol_lines_are_one_based(self, engine: ParseEngine, language: str):
        path, source = SAMPLES[language]
        result = engine.parse(source, language, path)
        assert result.symbols
        for symbol in result.symbols:
            assert symbol.start_line >= 1, (
                f"{language}: {symbol.qualified_name} has start_line "
                f"{symbol.start_line}; stored lines are 1-based"
            )

    @pytest.mark.parametrize("language", sorted(SAMPLES))
    def test_declaration_line_contains_its_name(self, engine: ParseEngine, language: str):
        """The stored line must actually be where the declaration sits.

        Indexing with 0-based lines still lands on real text, just the line
        above it, so comparing the two *numbers* is the only check that
        catches this: the line named by `start_line` must contain the symbol.
        """
        path, source = SAMPLES[language]
        result = engine.parse(source, language, path)
        lines = source.decode("utf-8", "replace").splitlines()
        checked = 0
        for symbol in result.symbols:
            index = symbol.start_line - 1
            if not (0 <= index < len(lines)) or symbol.name not in lines[index]:
                continue
            checked += 1
        assert checked, f"{language}: no symbol line could be cross-checked"

    def test_first_symbol_starts_on_line_one_when_it_is_first(self, engine: ParseEngine):
        source = b"def first():\n    pass\n\n\ndef second():\n    pass\n"
        result = engine.parse(source, "python", "m.py")
        by_name = {s.name: s for s in result.symbols}
        assert by_name["first"].start_line == 1
        assert by_name["second"].start_line == 5

    def test_reference_lines_are_one_based(self, engine: ParseEngine):
        source = b"import os\n\n\ndef run():\n    os.getcwd()\n"
        result = engine.parse(source, "python", "m.py")
        references = [r for r in result.references if r.location.line is not None]
        for reference in references:
            assert reference.location.line >= 1

    def test_markdown_heading_lines_are_one_based(self, engine: ParseEngine):
        source = b"# Title\n\nbody\n\n## Section\n\nmore\n"
        result = engine.parse(source, "markdown", "doc.md")
        sections = {s.name: s for s in result.symbols}
        assert sections["Title"].start_line == 1
        assert sections["Section"].start_line == 5


class TestResolverLanguageScoping:
    """An unresolved name must never bind across languages.

    Binding a JavaScript `headers.delete()` to a Python `def delete(...)`
    produces an edge that looks entirely plausible and is entirely false.
    """

    def _resolver(self):
        from poldergraph.parsing.resolver import FileIndex, Resolver

        resolver = Resolver()
        py = FileIndex(root_id="r", path="scripts/tool.py", language="python")
        py.symbols["delete"] = "py-delete"
        py.by_name["delete"] = ["py-delete"]
        js = FileIndex(root_id="r", path="worker.js", language="javascript")
        # Both sides deliberately declare `delete`. The only thing that can
        # stop the JavaScript file binding to the Python function is the
        # language guard, so a missing same-named symbol here would make the
        # test pass for the wrong reason.
        js.symbols["delete"] = "js-delete"
        js.by_name["delete"] = ["js-delete"]
        for file in (py, js):
            resolver.register_file(file)
        return resolver, py, js

    def test_python_symbol_does_not_resolve_from_javascript(self):
        """A JS reference must never bind to the same-named Python function.

        Both files declare `delete`, so the guard is what keeps the Python
        definition out of the JavaScript candidate set; the JS local is a
        legitimate target.
        """
        resolver, _, js = self._resolver()
        candidates = resolver._candidates(js, "delete", None, "calls")
        assert "py-delete" not in candidates
        assert candidates == ["js-delete"]

    def test_same_language_name_still_resolves(self):
        """The language guard must not block legitimate local resolution."""
        resolver, py, _ = self._resolver()
        assert resolver._candidates(py, "delete", None, "calls") == ["py-delete"]

    def test_same_language_symbol_still_resolves(self):
        from poldergraph.parsing.resolver import FileIndex, Resolver

        resolver = Resolver()
        lib = FileIndex(root_id="r", path="lib/util.js", language="javascript")
        lib.symbols["helper"] = "js-helper"
        lib.by_name["helper"] = ["js-helper"]
        main = FileIndex(root_id="r", path="main.js", language="javascript")
        resolver.register_file(lib)
        resolver.register_file(main)
        assert resolver._candidates(main, "helper", None, "calls") == ["js-helper"]

    def test_typescript_may_bind_to_javascript(self):
        from poldergraph.parsing.resolver import FileIndex, Resolver

        resolver = Resolver()
        lib = FileIndex(root_id="r", path="lib/util.js", language="javascript")
        lib.symbols["helper"] = "js-helper"
        lib.by_name["helper"] = ["js-helper"]
        app = FileIndex(root_id="r", path="src/app.ts", language="typescript")
        resolver.register_file(lib)
        resolver.register_file(app)
        resolver.index_module_path("lib/util.js", "lib/util.js")
        app.import_aliases["util"] = "lib/util.js"
        assert resolver._candidates(app, "helper", "util", "calls") == ["js-helper"]

    def test_unknown_language_is_not_a_match(self):
        from poldergraph.parsing.resolver import _same_language

        assert _same_language(None, "python") is False
        assert _same_language("python", None) is False
        assert _same_language(None, None) is True


class TestPythonAdapter:
    def test_docstrings_are_captured(self, engine: ParseEngine):
        path, source = SAMPLES["python"]
        result = engine.parse(source, language="python", path=path)
        by_name = {s.qualified_name: s for s in result.symbols}
        assert "Validate one session token." in (by_name["AuthService.validate_session"].docstring or "")

    def test_inheritance_is_extracted(self, engine: ParseEngine):
        path, source = SAMPLES["python"]
        result = engine.parse(source, "python", path)
        inherits = {r.name for r in result.references if r.edge_type == "inherits"}
        assert "BaseThing" in inherits

    def test_relative_import_module_is_not_doubled(self, engine: ParseEngine):
        result = engine.parse(b"from typing import List\n", "python", "a.py")
        modules = [i.module for i in result.imports]
        assert "typing" in modules
        assert "typing.typing" not in modules

    def test_aliased_import_keeps_local_name(self, engine: ParseEngine):
        result = engine.parse(b"from mylib import Helper as H\n", "python", "a.py")
        assert result.imports[0].aliases == {"H": "Helper"}


class TestJavaScriptReferences:
    """A value read but never called is still a dependency.

    Capturing only call targets meant `pathname.slice(MEDIA_PREFIX.length)`
    produced no edge at all, so reverse dependency analysis reported that
    nothing depended on `MEDIA_PREFIX`.
    """

    def test_bare_identifier_read_is_recorded(self, engine: ParseEngine):
        source = b"const PREFIX = '/media/';\nfunction key(p) {\n  return p.slice(PREFIX.length);\n}\n"
        result = engine.parse(source, "javascript", "w.js")
        reads = [r for r in result.references if r.name == "PREFIX"]
        assert reads, "reading a constant must produce a reference"
        # Line 3 is `return p.slice(PREFIX.length);`.
        assert reads[0].location.line == 3

    def test_declaration_is_not_a_reference(self, engine: ParseEngine):
        source = b"const PREFIX = '/media/';\n"
        result = engine.parse(source, "javascript", "w.js")
        assert not [r for r in result.references if r.name == "PREFIX"]

    def test_property_key_is_not_a_reference(self, engine: ParseEngine):
        source = b"function f(o) {\n  return { key: 1 };\n}\n"
        result = engine.parse(source, "javascript", "w.js")
        assert not [r for r in result.references if r.name == "key"]

    def test_member_property_is_not_a_reference(self, engine: ParseEngine):
        source = b"function f(o) {\n  return o.deep.prop;\n}\n"
        result = engine.parse(source, "javascript", "w.js")
        assert not [r for r in result.references if r.name == "prop"]

    def test_template_substitution_is_recorded(self, engine: ParseEngine):
        source = b"function f() {\n  return `${MEDIA_PREFIX}x`;\n}\n"
        result = engine.parse(source, "javascript", "w.js")
        assert [r for r in result.references if r.name == "MEDIA_PREFIX"]


class TestIndexing:
    def test_entities_and_relations_are_created(self, indexed_workspace):
        from poldergraph.storage.repository import Repository

        repo = Repository(indexed_workspace.con)
        names = {
            row[0]
            for row in repo.con.execute("SELECT qualified_name FROM entities WHERE qualified_name IS NOT NULL")
        }
        assert "AuthService" in names
        assert "AuthService.validate_session" in names
        assert "Session" in names

    def test_cross_file_calls_resolve(self, indexed_workspace):
        from poldergraph.storage.repository import Repository

        repo = Repository(indexed_workspace.con)
        calls = repo.con.execute(
            "SELECT source_id, target_id FROM edges WHERE type='calls' AND provenance='resolved'"
        ).fetchall()
        assert calls, "expected at least one resolved cross-file call"

    def test_no_orphan_edges(self, indexed_workspace):
        from poldergraph.storage.repository import Repository

        repo = Repository(indexed_workspace.con)
        orphans = repo.con.execute(
            "SELECT COUNT(*) FROM edges e"
            " LEFT JOIN entities s ON s.id=e.source_id"
            " LEFT JOIN entities t ON t.id=e.target_id"
            " WHERE s.id IS NULL OR t.id IS NULL"
        ).fetchone()[0]
        assert orphans == 0

    def test_memberships_reference_real_entities(self, indexed_workspace):
        from poldergraph.storage.repository import Repository

        repo = Repository(indexed_workspace.con)
        known = {row[0] for row in repo.con.execute("SELECT id FROM entities")}
        members = [row[0] for row in repo.con.execute("SELECT entity_id FROM community_members")]
        assert members, "expected community memberships"
        for member in members:
            assert member in known, f"community member {member!r} is not an entity ID"

    def test_doctor_reports_healthy(self, indexed_workspace):
        from poldergraph.storage.integrity import run_doctor
        from poldergraph.storage.repository import Repository

        report = run_doctor(Repository(indexed_workspace.con), dimensions=256)
        assert report.ok, [check.name for check in report.failures]


class TestIncrementalUpdate:
    def test_embedding_space_change_forces_unchanged_files_to_reindex(self, indexed_workspace):
        from poldergraph.indexing.incremental import plan_update
        from poldergraph.indexing.pipeline import Indexer
        from poldergraph.storage.repository import Repository
        from poldergraph.storage.sqlite import set_meta

        repo = Repository(indexed_workspace.con)
        set_meta(repo.con, "embedding_space_id", "old-space")
        indexer = Indexer(indexed_workspace, backend=None)
        discovered = indexer.discover()
        plan = plan_update(
            repo, discovered, root_id=indexed_workspace.root_id(),
            embedding_space_id="new-space",
        )
        assert plan.embedding_space_changed
        assert len(plan.to_index) == len(discovered)
        assert not plan.unchanged

    def test_switching_embedding_spaces_rebuilds_and_preserves_vectors(self, sample_repo):
        from poldergraph.config.models import Config
        from poldergraph.embedding.protocol import ModelInfo
        from poldergraph.indexing.incremental import embedding_space_fingerprint, plan_update
        from poldergraph.indexing.pipeline import Indexer
        from poldergraph.storage.repository import Repository
        from poldergraph.storage.vectors import create_vector_store, get_entity_vector
        from poldergraph.workspace import create_index, open_workspace

        class FakeBackend:
            def __init__(self, model_id, vector):
                self._info = ModelInfo(
                    model_id=model_id, revision="revision-1", dimensions=256, backend="api"
                )
                self.vector = vector
                self.calls = 0

            def capabilities(self):
                return {"text"}

            def model_info(self):
                return self._info

            def embed_texts(self, items, *, task, dimensions, on_batch=None):
                self.calls += len(items)
                if on_batch:
                    on_batch(len(items), len(items))
                return [self.vector for _ in items]

        create_index(sample_repo, Config(embedding={"backend": "none"}))
        workspace = open_workspace(sample_repo)
        first = FakeBackend("api:first-model:provider-a", [1.0, *([0.0] * 255)])
        second = FakeBackend("api:second-model:provider-b", [0.0, 1.0, *([0.0] * 254)])
        try:
            indexer = Indexer(workspace, backend=first)
            indexer.ensure_root()
            files = indexer.discover()
            initial = indexer.run(
                files, embedding_space_id=embedding_space_fingerprint(first)
            )
            assert initial.embeddings_written > 0

            repo = Repository(workspace.con)
            second_plan = plan_update(
                repo, files, root_id=workspace.root_id(),
                embedding_space_id=embedding_space_fingerprint(second),
            )
            assert second_plan.embedding_space_changed
            assert len(second_plan.to_index) == len(files)
            changed = Indexer(workspace, backend=second).run(
                files,
                changed=second_plan.to_index,
                removed_paths=second_plan.removed,
                embedding_space_id=embedding_space_fingerprint(second),
            )
            assert changed.embeddings_written > 0
            entity_id = workspace.con.execute(
                "SELECT id FROM entities WHERE name='AuthService' LIMIT 1"
            ).fetchone()[0]
            first_store = create_vector_store(
                workspace.con, dimensions=256, model_id=first.model_info().model_id
            )
            second_store = create_vector_store(
                workspace.con, dimensions=256, model_id=second.model_info().model_id
            )
            assert get_entity_vector(first_store, entity_id) == pytest.approx(first.vector)
            assert get_entity_vector(second_store, entity_id) == pytest.approx(second.vector)

            first_plan = plan_update(
                repo, files, root_id=workspace.root_id(),
                embedding_space_id=embedding_space_fingerprint(first),
            )
            restored = Indexer(workspace, backend=first).run(
                files,
                changed=first_plan.to_index,
                removed_paths=first_plan.removed,
                embedding_space_id=embedding_space_fingerprint(first),
            )
            assert restored.embeddings_written == 0
            assert restored.embeddings_reused > 0
            assert get_entity_vector(first_store, entity_id) == pytest.approx(first.vector)

            # A changed representation invalidates only that entity's vectors
            # in the active space, rather than leaving duplicate stale hits.
            source = sample_repo / "pkg" / "auth.py"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "Validate session tokens.", "Validate API session tokens."
                ),
                encoding="utf-8",
            )
            first.vector = [0.0, 0.0, 1.0, *([0.0] * 253)]
            changed_files = indexer.discover()
            changed_plan = plan_update(
                repo, changed_files, root_id=workspace.root_id(),
                embedding_space_id=embedding_space_fingerprint(first),
            )
            changed_content = Indexer(workspace, backend=first).run(
                changed_files,
                changed=changed_plan.to_index,
                removed_paths=changed_plan.removed,
                embedding_space_id=embedding_space_fingerprint(first),
            )
            assert changed_content.embeddings_written > 0
            current_records = [
                record for record in repo.embedding_info(entity_id)
                if record["model_id"] == first.model_info().model_id
            ]
            assert len(current_records) == 1
            assert get_entity_vector(first_store, entity_id) == pytest.approx(first.vector)
        finally:
            workspace.close()

    def test_unchanged_files_are_skipped(self, indexed_workspace):
        from poldergraph.indexing.incremental import plan_update
        from poldergraph.indexing.pipeline import Indexer
        from poldergraph.storage.repository import Repository

        repo = Repository(indexed_workspace.con)
        indexer = Indexer(indexed_workspace, backend=None)
        plan = plan_update(repo, indexer.discover(), root_id=indexed_workspace.root_id())
        assert not plan.added and not plan.changed and not plan.removed

    def test_modified_file_is_detected(self, indexed_workspace):
        from poldergraph.indexing.incremental import plan_update
        from poldergraph.indexing.pipeline import Indexer
        from poldergraph.storage.repository import Repository

        target = indexed_workspace.root / "pkg" / "models.py"
        target.write_text(target.read_text() + "\n\ndef added():\n    return 1\n")

        repo = Repository(indexed_workspace.con)
        indexer = Indexer(indexed_workspace, backend=None)
        plan = plan_update(repo, indexer.discover(), root_id=indexed_workspace.root_id())
        assert [f.path for f in plan.changed] == ["pkg/models.py"]

    def test_deleted_file_is_removed_from_index(self, indexed_workspace):
        from poldergraph.indexing.pipeline import Indexer
        from poldergraph.storage.repository import Repository

        repo = Repository(indexed_workspace.con)
        (indexed_workspace.root / "pkg" / "models.py").unlink()

        indexer = Indexer(indexed_workspace, backend=None)
        discovered = indexer.discover()
        indexer.run(discovered, changed=[], removed_paths=["pkg/models.py"])

        remaining = repo.con.execute(
            "SELECT COUNT(*) FROM entities WHERE path='pkg/models.py'"
        ).fetchone()[0]
        assert remaining == 0
        orphans = repo.con.execute(
            "SELECT COUNT(*) FROM edges e"
            " LEFT JOIN entities s ON s.id=e.source_id"
            " LEFT JOIN entities t ON t.id=e.target_id"
            " WHERE s.id IS NULL OR t.id IS NULL"
        ).fetchone()[0]
        assert orphans == 0

    def test_reindex_replaces_stale_entities(self, indexed_workspace):
        """Re-indexing a file must not duplicate its entities."""
        from poldergraph.indexing.pipeline import Indexer
        from poldergraph.storage.repository import Repository

        repo = Repository(indexed_workspace.con)
        before = repo.count_entities(root_id=indexed_workspace.root_id())

        indexer = Indexer(indexed_workspace, backend=None)
        discovered = indexer.discover()
        indexer.run(discovered, changed=[f for f in discovered if f.path == "pkg/auth.py"])

        after = repo.count_entities(root_id=indexed_workspace.root_id())
        assert after == before

    def test_rename_removes_old_and_adds_new(self, indexed_workspace):
        from poldergraph.indexing.pipeline import Indexer
        from poldergraph.storage.repository import Repository

        repo = Repository(indexed_workspace.con)
        old = indexed_workspace.root / "pkg" / "models.py"
        new = indexed_workspace.root / "pkg" / "entities.py"
        old.rename(new)

        indexer = Indexer(indexed_workspace, backend=None)
        discovered = indexer.discover()
        indexer.run(discovered, changed=[f for f in discovered if f.path == "pkg/entities.py"],
                    removed_paths=["pkg/models.py"])

        assert repo.con.execute(
            "SELECT COUNT(*) FROM entities WHERE path='pkg/models.py'"
        ).fetchone()[0] == 0
        assert repo.con.execute(
            "SELECT COUNT(*) FROM entities WHERE path='pkg/entities.py'"
        ).fetchone()[0] > 0


class TestAgentInstructions:
    def test_block_is_idempotent(self, tmp_path: Path):
        from poldergraph.agents.setup import AGENTS_BLOCK, update_block

        first, changed = update_block("# My notes\n", AGENTS_BLOCK)
        assert changed
        second, changed_again = update_block(first, AGENTS_BLOCK)
        assert not changed_again
        assert second == first
        assert "# My notes" in second

    def test_existing_block_is_replaced_not_duplicated(self, tmp_path: Path):
        from poldergraph.agents.setup import AGENTS_BLOCK, update_block

        first, _ = update_block("", AGENTS_BLOCK)
        second, _ = update_block(first, AGENTS_BLOCK)
        assert second.count("<!-- poldergraph:start -->") == 1

    def test_user_content_is_preserved(self, tmp_path: Path):
        from poldergraph.agents.setup import AGENTS_BLOCK, update_block

        content = "# Title\n\nImportant user note.\n"
        updated, _ = update_block(content, AGENTS_BLOCK)
        assert "Important user note." in updated
