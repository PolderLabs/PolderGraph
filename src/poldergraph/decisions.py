"""Typed decision API with interchangeable Jev, OpenAI, and local Laya backends.

No backend is selected implicitly. Hosted providers transmit ``state`` to the
configured service; local Laya loads model weights on this machine.
"""

from __future__ import annotations

import importlib
import json
import os
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

QuestionType = Literal["choice", "score", "predicate"]
Provider = Literal["typesafe", "openai", "laya"]


class DecisionError(RuntimeError):
    """A decision request could not be validated or completed."""


@dataclass(frozen=True)
class DecisionQuestion:
    """Provider-neutral typed question.

    ``options`` maps choice labels to their descriptions. ``levels`` is an
    ordered sequence of label/description pairs for score questions.
    Predicate questions use an explicit ``statement``.
    """

    name: str
    type: QuestionType
    instructions: str
    options: Mapping[str, str] = field(default_factory=dict)
    levels: Sequence[str | Mapping[str, str]] = field(default_factory=tuple)
    statement: str | None = None

    def validate(self) -> None:
        if self.type not in ("choice", "score", "predicate"):
            raise DecisionError(f"Unsupported decision type {self.type!r}.")
        if not self.name.strip() or not self.instructions.strip():
            raise DecisionError("Every question needs a non-empty name and instructions.")
        if self.type == "choice" and len(self.options) < 2:
            raise DecisionError(f"Choice question {self.name!r} needs at least two options.")
        if self.type == "score" and len(self.levels) < 2:
            raise DecisionError(f"Score question {self.name!r} needs at least two ordered levels.")
        if self.type == "predicate" and not (self.statement or self.instructions).strip():
            raise DecisionError(f"Predicate question {self.name!r} needs a statement.")


def choice(name: str, instructions: str, options: Mapping[str, str]) -> DecisionQuestion:
    """Create a choice question; option labels are keys and descriptions values."""
    return DecisionQuestion(name, "choice", instructions, options=options)


def score(
    name: str, instructions: str, levels: Sequence[str | Mapping[str, str]]
) -> DecisionQuestion:
    """Create an ordinal score question with levels ordered low to high."""
    return DecisionQuestion(name, "score", instructions, levels=levels)


def predicate(name: str, statement: str, instructions: str | None = None) -> DecisionQuestion:
    """Create a yes/no question about an explicit statement."""
    return DecisionQuestion(
        name, "predicate", instructions or statement, statement=statement
    )


def _coerce_questions(
    questions: Mapping[str, DecisionQuestion | Mapping[str, Any]]
) -> dict[str, DecisionQuestion]:
    if not questions:
        raise DecisionError("Provide at least one decision question.")
    result: dict[str, DecisionQuestion] = {}
    for name, value in questions.items():
        if isinstance(value, DecisionQuestion):
            question = value
            if question.name != name:
                raise DecisionError(f"Question key {name!r} does not match its name.")
        else:
            raw = dict(value)
            kind = raw.get("type")
            if kind == "noul":
                kind = "predicate"
            if kind not in ("choice", "score", "predicate"):
                raise DecisionError(f"Unsupported decision type {kind!r} for {name!r}.")
            question = DecisionQuestion(
                name=name,
                type=kind,
                instructions=raw.get("instructions", raw.get("statement", "")),
                options=raw.get("options", raw.get("criteria", {})) if kind == "choice" else {},
                levels=raw.get("levels", raw.get("criteria", ())) if kind == "score" else (),
                statement=raw.get("statement") if kind == "predicate" else None,
            )
        question.validate()
        result[name] = question
    return result


