# MVP Specification — Agentic Web-App Test Executor (DS 1) · Phase-2

| Field | Value |
|---|---|
| **Document ID** | DS1-PHASE2-001 |
| **Version** | 2.0 |
| **Status** | Demo-ready (Phase-2) |
| **Date** | 3 September 2026 |
| **Project** | B.Tech AIML Major Project · AY 2026–27 |
| **Industry Partner** | Dassault Systèmes (ENOVIA) · Quality Engineering |
| **Team** | Shwet Gaur · Sahishnu Raut · Eesha Barad · Saksham Sharma |
| **Guide** | Mayur Gaikwad |
| **Repository** | https://github.com/shwetgaur/agentic-webapp-test-executor |
| **Live Demo** | https://agentic-webapp-test-executor.onrender.com |
| **Supersedes** | DS1-MVP-001 (Phase-1, 12 August 2026) |

---

## 1. Executive Summary

The **Agentic Web-App Test Executor** is a Quality Engineering automation platform that accepts **structured test prompts**, runs them through a **3-agent AI pipeline**, executes browser tests with **Playwright**, produces auditable pass/fail evidence, and routes failure alerts to the owning product team.

Phase-2 extends the Phase-1 vertical slice with **LLM-assisted step planning**, **automatic module discovery**, **self-healing locators**, a **production web UI**, and **cloud deployment** on Render. The system has been validated against **Sauce Demo**, **Zoho** public flows, and the team's deployed app **Campus Voice** (`fs-blind.vercel.app`).

**One-line value proposition:**  
*Structured test intent → 3-agent pipeline (plan · discover · execute) → evidence-backed report → team notification on failure.*

---

## 2. Problem Statement

Phase-1 proved that structured prompts can drive deterministic Playwright execution. Phase-2 addresses the gaps mentors and real-world QA teams raised:

1. **Natural-language steps** — Testers write steps conversationally (`verify that the text Projects is visible`); the system must interpret them reliably, not only rigid templates.
2. **Dynamic UIs** — Selectors break when apps change; discovery and healing must reduce manual script maintenance.
3. **Multi-site flows** — Login on one URL (e.g. `accounts.zoho.com`) and assert on another (e.g. `www.zoho.com/projects/`) requires scanning multiple pages and SPA-aware navigation.
4. **Demo readiness** — A hosted URL, health monitoring, and a professional UI are required for industry review beyond local Streamlit.
5. **Agent architecture** — DS 1 team definition: (1) get test steps, (2) discover modules on site, (3) test / report / notify — combined with Playwright-inspired planner / generator / healer patterns.

**Mentor refinement (Aug 2026, unchanged):** Testers submit a **structured prompt** with fixed metadata fields (site URL, feature, objective, expected outcome, steps) — step *lines* may be natural language when LLM Step Agent is enabled.

---

## 3. Phase-2 Goals & Success Criteria

| Goal | Phase-2 Status |
|---|---|
| 3-agent pipeline: Step → Discovery → Test & Report | ✅ Done |
| LLM step planner + generator (Groq / OpenAI / Ollama) with rule fallback | ✅ Done |
| Flexible natural-language step parsing + LLM output normalizer | ✅ Done |
| Module Discovery Agent (scan site, map selectors) | ✅ Done |
| Healer on step failure (rule + optional LLM) | ✅ Done |
| Production web UI (HTML/CSS/JS + FastAPI) | ✅ Done |
| Cloud deploy (Docker + Playwright on Render) | ✅ Done |
| Uptime monitoring (`/health`, `/ping` with HEAD support) | ✅ Done |
| Structured prompt validation (unchanged contract) | ✅ Done |
| JSON + Markdown reports + failure screenshots | ✅ Done |
| Detailed step logs (per-step timestamps + duration) | ✅ Done |
| Notify owning team on failure with ticket ID | ✅ Done (console; Slack hook ready) |
| Demo: Sauce Demo PASS + intentional FAIL + real apps (Zoho, Campus Voice) | ✅ Done |
| Unit test suite for parser, agents, URL assertions | ✅ Done (21 tests) |

