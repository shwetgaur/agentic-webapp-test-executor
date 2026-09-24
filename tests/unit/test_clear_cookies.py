"""Tests for cookie/storage clearance step actions."""

from __future__ import annotations

from src.agent.parser import parse_plain_text_case
from src.common.models import StepAction


def test_parser_clear_cookies_step():
    suite = parse_plain_text_case("1. Clear cookies\n2. Open https://example.com")
    actions = [s.action for s in suite.steps]
    assert StepAction.CLEAR_COOKIES in actions


def test_parser_clear_storage_step():
    suite = parse_plain_text_case("1. Clear browser storage")
    assert suite.steps[0].action == StepAction.CLEAR_STORAGE
