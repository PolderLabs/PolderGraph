"""Unit tests for stable identity, config precedence and path safety."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from poldergraph.config.loader import env_overrides, load_config, write_config
from poldergraph.config.models import Config
from poldergraph.discovery.scanner import safe_join
from poldergraph.models.edge import Edge, EdgeType, Provenance
from poldergraph.models.entity import Entity, stable_id
from poldergraph.storage.sqlite import migrate
from poldergraph.storage.vectors import BruteForceStore, SQLiteVecStore, VectorRecord, l2_normalize


class TestStableIdentity:
    def test_same_inputs_give_same_id(self):
        kwargs = dict(root_id="r1", kind="function", language="python", path="src/a.py", qualified_name="A.f")
        assert stable_id(**kwargs) == stable_id(**kwargs)

    def test_line_numbers_are_not_part_of_identity(self):
        base = dict(root_id="r1", kind="function", language="python", path="src/a.py", qualified_name="A.f")
        first = stable_id(**base)
        # Moving a definition within its file must not change its ID.
        entity = Entity(id=first, root_id="r1", kind="function", name="f", **{
            k: v for k, v in base.items() if k not in {"root_id", "kind"}
        }, start_line=5)
        entity.start_line = 900
        assert stable_id(**base) == first
        assert entity.id == first

    def test_path_normalization(self):
        a = stable_id(root_id="r", kind="file", language=None, path="./src/a.py", qualified_name="a")
        b = stable_id(root_id="r", kind="file", language=None, path="src/a.py", qualified_name="a")
        assert a == b

    def test_different_roots_differ(self):
        kwargs = dict(kind="function", language="python", path="src/a.py", qualified_name="A.f")
        assert stable_id(root_id="r1", **kwargs) != stable_id(root_id="r2", **kwargs)

    def test_overloads_are_distinguished(self):
        kwargs = dict(root_id="r", kind="method", language="python", path="a.py", qualified_name="A.f")
        assert stable_id(**kwargs, discriminator="100") != stable_id(**kwargs, discriminator="200")


class TestProvenance:
    def test_extracted_has_full_confidence(self):
        edge = Edge(source_id="a", target_id="b", type=EdgeType.CALLS, provenance=Provenance.EXTRACTED)
        assert edge.confidence == 1.0
        assert edge.is_structural
        assert not edge.is_semantic

    def test_semantic_edge_is_not_structural(self):
        edge = Edge(
            source_id="a",
            target_id="b",
            type="semantically_related",
            provenance=Provenance.SEMANTIC,
        )
        assert edge.is_semantic
        assert not edge.is_structural

    def test_edge_roundtrip(self):
        edge = Edge(source_id="a", target_id="b", type=EdgeType.CALLS)
        assert Edge.from_row(edge.to_row()).id == edge.id


class TestConfigPrecedence:
    def test_defaults(self):
        config = load_config(Path("/nonexistent"), environ={}).config
        assert config.index.dimensions == 256
        assert config.embedding.model == "google/embeddinggemma-2"
        assert config.ui.host == "127.0.0.1"

    def test_env_beats_defaults(self):
        loaded = load_config(Path("/nonexistent"), environ={"POLDERGRAPH_INDEX__DIMENSIONS": "512"})
        assert loaded.config.index.dimensions == 512
        assert loaded.origin_of("index.dimensions") == "env"

    def test_cli_beats_env(self):
        loaded = load_config(
            Path("/nonexistent"),
            environ={"POLDERGRAPH_INDEX__DIMENSIONS": "512"},
            cli_overrides={"index": {"dimensions": 128}},
        )
        assert loaded.config.index.dimensions == 128
        assert loaded.origin_of("index.dimensions") == "cli"

    def test_invalid_dimensions_rejected(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Config.model_validate({"index": {"dimensions": 999}})

    def test_toml_roundtrip(self, tmp_path: Path):
        original = Config()
        write_config(original, tmp_path)
        loaded = load_config(tmp_path, environ={})
        assert loaded.config.index.dimensions == original.index.dimensions
        assert loaded.config.retrieval.weights == original.retrieval.weights
        assert loaded.config.ui.port == original.ui.port
        assert loaded.config.decisions.provider == "disabled"
        assert loaded.config.decisions.confidence_threshold == 0.9

    def test_typed_decision_config_uses_nested_environment_overrides(self):
        loaded = load_config(
            environ={
                "POLDERGRAPH_DECISIONS__PROVIDER": "typesafe",
                "POLDERGRAPH_DECISIONS__CONFIDENCE_THRESHOLD": "0.96",
            },
            user_path=Path("/path/that/does/not/exist"),
        )
        assert loaded.config.decisions.provider == "typesafe"
        assert loaded.config.decisions.confidence_threshold == 0.96
        assert loaded.origin_of("decisions.provider") == "env"

    def test_env_var_nesting(self):
        assert env_overrides({"POLDERGRAPH_EMBEDDING__DEVICE": "cuda"}) == {
            "embedding": {"device": "cuda"}
        }


class TestPathSafety:
    def test_allows_inside_root(self, tmp_path: Path):
        assert safe_join(tmp_path, "src/a.py") == tmp_path / "src" / "a.py"

    @pytest.mark.parametrize(
        "bad",
        ["../etc/passwd", "/etc/passwd", "src/../../etc/passwd", "", "a\x00b"],
    )
    def test_blocks_traversal(self, tmp_path: Path, bad: str):
        assert safe_join(tmp_path, bad) is None

    def test_blocks_symlink_escape(self, tmp_path: Path):
        outside = tmp_path.parent / "outside.txt"
        outside.write_text("secret")
        link = tmp_path / "link.txt"
        link.symlink_to(outside)
        assert safe_join(tmp_path, "link.txt") is None


class TestVectorMath:
    def test_truncation_renormalizes(self):
        from poldergraph.embedding.protocol import truncate_and_normalize

        for dimension in (128, 256, 512, 768):
            vector = truncate_and_normalize([1.0] * 768, dimension)
            assert len(vector) == dimension
            assert math.isclose(math.sqrt(sum(v * v for v in vector)), 1.0, abs_tol=1e-6)

    def test_normalize_leaves_zero_vector(self):
        assert l2_normalize([0.0, 0.0]) == [0.0, 0.0]


class TestCommunities:
    def test_leiden_returns_entity_ids_not_indices(self):
        """Leiden addresses vertices by integer index; members must map back."""
        from poldergraph.config.models import Config
        from poldergraph.graph.communities import detect_communities
        from poldergraph.storage.repository import Repository
        from poldergraph.storage.sqlite import initialize, writer_transaction
        from poldergraph.models.edge import Edge, EdgeType

        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            con = initialize(Path(tmp) / "index.sqlite3")
            repo = Repository(con)
            ids = [f"file:e{i}" for i in range(6)]
            from poldergraph.models.entity import Entity

            with writer_transaction(con):
                repo.upsert_entities(
                    [
                        Entity(id=entity_id, root_id="r", kind="function", name=entity_id)
                        for entity_id in ids
                    ]
                )
                repo.upsert_edges(
                    [
                        Edge(source_id=a, target_id=b, type=EdgeType.CALLS)
                        for a, b in zip(ids, ids[1:], strict=False)
                    ]
                )

            result = detect_communities(repo, Config(), mode="structural", root_id="r")
            members = [m for group in result.memberships.values() for m in group]
            assert members, "expected at least one community"
            # Every member must be a real entity ID, never a bare integer.
            for member in members:
                assert member in set(ids), f"community member {member!r} is not an entity ID"
            con.close()


class TestVectorBackends:
    @staticmethod
    def _record(entity_id: str, vector: list[float]) -> VectorRecord:
        return VectorRecord(
            embedding_id=f"emb-{entity_id}",
            entity_id=entity_id,
            vector=vector,
            dimensions=4,
            model_id="m",
            model_revision="r",
            task_type="document",
            input_hash="h",
        )

    def test_backends_agree_on_cosine(self, tmp_path: Path):
        from poldergraph.storage.sqlite import initialize

        con = initialize(tmp_path / "index.sqlite3")
        records = [
            self._record("a", [1.0, 0.0, 0.0, 0.0]),
            self._record("b", [0.9, 0.1, 0.0, 0.0]),
        ]
        vec = SQLiteVecStore(con, dimensions=4, model_id="m")
        bf = BruteForceStore(con, dimensions=4, model_id="m")
        if not vec.available():
            pytest.skip("sqlite-vec unavailable")
        vec.upsert(records)
        bf.upsert(records)

        query = [1.0, 0.0, 0.0, 0.0]
        from_vec = [(h.entity_id, round(h.similarity, 6)) for h in vec.search(query, top_k=2)]
        from_bf = [(h.entity_id, round(h.similarity, 6)) for h in bf.search(query, top_k=2)]
        assert from_vec == from_bf
        expected = 0.9 / math.sqrt(0.82)
        assert abs(from_vec[1][1] - expected) < 1e-4
        con.close()

    def test_migration_is_idempotent(self, tmp_path: Path):
        from poldergraph.storage.sqlite import connect

        con = connect(tmp_path / "index.sqlite3")
        assert migrate(con) == migrate(con)
        con.close()
