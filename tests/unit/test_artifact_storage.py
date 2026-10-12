"""Tests for GCS/local artifact backends."""

from __future__ import annotations

from src.agents.artifact_storage import LocalArtifactBackend, reset_artifact_backend_for_tests
from src.agents.artifact_store import LocatorStore, SuiteStore
from src.common.models import ModuleMap, Step, StepAction, TestSuite


def test_local_backend_roundtrip(tmp_path):
    backend = LocalArtifactBackend(tmp_path)
    backend.write_text("locators/foo.json", '{"a": 1}')
    assert backend.read_text("locators/foo.json") == '{"a": 1}'
    assert backend.exists("locators/foo.json")


def test_locator_store_uses_storage_key(tmp_path, monkeypatch):
    from src.agents import artifact_storage

    backend = LocalArtifactBackend(tmp_path / "data")
    monkeypatch.setattr(artifact_storage, "_backend", backend)
    store = LocatorStore(tmp_path / "data" / "locators")
    store.save(
        ModuleMap(site_url="https://example.com", feature="login", elements={"email": "#e"})
    )
    assert backend.exists("locators/example.com_login.json")
    loaded = store.load("https://example.com", "login")
    assert loaded is not None
    assert loaded.elements["email"] == "#e"
    reset_artifact_backend_for_tests()


def test_suite_upload_roundtrip(tmp_path, monkeypatch):
    from src.agents import artifact_storage

    backend = LocalArtifactBackend(tmp_path / "data")
    monkeypatch.setattr(artifact_storage, "_backend", backend)
    store = SuiteStore(tmp_path / "data" / "suites")
    suite = TestSuite(
        suite_id="TC_UPLOAD",
        name="Upload test",
        steps=[Step(id="s1", action=StepAction.GOTO, url="https://example.com")],
    )
    store.save_latest("TC_UPLOAD", suite)
    assert backend.exists("suites/tc_upload_latest.json")
    loaded = store.load_latest("TC_UPLOAD")
    assert loaded is not None
    assert loaded.suite_id == "TC_UPLOAD"
    reset_artifact_backend_for_tests()
