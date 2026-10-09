"""Offline context routing must not start the daemon or retain remote decisions."""

from types import SimpleNamespace

from typer.testing import CliRunner

from poldergraph.cli import app


def test_context_offline_uses_in_process_service_and_disables_decisions(monkeypatch):
    import poldergraph.cli as cli

    seen = {}

    class Result:
        def to_dict(self):
            return {"entities": [], "snippets": [], "token_estimate": 0}

    class Service:
        root = "/tmp/offline-project"
        config = SimpleNamespace(decisions=SimpleNamespace(provider="openai"))
        backend = None

        def context(self, *args, **kwargs):
            return Result()

        def freshness(self):
            return {"fresh": True}

    class Workspace:
        config = Service.config

        def close(self):
            pass

    def build_service(root, *, need_backend=False, offline=False):
        seen["offline"] = offline
        seen["need_backend"] = need_backend
        return Workspace(), object(), Service()

    monkeypatch.setattr(cli, "build_service", build_service)
    monkeypatch.setattr(cli, "try_daemon", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("daemon used")))
    monkeypatch.setattr(cli, "add_memories_to_context", lambda *args, **kwargs: None, raising=False)

    result = CliRunner().invoke(app, ["context", "how does this work", "--offline", "--no-json"])
    assert result.exit_code == 0, result.output
    assert seen == {"offline": True, "need_backend": False}
    assert Workspace.config.decisions.provider == "disabled"


def test_update_no_embed_does_not_load_embedding_model(indexed_workspace, monkeypatch):
    import poldergraph.embedding.gemma as gemma

    source = indexed_workspace.root / "pkg" / "auth.py"
    source.write_text(source.read_text() + "\n# changed\n")
    monkeypatch.setattr(
        gemma,
        "create_backend",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("embedding model loaded")),
    )

    result = CliRunner().invoke(app, ["update", str(indexed_workspace.root), "--no-embed", "--quiet", "--json"])
    assert result.exit_code == 0, result.output
