"""Agent 3 — Test & Report Agent (execute, heal, report, notify)."""

from __future__ import annotations

import time
from dataclasses import dataclass

from src.agents.artifact_store import LocatorStore
from src.agents.healer import HealerAgent
from src.agents.llm_client import LLMClient
from src.common.models import AgentTrace, LLMCallMetrics, PhaseTiming, Step, TestReport, TestSuite
from src.executor.runner import PlaywrightExecutor
from src.notify.agent import NotifyAgent
from src.reporting.detailed_log import save_detailed_log
from src.reporting.writer import save_json_report, save_markdown_report


@dataclass
class TestReportAgentResult:
    report: TestReport
    traces: list[AgentTrace]
    suite: TestSuite


class TestReportAgent:
    """Run Playwright with optional healing; persist reports and notify on failure."""

    def __init__(
        self,
        *,
        headless: bool = True,
        use_healer: bool = True,
        save_reports: bool = True,
        healer_llm: LLMClient | None = None,
        locator_store: LocatorStore | None = None,
    ) -> None:
        self.headless = headless
        self.use_healer = use_healer
        self.save_reports = save_reports
        self.healer = HealerAgent(llm=healer_llm)
        self.locator_store = locator_store or LocatorStore()

    def run(
        self,
        suite: TestSuite,
        *,
        prior_traces: list[AgentTrace] | None = None,
        phase_timings: list[PhaseTiming] | None = None,
        llm_metrics: list[LLMCallMetrics] | None = None,
    ) -> TestReportAgentResult:
        traces = list(prior_traces or [])
        timings = list(phase_timings or [])

        if self.use_healer:
            self.healer.reset()
        healer_fn = self.healer.heal if self.use_healer else None
        executor = PlaywrightExecutor(headless=self.headless)

        t0 = time.perf_counter()
        report = executor.run(suite, healer=healer_fn)
        suite = _apply_healed_selectors(suite, self.healer.healed_selectors)
        if self.healer.healed_selectors and suite.base_url and suite.module:
            self.locator_store.merge_elements(
                suite.base_url,
                suite.module,
                _selector_hints_from_heals(suite, self.healer.healed_selectors),
            )
        execute_ms = int((time.perf_counter() - t0) * 1000)
        traces.append(
            AgentTrace(
                agent="test_report_agent",
                phase="execute",
                detail=(
                    f"Playwright finished {len(report.steps)} steps "
                    f"(healer={'on' if self.use_healer else 'off'}) — status={report.status.value}"
                ),
                duration_ms=execute_ms,
            )
        )
        timings.append(PhaseTiming(phase="execute", duration_ms=execute_ms))

        if self.use_healer:
            traces.extend(self.healer.traces)

        t0 = time.perf_counter()
        report = NotifyAgent().maybe_notify(report)
        notify_ms = int((time.perf_counter() - t0) * 1000)
        if report.notify.triggered:
            traces.append(
                AgentTrace(
                    agent="test_report_agent",
                    phase="notify",
                    detail=f"Alert {report.notify.ticket_id} -> {report.notify.team} via {report.notify.channel}",
                    duration_ms=notify_ms,
                )
            )
        else:
            traces.append(
                AgentTrace(
                    agent="test_report_agent",
                    phase="notify",
                    detail="No failure alert (passed or notify disabled)",
                    duration_ms=notify_ms,
                )
            )
        timings.append(PhaseTiming(phase="notify", duration_ms=notify_ms))

        report = report.model_copy(
            update={
                "agent_traces": traces,
                "llm_calls": llm_metrics or [],
                "phase_timings": timings,
            }
        )

        if self.save_reports:
            t0 = time.perf_counter()
            save_json_report(report)
            save_markdown_report(report)
            save_detailed_log(report)
            report_ms = int((time.perf_counter() - t0) * 1000)
            traces.append(
                AgentTrace(
                    agent="test_report_agent",
                    phase="report",
                    detail=f"Persisted JSON/MD/log for {report.run_id}",
                    duration_ms=report_ms,
                )
            )
            timings.append(PhaseTiming(phase="report", duration_ms=report_ms))
            report = report.model_copy(update={"agent_traces": traces, "phase_timings": timings})

        return TestReportAgentResult(report=report, traces=traces, suite=suite)


def _apply_healed_selectors(suite: TestSuite, healed: dict[str, str]) -> TestSuite:
    if not healed:
        return suite
    steps: list[Step] = []
    for step in suite.steps:
        if step.id in healed:
            steps.append(step.model_copy(update={"selector": healed[step.id]}))
        else:
            steps.append(step)
    return suite.model_copy(update={"steps": steps})


def _selector_hints_from_heals(suite: TestSuite, healed: dict[str, str]) -> dict[str, str]:
    hints: dict[str, str] = {}
    for step in suite.steps:
        if step.id not in healed or not healed[step.id]:
            continue
        hint = (step.description or step.selector or step.id).lower().strip()
        if hint:
            hints[hint[:80]] = healed[step.id]
    return hints
