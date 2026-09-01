# Deploy on Render

## Overview

The web UI is served by **FastAPI** at `/` (no Streamlit required for production).

- **UI:** `frontend/index.html` + static CSS/JS
- **API:** same service (`/api/v1/...`)
- **Runtime:** Docker (Playwright + Chromium)

## Prerequisites

1. [Render](https://render.com) account
2. GitHub repo pushed: `agentic-webapp-test-executor`
3. Groq API key (optional, for LLM Step Agent)

## Option A — Blueprint (recommended)

1. Push this repo to GitHub
2. In Render Dashboard → **New** → **Blueprint**
3. Connect repo — Render reads `render.yaml`
4. Set **GROQ_API_KEY** when prompted (secret)
5. Deploy

Your app will be at: `https://agentic-webapp-test-executor.onrender.com` (name may vary)

## Option B — Manual Docker Web Service

1. **New** → **Web Service** → connect GitHub repo
2. **Runtime:** Docker
3. **Dockerfile path:** `./Dockerfile`
4. **Health check path:** `/health`
5. **Environment variables:**

| Key | Value |
|---|---|
| `GROQ_API_KEY` | your Groq key (secret) |
| `LLM_PROVIDER` | `groq` |
| `LLM_MODEL` | `openai/gpt-oss-20b` |
| `HEADLESS` | `true` |
| `NOTIFY_CHANNEL` | `console` or `slack` |
| `SLACK_WEBHOOK_URL` | optional |

6. **Create Web Service**

## Run locally (production-like)

```powershell
docker build -t ds1-executor .
docker run -p 8000:8000 --env-file .env ds1-executor
```

Open http://localhost:8000

Or without Docker:

```powershell
uvicorn src.backend.app:app --reload --port 8000
```

Open http://localhost:8000

## Notes

- **Playwright** needs Docker on Render — the included `Dockerfile` uses Microsoft's Playwright Python image.
- **Starter plan** recommended; free tier may timeout on long test runs.
- **Ephemeral disk:** reports in `data/reports/` are lost on redeploy — fine for demo.
- **Streamlit** remains in repo for local dev only (`streamlit run demo/streamlit_app.py`).

## Troubleshooting

| Issue | Fix |
|---|---|
| Health check fails | Wait for Docker build; check logs for uvicorn start |
| Test timeout | Sauce Demo network slow; retry or increase `DEFAULT_TIMEOUT_MS` |
| LLM 404 | Use `LLM_MODEL=openai/gpt-oss-20b` not deprecated llama models |
| Browser crash | Ensure Docker deploy (not native Python runtime on Render) |
