from poldergraph.retrieval.context_plan import plan_context
from poldergraph.retrieval.service import QueryService
from poldergraph.storage.repository import Repository


def test_social_messages_skip_context():
    for prompt in ("hi", "Thanks!", "Good morning", "tell me a joke"):
        plan = plan_context(prompt, 3000)
        assert plan.skipped is True
        assert plan.budget == 0
        assert plan.lanes == ()


def test_narrow_lookup_gets_small_lexical_plan():
    plan = plan_context("Where is the AuthService class defined?", 3000)
    assert plan.skipped is False
    assert plan.intent == "locate"
    assert plan.budget == 1200
    assert plan.lanes == ("exact", "lexical")


def test_change_task_gets_structural_evidence_plan():
    plan = plan_context("Refactor the authentication flow and update tests", 3000)
    assert plan.intent == "modify"
    assert "structural" in plan.lanes
    assert "tests" in plan.lanes


def test_skipped_context_does_not_run_retrieval(indexed_workspace, monkeypatch):
    service = QueryService(
        Repository(indexed_workspace.con),
        indexed_workspace.config,
        root_id=indexed_workspace.root_id(),
        workspace=indexed_workspace,
    )
    monkeypatch.setattr(
        service,
        "search",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("retrieval must be skipped")),
    )

    context = service.context("Thanks", token_budget=3000).to_dict()
    assert context["plan"]["skipped"] is True
    assert context["entities"] == []
    assert context["snippets"] == []


def test_change_context_includes_bounded_linked_test_evidence(indexed_workspace):
    service = QueryService(
        Repository(indexed_workspace.con),
        indexed_workspace.config,
        root_id=indexed_workspace.root_id(),
        workspace=indexed_workspace,
    )

    context = service.context(
        "Refactor AuthService and update the tests", token_budget=3000
    ).to_dict()

    assert "tests" in context["plan"]["lanes"]
    assert context["relevant_tests"]
    assert any("test_auth.py" in item["path"] for item in context["relevant_tests"])
    assert all(item["evidence"] in {
        "structural_test_edge", "lexical_test_file_match"
    } for item in context["relevant_tests"])
    assert context["token_estimate"] <= 3000
