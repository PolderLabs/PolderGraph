import json
from pathlib import Path

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
    # Reported events are the real host hook names, not conceptual lifecycle
    # points, so an unimplemented event is never advertised as wired.
    assert codex["native_events"] == ["UserPromptSubmit"]
    assert codex["covered_events"] == ["task_start"]
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


def test_omp_reports_only_events_the_extension_actually_subscribes_to():
    """A capability report must not claim a lifecycle event with no host hook."""
    from poldergraph.agents.capabilities import _CAPABILITIES

    omp = _CAPABILITIES["omp"]
    extension = (Path(__file__).resolve().parents[2] / "omp" / "index.ts").read_text(
        encoding="utf-8"
    )

    for event in omp["native_events"]:
        assert f'pi.on("{event}"' in extension, f"OMP extension does not wire {event}"
    # Conceptual lifecycle points stay in covered_events, never in native_events.
    for conceptual in ("workspace_open", "task_start", "after_edit"):
        assert conceptual not in omp["native_events"]
        assert conceptual in omp["covered_events"]
