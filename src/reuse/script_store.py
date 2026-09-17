"""Persist enriched TestSuite JSON + generated Playwright script for replay."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from src.common.models import TestSuite, _utc_now
from src.reuse.locator_store import site_host
from src.reuse.playwright_gen import generate_playwright_script

_UNSAFE = re.compile(r"[^a-zA-Z0-9._-]+")


class ScriptArtifact(BaseModel):
    """Stored executable suite plus a standalone Playwright script."""

    suite_id: str
    site_url: str | None = None
    feature: str | None = None
    saved_at: datetime = Field(default_factory=_utc_now)
    suite: TestSuite
    playwright_script: str
    json_path: str | None = None
    py_path: str | None = None
    locator_path: str | None = None
    source: str = "agent_pipeline"


def suite_slug(suite_id: str) -> str:
    slug = _UNSAFE.sub("-", (suite_id or "suite").strip()).strip("-")
    return slug or "suite"


def script_stem(suite_id: str, site_url: str | None = None) -> str:
    base = suite_slug(suite_id)
    host = site_host(site_url)
    if host and host != "unknown":
        return f"{base}__{host}"
    return base


class ScriptStore:
    """Writes `data/scripts/<suite>__<host>.json` and `.py` for later replay."""

    def __init__(self, root: str | Path = "data/scripts") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, suite_id: str, site_url: str | None = None, suffix: str = ".json") -> Path:
        return self.root / f"{script_stem(suite_id, site_url)}{suffix}"

    def save(
        self,
        suite: TestSuite,
        *,
        feature: str | None = None,
        locator_path: str | Path | None = None,
        source: str = "agent_pipeline",
    ) -> ScriptArtifact:
        site_url = suite.base_url
        feat = feature or suite.module
        script = generate_playwright_script(suite)
        json_path = self.path_for(suite.suite_id, site_url, ".json")
        py_path = self.path_for(suite.suite_id, site_url, ".py")
        artifact = ScriptArtifact(
            suite_id=suite.suite_id,
            site_url=site_url,
            feature=feat,
            saved_at=datetime.now(timezone.utc),
            suite=suite,
            playwright_script=script,
            json_path=str(json_path).replace("\\", "/"),
            py_path=str(py_path).replace("\\", "/"),
            locator_path=str(locator_path).replace("\\", "/") if locator_path else None,
            source=source,
        )
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
        py_path.write_text(script, encoding="utf-8")
        latest = self.root / f"{suite_slug(suite.suite_id)}.json"
        if latest.resolve() != json_path.resolve():
            latest.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
        return artifact

    def load(self, suite_id: str, site_url: str | None = None) -> ScriptArtifact | None:
        candidates = []
        if site_url:
            candidates.append(self.path_for(suite_id, site_url, ".json"))
        candidates.append(self.root / f"{suite_slug(suite_id)}.json")
        for path in candidates:
            artifact = self.load_path(path)
            if artifact:
                return artifact
        matches = sorted(self.root.glob(f"{suite_slug(suite_id)}__*.json"))
        for path in matches:
            artifact = self.load_path(path)
            if artifact:
                return artifact
        return None

    def load_path(self, path: str | Path) -> ScriptArtifact | None:
        file_path = Path(path)
        if not file_path.is_file():
            return None
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if isinstance(data, dict) and "suite" in data:
            try:
                return ScriptArtifact.model_validate(data)
            except ValueError:
                pass
        if isinstance(data, dict) and "steps" in data:
            try:
                suite = TestSuite.model_validate(data)
                return ScriptArtifact(
                    suite_id=suite.suite_id,
                    site_url=suite.base_url,
                    feature=suite.module,
                    suite=suite,
                    playwright_script=generate_playwright_script(suite),
                    json_path=str(file_path).replace("\\", "/"),
                    source="suite_json",
                )
            except ValueError:
                return None
        return None
