"""Persist Discovery Agent selectors per website + feature (page-object cache)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from src.common.models import ModuleMap, Step, StepAction

_UNSAFE = re.compile(r"[^a-z0-9._-]+")


def site_host(url: str | None) -> str:
    if not url:
        return "unknown"
    parsed = urlparse(url)
    host = (parsed.netloc or parsed.path.split("/")[0]).lower()
    if host.startswith("www."):
        host = host[4:]
    return host or "unknown"


def feature_slug(feature: str | None) -> str:
    slug = _UNSAFE.sub("-", (feature or "default").strip().lower()).strip("-")
    return slug or "default"


def locator_stem(site_url: str | None, feature: str | None) -> str:
    return f"{site_host(site_url)}__{feature_slug(feature)}"


def hint_from_step(step: Step) -> str:
    """Normalize a fill/click/select step into a page-object key."""
    desc = (step.description or "").lower()
    if step.action == StepAction.FILL:
        m = re.search(r"fill\s+(.+?)\s+with", desc)
        if m:
            return _norm(m.group(1))
    if step.action == StepAction.CLICK:
        m = re.search(r"click\s+(?:the\s+)?(.+?)(?:\s+button|\s+link)?$", desc)
        if m:
            return _norm(m.group(1))
    if step.action == StepAction.SELECT:
        m = re.search(r"from\s+(?:the\s+)?(.+)$", desc)
        if m:
            return _norm(m.group(1))
    if step.selector and step.selector.startswith("text="):
        return _norm(step.selector[5:])
    return ""


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


class LocatorStore:
    """File-backed page object: host + feature → hint → selector."""

    def __init__(self, root: str | Path = "data/locators") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, site_url: str | None, feature: str | None) -> Path:
        return self.root / f"{locator_stem(site_url, feature)}.json"

    def load(self, site_url: str | None, feature: str | None) -> ModuleMap | None:
        path = self.path_for(site_url, feature)
        if not path.is_file():
            return None
        try:
            return ModuleMap.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def save(self, module_map: ModuleMap) -> Path:
        updated = module_map.model_copy(
            update={
                "updated_at": datetime.now(timezone.utc),
                "source": module_map.source or "discovery",
            }
        )
        path = self.path_for(updated.site_url, updated.feature)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated.model_dump_json(indent=2), encoding="utf-8")
        return path

    def merge_save(self, module_map: ModuleMap) -> Path:
        existing = self.load(module_map.site_url, module_map.feature)
        if not existing:
            return self.save(module_map)
        merged_elements = dict(existing.elements)
        merged_elements.update(module_map.elements)
        page_urls = list(dict.fromkeys([*existing.page_urls, *module_map.page_urls]))
        merged = module_map.model_copy(update={"elements": merged_elements, "page_urls": page_urls})
        return self.save(merged)

    def upsert_selector(
        self, site_url: str | None, feature: str | None, hint: str, selector: str
    ) -> Path | None:
        if not hint or not selector or not site_url:
            return None
        existing = self.load(site_url, feature) or ModuleMap(
            site_url=site_url,
            feature=feature or "default",
            elements={},
            source="healer",
        )
        elements = dict(existing.elements)
        elements[hint] = selector
        return self.save(existing.model_copy(update={"elements": elements, "source": "healer"}))
