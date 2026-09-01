"""Chromium launch helpers for local dev and container hosts (Render, Docker)."""

from __future__ import annotations

import os
from pathlib import Path


def is_container_runtime() -> bool:
    """True when running inside Docker or on Render."""
    if os.getenv("RENDER") == "true":
        return True
    if Path("/.dockerenv").exists():
        return True
    return os.getenv("PLAYWRIGHT_NO_SANDBOX", "").lower() in ("1", "true", "yes")


def chromium_launch_kwargs(*, headless: bool) -> dict:
    """Launch options that work in restricted Linux containers."""
    kwargs: dict = {"headless": headless}
    if is_container_runtime():
        kwargs["args"] = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]
    return kwargs
