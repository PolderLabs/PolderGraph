import json

from poldergraph.agents.capabilities import integration_capabilities


def test_integration_report_detects_codex_hook_events(tmp_path):
    hook_file = tmp_path / ".codex" / "hooks.json"
    hook_file.parent.mkdir()
    hook_file.write_text(
        json.dumps(
            {
                "hooks": {
                    "UserPromptSubmit": [
                        {"hooks": [{"type": "command", "command": "poldergraph codex-hook"}]}
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    report = integration_capabilities(tmp_path)
    codex = next(item for item in report["integrations"] if item["agent"] == "codex")

    assert codex["mode"] == "native-hooks"
    assert codex["native_events"] == ["task_start"]
    assert codex["remediation"] is None


def test_guidance_only_adapter_does_not_claim_native_events(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("PolderGraph guidance", encoding="utf-8")

    report = integration_capabilities(tmp_path)
    claude = next(item for item in report["integrations"] if item["agent"] == "claude")

    assert claude["mode"] == "guidance-only"
    assert claude["native_events"] == []
    assert claude["remediation"]


def test_doctor_integrations_cli_reports_capabilities():
    from typer.testing import CliRunner

    from poldergraph.cli import app

    result = CliRunner().invoke(app, ["doctor", "integrations", "--json"])

    assert result.exit_code == 0, result.output
    assert '"command":"doctor integrations"' in result.output
    assert '"native_events"' in result.output
