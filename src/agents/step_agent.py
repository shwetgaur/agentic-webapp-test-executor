"""Agent 1 — Test Step Agent (Planner + Generator with rule fallback)."""

from __future__ import annotations

from dataclasses import dataclass

from src.agent.flexible_steps import normalize_llm_suite, suite_from_natural_steps
from src.agent.structured_prompt import structured_prompt_to_suite
from src.agents.llm_client import LLMClient
from src.common.models import AgentTrace, StructuredTestPrompt, TestSuite

_PLANNER_SYSTEM = """You are a QA test planner. The user writes natural-language test steps — keep their wording style.
Return ONLY a JSON array of strings — one executable step per line.
Preserve phrases like "verify url contains …", "verify that the X text is visible", "fill … with …".
Add an Open URL step only if the list does not already start with navigation.
Do not add markdown or explanation."""

_GENERATOR_SYSTEM = """You are a test step generator. Convert natural-language test steps into JSON for browser automation.
Return ONLY valid JSON with this shape:
{
  "suite_id": "string",
  "name": "string",
  "module": "string",
  "base_url": "string",
  "steps": [
    {"id": "s1", "action": "goto|fill|click|select|assert_text|assert_url", "url": "...", "selector": "...", "value": "...", "expected": "...", "description": "..."}
  ]
}

CRITICAL rules for expected fields:
- assert_url: expected must be ONLY the URL fragment to search for (e.g. "zoho.com"), NEVER include the word "contains".
  Example: step "verify url contains zoho.com" -> {"action":"assert_url","expected":"zoho.com"}
- assert_text: expected must be ONLY the visible text (e.g. "Zoho"), not the full sentence.
  Example: step "verify that the zoho text is visible" -> {"action":"assert_text","expected":"Zoho"}
- goto needs url; fill/click/select need selector; copy the original step text into description."""


@dataclass
class StepAgentResult:
    suite: TestSuite
    refined_steps: list[str]
    traces: list[AgentTrace]


class StepAgent:
    """Validate prompt, plan/refine steps (Planner), parse to TestSuite (Generator)."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    def run(self, prompt: StructuredTestPrompt, *, use_llm: bool = True) -> StepAgentResult:
        traces: list[AgentTrace] = [
            AgentTrace(
                agent="step_agent",
                phase="validate",
                detail=f"Validated structured prompt {prompt.test_id}",
            )
        ]

        steps = list(prompt.steps)
        if use_llm and self.llm.is_available():
            planned = self._plan_steps(prompt)
            if planned:
                steps = planned
                traces.append(
                    AgentTrace(
                        agent="step_agent",
                        phase="planner",
                        detail=f"LLM refined {len(steps)} steps for objective: {prompt.objective[:80]}",
                    )
                )
            else:
                traces.append(
                    AgentTrace(
                        agent="step_agent",
                        phase="planner",
                        detail="LLM planner skipped; using original steps",
                    )
                )
        else:
            traces.append(
                AgentTrace(
                    agent="step_agent",
                    phase="planner",
                    detail="Rule-based planner (LLM unavailable or disabled)",
                )
            )

        working_prompt = prompt.model_copy(update={"steps": steps})

        if use_llm and self.llm.is_available():
            suite = self._generate_suite_llm(working_prompt)
            if suite:
                suite = normalize_llm_suite(suite, working_prompt, source_lines=steps)
                traces.append(
                    AgentTrace(
                        agent="step_agent",
                        phase="generator",
                        detail=f"LLM generated TestSuite with {len(suite.steps)} steps (normalized)",
                    )
                )
                return StepAgentResult(suite=suite, refined_steps=steps, traces=traces)

        suite = structured_prompt_to_suite(working_prompt)
        traces.append(
            AgentTrace(
                agent="step_agent",
                phase="generator",
                detail=f"Rule parser produced TestSuite with {len(suite.steps)} steps",
            )
        )
        return StepAgentResult(suite=suite, refined_steps=steps, traces=traces)

    def _plan_steps(self, prompt: StructuredTestPrompt) -> list[str] | None:
        user = (
            f"Site: {prompt.site_url}\nFeature: {prompt.feature}\n"
            f"Objective: {prompt.objective}\nExpected: {prompt.expected_outcome}\n"
            f"Steps:\n" + "\n".join(f"- {s}" for s in prompt.steps)
        )
        try:
            data = self.llm.chat_json(_PLANNER_SYSTEM, user)
        except Exception:
            return None
        if isinstance(data, list) and all(isinstance(x, str) for x in data) and data:
            return [s.strip() for s in data if s.strip()]
        return None

    def _generate_suite_llm(self, prompt: StructuredTestPrompt) -> TestSuite | None:
        user = (
            f"test_id: {prompt.test_id}\nname: {prompt.test_name}\nmodule: {prompt.feature}\n"
            f"base_url: {prompt.site_url}\nobjective: {prompt.objective}\n"
            f"steps:\n" + "\n".join(prompt.steps)
        )
        try:
            data = self.llm.chat_json(_GENERATOR_SYSTEM, user)
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        try:
            data.setdefault("suite_id", prompt.test_id)
            data.setdefault("name", prompt.test_name)
            data.setdefault("module", prompt.feature)
            data.setdefault("base_url", prompt.site_url)
            suite = TestSuite.model_validate(data)
            return suite.model_copy(
                update={
                    "objective": prompt.objective,
                    "expected_outcome": prompt.expected_outcome,
                    "environment": prompt.environment.value,
                }
            )
        except Exception:
            # LLM JSON invalid — fall back to flexible natural-language parser.
            try:
                return suite_from_natural_steps(prompt, prompt.steps)
            except ValueError:
                return None
