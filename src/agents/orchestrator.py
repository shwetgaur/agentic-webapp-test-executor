"""Orchestrates the combined 3-agent pipeline."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from src.agents.artifact_store import LocatorStore, SuiteStore
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
        use_replay: bool = False,
        save_artifacts: bool = True,
        locator_store: LocatorStore | None = None,
        suite_store: SuiteStore | None = None,
    ) -> None:
        self.headless = headless
        self.use_llm = use_llm
        self.use_discovery = use_discovery
        self.use_healer = use_healer
        self.use_replay = use_replay
        self.save_artifacts = save_artifacts
        self.locator_store = locator_store or LocatorStore()
        self.suite_store = suite_store or SuiteStore()

    def run(self, prompt: StructuredTestPrompt) -> OrchestratorResult:
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        llm = LLMClient(run_id=run_id)
        all_traces: list[AgentTrace] = []
        phase_timings: list[PhaseTiming] = []
        suite: TestSuite

        if self.use_replay:
            t0 = time.perf_counter()
            loaded = self.suite_store.load_latest(prompt.test_id)
            load_ms = int((time.perf_counter() - t0) * 1000)
            if not loaded:
                raise ValueError(
                    f"No cached suite for test_id '{prompt.test_id}'. "
                    "Run the full 3-agent pipeline once to generate and store the Playwright suite."
                )
            suite = loaded
            all_traces.append(
                AgentTrace(
                    agent="orchestrator",
                    phase="replay",
                    detail=f"Loaded cached TestSuite with {len(suite.steps)} steps (skipped LLM + discovery)",
                    duration_ms=load_ms,
                )
            )
            phase_timings.append(
                PhaseTiming(phase="replay", duration_ms=load_ms, detail=prompt.test_id)
            )
        else:
            t0 = time.perf_counter()
            step_out = StepAgent(llm=llm).run(prompt, use_llm=self.use_llm)
            step_ms = int((time.perf_counter() - t0) * 1000)
            all_traces.extend(step_out.traces)
            phase_timings.append(
                PhaseTiming(phase="step_agent", duration_ms=step_ms, detail=prompt.test_id)
            )
            suite = step_out.suite

            if self.use_discovery and _suite_needs_discovery(suite):
                t0 = time.perf_counter()
                disc_out = DiscoveryAgent(
                    headless=self.headless,
                    locator_store=self.locator_store,
                ).run(suite, prompt.feature)
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
            locator_store=self.locator_store,
        ).run(
            suite,
            prior_traces=all_traces,
            phase_timings=phase_timings,
            llm_metrics=_llm_metrics_from_client(llm),
        )

        suite = report_out.suite
        report = report_out.report
        snapshot_path: str | None = None

        if self.save_artifacts and not self.use_replay:
            saved = self.suite_store.save_latest(
                prompt.test_id, suite, run_id=report.run_id
            )
            snapshot_path = str(saved).replace("\\", "/")

        report = report.model_copy(
            update={
                "replay_mode": self.use_replay,
                "suite_snapshot_path": snapshot_path,
            }
        )

        if self.save_artifacts and snapshot_path:
            from src.reporting.writer import save_json_report

            save_json_report(report)

        return OrchestratorResult(
            report=report,
            suite=suite,
            traces=report_out.traces,
        )
