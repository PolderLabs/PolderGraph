from __future__ import annotations

from types import SimpleNamespace

import pytest

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
            remote_authorized=True,
            endpoint_authorized=True,
            authorized_remote_providers=["typesafe", "openai"],
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


def test_hosted_provider_requires_trusted_remote_consent(monkeypatch):
    config = _config()
    config.decisions.remote_authorized = False
    monkeypatch.setattr(
        decision_runtime,
        "decide",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must fail closed")),
    )
    assert not decision_runtime.provider_enabled(config)
    assert decision_runtime.run_decision("private task", {}, config) is None


def test_runtime_accepts_config_and_decisions_config_shapes():
    config = _config()
    assert decision_runtime.provider_enabled(config)
    assert decision_runtime.provider_enabled(config.decisions)


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
        "abstained": 0,
        "confidence_threshold": 0.9,
    }


def test_memory_decisions_bind_one_bounded_candidate_per_request(monkeypatch):
    seen = []

    def fake_run(state, questions, config):
        seen.append((state, questions))
        answers = {
            name: {"probability": 0.01 if "candidate ID mem_0 " in question.statement else 0.99}
            for name, question in questions.items()
        }
        return {
            "provider": "laya",
            "model": "fixture",
            "answers": answers,
        }

    monkeypatch.setattr(decision_runtime, "run_decision", fake_run)
    memories = [
        {
            "id": f"mem_{index}",
            "kind": "fact",
            "content": f"candidate {index} " + ("long text " * 500),
            "lexical_score": 0.4,
            "semantic_score": None,
        }
        for index in range(20)
    ]
    remaining, info = decision_runtime.decide_memory_relevance("task " * 1000, memories, _config())
    assert len(seen) == 1
    state, questions = seen[0]
    assert len(str(state["task"])) < 500
    assert len(questions) == 20
    assert all(len(question.statement) < 500 for question in questions.values())
    assert "candidate ID mem_0" in questions["relevant_0"].statement
    assert "candidate ID mem_19" in questions["relevant_19"].statement
    assert "excerpt_truncated=true" in questions["relevant_0"].statement
    assert [item["id"] for item in remaining] == [f"mem_{i}" for i in range(1, 20)]
    assert info["evaluated"] == 20


def test_memory_candidate_overflow_is_reported_and_retained(monkeypatch):
    monkeypatch.setattr(
        decision_runtime,
        "run_decision",
        lambda state, questions, config: {
            "provider": "typesafe",
            "answers": {
                name: {"probability": 0.01} for name in questions
            },
        },
    )
    memories = [
        {
            "id": f"mem_{index}",
            "kind": "fact",
            "content": f"memory {index}",
            "lexical_score": 0.4,
            "semantic_score": None,
        }
        for index in range(21)
    ]
    remaining, info = decision_runtime.decide_memory_relevance("task", memories, _config())
    assert [item["id"] for item in remaining] == ["mem_20"]
    assert info["evaluated"] == 20
    assert info["abstained"] == 1


@pytest.mark.parametrize("count", [2, 8, 20])
def test_hosted_candidate_answers_keep_first_middle_last_bindings(monkeypatch, count):
    rejected_indexes = {0, count // 2, count - 1}

    def fake_run(state, questions, config):
        answers = {}
        for name, question in questions.items():
            rejected = any(f"candidate ID mem_{index} " in question.statement for index in rejected_indexes)
            answers[name] = {"probability": 0.01 if rejected else 0.99}
        return {"provider": "typesafe", "model": "fixture", "answers": answers}

    monkeypatch.setattr(decision_runtime, "run_decision", fake_run)
    memories = [
        {"id": f"mem_{index}", "kind": "fact", "content": f"memory {index}",
         "lexical_score": 0.4, "semantic_score": None}
        for index in range(count)
    ]
    remaining, info = decision_runtime.decide_memory_relevance("task", memories, _config())
    assert {item["id"] for item in memories} - {item["id"] for item in remaining} == {
        f"mem_{index}" for index in rejected_indexes
    }
    assert info["evaluated"] == count


def test_local_batch_keeps_aligned_results_and_uses_cache(monkeypatch):
    calls = []

    def fake_batch(states, questions, **kwargs):
        calls.append((states, questions, kwargs))
        return [
            {"provider": "laya", "model": "fixture", "answers": {"ok": {"probability": i / 20}}}
            for i, _state in enumerate(states)
        ]

    monkeypatch.setattr(decision_runtime, "decide_batch", fake_batch)
    question = DecisionQuestion("ok", "predicate", "Is this item useful?")
    states = [{"id": index} for index in range(20)]
    first = decision_runtime.run_local_decision_batch(states, {"ok": question}, _config("laya"))
    second = decision_runtime.run_local_decision_batch(states, {"ok": question}, _config("laya"))
    assert len(calls) == 1
    assert calls[0][0] == states
    assert [item["answers"]["ok"]["probability"] for item in first] == [
        item["answers"]["ok"]["probability"] for item in second
    ]


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
