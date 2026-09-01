"""Agent 2 — Module Discovery Agent (scan site, map feature → selectors)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from playwright.sync_api import sync_playwright

from src.common.models import AgentTrace, ModuleMap, Step, StepAction, TestSuite


@dataclass
class DiscoveryAgentResult:
    suite: TestSuite
    module_map: ModuleMap
    traces: list[AgentTrace]


class DiscoveryAgent:
    """Open target site, discover interactive elements, enrich step selectors."""

    def __init__(self, *, headless: bool = True, timeout_ms: int = 15000) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms

    def run(self, suite: TestSuite, feature: str) -> DiscoveryAgentResult:
        site_url = suite.base_url or ""
        if not site_url:
            raise ValueError("Discovery requires suite.base_url")

        traces: list[AgentTrace] = [
            AgentTrace(
                agent="discovery_agent",
                phase="start",
                detail=f"Scanning {site_url} for feature '{feature}'",
            )
        ]

        module_map = self._scan_site(site_url, feature)
        traces.append(
            AgentTrace(
                agent="discovery_agent",
                phase="scan",
                detail=f"Discovered {len(module_map.elements)} elements on {len(module_map.page_urls)} page(s)",
            )
        )

        enriched_steps = [self._enrich_step(step, module_map, traces) for step in suite.steps]
        enriched = suite.model_copy(update={"steps": enriched_steps})
        traces.append(
            AgentTrace(
                agent="discovery_agent",
                phase="enrich",
                detail="Mapped discovered selectors onto TestSuite steps",
            )
        )
        return DiscoveryAgentResult(suite=enriched, module_map=module_map, traces=traces)

    def _scan_site(self, site_url: str, feature: str) -> ModuleMap:
        elements: dict[str, str] = {}
        page_urls: list[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            page.set_default_timeout(self.timeout_ms)
            page.goto(site_url)
            page_urls.append(page.url)

            for loc in page.locator("input, textarea, select").all():
                sel = self._selector_for_locator(loc)
                if not sel:
                    continue
                for label in self._labels_for_input(loc, page):
                    elements[self._norm(label)] = sel
                el_id = loc.get_attribute("id") or ""
                el_name = loc.get_attribute("name") or ""
                if el_id:
                    elements[self._norm(el_id)] = sel
                if el_name:
                    elements[self._norm(el_name)] = sel

            for loc in page.locator("button, input[type='submit'], a").all():
                sel = self._selector_for_locator(loc)
                if not sel:
                    continue
                text = (loc.inner_text() or loc.get_attribute("value") or "").strip()
                if text:
                    elements[self._norm(text)] = sel
                el_id = loc.get_attribute("id") or ""
                if el_id:
                    elements[self._norm(el_id)] = sel

            if feature.lower() in ("login", "auth"):
                for key in ("username", "user-name", "password", "login"):
                    if key not in elements:
                        guess = {
                            "username": "#user-name",
                            "user-name": "#user-name",
                            "password": "#password",
                            "login": "#login-button",
                        }.get(key)
                        if guess and page.locator(guess).count():
                            elements[key] = guess

            browser.close()

        return ModuleMap(site_url=site_url, feature=feature, elements=elements, page_urls=page_urls)

    def _enrich_step(self, step: Step, module_map: ModuleMap, traces: list[AgentTrace]) -> Step:
        if step.action not in (StepAction.FILL, StepAction.CLICK, StepAction.SELECT):
            return step
        hint = self._hint_from_step(step)
        if not hint:
            return step
        discovered = self._lookup(module_map.elements, hint)
        if discovered and discovered != step.selector:
            traces.append(
                AgentTrace(
                    agent="discovery_agent",
                    phase="map",
                    detail=f"{step.id}: {step.selector} -> {discovered} (hint: {hint})",
                )
            )
            return step.model_copy(update={"selector": discovered})
        return step

    def _hint_from_step(self, step: Step) -> str:
        desc = (step.description or "").lower()
        if step.action == StepAction.FILL:
            m = re.search(r"fill\s+(.+?)\s+with", desc)
            if m:
                return self._norm(m.group(1))
        if step.action == StepAction.CLICK:
            m = re.search(r"click\s+(?:the\s+)?(.+?)(?:\s+button|\s+link)?$", desc)
            if m:
                return self._norm(m.group(1))
        if step.action == StepAction.SELECT:
            m = re.search(r"from\s+(?:the\s+)?(.+)$", desc)
            if m:
                return self._norm(m.group(1))
        if step.selector and step.selector.startswith("text="):
            return self._norm(step.selector[5:])
        return ""

    def _lookup(self, elements: dict[str, str], hint: str) -> str | None:
        if hint in elements:
            return elements[hint]
        for key, sel in elements.items():
            if hint in key or key in hint:
                return sel
        return None

    def _norm(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def _selector_for_locator(self, loc) -> str | None:
        el_id = loc.get_attribute("id")
        if el_id:
            return f"#{el_id}"
        name = loc.get_attribute("name")
        if name:
            tag = loc.evaluate("el => el.tagName.toLowerCase()")
            return f"{tag}[name='{name}']"
        data_test = loc.get_attribute("data-test")
        if data_test:
            return f"[data-test='{data_test}']"
        return None

    def _labels_for_input(self, loc, page) -> list[str]:
        labels: list[str] = []
        el_id = loc.get_attribute("id")
        if el_id:
            for label_loc in page.locator(f"label[for='{el_id}']").all():
                t = label_loc.inner_text().strip()
                if t:
                    labels.append(t)
        placeholder = loc.get_attribute("placeholder") or ""
        if placeholder:
            labels.append(placeholder)
        aria = loc.get_attribute("aria-label") or ""
        if aria:
            labels.append(aria)
        return labels
