"""Tests for locator cache download API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.agents.artifact_store import LocatorStore
from src.backend.app import app
from src.common.models import ModuleMap

client = TestClient(app)


def test_get_locator_cache_not_found():
    res = client.get(
        "/api/v1/locators",
        params={"site_url": "https://example.com/", "feature": "login"},
    )
    assert res.status_code == 404


def test_get_locator_cache_requires_params():
    res = client.get("/api/v1/locators", params={"site_url": "https://example.com/"})
    assert res.status_code == 422


def test_locator_cache_roundtrip_via_api(tmp_path, monkeypatch):
    store = LocatorStore(tmp_path)
    monkeypatch.setattr("src.backend.app.LocatorStore", lambda: store)

    module_map = ModuleMap(
        site_url="https://accounts.zoho.com/signin",
        feature="login",
        elements={"email": "#login_id", "password": "#password"},
        page_urls=["https://accounts.zoho.com/signin"],
    )
    store.save(module_map)

    exists = client.get(
        "/api/v1/locators/exists",
        params={"site_url": "https://accounts.zoho.com/signin", "feature": "login"},
    )
    assert exists.status_code == 200
    body = exists.json()
    assert body["cached"] is True
    assert "accounts.zoho.com" in body["cache_key"]

    res = client.get(
        "/api/v1/locators",
        params={"site_url": "https://accounts.zoho.com/signin", "feature": "login"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["elements"]["email"] == "#login_id"
    assert data["elements"]["password"] == "#password"
