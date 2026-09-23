# Deploy Agentic Web-App Test Executor to Google Cloud Run (us-central1)
# Usage: .\scripts\deploy_cloud_run.ps1 [-ProjectId YOUR_GCP_PROJECT]

param(
    [string]$ProjectId = "",
    [string]$Region = "us-central1",
    [string]$Service = "agentic-webapp-test-executor"
)

$ErrorActionPreference = "Stop"

if ($ProjectId) {
    gcloud config set project $ProjectId
}

Write-Host "Deploying $Service to Cloud Run ($Region)..." -ForegroundColor Cyan

gcloud run deploy $Service `
  --source . `
  --region $Region `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 900 `
  --concurrency 4 `
  --max-instances 3 `
  --set-env-vars "HEADLESS=true,LLM_PROVIDER=groq,LLM_MODEL=openai/gpt-oss-20b,PLAYWRIGHT_NO_SANDBOX=true,NOTIFY_ENABLED=true,NOTIFY_CHANNEL=console,NAVIGATION_TIMEOUT_MS=45000,GOTO_WAIT_UNTIL=domcontentloaded,LANGSMITH_PROJECT=agentic-test-executor,LANGSMITH_TRACING_ENABLED=true"

Write-Host ""
Write-Host "Done. Service URL:" -ForegroundColor Green
gcloud run services describe $Service --region $Region --format "value(status.url)"
Write-Host ""
Write-Host "Set GROQ_API_KEY and LANGSMITH_API_KEY in Cloud Run console if not using Secret Manager."
