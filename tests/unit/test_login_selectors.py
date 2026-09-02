"""Tests for login selector helpers and discovery URL selection."""

from __future__ import annotations

from src.agent.parser import _guess_selector
from src.agent.selectors import login_field_selector_candidates
from src.agents.discovery_agent import _discovery_scan_urls
from src.common.models import Step, StepAction, TestSuite


def test_email_guess_uses_login_id_not_text():
    assert _guess_selector("email") == "#login_id"
    assert "#login_id" in login_field_selector_candidates("email")


def test_discovery_scans_all_goto_urls():
    suite = TestSuite(
        suite_id="ZOHO_TC05",
        name="Projects portal",
        base_url="https://projects.zoho.com/",
        steps=[
            Step(id="s1", action=StepAction.GOTO, url="https://accounts.zoho.com/signin"),
            Step(id="s2", action=StepAction.FILL, selector="#login_id", value="x", description="fill email with x"),
            Step(id="s5", action=StepAction.GOTO, url="https://projects.zoho.com/"),
        ],
    )
    urls = _discovery_scan_urls(suite)
    assert "https://accounts.zoho.com/signin" in urls
    assert "https://projects.zoho.com/" in urls
    assert urls.index("https://accounts.zoho.com/signin") < urls.index("https://projects.zoho.com/")