---

## 4. Scope

### 4.1 In Scope (Phase-2)

| Area | Deliverable |
|---|---|
| **Agent 1 — Test Step** | LLM planner (refine steps) + generator (TestSuite JSON); flexible parser + normalizer; rule fallback when LLM unavailable |
| **Agent 2 — Module Discovery** | Scan all `goto` URLs; map feature → selectors; skip when suite is assert-only; SPA hydration wait |
| **Agent 3 — Test & Report** | Playwright execute; healer retry; JSON/MD reports; detailed `.log` with step timestamps; notify on failure; agent trace audit lines |
| **Executor enhancements** | Container-safe Chromium; `domcontentloaded` navigation; post-login redirect wait; redirect-aware URL assert |
| **Input** | Structured test prompt (YAML / JSON / web form) — same contract as Phase-1 |
| **Interfaces** | Web UI at `/`, FastAPI REST, CLI (`run_suite.py --agents`), legacy Streamlit (local) |
| **Deployment** | `Dockerfile`, `render.yaml`, `requirements-prod.txt`, `docs/DEPLOY_RENDER.md` |
| **Monitoring** | `GET /health`, `GET /ping` (UptimeRobot-compatible HEAD) |
| **LLM** | Groq default (`openai/gpt-oss-20b`); env: `GROQ_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL` |
| **Target apps** | Sauce Demo; Zoho marketing/login flows; Campus Voice (Vercel) |
| **Samples** | `TC01`, `TC10`, `CV_test_login_1` loadable from UI |
| **Config** | Team ownership map (`config/team_ownership.yaml`) |
| **Contracts** | JSON schemas (steps, reports, structured prompts) — unchanged v1 |

### 4.2 Out of Scope (Post Phase-2)

| Item | Planned Phase |
|---|---|
| Persistent run history database (SQLite/Postgres) | Phase-3 |
| Batch suite orchestration + CI/CD GitHub Action | Phase-3 |
| ClickUp / Jira / Zoho ticket creation on failure | Phase-4 |
| Production email notification | Phase-4 |
| Multi-browser matrix (Firefox, WebKit) | Phase-3 |
| Full analytics dashboard (trends, flakiness scores) | Phase-3 |
| API authentication / RBAC | Phase-3 |
| Excel test-case import | Deferred (per mentor) |
| RL-based healing | Phase-4 (research) |
| Evaluation paper / benchmark metrics | Phase-4 |

---

## 5. System Architecture

```
Structured Test Prompt (YAML / JSON / Web UI)
         │
         ▼
┌─────────────────────────────────────────┐
│  AGENT 1 — Test Step Agent               │
│  · Validate structured fields (Pydantic) │
│  · Planner — LLM refine step lines         │
│  · Generator — LLM or rule → TestSuite   │
│  · Normalizer — fix assert_url/text values │
└─────────────────┬───────────────────────┘
                  │ TestSuite (JSON)
                  ▼
┌─────────────────────────────────────────┐
│  AGENT 2 — Module Discovery Agent        │
│  · Scan each goto URL (SPA-aware)        │
│  · Map feature hints → CSS selectors     │
│  · Enrich fill/click/select steps        │
│  · Skip if assert-only suite             │
└─────────────────┬───────────────────────┘
                  │ Enriched TestSuite
                  ▼
┌─────────────────────────────────────────┐
│  AGENT 3 — Test & Report Agent           │
│  · Playwright execute (Chromium)         │
│  · Healer — retry failed locators        │
│  · Report Writer — JSON + Markdown       │
│  · Notify Agent — team map → alert       │
└─────────────────┬───────────────────────┘
                  │ TestReport + agent_traces
                  ▼
        data/reports/ · data/screenshots/ · data/logs/
```

### Module map

