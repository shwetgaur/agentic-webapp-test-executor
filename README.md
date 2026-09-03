# Agentic Web-App Test Executor (DS 1)


Structured test prompt → Playwright execution → pass/fail report → team notification on failure.

**Web UI:** FastAPI serves the dashboard at `/` (recommended for demo & Render deploy).

## Quick start (web UI)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
uvicorn src.backend.app:app --reload --port 8000
```

Open **http://localhost:8000**

## Deploy on Render

Docker-based deploy with Playwright. See [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md).

```bash
# Push to GitHub, then Render Dashboard → Blueprint → connect repo (render.yaml)
```

## Legacy Streamlit demo (local only)

```powershell
streamlit run demo/streamlit_app.py
```

## Structured test prompt 

Testers must fill fixed fields — **no free-form-only input**:

- Site URL, Feature, Test ID, Name, Objective, Expected Outcome, Steps

Details: [docs/STRUCTURED_PROMPT.md](docs/STRUCTURED_PROMPT.md)

## Documentation

- [Deploy on Render](docs/DEPLOY_RENDER.md) — Docker + Playwright production deploy
- [MVP Specification (Phase-1)](docs/MVP_SPECIFICATION.md) — Phase-1 baseline document
- [Phase-2 Specification](docs/PHASE2_SPECIFICATION.md) — 3-agent pipeline, web UI, cloud deploy
- [Demo Prep & Q&A](docs/DEMO_PREP.md) — demo script, mentor questions, PPT alignment

## CLI

```bash
# Structured YAML (recommended)
python scripts/run_suite.py --structured tests/samples/structured/TC01_login_success.yaml

# 3-agent pipeline (Step → Discovery → Test & Report)
python scripts/run_suite.py --structured tests/samples/structured/TC01_login_success.yaml --agents

# Legacy plain text / JSON
python scripts/run_suite.py --text tests/samples/text/TC01_login_success.txt
python scripts/run_suite.py --json tests/samples/json/TC01_login_success.json
```

## API

```bash
uvicorn src.backend.app:app --reload --port 8000
```

- `GET /health`
- `POST /api/v1/run/structured` — structured prompt body (`use_agents: true` for pipeline)
- `POST /api/v1/run/agents` — 3-agent pipeline
- `POST /api/v1/run/text` — legacy plain text
- `GET /api/v1/reports/{run_id}`

## Project layout

```
frontend/          Web UI (HTML/CSS/JS)
demo/              Streamlit (local dev fallback)
src/agents/        3-agent pipeline (step, discovery, test/report)
src/agent/         Rule parser + structured prompt
src/executor/      Playwright runner
src/reporting/     Pass/fail reports
src/notify/        Failure alerts
schemas/           JSON schemas
tests/samples/     Sample cases
```

## Team

Shwet Gaur · Sahishnu Raut · Eesha Barad · Saksham Sharma

Guide: Mayur Gaikwad · Industry: Dassault Systemes (ENOVIA)
