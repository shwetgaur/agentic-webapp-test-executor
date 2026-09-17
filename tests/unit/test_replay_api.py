"""API tests for stored-script replay endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.backend.app import app

client = TestClient(app)


def test_replay_missing_suite_returns_404():
    res = client.post("/api/v1/run/replay", json={"suite_id": "NO_SUCH_SUITE"})
    assert res.status_code == 404


def test_replay_requires_source():
    res = client.post("/api/v1/run/replay", json={})
    assert res.status_code == 400


def test_get_script_missing_returns_404():
    res = client.get("/api/v1/scripts/NO_SUCH_SUITE")
    assert res.status_code == 404


def test_get_locators_missing_returns_404():
    res = client.get(
        "/api/v1/locators",
        params={"site_url": "https://example.invalid/", "feature": "login"},
    )
    assert res.status_code == 404
