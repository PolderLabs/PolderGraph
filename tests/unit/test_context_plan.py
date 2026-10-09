import subprocess

import pytest

from poldergraph.errors import UsageError
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
    assert plan.budget == 1000
    assert plan.lanes == ("exact", "lexical")


def test_change_task_gets_structural_evidence_plan():
    plan = plan_context("Refactor the authentication flow and update tests", 3000)
    assert plan.intent == "modify"
    assert "structural" in plan.lanes
    assert "tests" in plan.lanes


def test_change_plan_carries_stable_bounded_dirty_file_focus():
    plan = plan_context(
        "Refactor the authentication flow",
        3000,
        changed_paths=["pkg/z.py", "pkg/auth.py", "pkg/z.py"],
    )
    assert plan.changed_paths == ("pkg/auth.py", "pkg/z.py")
    assert "changed_files" in plan.lanes
    assert plan.to_dict()["changed_paths_source_read_required"] is True


def test_context_budget_adapts_to_task_intent_and_respects_user_limit():
    locate = plan_context("Where is AuthService defined?", 6000)
    debug = plan_context("Debug the failing auth token refresh behavior", 6000)
    architecture = plan_context("Explain the repository architecture", 6000)

    assert locate.budget == 1000
    assert debug.budget == 3200
    assert architecture.budget == 4200
    assert plan_context("Debug the token flow", 900).budget == 900


def test_context_evidence_cursor_suppresses_duplicates_and_surfaces_updates(indexed_workspace):
    service = QueryService(
        Repository(indexed_workspace.con),
        indexed_workspace.config,
        root_id=indexed_workspace.root_id(),
        workspace=indexed_workspace,
    )
    query = "Explain the AuthService authentication token flow"
    first = service.context(query, token_budget=3000).to_dict()
    assert first["evidence_cursor"]
    assert first["new_evidence_count"] > 0

    repeated = service.context(
        query, token_budget=3000, new_evidence_since=first["evidence_cursor"]
    ).to_dict()
    assert repeated["new_evidence_count"] == 0
    assert repeated["entities"] == []
    assert repeated["snippets"] == []

    source = indexed_workspace.root / "pkg" / "auth.py"
    source.write_text(source.read_text().replace("Check a token is valid.", "Check a signed access token is valid."))
    from poldergraph.agents.bootstrap import ensure_workspace_ready

    ensure_workspace_ready(indexed_workspace.root)
    updated = service.context(
        query, token_budget=3000, new_evidence_since=first["evidence_cursor"]
    ).to_dict()
    assert updated["new_evidence_count"] > 0
    assert updated["snippets"] or updated["entities"]


def test_context_rejects_malformed_evidence_cursor(indexed_workspace):
    service = QueryService(
        Repository(indexed_workspace.con),
        indexed_workspace.config,
        root_id=indexed_workspace.root_id(),
        workspace=indexed_workspace,
    )
    with pytest.raises(UsageError, match="evidence cursor"):
        service.context("Explain AuthService", new_evidence_since="invalid")


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


def test_change_context_surfaces_unindexed_source_drift(indexed_workspace):
    source = indexed_workspace.root / "pkg" / "auth.py"
    source.write_text(source.read_text() + "\n# pending local edit\n")
    service = QueryService(
        Repository(indexed_workspace.con),
        indexed_workspace.config,
        root_id=indexed_workspace.root_id(),
        workspace=indexed_workspace,
    )

    context = service.context("Refactor AuthService", token_budget=3000).to_dict()

    assert "pkg/auth.py" in context["plan"]["changed_paths"]
    assert context["plan"]["changed_paths_source_read_required"] is True
    assert "changed_files" in context["plan"]["lanes"]


def test_typed_decision_trace_is_bounded_and_explains_execution(indexed_workspace, monkeypatch):
    import poldergraph.retrieval.service as retrieval_service

    monkeypatch.setattr(retrieval_service, "provider_enabled", lambda _config: True)
    monkeypatch.setattr(retrieval_service, "exact_matches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(retrieval_service, "lexical_candidates", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        retrieval_service,
        "decide_query_route",
        lambda *_args: {
            "status": "applied",
            "provider": "laya",
            "model": "fixture",
            "intent": {"value": "how_reaches", "confidence": 0.97},
            "retrieval": {"value": "graph", "confidence": 0.96},
        },
    )
    service = QueryService(
        Repository(indexed_workspace.con),
        indexed_workspace.config,
        root_id=indexed_workspace.root_id(),
        workspace=indexed_workspace,
    )

    result = service.search(
        "why does privacy handling interact with custom semantic concepts?",
        include_semantic=False,
    )

    trace = result.routing["trace"]
    assert trace["allowed_actions"] == ["lexical", "hybrid", "graph"]
    assert trace["requested_action"] == "graph"
    assert trace["outcome"] == "executed"
    assert trace["evidence_source"] == "typed_decision"
    assert trace["index_revision"] == indexed_workspace.con.execute(
        "SELECT value FROM meta WHERE key='index_generation'"
    ).fetchone()[0]
    assert trace["deadline_seconds"] == indexed_workspace.config.decisions.timeout
    assert trace["confidence"]["retrieval"] == 0.96


def test_change_context_keeps_active_diff_focus_after_reindex(indexed_workspace):
    root = indexed_workspace.root
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "test@example.invalid"],
        check=True,
    )
    subprocess.run(["git", "-C", str(root), "add", "pkg/auth.py"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", "baseline"], check=True
    )
    source = root / "pkg" / "auth.py"
    source.write_text(source.read_text() + "\n# active work\n")

    from poldergraph.agents.bootstrap import ensure_workspace_ready

    ensure_workspace_ready(root)
    service = QueryService(
        Repository(indexed_workspace.con),
        indexed_workspace.config,
        root_id=indexed_workspace.root_id(),
        workspace=indexed_workspace,
    )

    context = service.context("Refactor AuthService", token_budget=3000).to_dict()

    assert context["index"]["fresh"] is True
    assert "pkg/auth.py" in context["plan"]["changed_paths"]
    assert "changed_files" in context["plan"]["lanes"]
    assert context["plan"]["changed_paths_source_read_required"] is True
    assert any(
        item.get("path", "").startswith("pkg/auth.py")
        for item in [*context["entities"], *context["snippets"]]
    )
