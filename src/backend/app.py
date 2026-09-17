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
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.agent.parser import parse_plain_text_case
from src.agent.structured_prompt import structured_prompt_to_suite
from src.agents.orchestrator import AgentOrchestrator
from src.common.models import StructuredTestPrompt, TestReport, TestSuite
from src.common.settings import settings
from src.executor.runner import PlaywrightExecutor
from src.notify.agent import NotifyAgent
from src.reporting.detailed_log import render_detailed_log, save_detailed_log
from src.reporting.writer import save_json_report, save_markdown_report
from src.reuse.locator_store import LocatorStore
from src.reuse.replay import load_replay_source, replay_stored_suite
from src.reuse.script_store import ScriptStore

FRONTEND_DIR = ROOT / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
SAMPLES_DIR = ROOT / "tests" / "samples" / "structured"

SAMPLE_MAP = {
    "tc01": "TC01_login_success.yaml",
    "tc10": "TC10_intentional_fail.yaml",
    "cv01": "CV_test_login_1.yaml",
}

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    for sub in ("data/reports", "data/screenshots", "data/logs", "data/locators", "data/scripts"):
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
    prefer_replay: bool = False
    refresh_locators: bool = False


class AgentRunRequest(BaseModel):
    prompt: StructuredTestPrompt
    headless: bool = True
    use_llm: bool = True
    use_discovery: bool = True
    use_healer: bool = True
    prefer_replay: bool = False
    refresh_locators: bool = False


class ReplayRunRequest(BaseModel):
    suite_id: str | None = None
    site_url: str | None = None
    script_path: str | None = None
    suite: TestSuite | None = None
    headless: bool = True
    use_healer: bool = False


def _execute_suite(suite: TestSuite, headless: bool) -> TestReport:
    try:
        executor = PlaywrightExecutor(headless=headless)
        report = executor.run(suite)
        report = NotifyAgent().maybe_notify(report)
        save_json_report(report)
        save_markdown_report(report)
        save_detailed_log(report)
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
            prefer_replay=body.prefer_replay,
            refresh_locators=body.refresh_locators,
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
                    prefer_replay=body.prefer_replay,
                    refresh_locators=body.refresh_locators,
                )
            )
        suite = structured_prompt_to_suite(body.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _execute_suite(suite, body.headless)


@app.post("/api/v1/run/agents", response_model=TestReport)
def run_from_agents(body: AgentRunRequest):
    return _run_agents(body)


@app.post("/api/v1/run/replay", response_model=TestReport)
def run_from_replay(body: ReplayRunRequest):
    """Execute a stored TestSuite / Playwright artifact without Step + Discovery agents."""
    try:
        if body.suite is not None:
            suite = body.suite
        elif body.script_path:
            suite = load_replay_source(body.script_path).suite
        elif body.suite_id:
            suite = load_replay_source(body.suite_id, site_url=body.site_url).suite
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide suite, suite_id, or script_path",
            )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Replay load failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return replay_stored_suite(suite, headless=body.headless, use_healer=body.use_healer)


@app.get("/api/v1/scripts/{suite_id}")
def get_stored_script(suite_id: str, site_url: str | None = None):
    artifact = ScriptStore().load(suite_id, site_url)
    if not artifact:
        raise HTTPException(status_code=404, detail="Stored script not found")
    return artifact


@app.get("/api/v1/locators")
def get_stored_locators(site_url: str, feature: str):
    stored = LocatorStore().load(site_url, feature)
    if not stored:
        raise HTTPException(status_code=404, detail="Stored locators not found")
    return stored


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


@app.get("/api/v1/reports/{run_id}/log")
def get_report_log(run_id: str):
    log_path = Path("data/logs") / f"{run_id}.log"
    if log_path.exists():
        text = log_path.read_text(encoding="utf-8")
    else:
        json_path = Path("data/reports") / f"{run_id}.json"
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="Detailed log not found")
        report = TestReport.model_validate_json(json_path.read_text(encoding="utf-8"))
        text = render_detailed_log(report)
    return Response(
        content=text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{run_id}.log"'},
    )


@app.get("/api/v1/screenshots/{filename}")
def get_screenshot(filename: str):
    """Serve failure screenshots saved during test runs."""
    if not filename.endswith(".png") or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid screenshot filename")
    path = Path("data/screenshots") / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return FileResponse(path, media_type="image/png")