def _question_payload(question: DecisionQuestion, provider: Provider) -> dict[str, Any]:
    if provider == "typesafe":
        kind = {"predicate": "noul"}.get(question.type, question.type)
        if kind == "choice":
            criteria = dict(question.options)
        elif kind == "score":
            criteria = [
                item if isinstance(item, str) else item.get("description", item.get("label", ""))
                for item in question.levels
            ]
        else:
            criteria = {"true": question.statement or question.instructions}
        return {"type": kind, "instructions": question.instructions, "criteria": criteria}
    if provider == "openai":
        if question.type == "choice":
            choices = [
                {"value": label, "description": description}
                for label, description in question.options.items()
            ]
            return {"type": "choice", "name": question.name,
                    "instructions": question.instructions, "choices": choices}
        if question.type == "score":
            levels = []
            for level in question.levels:
                if isinstance(level, str):
                    levels.append({"label": level, "description": level})
                else:
                    levels.append({"label": level.get("label", ""),
                                   "description": level.get("description", level.get("label", ""))})
            return {"type": "score", "name": question.name,
                    "instructions": question.instructions, "levels": levels}
        instructions = question.instructions
        if question.statement and question.statement != instructions:
            instructions = f"{instructions}\nStatement to evaluate: {question.statement}"
        return {"type": "predicate", "name": question.name, "instructions": instructions}
    kind = {"predicate": "noul"}.get(question.type, question.type)
    criteria: Any
    if question.type == "choice":
        criteria = dict(question.options)
    elif question.type == "score":
        criteria = [
            item if isinstance(item, str) else item.get("description", item.get("label", ""))
            for item in question.levels
        ]
    else:
        criteria = None
    payload: dict[str, Any] = {"type": kind, "instructions": question.instructions}
    if criteria is not None:
        payload["criteria"] = criteria
    if question.statement:
        payload["statement"] = question.statement
    return payload


def _normalize_openai(payload: Mapping[str, Any]) -> dict[str, Any]:
    answers: dict[str, Any] = {}
    for answer in payload.get("answers", []):
        name = answer.get("name")
        if not name:
            continue
        kind = answer.get("type")
        if kind == "choice":
            probabilities = answer.get("probabilities", [])
            answers[name] = {
                "type": kind, "choice": answer.get("choice"),
                "probabilities": {
                    item.get("value"): item.get("probability") for item in probabilities
                },
                "confidence": answer.get("confidence"),
            }
        elif kind == "score":
            answers[name] = {
                "type": kind, "score": answer.get("score"),
                "probabilities": {
                    item.get("label", item.get("value")): item.get("probability")
                    for item in answer.get("probabilities", [])
                },
                "confidence": answer.get("confidence"),
            }
        elif kind == "predicate":
            answers[name] = {"type": kind, "probability": answer.get("probability")}
        else:
            answers[name] = {"type": kind or "refusal", "refusal": True}
    return {"provider": "openai", "model": payload.get("model"), "answers": answers,
            "usage": payload.get("usage", {})}


def _normalize_systemone(
    provider: str,
    model: str,
    payload: Mapping[str, Any],
    questions: Mapping[str, DecisionQuestion],
) -> dict[str, Any]:
    """Normalize Jev and Laya's shared System One answer contract."""
    answers: dict[str, Any] = {}
    for name, answer in payload.get("answers", {}).items():
        kind = answer.get("type")
        if kind == "choice" or "choice" in answer:
            kind = "choice"
            normalized = {
                "type": kind,
                "choice": answer.get("choice"),
                "probabilities": answer.get("probabilities", {}),
                "confidence": answer.get("answer_confidence", answer.get("confidence")),
            }
        elif kind == "score" or "score" in answer:
            kind = "score"
            raw_probabilities = answer.get("probabilities", {})
            if isinstance(raw_probabilities, list):
                level_names = [
                    level if isinstance(level, str) else level.get("label", str(index))
                    for index, level in enumerate(questions[name].levels)
                ]
                raw_probabilities = {
                    level_names[index]: (
                        probability.get("probability", 0.0)
                        if isinstance(probability, Mapping)
                        else probability
                    )
                    for index, probability in enumerate(raw_probabilities)
                    if index < len(level_names)
                }
            normalized = {
                "type": kind,
                "score": answer.get("score"),
                "probabilities": raw_probabilities,
                "confidence": answer.get("answer_confidence", answer.get("confidence")),
            }
        elif kind in ("noul", "predicate") or "noul" in answer:
            normalized = {
                "type": "predicate",
                "probability": answer.get("noul", answer.get("probability")),
            }
        else:
            normalized = dict(answer)
        answers[name] = normalized
    return {
        "provider": provider,
        "model": payload.get("model", model),
        "answers": answers,
        "usage": payload.get("usage", {}),
    }


