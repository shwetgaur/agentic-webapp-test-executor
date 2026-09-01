"""Orchestrates the combined 3-agent pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.agents.discovery_agent import DiscoveryAgent
from src.agents.step_agent import StepAgent
from src.agents.test_report_agent import TestReportAgent
from src.common.models import AgentTrace, StructuredTestPrompt, TestReport, TestSuite


@dataclass
class OrchestratorResult:
    report: TestReport
    suite: TestSuite
    traces: list[AgentTrace] = field(default_factory=list)


class AgentOrchestrator:
    """
    Combined architecture:
      Agent 1 — Test Step (Planner + Generator)
      Agent 2 — Module Discovery
      Agent 3 — Test & Report (Execute + Healer + Notify)
    """

    def __init__(
        self,
        *,
        headless: bool = True,
        use_llm: bool = True,
        use_discovery: bool = True,
        use_healer: bool = True,
    ) -> None:
        self.headless = headless
        self.use_llm = use_llm
        self.use_discovery = use_discovery
        self.use_healer = use_healer

    def run(self, prompt: StructuredTestPrompt) -> OrchestratorResult:
        all_traces: list[AgentTrace] = []

        step_out = StepAgent().run(prompt, use_llm=self.use_llm)
        all_traces.extend(step_out.traces)
        suite = step_out.suite

        if self.use_discovery:
            disc_out = DiscoveryAgent(headless=self.headless).run(suite, prompt.feature)
            all_traces.extend(disc_out.traces)
            suite = disc_out.suite

        report_out = TestReportAgent(
            headless=self.headless,
            use_healer=self.use_healer,
        ).run(suite, prior_traces=all_traces)

        return OrchestratorResult(
            report=report_out.report,
            suite=suite,
            traces=report_out.traces,
        )