| Package | Responsibility |
|---|---|
| `src/agents/step_agent.py` | Agent 1 — validate, plan, generate, normalize |
| `src/agents/discovery_agent.py` | Agent 2 — scan site, map selectors |
| `src/agents/test_report_agent.py` | Agent 3 — execute, report, notify |
| `src/agents/healer.py` | Locator recovery on failure (rule + LLM) |
| `src/agents/orchestrator.py` | Runs Agent 1 → 2 → 3 |
| `src/agents/llm_client.py` | Groq / OpenAI / Ollama chat + JSON |
| `src/agent/flexible_steps.py` | Natural-language step parse + LLM cleanup |
| `src/agent/selectors.py` | Login-field selector hints (`#email`, `#password`, …) |
| `src/agent/structured_prompt.py` | Structured prompt → TestSuite (rule path) |
| `src/executor/runner.py` | Playwright step dispatch + healer hook |
| `src/executor/navigation.py` | SPA-friendly goto (`domcontentloaded`, 45s timeout) |
| `src/executor/url_assertions.py` | Redirect-aware URL matching |
| `src/executor/browser_launch.py` | Container-safe Chromium flags (Render/Docker) |
| `src/reporting/` | JSON + Markdown report writers + detailed `.log` renderer |
| `src/notify/` | Module → team routing; console / Slack |
| `src/backend/` | FastAPI API + static web UI |
| `frontend/` | Production dashboard (HTML/CSS/JS) |
| `demo/` | Streamlit (local dev fallback) |
| `schemas/` | Versioned JSON contracts |
| `config/` | Team ownership and notification defaults |

---

## 6. Structured Test Prompt Contract

Every test run requires the following fields. Incomplete prompts are rejected at validation time. **Unchanged from Phase-1.**

| Field | Required | Description |
|---|---|---|
| `test_id` | Yes | Unique identifier e.g. `TC01_login_success`, `CV_test_login_1` |
| `site_url` | Yes | Primary application URL under test |
| `feature` | Yes | Module/feature e.g. `login`, `navigation`, `checkout` |
| `test_name` | Yes | Short human-readable title |
| `objective` | Yes | What the test validates |
| `expected_outcome` | Yes | Overall success criteria |
| `steps` | Yes | Ordered action lines (min. 1) — natural language supported with LLM ON |
| `environment` | No | `develop` \| `stage` \| `prod` (default: `develop`) |
| `owner_team` | No | Override for notification routing |

**Supported step verbs (rule + flexible parser):**  
Open · Fill · Click · Select · Verify URL contains · Verify text … is visible · Verify that the … text is visible

**UI toggles (web form):**

| Toggle | Effect |
|---|---|
| 3-agent pipeline | Uses `/api/v1/run/agents` (orchestrator) |
| LLM Step Agent | Agent 1 planner + generator |
| Module Discovery | Agent 2 scan + selector enrich |
| Healer on failure | Agent 3 retry with alternate locator |
| Headless browser | Playwright headless mode |

Schema: `schemas/structured_test_prompt.v1.json`  
Reference: [STRUCTURED_PROMPT.md](./STRUCTURED_PROMPT.md)

---

## 7. Technology Choices & Rationale

| Choice | Why this (Phase-2) | Why not alternatives |
|---|---|---|
| **3-agent orchestrator** | Matches DS 1 team definition + Playwright agent patterns | Monolithic script: no separation of plan / discover / execute |
| **Groq LLM (`openai/gpt-oss-20b`)** | Fast, free tier for demos; JSON step generation | Larger models: cost/latency on Render; retired `llama-3.1-8b` |
| **Rule fallback (always on)** | Deterministic path when LLM fails or key missing | LLM-only: brittle demos without API key |
| **Flexible step normalizer** | Fixes LLM mistakes (`contains zoho.com` → `zoho.com`) | Strict regex only: rejects mentor-approved natural wording |
| **Playwright + Docker** | Required for headless Chromium on Render | Native Python runtime on Render: no browser deps |
| **FastAPI + static frontend** | Production UI without React sprint; same process as API | Streamlit only: not ideal for public URL demo |
| **Render (Starter + Docker)** | Always-on option; GitHub auto-deploy | Free tier cold starts: bad for live demo + UptimeRobot |
| **UptimeRobot `/ping`** | HEAD + GET; plain `ok` body | Root `/` only: no keyword in SPA shell |
| **Console notify (default)** | Works without secrets in demo room | Slack-only: blocked when webhook unavailable |
| **File-based reports** | Simple, auditable artifacts for mentor review | DB-first: deferred to Phase-3 |

