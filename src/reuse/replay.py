"""Run a stored TestSuite / Playwright artifact without the agent pipeline."""

from __future__ import annotations

from pathlib import Path

from src.agents.test_report_agent import TestReportAgent
from src.common.models import AgentTrace, ArtifactInfo, TestReport, TestSuite
from src.reuse.script_store import ScriptArtifact, ScriptStore


def load_replay_source(
    source: str,
    *,
    site_url: str | None = None,
    store: ScriptStore | None = None,
) -> ScriptArtifact:
    """Load from a file path or a previously stored suite_id."""
    path = Path(source)
    store = store or ScriptStore()
    if path.exists():
        artifact = store.load_path(path)
        if artifact:
            return artifact
        raise FileNotFoundError(f"Not a stored TestSuite or script artifact: {path}")
    artifact = store.load(source, site_url)
    if artifact:
        return artifact
    raise FileNotFoundError(f"No stored script for suite_id={source!r}")


def replay_stored_suite(
    suite: TestSuite,
    *,
    headless: bool = True,
    use_healer: bool = False,
    prior_traces: list[AgentTrace] | None = None,
    artifacts: ArtifactInfo | None = None,
    save_reports: bool = True,
) -> TestReport:
    """Execute Playwright only — skip Step Agent and Discovery Agent."""
    traces = list(prior_traces or [])
    traces.append(
        AgentTrace(
            agent="replay",
            phase="execute",
            detail=(
                f"Replaying stored suite {suite.suite_id} "
                f"({len(suite.steps)} steps); agents skipped"
            ),
        )
    )
    info = (artifacts or ArtifactInfo()).model_copy(update={"replayed": True})
    result = TestReportAgent(
        headless=headless,
        use_healer=use_healer,
        save_reports=save_reports,
    ).run(suite, prior_traces=traces, artifacts=info)
    return result.report
