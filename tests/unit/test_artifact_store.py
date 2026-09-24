"""Tests for locator cache and suite replay storage."""

from __future__ import annotations

from src.agents.artifact_store import LocatorStore, SuiteStore, locator_cache_key
from src.common.models import ModuleMap, Step, StepAction, TestSuite


def test_locator_cache_key_normalizes_host():
    key = locator_cache_key("https://www.saucedemo.com/", "Login")
    assert "saucedemo" in key
    assert "login" in key


def test_locator_store_save_and_load(tmp_path):
    store = LocatorStore(tmp_path)
    module_map = ModuleMap(
        site_url="https://www.saucedemo.com/",
        feature="login",
        elements={"username": "#user-name", "password": "#password"},
    )
    store.save(module_map)
    loaded = store.load("https://www.saucedemo.com/", "login")
    assert loaded is not None
    assert loaded.elements["username"] == "#user-name"


def test_locator_store_merge_elements(tmp_path):
    store = LocatorStore(tmp_path)
    store.save(
        ModuleMap(
            site_url="https://example.com",
            feature="auth",
            elements={"email": "#email"},
        )
    )
    store.merge_elements("https://example.com", "auth", {"password": "#pass"})
    loaded = store.load("https://example.com", "auth")
    assert loaded is not None
    assert loaded.elements["email"] == "#email"
    assert loaded.elements["password"] == "#pass"


def test_suite_store_latest_roundtrip(tmp_path):
    store = SuiteStore(tmp_path)
    suite = TestSuite(
        suite_id="TC01",
        name="Login",
        base_url="https://www.saucedemo.com/",
        steps=[
            Step(id="s1", action=StepAction.GOTO, url="https://www.saucedemo.com/"),
        ],
    )
    store.save_latest("TC01", suite, run_id="run-abc")
    loaded = store.load_latest("TC01")
    assert loaded is not None
    assert loaded.suite_id == "TC01"
    assert store.has_latest("TC01")
    assert not store.has_latest("MISSING")
