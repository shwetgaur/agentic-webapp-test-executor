"""Tests for replay mode in the orchestrator."""

from __future__ import annotations

import pytest

from src.agents.artifact_store import SuiteStore
from src.agents.orchestrator import AgentOrchestrator
from src.common.models import Step, StepAction, StructuredTestPrompt, TestEnvironment, TestSuite


def _prompt() -> StructuredTestPrompt:
    return StructuredTestPrompt(
        test_id="TC01",
        site_url="https://www.saucedemo.com/",
        feature="login",
        test_name="Login",
        objective="Verify login",
        expected_outcome="Products page",
        environment=TestEnvironment.DEVELOP,
        steps=["Click Login"],
    )


def test_replay_requires_cached_suite(tmp_path):
    with pytest.raises(ValueError, match="No cached suite"):
        AgentOrchestrator(
            use_replay=True,
            suite_store=SuiteStore(tmp_path),
        ).run(_prompt())


def test_replay_loads_cached_suite(tmp_path, monkeypatch):
    store = SuiteStore(tmp_path)
    cached = TestSuite(
        suite_id="TC01",
        name="Login",
        base_url="https://www.saucedemo.com/",
        steps=[Step(id="s1", action=StepAction.GOTO, url="https://www.saucedemo.com/")],
    )
    store.save_latest("TC01", cached)

    from src.agents import test_report_agent as tra_mod
    from src.common.models import AgentTrace, RunStatus, RunSummary, TestReport
    from datetime import datetime, timezone

    def fake_run(self, suite, **kwargs):
        report = TestReport(
            run_id="run-test",
            suite_id=suite.suite_id,
            status=RunStatus.PASSED,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            duration_ms=1,
            summary=RunSummary(total=1, passed=1, failed=0, skipped=0),
            steps=[],
            agent_traces=list(kwargs.get("prior_traces") or []),
        )
        return tra_mod.TestReportAgentResult(report=report, traces=[], suite=suite)

    monkeypatch.setattr(tra_mod.TestReportAgent, "run", fake_run)

    result = AgentOrchestrator(
        use_replay=True,
        suite_store=store,
        save_artifacts=False,
    ).run(_prompt())

    assert result.report.replay_mode is True
    assert any(t.phase == "replay" for t in result.report.agent_traces)
