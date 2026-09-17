"""Orchestrates the combined 3-agent pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.agents.discovery_agent import DiscoveryAgent
from src.agents.step_agent import StepAgent
from src.agents.test_report_agent import TestReportAgent
from src.common.models import AgentTrace, ArtifactInfo, StepAction, StructuredTestPrompt, TestReport, TestSuite
from src.reuse.locator_store import LocatorStore
from src.reuse.replay import replay_stored_suite
from src.reuse.script_store import ScriptStore

_INTERACTIVE_ACTIONS = frozenset(
    {StepAction.FILL, StepAction.CLICK, StepAction.SELECT, StepAction.HOVER}
)


def _suite_needs_discovery(suite: TestSuite) -> bool:
    return any(step.action in _INTERACTIVE_ACTIONS for step in suite.steps)


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

    Locator cache + stored-script replay:
      · Discovery results are saved per site/feature and reused on later runs
      · Enriched TestSuite + Playwright script are stored under data/scripts/
      · prefer_replay skips agents 1–2 when a stored script already exists
    """

    def __init__(
        self,
        *,
        headless: bool = True,
        use_llm: bool = True,
        use_discovery: bool = True,
        use_healer: bool = True,
        prefer_replay: bool = False,
        refresh_locators: bool = False,
        locator_store: LocatorStore | None = None,
        script_store: ScriptStore | None = None,
    ) -> None:
        self.headless = headless
        self.use_llm = use_llm
        self.use_discovery = use_discovery
        self.use_healer = use_healer
        self.prefer_replay = prefer_replay
        self.refresh_locators = refresh_locators
        self.locator_store = locator_store or LocatorStore()
        self.script_store = script_store or ScriptStore()

    def run(self, prompt: StructuredTestPrompt) -> OrchestratorResult:
        all_traces: list[AgentTrace] = []

        if self.prefer_replay:
            stored = self.script_store.load(prompt.test_id, prompt.site_url)
            if stored:
                all_traces.append(
                    AgentTrace(
                        agent="replay",
                        phase="hit",
                        detail=f"Using stored script {stored.json_path or stored.suite_id}; skipping Step + Discovery agents",
                    )
                )
                artifacts = ArtifactInfo(
                    replayed=True,
                    script_json_path=stored.json_path,
                    script_py_path=stored.py_path,
                    locator_path=stored.locator_path,
                )
                report = replay_stored_suite(
                    stored.suite,
                    headless=self.headless,
                    use_healer=self.use_healer,
                    prior_traces=all_traces,
                    artifacts=artifacts,
                )
                return OrchestratorResult(report=report, suite=stored.suite, traces=report.agent_traces)
            all_traces.append(
                AgentTrace(
                    agent="replay",
                    phase="miss",
                    detail=f"No stored script for {prompt.test_id}; running full agent pipeline",
                )
            )

        step_out = StepAgent().run(prompt, use_llm=self.use_llm)
        all_traces.extend(step_out.traces)
        suite = step_out.suite
        locator_path = None

        if self.use_discovery and _suite_needs_discovery(suite):
            disc_out = DiscoveryAgent(
                headless=self.headless,
                locator_store=self.locator_store,
                reuse_locators=not self.refresh_locators,
                refresh_locators=self.refresh_locators,
            ).run(suite, prompt.feature)
            all_traces.extend(disc_out.traces)
            suite = disc_out.suite
            if disc_out.module_map.elements:
                locator_path = str(self.locator_store.path_for(prompt.site_url, prompt.feature)).replace("\\", "/")
        elif self.use_discovery:
            all_traces.append(
                AgentTrace(
                    agent="discovery_agent",
                    phase="skipped",
                    detail="No fill/click/select steps — discovery not needed for this run",
                )
            )

        artifact = self.script_store.save(
            suite,
            feature=prompt.feature,
            locator_path=locator_path,
        )
        all_traces.append(
            AgentTrace(
                agent="script_store",
                phase="save",
                detail=f"Stored enriched suite + Playwright script at {artifact.json_path}",
            )
        )
        artifacts = ArtifactInfo(
            replayed=False,
            script_json_path=artifact.json_path,
            script_py_path=artifact.py_path,
            locator_path=locator_path or artifact.locator_path,
        )

        report_out = TestReportAgent(
            headless=self.headless,
            use_healer=self.use_healer,
            locator_store=self.locator_store,
        ).run(suite, prior_traces=all_traces, artifacts=artifacts)

        return OrchestratorResult(
            report=report_out.report,
            suite=suite,
            traces=report_out.traces,
        )
