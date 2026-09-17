"""Tests for locator cache, stored scripts, and replay-without-agents."""

from __future__ import annotations

from src.agents.discovery_agent import DiscoveryAgent
from src.agents.orchestrator import AgentOrchestrator
from src.common.models import (
    AgentTrace,
    ArtifactInfo,
    ModuleMap,
    NotifyInfo,
    RunStatus,
    RunSummary,
    Step,
    StepAction,
    StepResult,
    StepStatus,
    StructuredTestPrompt,
    TestReport,
    TestSuite,
)
from src.reuse.locator_store import LocatorStore, hint_from_step
from src.reuse.playwright_gen import generate_playwright_script
from src.reuse.script_store import ScriptStore


def _login_suite() -> TestSuite:
    return TestSuite(
        suite_id="TC01",
        name="Login",
        module="login",
        base_url="https://www.saucedemo.com/",
        steps=[
            Step(id="s1", action=StepAction.GOTO, url="https://www.saucedemo.com/"),
            Step(
                id="s2",
                action=StepAction.FILL,
                selector="text=username",
                value="standard_user",
                description="Fill username with standard_user",
            ),
        ],
    )


def test_locator_store_roundtrip(tmp_path):
    store = LocatorStore(tmp_path)
    saved = store.save(
        ModuleMap(
            site_url="https://www.saucedemo.com/",
            feature="login",
            elements={"username": "#user-name"},
            source="scan",
        )
    )
    assert saved.exists()
    loaded = store.load("https://www.saucedemo.com/", "login")
    assert loaded is not None
    assert loaded.elements["username"] == "#user-name"
    # www. is stripped so the same host reuses the page object
    again = store.load("https://saucedemo.com/", "login")
    assert again is not None
    assert again.elements["username"] == "#user-name"


def test_locator_store_merge_and_heal(tmp_path):
    store = LocatorStore(tmp_path)
    store.save(
        ModuleMap(
            site_url="https://example.com",
            feature="login",
            elements={"username": "#old-user"},
        )
    )
    store.merge_save(
        ModuleMap(
            site_url="https://example.com",
            feature="login",
            elements={"password": "#password"},
        )
    )
    merged = store.load("https://example.com", "login")
    assert merged.elements["username"] == "#old-user"
    assert merged.elements["password"] == "#password"
    store.upsert_selector("https://example.com", "login", "username", "#user-name")
    healed = store.load("https://example.com", "login")
    assert healed.elements["username"] == "#user-name"


def test_discovery_reuses_cached_locators(tmp_path, monkeypatch):
    store = LocatorStore(tmp_path)
    store.save(
        ModuleMap(
            site_url="https://www.saucedemo.com/",
            feature="login",
            elements={"username": "#user-name"},
        )
    )
    agent = DiscoveryAgent(locator_store=store, reuse_locators=True)
    scanned = {"n": 0}

    def fake_scan(*_a, **_k):
        scanned["n"] += 1
        return ModuleMap(site_url="https://www.saucedemo.com/", feature="login", elements={})

    monkeypatch.setattr(agent, "_scan_site", fake_scan)
    result = agent.run(_login_suite(), "login")
    assert scanned["n"] == 0
    assert result.suite.steps[1].selector == "#user-name"
    assert any(t.phase == "cache" for t in result.traces)


def test_discovery_refresh_rescans(tmp_path, monkeypatch):
    store = LocatorStore(tmp_path)
    store.save(
        ModuleMap(
            site_url="https://www.saucedemo.com/",
            feature="login",
            elements={"username": "#stale"},
        )
    )
    agent = DiscoveryAgent(locator_store=store, refresh_locators=True)
    scanned = {"n": 0}

    def fake_scan(url, feature, has_login):
        scanned["n"] += 1
        return ModuleMap(
            site_url=url,
            feature=feature,
            elements={"username": "#user-name"},
            page_urls=[url],
        )

    monkeypatch.setattr(agent, "_scan_site", fake_scan)
    result = agent.run(_login_suite(), "login")
    assert scanned["n"] == 1
    assert result.suite.steps[1].selector == "#user-name"
    assert any(t.phase == "store" for t in result.traces)


def test_script_store_roundtrip(tmp_path):
    store = ScriptStore(tmp_path)
    suite = _login_suite()
    artifact = store.save(suite, feature="login")
    assert artifact.json_path
    loaded = store.load("TC01", "https://www.saucedemo.com/")
    assert loaded is not None
    assert loaded.suite.steps[1].selector == "text=username"
    assert "page.fill" in loaded.playwright_script
    by_id = store.load("TC01")
    assert by_id is not None
    from_path = store.load_path(artifact.json_path)
    assert from_path is not None
    assert from_path.suite.suite_id == "TC01"


def test_generate_playwright_script_contains_actions():
    script = generate_playwright_script(_login_suite())
    assert "page.goto('https://www.saucedemo.com/'" in script
    assert "page.fill('text=username', 'standard_user')" in script
    assert "if __name__ == '__main__':" in script


def test_hint_from_step():
    step = Step(
        id="s2",
        action=StepAction.FILL,
        selector="text=username",
        description="Fill username with standard_user",
    )
    assert hint_from_step(step) == "username"


def test_orchestrator_prefers_stored_script(tmp_path, monkeypatch):
    store = ScriptStore(tmp_path)
    store.save(_login_suite(), feature="login")
    orch = AgentOrchestrator(
        use_llm=False,
        use_discovery=False,
        use_healer=False,
        prefer_replay=True,
        script_store=store,
        locator_store=LocatorStore(tmp_path / "locators"),
    )
    called = {"step": 0, "replay": 0}

    def boom(*_a, **_k):
        called["step"] += 1
        raise AssertionError("StepAgent should not run on replay hit")

    monkeypatch.setattr("src.agents.orchestrator.StepAgent.run", boom)

    def fake_replay(suite, **kwargs):
        called["replay"] += 1
        traces = list(kwargs.get("prior_traces") or [])
        traces.append(AgentTrace(agent="replay", phase="execute", detail="stub"))
        report = TestReport(
            run_id="run_replay",
            suite_id=suite.suite_id,
            status=RunStatus.PASSED,
            started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            finished_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            summary=RunSummary(total=1, passed=1, failed=0, skipped=0),
            steps=[
                StepResult(step_id="s1", action="goto", status=StepStatus.PASSED),
            ],
            notify=NotifyInfo(),
            agent_traces=traces,
            artifacts=kwargs.get("artifacts") or ArtifactInfo(replayed=True),
        )
        return report

    monkeypatch.setattr("src.agents.orchestrator.replay_stored_suite", fake_replay)
    prompt = StructuredTestPrompt(
        test_id="TC01",
        site_url="https://www.saucedemo.com/",
        feature="login",
        test_name="Login",
        objective="Verify login",
        expected_outcome="Products",
        steps=["Fill username with standard_user"],
    )
    result = orch.run(prompt)
    assert called["step"] == 0
    assert called["replay"] == 1
    assert result.report.artifacts.replayed is True
    assert any(t.phase == "hit" for t in result.traces)
