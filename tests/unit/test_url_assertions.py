"""Tests for redirect-aware URL assertions."""

from __future__ import annotations

from src.executor.url_assertions import url_matches


def test_direct_substring_match():
    assert url_matches("https://projects.zoho.com/portal", "projects.zoho.com")


def test_zoho_subdomain_to_path_redirect():
    assert url_matches("https://www.zoho.com/projects/", "projects.zoho.com")
    assert url_matches("https://zoho.com/projects", "projects.zoho.com")


def test_no_false_positive():
    assert not url_matches("https://example.com/", "projects.zoho.com")
