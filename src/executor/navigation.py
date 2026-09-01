"""Shared Playwright navigation defaults for slow marketing sites."""

from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from src.common.settings import settings


def navigate(page: Page, url: str, *, timeout_ms: int | None = None) -> None:
    """
    Open a URL using settings tuned for heavy pages (e.g. Zoho marketing sites).

    Uses domcontentloaded instead of load so third-party scripts cannot block the test.
    Retries once with a lighter wait if the first navigation times out.
    """
    timeout = timeout_ms or settings.navigation_timeout_ms
    wait_until = settings.goto_wait_until
    try:
        page.goto(url, wait_until=wait_until, timeout=timeout)
    except PlaywrightTimeoutError:
        page.goto(url, wait_until="commit", timeout=timeout)
