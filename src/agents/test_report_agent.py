"""Agent 3 — Test & Report Agent (execute, heal, report, notify)."""

from __future__ import annotations

from dataclasses import dataclass

from src.agents.healer import HealerAgent
from src.common.models import AgentTrace, TestReport, TestSuite
from src.executor.runner import PlaywrightExecutor
from src.notify.agent import NotifyAgent
from src.reporting.writer import save_json_report, save_markdown_report


@dataclass
class TestReportAgentResult:
    report: TestReport
    traces: list[AgentTrace]


class TestReportAgent:
    """Run Playwright with optional healing; persist reports and notify on failure."""

    def __init__(
        self,
        *,
        headless: bool = True,
        use_healer: bool = True,
        save_reports: bool = True,
    ) -> None:
        self.headless = headless
        self.use_healer = use_healer
        self.save_reports = save_reports
        self.healer = HealerAgent()

    def run(self, suite: TestSuite, *, prior_traces: list[AgentTrace] | None = None) -> TestReportAgentResult:
        traces = list(prior_traces or [])
        traces.append(
            AgentTrace(
                agent="test_report_agent",
                phase="execute",
                detail=f"Running {len(suite.steps)} steps (healer={'on' if self.use_healer else 'off'})",
            )
        )

        healer_fn = self.healer.heal if self.use_healer else None
        executor = PlaywrightExecutor(headless=self.headless)
        report = executor.run(suite, healer=healer_fn)
        if self.use_healer:
            traces.extend(self.healer.traces)

        report = NotifyAgent().maybe_notify(report)
        if report.notify.triggered:
            traces.append(
                AgentTrace(
                    agent="test_report_agent",
                    phase="notify",
                    detail=f"Alert {report.notify.ticket_id} -> {report.notify.team} via {report.notify.channel}",
                )
            )
        else:
            traces.append(
                AgentTrace(
                    agent="test_report_agent",
                    phase="notify",
                    detail="No failure alert (passed or notify disabled)",
                )
            )

        if self.save_reports:
            save_json_report(report)
            save_markdown_report(report)
            traces.append(
                AgentTrace(
                    agent="test_report_agent",
                    phase="report",
                    detail=f"Saved report {report.run_id}",
                )
            )

        report = report.model_copy(update={"agent_traces": traces})
        return TestReportAgentResult(report=report, traces=traces)
