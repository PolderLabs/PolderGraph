from __future__ import annotations

from types import SimpleNamespace

from poldergraph import decision_runtime
from poldergraph.decisions import DecisionQuestion


def _config(provider: str = "typesafe", threshold: float = 0.9):
    return SimpleNamespace(
        decisions=SimpleNamespace(
            provider=provider,
            model=None,
            endpoint=None,
            timeout=0.1,
            confidence_threshold=threshold,
        )
    )


def setup_function():
    decision_runtime._CACHE.clear()
    decision_runtime._FAILURES.clear()


def test_disabled_provider_never_calls_decisions(monkeypatch):
    monkeypatch.setattr(
        decision_runtime,
        "decide",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must stay local")),
    )
    assert decision_runtime.run_decision("query", {}, _config("disabled")) is None


def test_decision_cache_keeps_only_digest_and_reuses_result(monkeypatch):
    calls = []

    def fake_decide(state, questions, **kwargs):
        calls.append(state)
        return {"provider": "typesafe", "model": "test-model", "answers": {}}

    monkeypatch.setattr(decision_runtime, "decide", fake_decide)
    questions = {
        "intent": DecisionQuestion("intent", "choice", "choose", options={"x": "x", "y": "y"})
    }
    assert decision_runtime.run_decision({"query": "private query"}, questions, _config())
    assert decision_runtime.run_decision({"query": "private query"}, questions, _config())
    assert len(calls) == 1
    assert all(len(key) == 64 and "private query" not in key for key in decision_runtime._CACHE)


def test_query_route_requires_confident_valid_typed_answers(monkeypatch):
    monkeypatch.setattr(
        decision_runtime,
        "run_decision",
        lambda *_: {
            "provider": "typesafe",
            "model": "jev-pinned",
            "answers": {
                "intent": {"choice": "architecture", "probabilities": {"architecture": 0.96}},
                "retrieval": {"choice": "graph", "probabilities": {"graph": 0.93}},
            },
        },
    )
    route = decision_runtime.decide_query_route(
        "how is this project structured?", "semantic", _config()
    )
    assert route["intent"] == {"value": "architecture", "confidence": 0.96}
    assert route["retrieval"]["value"] == "graph"
    assert route["provider"] == "typesafe"

    monkeypatch.setattr(
        decision_runtime,
        "run_decision",
        lambda *_: {
            "provider": "openai",
            "answers": {
                "intent": {"choice": "tests", "probabilities": {"tests": 0.62}},
                "retrieval": {"choice": "lexical", "probabilities": {"lexical": 0.98}},
            },
        },
    )
    route = decision_runtime.decide_query_route("how does startup work?", "semantic", _config())
    assert "intent" not in route
    assert route["retrieval"]["value"] == "lexical"


def test_relevance_filter_only_drops_confidently_irrelevant_weak_matches(monkeypatch):
    monkeypatch.setattr(
        decision_runtime,
        "run_decision",
        lambda *_: {
            "provider": "openai",
            "model": "test",
            "answers": {"relevant_0": {"probability": 0.02}},
        },
    )
    weak = {
        "id": "weak",
        "kind": "fact",
        "content": "old note",
        "lexical_score": 0.4,
        "semantic_score": None,
    }
    strong = {
        "id": "strong",
        "kind": "fact",
        "content": "matched note",
        "lexical_score": 0.95,
        "semantic_score": None,
    }
    remaining, info = decision_runtime.decide_memory_relevance(
        "current task", [weak, strong], _config()
    )
    assert [item["id"] for item in remaining] == ["strong"]
    assert info == {
        "status": "applied",
        "provider": "openai",
        "model": "test",
        "filtered": 1,
        "evaluated": 1,
        "confidence_threshold": 0.9,
    }


def test_provider_failure_preserves_deterministic_behavior(monkeypatch):
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise TimeoutError("private text")

    monkeypatch.setattr(
        decision_runtime,
        "decide",
        fail,
    )
    assert decision_runtime.run_decision("query", {}, _config()) is None
    assert decision_runtime.run_decision("query", {}, _config()) is None
    assert calls == [1]


def test_query_decision_redacts_secret_material_before_provider(monkeypatch):
    observed = {}

    def fake_run(state, questions, config):
        observed.update(state=state, questions=questions)
        return {"provider": "typesafe", "answers": {}}

    monkeypatch.setattr(decision_runtime, "run_decision", fake_run)
    decision_runtime.decide_query_route("where is key ghp_" + "x" * 36, "semantic", _config())
    serialized = str(observed["state"])
    assert "ghp_" not in serialized
    assert "[redacted]" in serialized
