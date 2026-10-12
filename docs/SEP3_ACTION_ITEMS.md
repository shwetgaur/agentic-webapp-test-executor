# Sep 3 & Sep 24 Mentor Action Items — Status

**Project:** DS-1 Agentic Web-App Test Executor  
**Guide:** Mayur Gaikwad · **Dassault:** Ajay KR

---

| # | Action item | Status | Notes |
|---|-------------|--------|--------|
| 1 | Locator caching | ✅ Done | `LocatorStore` + download API |
| 2 | Playwright suite JSON / replay | ✅ Done | `SuiteStore` + replay checkbox |
| 3 | LLM tokens + LangSmith | ✅ Done | In-app + LangSmith traces |
| 4 | Phase timing | ✅ Done | Reports + UI panel |
| 5 | Reduce execution time | ✅ Partial | Cache + replay |
| 6 | Cookie clearance | ✅ Done | TC06 + settings |
| 7 | Healer traces | ✅ Done | Accumulated in report |
| 8 | **Persistent storage (Sep 24)** | ✅ Done | `ARTIFACT_STORAGE=gcs` + `GCS_BUCKET`; dual-write local + GCS |
| 9 | **Excel import (Sep 24)** | ✅ Done | `POST /api/v1/import/excel` + UI **Import Excel** |
| 10 | **Visible browser replay (Sep 24)** | ✅ Done | Uncheck **Headless** (local); Cloud Run stays headless |
| 11 | **Restore suite after redeploy** | ✅ Done | **Upload cached suite JSON** + `POST /api/v1/suites/upload` |

---

## Excel column headers (flexible names)

| Required | Aliases |
|----------|---------|
| Test ID | test_id, id, case_id |
| Site URL | site url, url |
| Feature | module |
| Test Name | name, title |
| Objective | test_objective |
| Expected Outcome | expected result, expected |
| Steps | Multiline cell **or** columns Step 1, Step 2, … |

Optional: Environment, Owner Team

---

## Key files (new)

| Feature | Location |
|---------|----------|
| GCS / local storage | `src/agents/artifact_storage.py` |
| Excel import | `src/importers/excel_importer.py` |
| API | `src/backend/app.py` |

---

*Last updated: October 2026*
