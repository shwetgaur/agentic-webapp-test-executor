# Deploy on Google Cloud Run

Production URL:

**https://agentic-webapp-test-executor-275092957818.us-central1.run.app**

Playwright runs inside Docker (see root `Dockerfile`). Cloud Run needs enough memory for Chromium — use **at least 2 GiB** and a **long request timeout** (tests can take 60–120 s).

## Prerequisites

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud`) installed and logged in
2. GCP project with **Cloud Run** and **Cloud Build** APIs enabled
3. Billing enabled on the project

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

## Deploy from source (recommended)

From the repo root:

```bash
gcloud run deploy agentic-webapp-test-executor \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900 \
  --concurrency 4 \
  --max-instances 3 \
  --set-env-vars "HEADLESS=true,LLM_PROVIDER=groq,LLM_MODEL=openai/gpt-oss-20b,PLAYWRIGHT_NO_SANDBOX=true,NOTIFY_ENABLED=true,NOTIFY_CHANNEL=console,NAVIGATION_TIMEOUT_MS=45000,GOTO_WAIT_UNTIL=domcontentloaded,LANGSMITH_PROJECT=agentic-test-executor,LANGSMITH_TRACING_ENABLED=true" \
  --set-secrets "GROQ_API_KEY=GROQ_API_KEY:latest,LANGSMITH_API_KEY=LANGSMITH_API_KEY:latest"
```

If you are not using Secret Manager yet, set keys in the [Cloud Run console](https://console.cloud.google.com/run) → service → **Edit & deploy new revision** → **Variables & secrets**:

| Variable | Example |
|----------|---------|
| `GROQ_API_KEY` | `gsk_...` |
| `LANGSMITH_API_KEY` | `lsv2_pt_...` |
| `LANGSMITH_PROJECT` | `agentic-test-executor` |
| `LANGSMITH_TRACING_ENABLED` | `true` |
| `PLAYWRIGHT_NO_SANDBOX` | `true` |
| `HEADLESS` | `true` |

## Health check (UptimeRobot / monitoring)

```text
GET https://agentic-webapp-test-executor-275092957818.us-central1.run.app/ping
```

Expected: plain text body containing `ok`.

Do **not** ping `/api/v1/run/agents` — that runs Playwright and consumes Groq credits.

## Redeploy after code changes

1. Commit and push to GitHub
2. Re-run the `gcloud run deploy --source .` command above (builds a new image automatically)

Or connect **Cloud Build triggers** to your repo for deploy-on-push.

## LangSmith on Cloud Run

After deploy, run a test with **LLM enabled** on the live UI, then open [smith.langchain.com](https://smith.langchain.com) → **Projects** → `agentic-test-executor`.

Runs appear as `llm.planner`, `llm.generator`, `llm.healer`.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Browser crash / OOM | Increase memory to **2 GiB** or **4 GiB** |
| Request timeout | Increase Cloud Run timeout (max 3600 s); client timeout must match |
| Cold start slow | Set **min instances = 1** (costs more) or use UptimeRobot on `/ping` |
| 500 on first test | Wait for cold start; check Cloud Run **Logs** in GCP console |
| LangSmith empty | Confirm `LANGSMITH_TRACING_ENABLED=true` and LLM toggle is ON in UI |

## Legacy: Render

The repo still contains `render.yaml` and `docs/DEPLOY_RENDER.md` for reference. Production is now **Cloud Run only**.