---

## 8. API Surface (Phase-2)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web UI dashboard |
| `GET` | `/health` | JSON liveness (`status: ok`) — supports HEAD |
| `GET` | `/ping` | Plain-text liveness (`ok`) — supports HEAD |
| `GET` | `/api/v1/samples` | List loadable sample IDs |
| `GET` | `/api/v1/samples/{id}` | Fetch sample YAML as JSON |
| `POST` | `/api/v1/run/structured` | Run structured prompt (`use_agents` optional) |
| `POST` | `/api/v1/run/agents` | **3-agent pipeline** (recommended) |
| `POST` | `/api/v1/run/text` | Legacy plain-text steps |
| `POST` | `/api/v1/run/json` | Pre-built `TestSuite` JSON |
| `GET` | `/api/v1/reports/{run_id}` | Fetch saved JSON report |
| `GET` | `/api/v1/reports/{run_id}/markdown` | Fetch saved Markdown report |
| `GET` | `/api/v1/reports/{run_id}/log` | Fetch detailed text log (step timestamps + durations) |

### 8.1 Detailed execution logs

Each test run writes a mentor-friendly log to `data/logs/{run_id}.log`:

- Run-level start/finish timestamps and total duration
- Agent pipeline trace lines with UTC timestamps
- Per-step **START** and **END** lines with `started_at`, `finished_at`, and `duration_ms`
- Expected/actual values, errors, and screenshot paths on failure

The web UI shows step timing inline and offers **Download Detailed Log**. JSON reports include `started_at` / `finished_at` on each `StepResult`.

---

## 9. Sample Test Cases (Phase-2)

| ID | App | Type | Expected | Purpose |
|---|---|---|---|---|
| `TC01_login_success` | Sauce Demo | PASS | All steps green | Baseline happy-path login |
| `TC10_intentional_fail` | Sauce Demo | FAIL | Assert fails | Report + notify demo |
| `CV_test_login_1` | Campus Voice (Vercel) | PASS* | Redirect to `/feed` | Real deployed app; institute email login |
| Zoho TC01–TC06 | zoho.com | PASS/FAIL | Marketing + login flows | Industry site validation (manual prompts) |

\*Requires valid `@sitpune.edu.in` credentials in step lines.

**Load sample (UI):** TC01 Login PASS · TC10 Intentional FAIL · CV01 Campus Voice Login

**CLI:**

```bash
python scripts/run_suite.py --structured tests/samples/structured/TC01_login_success.yaml --agents
python scripts/run_suite.py --structured tests/samples/structured/CV_test_login_1.yaml --agents
```

---

## 10. Known Limitations

1. **LLM variability** — Planner/generator output may differ per run; normalizer and rule fallback mitigate but do not eliminate variance.
2. **Single browser session per agent phase** — Discovery and execute each launch Chromium (memory on Render Starter ~512 MB).
3. **No run database** — Reports are files under `data/reports/`; ephemeral on Render redeploy.
4. **Notification** — Default channel is console; Slack requires `SLACK_WEBHOOK_URL`.
5. **No API authentication** — Public demo URL; not for production secrets in prompts.
6. **Sequential execution** — One suite per request; no parallel batch runner.
7. **Environment label** — Metadata only; does not auto-switch URLs per `develop` / `stage` / `prod`.
8. **Captcha / MFA** — Not supported; login flows with bot detection may fail headless.
9. **Credentials in prompts** — Test passwords visible in UI/report; use test accounts only.
10. **Discovery accuracy** — Depends on page load time; very slow SPAs may map fewer elements on first scan.

---

## 11. Alignment with Phase-1 Proposal

