"""Persist discovery locators and enriched TestSuites for reuse and replay."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from src.common.models import ModuleMap, TestSuite


def _safe_slug(text: str) -> str:
    return re.sub(r"[^\w.-]", "_", text.strip().lower())


def locator_cache_key(site_url: str, feature: str) -> str:
    host = urlparse(site_url).netloc.replace(":", "_") or "unknown"
    return f"{_safe_slug(host)}_{_safe_slug(feature)}"


def suite_cache_key(test_id: str) -> str:
    return _safe_slug(test_id)


class LocatorStore:
    """Page-object style cache: site + feature → selector map."""

    def __init__(self, base_dir: str | Path = "data/locators") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, site_url: str, feature: str) -> Path:
        return self.base_dir / f"{locator_cache_key(site_url, feature)}.json"

    def load(self, site_url: str, feature: str) -> ModuleMap | None:
        path = self.path_for(site_url, feature)
        if not path.is_file():
            return None
        return ModuleMap.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, module_map: ModuleMap) -> Path:
        path = self.path_for(module_map.site_url, module_map.feature)
        path.write_text(module_map.model_dump_json(indent=2), encoding="utf-8")
        return path

    def merge_elements(self, site_url: str, feature: str, updates: dict[str, str]) -> Path:
        existing = self.load(site_url, feature)
        if existing:
            merged = {**existing.elements, **updates}
            return self.save(existing.model_copy(update={"elements": merged}))
        return self.save(ModuleMap(site_url=site_url, feature=feature, elements=updates))


class SuiteStore:
    """Store enriched TestSuite JSON for replay without re-running agents."""

    def __init__(self, base_dir: str | Path = "data/suites") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def latest_path(self, test_id: str) -> Path:
        return self.base_dir / f"{suite_cache_key(test_id)}_latest.json"

    def run_path(self, test_id: str, run_id: str) -> Path:
        safe_run = re.sub(r"[^\w.-]", "_", run_id)
        return self.base_dir / f"{suite_cache_key(test_id)}_{safe_run}.json"

    def load_latest(self, test_id: str) -> TestSuite | None:
        path = self.latest_path(test_id)
        if not path.is_file():
            return None
        return TestSuite.model_validate_json(path.read_text(encoding="utf-8"))

    def save_latest(self, test_id: str, suite: TestSuite, *, run_id: str | None = None) -> Path:
        path = self.latest_path(test_id)
        path.write_text(suite.model_dump_json(indent=2), encoding="utf-8")
        if run_id:
            self.run_path(test_id, run_id).write_text(suite.model_dump_json(indent=2), encoding="utf-8")
        return path

    def has_latest(self, test_id: str) -> bool:
        return self.latest_path(test_id).is_file()
