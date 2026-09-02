"""Healer — Playwright-inspired locator recovery on step failure."""

from __future__ import annotations

import json
import re
from typing import Optional

from src.agent.selectors import login_field_selector_candidates
from src.agents.llm_client import LLMClient
from src.common.models import AgentTrace, Step, StepAction

_HEALER_SYSTEM = """You fix broken web test locators. Given a failed step, error, and page element list, return ONLY JSON:
{"selector": "css or text selector", "action": "fill|click|select|assert_text|assert_url|goto", "value": "optional", "expected": "optional"}
Prefer stable selectors: #id, [data-test], short css. Use text= only if needed."""


class HealerAgent:
    """Suggest an alternate selector when a step fails (LLM + rule fallback)."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()
        self.traces: list[AgentTrace] = []

    def heal(self, step: Step, page, error: str) -> Optional[Step]:
        self.traces = []
        if step.action not in (StepAction.FILL, StepAction.CLICK, StepAction.SELECT, StepAction.ASSERT_VISIBLE):
            return None

        healed = self._heal_rules(step, page)
        if healed:
            self.traces.append(
                AgentTrace(
                    agent="test_report_agent",
                    phase="healer",
                    detail=f"{step.id}: rule heal -> {healed.selector}",
                )
            )
            return healed

        if self.llm.is_available():
            healed = self._heal_llm(step, page, error)
            if healed:
                self.traces.append(
                    AgentTrace(
                        agent="test_report_agent",
                        phase="healer",
                        detail=f"{step.id}: LLM heal -> {healed.selector}",
                    )
                )
                return healed

        self.traces.append(
            AgentTrace(
                agent="test_report_agent",
                phase="healer",
                detail=f"{step.id}: heal failed — {error[:120]}",
            )
        )
        return None

    def _heal_rules(self, step: Step, page) -> Optional[Step]:
        label = self._label_from_step(step)
        if not label:
            return None

        if step.action == StepAction.FILL:
            for sel in login_field_selector_candidates(label):
                try:
                    loc = page.locator(sel).first
                    if loc.count() and loc.is_visible():
                        return step.model_copy(update={"selector": sel})
                except Exception:
                    continue
            try:
                loc = page.get_by_label(re.compile(label, re.I))
                if loc.count() and loc.first.is_visible():
                    return step.model_copy(update={"selector": f"text={label}"})
            except Exception:
                pass
            try:
                loc = page.get_by_placeholder(re.compile(label, re.I))
                if loc.count() and loc.first.is_visible():
                    return step.model_copy(update={"selector": f"text={label}"})
            except Exception:
                pass
            return None

        candidates = [
            f"text={label}",
            f"text={label.title()}",
        ]
        if step.action == StepAction.CLICK:
            try:
                loc = page.get_by_role("button", name=re.compile(label, re.I))
                if loc.count():
                    return step.model_copy(update={"selector": f"text={label}"})
            except Exception:
                pass

        for sel in candidates:
            try:
                if page.locator(sel).count():
                    return step.model_copy(update={"selector": sel})
            except Exception:
                continue
        return None

    def _heal_llm(self, step: Step, page, error: str) -> Optional[Step]:
        elements = self._collect_elements(page)
        user = json.dumps(
            {
                "failed_step": step.model_dump(),
                "error": error,
                "elements": elements[:40],
            },
            indent=2,
        )
        data = self.llm.chat_json(_HEALER_SYSTEM, user)
        if not isinstance(data, dict) or not data.get("selector"):
            return None
        try:
            updates = {"selector": data["selector"]}
            if data.get("value") is not None:
                updates["value"] = data["value"]
            if data.get("expected") is not None:
                updates["expected"] = data["expected"]
            return step.model_copy(update=updates)
        except Exception:
            return None

    def _label_from_step(self, step: Step) -> str:
        desc = step.description or ""
        m = re.search(r"fill\s+(.+?)\s+with", desc, re.I)
        if m:
            return m.group(1).strip()
        m = re.search(r"click\s+(?:the\s+)?(.+?)(?:\s+button|\s+link)?$", desc, re.I)
        if m:
            return m.group(1).strip()
        if step.selector and step.selector.startswith("text="):
            return step.selector[5:]
        return ""

    def _collect_elements(self, page) -> list[dict]:
        out: list[dict] = []
        for loc in page.locator("input, button, a, select").all()[:30]:
            try:
                out.append(
                    {
                        "tag": loc.evaluate("el => el.tagName"),
                        "id": loc.get_attribute("id"),
                        "name": loc.get_attribute("name"),
                        "text": (loc.inner_text() or "")[:60],
                        "data_test": loc.get_attribute("data-test"),
                    }
                )
            except Exception:
                continue
        return out
