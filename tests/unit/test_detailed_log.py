"""Unit tests for detailed execution logs."""

from __future__ import annotations

from datetime import datetime, timezone

from src.common.models import (
    AgentTrace,
    NotifyInfo,
    RunStatus,
    RunSummary,
    StepResult,
    StepStatus,
    TestReport,
)
from src.reporting.detailed_log import render_detailed_log, save_detailed_log


def _sample_report() -> TestReport:
    started = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    step_start = datetime(2026, 8, 1, 10, 0, 1, 100000, tzinfo=timezone.utc)
    step_end = datetime(2026, 8, 1, 10, 0, 2, 500000, tzinfo=timezone.utc)
    finished = datetime(2026, 8, 1, 10, 0, 3, tzinfo=timezone.utc)
    return TestReport(
        run_id="run-test-001",
        suite_id="TC01",
        suite_name="Login success",
        module="login",
        site_url="https://example.com",
        objective="Verify login",
        expected_outcome="User lands on dashboard",
        environment="develop",
        status=RunStatus.PASSED,
        started_at=started,
        finished_at=finished,
        duration_ms=3000,
        summary=RunSummary(total=1, passed=1, failed=0, skipped=0),
        steps=[
            StepResult(
                step_id="s1",
                action="goto",
                description="Open login page",
                status=StepStatus.PASSED,
                started_at=step_start,
                finished_at=step_end,
                duration_ms=1400,
                actual="https://example.com/login",
            )
        ],
        notify=NotifyInfo(triggered=False),
        agent_traces=[
            AgentTrace(
                agent="step_agent",
                phase="validate",
                detail="Parsed 1 step",
                timestamp=started,
            )
        ],
    )


def test_render_detailed_log_includes_step_timestamps():
    text = render_detailed_log(_sample_report())
    assert "STEP s1 START" in text
    assert "STEP s1 END" in text
    assert "duration=1400ms" in text
    assert "2026-08-01T10:00:01.100Z" in text
    assert "step_agent.validate" in text


def test_save_detailed_log_writes_file(tmp_path):
    report = _sample_report()
    path = save_detailed_log(report, out_dir=tmp_path)
    assert path.exists()
    assert path.name == "run-test-001.log"
    content = path.read_text(encoding="utf-8")
    assert "TEST RUN LOG" in content
    assert report.run_id in content
