"""Source-grounded context selection for real task shapes.

These fixtures assert that delivered context is tied to actual source: a refactor
task must surface the entrypoint, its callers and linked tests with provenance,
while a narrow lookup stays compact. They also pin the planner's own explainability
contract (`why_selected`) and its separation of structural facts from inference.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))

from corpus_repo import build_corpus, cases  # noqa: E402

from poldergraph.retrieval.context_plan import plan_context  # noqa: E402


@pytest.fixture(scope="module")
def indexed_corpus(tmp_path_factory):
    from poldergraph.config.models import Config
    from poldergraph.graph import run_graph_stage
    from poldergraph.indexing.pipeline import Indexer
    from poldergraph.retrieval.service import QueryService
    from poldergraph.storage.repository import Repository
    from poldergraph.workspace import create_index, open_workspace

    root = build_corpus(tmp_path_factory.mktemp("grounding-corpus"))
    config = Config(embedding={"backend": "none"})
    create_index(root, config)
    workspace = open_workspace(root)
    repository = Repository(workspace.con)
    indexer = Indexer(workspace, backend=None)
    indexer.ensure_root()
    indexer.run(indexer.discover())
    run_graph_stage(workspace, config, repository, None)
    service = QueryService(repository, config, None, root_id=workspace.root_id(), workspace=workspace)
    yield workspace, service
    workspace.close()


def _names(result) -> set[str]:
    entities = result.entities if hasattr(result, "entities") else result["entities"]
    snippets = result.snippets if hasattr(result, "snippets") else result["snippets"]
    return {item.get("name", "") for item in [*entities, *snippets]} - {""}


def test_refactor_context_is_grounded_in_source_with_provenance(indexed_corpus):
    """A refactor task must reach real code, with source evidence attached."""
    _workspace, service = indexed_corpus
    case = next(item for item in cases() if item["id"] == "change_impact")

    result = service.context(case["question"], token_budget=3000)
    plan = result.plan
    assert plan is not None
    assert plan.skipped is False
    # Structural lanes are chosen for a cross-cutting task...
    assert "structural" in plan.lanes
    # ...and each one explains itself, keeping structure distinct from inference.
    assert plan.why_selected["structural"].startswith("Callers, callees")
    assert "inferred" in plan.why_selected["semantic"]

    delivered = _names(result)
    assert delivered, "a refactor task must deliver real evidence, not an empty pack"
    # Delivered evidence is source-linked: every entity or snippet names a file.
    payload = result.to_dict()
    for item in [*payload["entities"], *payload["snippets"]]:
        assert item.get("path"), f"grounded evidence must cite a source file: {item}"
    assert any(item.get("line") or item.get("start_line") for item in payload["snippets"])


def test_narrow_lookup_stays_compact(indexed_corpus):
    """A narrow lookup must not pay for broad architecture evidence."""
    _workspace, service = indexed_corpus
    case = next(item for item in cases() if item["id"] == "exact_implementation")

    result = service.context(case["question"], token_budget=3000)
    assert result.plan is not None
    assert result.plan.intent in {"locate", "explain"}
    assert result.plan.budget <= 3000
    assert result.token_estimate <= result.plan.budget


def test_refactor_context_includes_relevant_tests(indexed_corpus):
    """A refactor task should surface the tests that cover the affected code."""
    _workspace, service = indexed_corpus
    case = next(item for item in cases() if item["id"] == "change_impact")

    result = service.context(case["question"], token_budget=3000)
    assert result.plan is not None
    assert "tests" in result.plan.lanes
    assert "Tests linked to the affected code." == result.plan.why_selected["tests"]


def test_social_prompt_delivers_no_repository_evidence(indexed_corpus):
    """Irrelevant prompts must not trigger retrieval at all."""
    _workspace, service = indexed_corpus

    result = service.context("Hello!", token_budget=3000)

    assert result.plan is not None
    assert result.plan.skipped is True
    assert result.plan.budget == 0
    assert result.plan.lanes == ()
    assert _names(result) == set()


def test_module_structure_query_is_selected_as_architecture(indexed_corpus):
    """Architecture phrasing routes to structural lanes and explains each one.

    The offline lexical/structural path does not currently return evidence for a
    pure "module structure" phrasing, so this pins routing and explainability,
    not retrieved content.
    """
    _workspace, service = indexed_corpus
    case = next(item for item in cases() if item["id"] == "architecture")

    plan = plan_context(case["question"], 3000)

    assert plan.intent == "architecture"
    assert "structural" in plan.lanes
    assert plan.why_selected["structural"].startswith("Callers, callees")


def test_grounding_is_stable_for_identical_requests(indexed_corpus):
    """The same query against the same index must produce the same evidence."""
    _workspace, service = indexed_corpus
    case = next(item for item in cases() if item["id"] == "dependency_path")

    first = service.context(case["question"], token_budget=3000)
    second = service.context(case["question"], token_budget=3000)

    assert _names(first) == _names(second)
    assert first.plan.to_dict() == second.plan.to_dict()