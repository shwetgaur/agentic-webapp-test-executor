"""Minimal FastAPI app — API + web UI."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import logging

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.agent.parser import parse_plain_text_case
from src.agent.structured_prompt import structured_prompt_to_suite
from src.agents.orchestrator import AgentOrchestrator
from src.common.models import StructuredTestPrompt, TestReport, TestSuite
from src.common.settings import settings
from src.executor.runner import PlaywrightExecutor
from src.notify.agent import NotifyAgent
from src.reporting.writer import save_json_report, save_markdown_report

FRONTEND_DIR = ROOT / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
SAMPLES_DIR = ROOT / "tests" / "samples" / "structured"

SAMPLE_MAP = {
    "tc01": "TC01_login_success.yaml",
    "tc10": "TC10_intentional_fail.yaml",
}

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    for sub in ("data/reports", "data/screenshots"):
        Path(sub).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or exc.__class__.__name__},
    )


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


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
    use_agents: bool = False
    use_llm: bool = True
    use_discovery: bool = True
    use_healer: bool = True


class AgentRunRequest(BaseModel):
    prompt: StructuredTestPrompt
    headless: bool = True
    use_llm: bool = True
    use_discovery: bool = True
    use_healer: bool = True


def _execute_suite(suite: TestSuite, headless: bool) -> TestReport:
    try:
        executor = PlaywrightExecutor(headless=headless)
        report = executor.run(suite)
        report = NotifyAgent().maybe_notify(report)
        save_json_report(report)
        save_markdown_report(report)
        return report
    except Exception as exc:
        logger.exception("Suite execution failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _run_agents(body: AgentRunRequest) -> TestReport:
    try:
        return AgentOrchestrator(
            headless=body.headless,
            use_llm=body.use_llm,
            use_discovery=body.use_discovery,
            use_healer=body.use_healer,
        ).run(body.prompt).report
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Agent pipeline failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/")
def index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    return FileResponse(index_path)


@app.get("/health")
@app.head("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "llm_available": bool(settings.groq_api_key or settings.openai_api_key),
    }


@app.get("/ping")
@app.head("/ping")
def ping():
    """Minimal liveness probe for UptimeRobot / Render (plain body contains 'ok')."""
    return PlainTextResponse("ok", media_type="text/plain")


@app.get("/api/v1/samples")
def list_samples():
    return [{"id": k, "file": v} for k, v in SAMPLE_MAP.items()]


@app.get("/api/v1/samples/{sample_id}")
def get_sample(sample_id: str):
    filename = SAMPLE_MAP.get(sample_id.lower())
    if not filename:
        raise HTTPException(status_code=404, detail="Sample not found")
    path = SAMPLES_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Sample file missing")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


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
        if body.use_agents:
            return _run_agents(
                AgentRunRequest(
                    prompt=body.prompt,
                    headless=body.headless,
                    use_llm=body.use_llm,
                    use_discovery=body.use_discovery,
                    use_healer=body.use_healer,
                )
            )
        suite = structured_prompt_to_suite(body.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _execute_suite(suite, body.headless)


@app.post("/api/v1/run/agents", response_model=TestReport)
def run_from_agents(body: AgentRunRequest):
    return _run_agents(body)


@app.post("/api/v1/run/json", response_model=TestReport)
def run_from_json(body: JsonRunRequest):
    return _execute_suite(body.suite, body.headless)


@app.get("/api/v1/reports/{run_id}", response_model=TestReport)
def get_report(run_id: str):
    path = Path("data/reports") / f"{run_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return TestReport.model_validate_json(path.read_text(encoding="utf-8"))


@app.get("/api/v1/reports/{run_id}/markdown")
def get_report_markdown(run_id: str):
    path = Path("data/reports") / f"{run_id}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Markdown report not found")
    return PlainTextResponse(path.read_text(encoding="utf-8"), media_type="text/markdown")
