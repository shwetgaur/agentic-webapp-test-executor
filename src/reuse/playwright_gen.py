"""Render an enriched TestSuite as a standalone Playwright Python script."""

from __future__ import annotations

from src.common.models import Step, StepAction, TestSuite


def generate_playwright_script(suite: TestSuite) -> str:
    """Produce a replayable Playwright script from stored steps (no agents)."""
    lines = [
        '"""Auto-generated Playwright replay script.',
        f"Suite: {suite.suite_id} — {suite.name}",
        f"Site: {suite.base_url or 'n/a'}  Feature: {suite.module or 'n/a'}",
        "Replay this file with: python <this-file>.py",
        "Do not re-run the agent pipeline unless locators need a refresh.",
        '"""',
        "",
        "from playwright.sync_api import sync_playwright",
        "",
        "",
        "def run() -> None:",
        "    with sync_playwright() as p:",
        "        browser = p.chromium.launch(headless=True)",
        "        page = browser.new_page()",
        "        page.set_default_timeout(30000)",
        "",
    ]
    for step in suite.steps:
        label = step.description or step.action.value
        lines.append(f"        # {step.id}: {label}")
        lines.append(f"        {_emit_step(step)}")
        lines.append("")
    lines.extend(
        [
            "        browser.close()",
            "",
            "",
            "if __name__ == '__main__':",
            "    run()",
            "",
        ]
    )
    return "\n".join(lines)


def _emit_step(step: Step) -> str:
    action = step.action
    if action == StepAction.GOTO:
        return f"page.goto({(step.url or '')!r}, wait_until='domcontentloaded')"
    if action == StepAction.FILL:
        return f"page.fill({(step.selector or '')!r}, {(step.value or '')!r})"
    if action == StepAction.CLICK:
        return f"page.click({(step.selector or '')!r})"
    if action == StepAction.SELECT:
        return f"page.select_option({(step.selector or '')!r}, label={(step.value or '')!r})"
    if action == StepAction.HOVER:
        return f"page.hover({(step.selector or '')!r})"
    if action == StepAction.PRESS_KEY:
        return f"page.keyboard.press({(step.key or 'Enter')!r})"
    if action == StepAction.WAIT:
        return f"page.wait_for_timeout({step.timeout_ms or 1000})"
    if action == StepAction.ASSERT_TEXT:
        return (
            f"page.get_by_text({(step.expected or '')!r}, exact=False)"
            ".first.wait_for(state='visible')"
        )
    if action == StepAction.ASSERT_URL:
        return f"assert {(step.expected or '')!r} in page.url"
    if action == StepAction.ASSERT_VISIBLE:
        return f"assert page.locator({(step.selector or '')!r}).is_visible()"
    if action == StepAction.SCREENSHOT:
        return f"page.screenshot(path='{step.id}.png')"
    return f"raise NotImplementedError({action.value!r})"
