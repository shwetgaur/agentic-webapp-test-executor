"""Orchestrates the combined 3-agent pipeline."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from src.agents.discovery_agent import DiscoveryAgent
from src.agents.llm_client import LLMClient
from src.agents.step_agent import StepAgent
from src.agents.test_report_agent import TestReportAgent
from src.common.models import (
    AgentTrace,
    LLMCallMetrics,
    PhaseTiming,
    StepAction,
    StructuredTestPrompt,
    TestReport,
    TestSuite,
)

_INTERACTIVE_ACTIONS = frozenset(
    {StepAction.FILL, StepAction.CLICK, StepAction.SELECT, StepAction.HOVER}
)


def _suite_needs_discovery(suite: TestSuite) -> bool:
    return any(step.action in _INTERACTIVE_ACTIONS for step in suite.steps)


def _llm_metrics_from_client(llm: LLMClient) -> list[LLMCallMetrics]:
    return [
        LLMCallMetrics(
            caller=record.caller,
            provider=record.provider,
            model=record.model,
            prompt_tokens=record.prompt_tokens,
            completion_tokens=record.completion_tokens,
            total_tokens=record.total_tokens,
            latency_ms=record.latency_ms,
            success=record.success,
        )
        for record in llm.call_log
    ]


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
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        llm = LLMClient(run_id=run_id)
        all_traces: list[AgentTrace] = []
        phase_timings: list[PhaseTiming] = []

        t0 = time.perf_counter()
        step_out = StepAgent(llm=llm).run(prompt, use_llm=self.use_llm)
        step_ms = int((time.perf_counter() - t0) * 1000)
        all_traces.extend(step_out.traces)
        phase_timings.append(PhaseTiming(phase="step_agent", duration_ms=step_ms, detail=prompt.test_id))
        suite = step_out.suite

        if self.use_discovery and _suite_needs_discovery(suite):
            t0 = time.perf_counter()
            disc_out = DiscoveryAgent(headless=self.headless).run(suite, prompt.feature)
            disc_ms = int((time.perf_counter() - t0) * 1000)
            all_traces.extend(disc_out.traces)
            phase_timings.append(
                PhaseTiming(phase="discovery_agent", duration_ms=disc_ms, detail=prompt.feature)
            )
            suite = disc_out.suite
        elif self.use_discovery:
            all_traces.append(
                AgentTrace(
                    agent="discovery_agent",
                    phase="skipped",
                    detail="No fill/click/select steps — discovery not needed for this run",
                    duration_ms=0,
                )
            )

        report_out = TestReportAgent(
            headless=self.headless,
            use_healer=self.use_healer,
            healer_llm=llm,
        ).run(suite, prior_traces=all_traces, phase_timings=phase_timings, llm_metrics=_llm_metrics_from_client(llm))

        return OrchestratorResult(
            report=report_out.report,
            suite=suite,
            traces=report_out.traces,
        )
