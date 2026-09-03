"""Tests for failure screenshot API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.backend.app import app

client = TestClient(app)


def test_get_screenshot_not_found():
    res = client.get("/api/v1/screenshots/run_nonexistent_s1.png")
    assert res.status_code == 404


def test_get_screenshot_rejects_invalid_filename():
    res = client.get("/api/v1/screenshots/not-a-png.txt")
    assert res.status_code == 400