def _post_json(url: str, token: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read())
    except HTTPError as exc:
        detail = exc.read(2000).decode("utf-8", errors="replace")
        raise DecisionError(f"Decision provider returned HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise DecisionError(f"Could not reach decision provider: {exc}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DecisionError("Decision provider returned invalid JSON.") from exc
    if not isinstance(result, dict):
        raise DecisionError("Decision provider returned an unexpected response.")
    return result


_laya_lock = threading.Lock()
_laya_models: dict[str, Any] = {}


def decide(
    state: str | Mapping[str, Any] | Sequence[Any],
    questions: Mapping[str, DecisionQuestion | Mapping[str, Any]],
    *,
    provider: Provider | str,
    model: str | None = None,
    api_key: str | None = None,
    endpoint: str | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Evaluate typed questions using the explicitly selected backend.

    Providers are ``typesafe``, ``openai``, and ``laya``. Hosted provider keys
    default to ``TYPESAFE_API_KEY`` and ``OPENAI_API_KEY`` respectively. Laya
    requires the optional ``poldergraph[decision-laya]`` extra and loads locally.
    The returned mapping has provider, model, answers and usage fields.
    """
    if provider not in ("typesafe", "openai", "laya"):
        raise DecisionError("Choose provider='typesafe', 'openai', or 'laya'.")
    if timeout <= 0:
        raise DecisionError("timeout must be greater than zero.")
    if not isinstance(state, (str, Mapping, list, tuple)):
        raise DecisionError("state must be text, an object, or a sequence of messages.")
    normalized_questions = _coerce_questions(questions)

    if provider == "laya":
        try:
            laya = importlib.import_module("laya")
        except ImportError as exc:
            raise DecisionError(
                "Local Laya is not installed. Install it with: pip install 'poldergraph[decision-laya]'"
            ) from exc
        checkpoint = model or "convaiinnovations/laya"
        with _laya_lock:
            agent = _laya_models.get(checkpoint)
            if agent is None:
                agent = laya.load(checkpoint)
                _laya_models[checkpoint] = agent
        result = agent.predict(state, {
            name: _question_payload(question, "laya")
            for name, question in normalized_questions.items()
        })
        return _normalize_systemone("laya", checkpoint, result, normalized_questions)

    env_name = "TYPESAFE_API_KEY" if provider == "typesafe" else "OPENAI_API_KEY"
    token = api_key or os.environ.get(env_name)
    if not token:
        raise DecisionError(f"Set {env_name} or pass api_key to use provider={provider!r}.")
    if provider == "typesafe":
        base = (endpoint or "https://api.typesafe.ai").rstrip("/")
        request_payload = {
            "model": model or "jev-latest",
            "state": state,
            "questions": {
                name: _question_payload(question, "typesafe")
                for name, question in normalized_questions.items()
            },
        }
        response = _post_json(f"{base}/v1/systemone", token, request_payload, timeout)
        return _normalize_systemone(
            "typesafe", request_payload["model"], response, normalized_questions
        )

    base = (endpoint or "https://api.openai.com/v1").rstrip("/")
    request_payload = {
        "model": model or "gpt-6-luna",
        "input": (
            state
            if isinstance(state, (str, list))
            else json.dumps(state, ensure_ascii=False, separators=(",", ":"))
        ),
        "questions": [
            _question_payload(question, "openai") for question in normalized_questions.values()
        ],
    }
    response = _post_json(f"{base}/decisions", token, request_payload, timeout)
    return _normalize_openai(response)


__all__ = ["DecisionError", "DecisionQuestion", "choice", "decide", "predicate", "score"]
