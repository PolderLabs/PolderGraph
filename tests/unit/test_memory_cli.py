"""Command-line access to the shared coding-agent memory store."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from poldergraph.embedding.protocol import ModelInfo


class FakeMemoryBackend:
    def capabilities(self):
        return {"text"}

    def model_info(self):
        return ModelInfo(model_id="fake/cli", revision="r1", dimensions=3)

    def embed_texts(self, items, *, task, dimensions):
        return [[1.0, 0.0, 0.0] for _ in items]


def test_memory_cli_crud_is_machine_readable(tmp_path, monkeypatch):
    from poldergraph import decision_runtime
    from poldergraph.cli import app

    monkeypatch.setenv("POLDERGRAPH_MEMORY_DB", str(tmp_path / "memory.sqlite3"))
    monkeypatch.setattr(
        "poldergraph.memory.memory_backend", lambda preferred=None: FakeMemoryBackend()
    )
    decision_calls = []

    def retain_with_decision(query, results, config):
        decision_calls.append(query)
        return results, {"status": "applied", "filtered": 0}

    monkeypatch.setattr(decision_runtime, "decide_memory_relevance", retain_with_decision)
    runner = CliRunner()

    saved = runner.invoke(
        app,
        [
            "memory",
            "add",
            "Keep agent responses concise",
            "--scope",
            "user",
            "--kind",
            "preference",
            "--tag",
            "writing",
            "--json",
        ],
    )
    assert saved.exit_code == 0, saved.output
    record = json.loads(saved.output)
    assert record["command"] == "memory.add"
    memory_id = record["data"]["id"]
    assert record["data"]["vectorized"] is True

    recalled = runner.invoke(app, ["memory", "search", "brief response", "--json"])
    assert recalled.exit_code == 0, recalled.output
    recalled_data = json.loads(recalled.output)["data"]
    assert recalled_data["results"][0]["id"] == memory_id
    assert recalled_data["memory_decision"] == {"status": "applied", "filtered": 0}
    assert decision_calls == ["brief response"]

    updated = runner.invoke(
        app, ["memory", "update", memory_id, "--kind", "fact", "--clear-tags", "--json"]
    )
    assert updated.exit_code == 0, updated.output
    assert json.loads(updated.output)["data"]["tags"] == []

    forgotten = runner.invoke(app, ["memory", "forget", memory_id, "--json"])
    assert forgotten.exit_code == 0, forgotten.output
    assert json.loads(forgotten.output)["data"]["id"] == memory_id
