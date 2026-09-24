"""Tests for discovery locator cache reuse."""

from __future__ import annotations

from src.agents.artifact_store import LocatorStore
from src.agents.discovery_agent import DiscoveryAgent
from src.common.models import ModuleMap, Step, StepAction, TestSuite


def test_discovery_uses_locator_cache(tmp_path):
    store = LocatorStore(tmp_path)
    store.save(
        ModuleMap(
            site_url="https://www.saucedemo.com/",
            feature="login",
            elements={"username": "#user-name", "password": "#password", "login": "#login-button"},
        )
    )
    suite = TestSuite(
        suite_id="T1",
        name="Login",
        base_url="https://www.saucedemo.com/",
        steps=[
            Step(
                id="s2",
                action=StepAction.FILL,
                selector="text=username",
                value="standard_user",
                description="Fill username with standard_user",
            )
        ],
    )
    agent = DiscoveryAgent(locator_store=store)
    result = agent.run(suite, "login")
    assert any(t.phase == "cache_hit" for t in result.traces)
    assert result.suite.steps[0].selector == "#user-name"
