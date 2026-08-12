"""Tests for structured test prompt validation and conversion."""

from __future__ import annotations

import pytest

from src.agent.structured_prompt import structured_prompt_to_suite
from src.common.models import StructuredTestPrompt, StepAction


def test_structured_prompt_requires_fields():
    with pytest.raises(Exception):
        StructuredTestPrompt(
            test_id="T1",
            site_url="https://example.com",
            feature="login",
            test_name="x",
            objective="x",
            expected_outcome="x",
            steps=[],
        )


def test_structured_prompt_auto_opens_site():
    prompt = StructuredTestPrompt(
        test_id="TC01",
        site_url="https://www.saucedemo.com/",
        feature="login",
        test_name="Login",
        objective="Verify login",
        expected_outcome="Products visible",
        steps=[
            "Fill username with standard_user",
            "Click Login",
        ],
    )
    suite = structured_prompt_to_suite(prompt)
    assert suite.base_url == "https://www.saucedemo.com/"
    assert suite.steps[0].action == StepAction.GOTO
    assert suite.steps[0].url == "https://www.saucedemo.com/"
    assert suite.objective == "Verify login"


def test_structured_rejects_bad_step():
    prompt = StructuredTestPrompt(
        test_id="TC02",
        site_url="https://www.saucedemo.com/",
        feature="login",
        test_name="Bad",
        objective="x",
        expected_outcome="x",
        steps=["do something random without pattern"],
    )
    with pytest.raises(ValueError, match="Unrecognized step"):
        structured_prompt_to_suite(prompt)
