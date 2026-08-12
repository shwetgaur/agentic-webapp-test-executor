"""Minimal FastAPI app for Phase-1/2 demos."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.agent.parser import parse_plain_text_case
from src.agent.structured_prompt import parse_structured_yaml_or_json, structured_prompt_to_suite
from src.common.models import StructuredTestPrompt, TestReport, TestSuite
from src.common.settings import settings
from src.executor.runner import PlaywrightExecutor
from src.notify.agent import NotifyAgent
from src.reporting.writer import save_json_report, save_markdown_report

app = FastAPI(title=settings.app_name, version="0.1.0")


class TextRunRequest(BaseModel):
    text: str = Field(..., description="Plain-text numbered test steps")
    suite_id: str | None = None
    name: str | None = None
    module: str | None = None
    headless: bool = True


class JsonRunRequest(BaseModel):
    suite: TestSuite
    headless: bool = True


class StructuredRunRequest(BaseModel):
    prompt: StructuredTestPrompt
    headless: bool = True


def _execute_suite(suite: TestSuite, headless: bool) -> TestReport:
    executor = PlaywrightExecutor(headless=headless)
    report = executor.run(suite)
    report = NotifyAgent().maybe_notify(report)
    save_json_report(report)
    save_markdown_report(report)
    return report


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.post("/api/v1/run/text", response_model=TestReport)
def run_from_text(body: TextRunRequest):
    try:
        suite = parse_plain_text_case(
            body.text,
            suite_id=body.suite_id,
            name=body.name,
            module=body.module,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _execute_suite(suite, body.headless)


@app.post("/api/v1/run/structured", response_model=TestReport)
def run_from_structured(body: StructuredRunRequest):
    try:
        suite = structured_prompt_to_suite(body.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _execute_suite(suite, body.headless)


@app.post("/api/v1/run/json", response_model=TestReport)
def run_from_json(body: JsonRunRequest):
    return _execute_suite(body.suite, body.headless)


@app.get("/api/v1/reports/{run_id}")
def get_report(run_id: str):
    path = Path("data/reports") / f"{run_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return TestReport.model_validate_json(path.read_text(encoding="utf-8"))