| PPT / Proposal Item | Phase-1 | Phase-2 |
|---|---|---|
| Text steps → automated execution | ✅ Rule parser | ✅ + LLM + natural language |
| Playwright executor | ✅ | ✅ + SPA navigation + container deploy |
| Pass/fail documentation | ✅ | ✅ + agent trace audit |
| Team notify on failure | ✅ Console | ✅ Console + Slack-ready |
| AI / LLM parser | ⏳ Phase-2 | ✅ Agent 1 |
| Self-healing locators | ⏳ Phase-3 | ✅ Agent 3 healer (rule + LLM) |
| Dashboard UI | Streamlit | ✅ Production web UI |
| Module discovery | ⏳ | ✅ Agent 2 |
| Cloud-hosted demo | ⏳ | ✅ Render |
| Evaluation on sample apps | Sauce Demo | ✅ + Zoho + Campus Voice |

**Overall vs full proposal: ~75–80% of final vision; Phase-2 demo-ready for CA-2 / industry review.**

---

## 12. How to Run (Demo)

### Local (web UI)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
# Set GROQ_API_KEY in .env for LLM
uvicorn src.backend.app:app --reload --port 8000
```

Open **http://localhost:8000** → Load sample → Run Test.

### Live (Render)

**https://agentic-webapp-test-executor.onrender.com**

Env vars: `GROQ_API_KEY`, `LLM_PROVIDER=groq`, `LLM_MODEL=openai/gpt-oss-20b`, `HEADLESS=true`, `PLAYWRIGHT_NO_SANDBOX=true`

### Recommended demo sequence

1. **TC01** — Sauce Demo PASS (fast baseline)  
2. **CV01** — Campus Voice login → feed (real app)  
3. **TC10** — intentional FAIL → show notify ticket + agent traces  

---

## 13. Metrics (Phase-2)

| Metric | Value |
|---|---|
| Unit tests | 21 passing |
| Supported step actions | 6 (+ wait/hover in schema; core 6 used in MVP flows) |
| API endpoints | 13 |
| Structured sample cases | 3 runnable (TC01, TC10, CV01) |
| Agent pipeline phases logged | validate · planner · generator · scan · enrich · execute · healer · report · notify |
| Report formats | JSON, Markdown, detailed `.log` |
| Notification channels | Console (+ Slack optional) |
| Deployment target | Render Docker (Playwright base image) |
| Packages (application) | `src/agents/`, `src/agent/`, `src/executor/`, `src/backend/`, `frontend/` |

---

## 14. Document History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 12 Aug 2026 | Team DS1 | Phase-1 MVP specification (DS1-MVP-001) |
| 2.0 | 3 Sep 2026 | Team DS1 | Phase-2: 3-agent pipeline, web UI, Render deploy, LLM, healer, real-app tests |

---

## Appendix A — File Index (Phase-2 additions)

```
frontend/                      Production web UI
src/agents/                    3-agent pipeline
src/agent/flexible_steps.py    Natural-language parse + LLM normalizer
src/agent/selectors.py         Login selector hints
src/executor/navigation.py     SPA-friendly navigation
src/executor/url_assertions.py Redirect-aware URL checks
src/executor/browser_launch.py Container Chromium flags
Dockerfile                     Playwright production image
render.yaml                    Render Blueprint
requirements-prod.txt          Lean production dependencies
docs/DEPLOY_RENDER.md          Deploy guide
docs/ARCHITECTURE.md           3-agent diagram
tests/samples/structured/CV_test_login_1.yaml   Campus Voice sample
```

## Appendix B — Related Documents

- [MVP_SPECIFICATION.md](./MVP_SPECIFICATION.md) — Phase-1 baseline (DS1-MVP-001)
- [ARCHITECTURE.md](./ARCHITECTURE.md) — 3-agent architecture diagram
- [STRUCTURED_PROMPT.md](./STRUCTURED_PROMPT.md) — Prompt format reference
- [DEPLOY_RENDER.md](./DEPLOY_RENDER.md) — Cloud deployment guide
- [DEMO_PREP.md](./DEMO_PREP.md) — Demo script and mentor Q&A
- [OBJECTIVES.md](./OBJECTIVES.md) — Project objectives
- [LITERATURE_REVIEW.md](./LITERATURE_REVIEW.md) — Research baseline
