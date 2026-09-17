"""Agent 3 — Test & Report Agent (execute, heal, report, notify)."""

from __future__ import annotations

from dataclasses import dataclass

from src.agents.healer import HealerAgent
from src.common.models import AgentTrace, ArtifactInfo, Step, TestReport, TestSuite
from src.executor.runner import PlaywrightExecutor
from src.notify.agent import NotifyAgent
from src.reporting.detailed_log import save_detailed_log
from src.reporting.writer import save_json_report, save_markdown_report
from src.reuse.locator_store import LocatorStore, hint_from_step


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
        locator_store: LocatorStore | None = None,
    ) -> None:
        self.headless = headless
        self.use_healer = use_healer
        self.save_reports = save_reports
        self.healer = HealerAgent()
        self.locator_store = locator_store or LocatorStore()

    def run(
        self,
        suite: TestSuite,
        *,
        prior_traces: list[AgentTrace] | None = None,
        artifacts: ArtifactInfo | None = None,
    ) -> TestReportAgentResult:
        traces = list(prior_traces or [])
        traces.append(
            AgentTrace(
                agent="test_report_agent",
                phase="execute",
                detail=f"Running {len(suite.steps)} steps (healer={'on' if self.use_healer else 'off'})",
            )
        )

        healer_fn = self._heal_and_cache(suite) if self.use_healer else None
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
            traces.append(
                AgentTrace(
                    agent="test_report_agent",
                    phase="report",
                    detail=f"Persisting report {report.run_id}",
                )
            )

        report = report.model_copy(
            update={"agent_traces": traces, "artifacts": artifacts or ArtifactInfo()}
        )

        if self.save_reports:
            save_json_report(report)
            save_markdown_report(report)
            save_detailed_log(report)

        return TestReportAgentResult(report=report, traces=traces)

    def _heal_and_cache(self, suite: TestSuite):
        def _heal(step: Step, page, error: str) -> Step | None:
            healed = self.healer.heal(step, page, error)
            if healed and healed.selector and healed.selector != step.selector:
                hint = hint_from_step(step)
                path = self.locator_store.upsert_selector(
                    suite.base_url, suite.module, hint, healed.selector
                )
                if path:
                    self.healer.traces.append(
                        AgentTrace(
                            agent="test_report_agent",
                            phase="locator_store",
                            detail=f"Cached healed selector {healed.selector} → {path}",
                        )
                    )
            return healed

        return _heal
