# Tomorrow Demo Script (5–7 min)

## Before demo

```powershell
cd C:\Users\shwet\Projects\agentic-webapp-test-executor
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
streamlit run demo/streamlit_app.py
```

Opens browser UI at `http://localhost:8501`

## What to say

1. **Problem:** Dassault DS1 — run web tests from structured text steps, verify pass/fail, notify team.
2. **Mentor ask:** testers cannot give random prompts — we enforce **structured fields** (site, feature, objective, steps, expected outcome).
3. **Show form** on left — explain each field.
4. **Demo PASS:** Load `TC01 Login PASS` → Run Test → show green status + step table + report paths.
5. **Demo FAIL:** Load `TC10 Intentional FAIL` → Run Test → show red status + screenshot + **notify ticket** to QA team.
6. **Close:** this is MVP; next is LLM parser + dashboard + ClickUp if mentors allow.

## Backup (CLI if Streamlit fails)

```powershell
python scripts/run_suite.py --structured tests/samples/structured/TC01_login_success.yaml
python scripts/run_suite.py --structured tests/samples/structured/TC10_intentional_fail.yaml
```

Reports in `data/reports/`
