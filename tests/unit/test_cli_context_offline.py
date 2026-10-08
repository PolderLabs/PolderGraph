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
    assert seen == {"offline": True, "need_backend": True}
    assert Workspace.config.decisions.provider == "disabled"
