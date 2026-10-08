from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from poldergraph import decisions
from poldergraph.decisions import DecisionError, choice, decide, predicate, score


def _questions():
    return {
        "action": choice(
            "action",
            "Should this become durable memory?",
            {"store": "Durable and useful", "reject": "Temporary or ambiguous"},
        ),
        "confidence": predicate("confidence", "The user stated this explicitly."),
        "durability": score("durability", "How durable is it?", ["temporary", "durable"]),
    }


def test_typesafe_provider_serializes_systemone_contract(monkeypatch):
    captured = {}

    def post(url, token, payload, timeout):
        captured.update(url=url, token=token, payload=payload, timeout=timeout)
        return {
            "model": "jev-1.13.0",
            "answers": {
                "action": {"choice": "store", "probabilities": {"store": 0.9, "reject": 0.1}, "confidence": 0.9},
                "confidence": {"noul": 0.98},
                "durability": {"score": 0.8, "probabilities": [0.2, 0.8]},
            },
            "usage": {"input_tokens": 15},
        }

    monkeypatch.setattr(decisions, "_post_json", post)
    result = decide("an explicit preference", _questions(), provider="typesafe", api_key="secret")

    assert captured["url"] == "https://api.typesafe.ai/v1/systemone"
    assert captured["payload"]["questions"]["confidence"]["type"] == "noul"
    assert captured["payload"]["questions"]["confidence"]["criteria"]["true"]
    assert result["model"] == "jev-1.13.0"
    assert result["answers"]["action"]["choice"] == "store"
    assert result["answers"]["confidence"]["probability"] == 0.98


def test_openai_provider_serializes_decisions_and_normalizes_answers(monkeypatch):
    captured = {}

    def post(url, token, payload, timeout):
        captured.update(url=url, token=token, payload=payload)
        return {
            "model": "gpt-6-luna",
            "answers": [
                {
                    "type": "choice", "name": "action", "choice": "store", "confidence": 0.9,
                    "probabilities": [{"value": "store", "probability": 0.9}, {"value": "reject", "probability": 0.1}],
                },
                {"type": "predicate", "name": "confidence", "probability": 0.98},
                {
                    "type": "score", "name": "durability", "score": 0.8, "confidence": 0.8,
                    "probabilities": [{"value": 0, "label": "temporary", "probability": 0.2}, {"value": 1, "label": "durable", "probability": 0.8}],
                },
            ],
        }

    monkeypatch.setattr(decisions, "_post_json", post)
    result = decide({"text": "hello"}, _questions(), provider="openai", api_key="secret")

    assert captured["url"] == "https://api.openai.com/v1/decisions"
    assert captured["payload"]["input"] == '{"text":"hello"}'
    assert captured["payload"]["questions"][0]["choices"][0]["value"] == "store"
    assert result["answers"]["action"]["probabilities"] == {"store": 0.9, "reject": 0.1}
    assert result["answers"]["durability"]["probabilities"] == {"temporary": 0.2, "durable": 0.8}


def test_laya_is_explicit_and_runs_locally(monkeypatch):
    calls = {}

    class FakeLayaAgent:
        def predict(self, state, questions):
            calls["state"] = state
            calls["questions"] = questions
            return {
                "model": "test-local",
                "answers": {"action": {"choice": "store", "probabilities": {"store": 1.0}, "answer_confidence": 1.0}},
                "usage": {"input_tokens": 3},
            }

    fake_module = SimpleNamespace(load=lambda model: (calls.update(model=model) or FakeLayaAgent()))
    monkeypatch.setitem(sys.modules, "laya", fake_module)
    decisions._laya_models.pop("test-local", None)

    result = decide("state", {"action": choice("action", "What?", {"store": "yes", "reject": "no"})}, provider="laya", model="test-local")

    assert calls["model"] == "test-local"
    assert calls["state"] == "state"
    assert result["provider"] == "laya"
    assert result["answers"]["action"]["confidence"] == 1.0
    decisions._laya_models.pop("test-local", None)


def test_laya_batch_preserves_candidate_alignment(monkeypatch):
    calls = {}

    class FakeLayaAgent:
        def predict_batch(self, states, questions, batch_size=None):
            calls.update(states=states, questions=questions, batch_size=batch_size)
            return [
                {"answers": {"decision": {"probability": state["id"] / 20}}}
                for state in states
            ]

    fake_module = SimpleNamespace(load=lambda model: FakeLayaAgent())
    monkeypatch.setitem(sys.modules, "laya", fake_module)
    decisions._laya_models.pop("test-batch", None)
    states = [{"id": index} for index in range(20)]
    results = decisions.decide_batch(
        states,
        {"decision": predicate("decision", "Is this candidate relevant?")},
        model="test-batch",
    )
    assert calls["states"] == states
    assert calls["batch_size"] == 8
    assert [item["answers"]["decision"]["probability"] for item in results] == [
        index / 20 for index in range(20)
    ]
    decisions._laya_models.pop("test-batch", None)

def test_provider_and_question_validation_is_explicit():
    with pytest.raises(DecisionError, match="Choose provider"):
        decide("state", _questions(), provider="automatic")
    with pytest.raises(DecisionError, match="at least two options"):
        decide("state", {"one": choice("one", "Pick", {"only": "one"})}, provider="laya")
