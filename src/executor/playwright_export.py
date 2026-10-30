"""Export TestSuite JSON to a runnable Playwright TypeScript spec."""

from __future__ import annotations

import json
import re

from src.common.models import Step, StepAction, TestSuite


def _ts_string(value: str) -> str:
    return json.dumps(value)


def _locator_expr(selector: str) -> str:
    sel = selector.strip()
    if sel.startswith("text="):
        return f"page.getByText({_ts_string(sel[5:])})"
    if sel.startswith("role="):
        return f"page.locator({_ts_string(sel)})"
    return f"page.locator({_ts_string(sel)})"


def step_to_playwright_lines(step: Step) -> list[str]:
    action = step.action
    lines: list[str] = []
    desc = (step.description or step.id).replace("*/", "* /")
    lines.append(f"  // {desc}")

    if action == StepAction.GOTO:
        url = step.url or step.value or ""
        lines.append(f"  await page.goto({_ts_string(url)});")
    elif action == StepAction.FILL:
        loc = _locator_expr(step.selector or "body")
        lines.append(f"  await {loc}.fill({_ts_string(step.value or '')});")
    elif action == StepAction.CLICK:
        loc = _locator_expr(step.selector or "body")
        lines.append(f"  await {loc}.click();")
    elif action == StepAction.SELECT:
        loc = _locator_expr(step.selector or "select")
        lines.append(f"  await {loc}.selectOption({_ts_string(step.value or '')});")
    elif action == StepAction.ASSERT_TEXT:
        expected = step.expected or step.value or ""
        if step.selector:
            loc = _locator_expr(step.selector)
            lines.append(f"  await expect({loc}).toContainText({_ts_string(expected)});")
        else:
            lines.append(f"  await expect(page.getByText({_ts_string(expected)})).toBeVisible();")
    elif action == StepAction.ASSERT_URL:
        expected = step.expected or step.value or ""
        lines.append(f"  await expect(page).toHaveURL(/{re.escape(expected)}/);")
    elif action == StepAction.ASSERT_VISIBLE:
        loc = _locator_expr(step.selector or step.expected or "body")
        lines.append(f"  await expect({loc}).toBeVisible();")
    elif action == StepAction.WAIT:
        ms = step.timeout_ms or 1000
        lines.append(f"  await page.waitForTimeout({ms});")
    elif action in (StepAction.CLEAR_COOKIES, StepAction.CLEAR_STORAGE):
        lines.append("  await page.context().clearCookies();")
        lines.append(
            "  await page.evaluate(() => { localStorage.clear(); sessionStorage.clear(); });"
        )
    else:
        lines.append(f"  // unsupported action: {action.value}")
    return lines


def suite_to_playwright_spec(suite: TestSuite) -> str:
    """Generate Playwright Test .spec.ts source from cached TestSuite JSON."""
    safe_name = re.sub(r"[^\w\s-]", "", suite.name or suite.suite_id)[:80].strip() or suite.suite_id
    header = [
        "import { test, expect } from '@playwright/test';",
        "",
        f"test({_ts_string(safe_name)}, async ({{ page }}) => {{",
    ]
    body: list[str] = []
    for step in suite.steps:
        body.extend(step_to_playwright_lines(step))
    footer = ["});", ""]
    return "\n".join(header + body + footer)
