import subprocess

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
