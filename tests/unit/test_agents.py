"""Tests for the combined 3-agent pipeline."""

from __future__ import annotations

from src.agents.discovery_agent import DiscoveryAgent
from src.agents.orchestrator import AgentOrchestrator
from src.agents.step_agent import StepAgent
from src.common.models import ModuleMap, Step, StepAction, StructuredTestPrompt, TestSuite


def test_step_agent_rule_fallback():
    prompt = StructuredTestPrompt(
        test_id="TC01",
        site_url="https://www.saucedemo.com/",
        feature="login",
        test_name="Login",
        objective="Verify login works",
        expected_outcome="Products visible",
        steps=[
            "Fill username with standard_user",
            "Fill password with secret_sauce",
            "Click Login",
        ],
    )
    result = StepAgent().run(prompt, use_llm=False)
    assert len(result.suite.steps) >= 4
    assert result.suite.steps[0].action == StepAction.GOTO
    assert any(t.phase == "generator" for t in result.traces)


def test_discovery_enriches_selectors():
    suite = TestSuite(
        suite_id="T1",
        name="Login",
        module="login",
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
    agent = DiscoveryAgent()
    module_map = ModuleMap(
        site_url="https://www.saucedemo.com/",
        feature="login",
        elements={"username": "#user-name", "login": "#login-button"},
    )
    traces = []
    enriched = agent._enrich_step(suite.steps[0], module_map, traces)
    assert enriched.selector == "#user-name"
    assert traces


def test_orchestrator_builds():
    orch = AgentOrchestrator(use_llm=False, use_discovery=False, use_healer=False)
    assert orch.use_llm is False
