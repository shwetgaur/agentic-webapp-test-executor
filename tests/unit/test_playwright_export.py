"""Playwright spec export from TestSuite JSON."""

from src.common.models import Step, StepAction, TestSuite
from src.executor.playwright_export import suite_to_playwright_spec


def test_suite_to_playwright_spec_includes_goto_and_fill():
    suite = TestSuite(
        suite_id="TC01",
        name="Login",
        base_url="https://example.com",
        steps=[
            Step(id="s1", action=StepAction.GOTO, url="https://example.com/login"),
            Step(id="s2", action=StepAction.FILL, selector="#user", value="alice"),
            Step(id="s3", action=StepAction.CLICK, selector="#submit"),
        ],
    )
    text = suite_to_playwright_spec(suite)
    assert "page.goto" in text
    assert "#user" in text
    assert "@playwright/test" in text
