# Agentic Web-App Test Executor (DS 1)

**Dassault Systemes | Quality Engineering | B.Tech AIML AY 2026-27**

Structured test prompt → Playwright execution → pass/fail report → team notification on failure.

## MVP demo (tomorrow)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
streamlit run demo/streamlit_app.py
```

See [docs/DEMO.md](docs/DEMO.md) for the 5-minute demo script.

## Structured test prompt (mentor requirement)

Testers must fill fixed fields — **no free-form-only input**:

- Site URL, Feature, Test ID, Name, Objective, Expected Outcome, Steps

Details: [docs/STRUCTURED_PROMPT.md](docs/STRUCTURED_PROMPT.md)

## CLI

```bash
# Structured YAML (recommended)
python scripts/run_suite.py --structured tests/samples/structured/TC01_login_success.yaml

# Legacy plain text / JSON
python scripts/run_suite.py --text tests/samples/text/TC01_login_success.txt
python scripts/run_suite.py --json tests/samples/json/TC01_login_success.json
```

## API

```bash
uvicorn src.backend.app:app --reload --port 8000
```

- `GET /health`
- `POST /api/v1/run/structured` — structured prompt body
- `POST /api/v1/run/text` — legacy plain text
- `GET /api/v1/reports/{run_id}`

## Project layout

```
demo/              Streamlit MVP UI
src/agent/         Parser + structured prompt
src/executor/      Playwright runner
src/reporting/     Pass/fail reports
src/notify/        Failure alerts
schemas/           JSON schemas
tests/samples/     Sample cases
```

## Team

Shwet Gaur · Sahishnu Raut · Eesha Barad · Saksham Sharma

Guide: Mayur Gaikwad · Industry: Dassault Systemes (ENOVIA)
