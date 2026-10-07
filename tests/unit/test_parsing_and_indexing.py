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