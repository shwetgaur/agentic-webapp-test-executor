"""Tests for flexible natural-language step parsing."""

from __future__ import annotations

from src.agent.flexible_steps import (
    clean_url_fragment,
    normalize_llm_suite,
    normalize_step,
    parse_flexible_line,
    suite_from_natural_steps,
)
from src.common.models import Step, StepAction, StructuredTestPrompt, TestSuite


def test_parse_zoho_url_step():
    step = parse_flexible_line("s1", "verify url contains zoho.com")
    assert step is not None
    assert step.action == StepAction.ASSERT_URL
    assert step.expected == "zoho.com"


def test_parse_zoho_text_step_natural_wording():
    step = parse_flexible_line("s2", "verify that the zoho text is visible")
    assert step is not None
    assert step.action == StepAction.ASSERT_TEXT
    assert step.expected == "zoho"


def test_clean_url_fragment_strips_contains_prefix():
    assert clean_url_fragment("contains zoho.com") == "zoho.com"
    assert clean_url_fragment("url contains zoho.com") == "zoho.com"


def test_normalize_llm_assert_url_mistake():
    bad = Step(
        id="s2",
        action=StepAction.ASSERT_URL,
        expected="contains zoho.com",
        description="Verify the current URL contains 'zoho.com'",
    )
    fixed = normalize_step(bad, source_line="verify url contains zoho.com")
    assert fixed.expected == "zoho.com"


def test_normalize_llm_suite_for_zoho_prompt():
    prompt = StructuredTestPrompt(
        test_id="ZOHO_TC01_homepage",
        site_url="https://www.zoho.com/",
        feature="navigation",
        test_name="Zoho homepage loads",
        objective="Verify Zoho marketing homepage opens and shows brand content",
        expected_outcome="Homepage loads with Zoho-related visible text",
        steps=[
            "verify url contains zoho.com",
            "verify that the zoho text is visible",
        ],
    )
    llm_suite = TestSuite(
        suite_id="ZOHO_TC01_homepage",
        name="Zoho homepage loads",
        module="navigation",
        base_url="https://www.zoho.com/",
        steps=[
            Step(id="s1", action=StepAction.GOTO, url="https://www.zoho.com/", description="Open"),
            Step(
                id="s2",
                action=StepAction.ASSERT_URL,
                expected="contains zoho.com",
                description="Verify the current URL contains 'zoho.com'",
            ),
            Step(
                id="s3",
                action=StepAction.ASSERT_TEXT,
                expected="the zoho text",
                description="Verify that the text 'Zoho' is visible on the page",
            ),
        ],
    )
    suite = normalize_llm_suite(llm_suite, prompt, source_lines=prompt.steps)
    assert suite.steps[1].expected == "zoho.com"
    assert suite.steps[2].expected == "zoho"


def test_suite_from_natural_steps_auto_opens_site():
    prompt = StructuredTestPrompt(
        test_id="ZOHO_TC01_homepage",
        site_url="https://www.zoho.com/",
        feature="navigation",
        test_name="Zoho homepage loads",
        objective="Verify homepage",
        expected_outcome="Zoho visible",
        steps=[
            "verify url contains zoho.com",
            "verify that the zoho text is visible",
        ],
    )
    suite = suite_from_natural_steps(prompt, prompt.steps)
    assert suite.steps[0].action == StepAction.GOTO
    assert suite.steps[1].expected == "zoho.com"
    assert suite.steps[2].expected == "zoho"
