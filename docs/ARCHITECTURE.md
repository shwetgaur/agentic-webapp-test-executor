# System Architecture — Phase-2 (September 2026)

| Field | Value |
|---|---|
| **Project** | DS1 — Agentic Web-App Test Executor |
| **Team** | Shwet Gaur · Sahishnu Raut · Eesha Barad · Saksham Sharma |
| **Guide** | Mayur Gaikwad |
| **Industry partner** | Dassault Systèmes (ENOVIA) · Quality Engineering |
| **Live demo** | https://agentic-webapp-test-executor-275092957818.us-central1.run.app |
| **Repository** | https://github.com/shwetgaur/agentic-webapp-test-executor |
| **Status** | Phase-2 complete — 3-agent pipeline, caching, observability, Cloud Run |

---

## 1. Purpose

The system accepts a **structured test prompt** (fixed metadata + ordered step lines), runs them through a **3-agent AI pipeline**, executes browser tests with **Playwright**, produces auditable reports, and routes failure alerts to the owning team.

**One-line flow:**

> Structured prompt → plan & generate steps → discover selectors → execute headlessly → heal on failure → report + notify

This document describes the **current architecture** after Phase-2 work, including Sep 2026 mentor action items (locator cache, suite replay, observability, cookie clearance).

---

## 2. Mentor alignment

### 2.1 Structured input (Aug 2026 — unchanged)

Testers submit a **StructuredTestPrompt** with fixed fields. Step *lines* may be natural language when LLM is enabled.

| Field | Role |
|---|---|
| `test_id` | Unique case ID; keys suite cache and reports |
| `site_url` | Primary application URL |
| `feature` | Module name (e.g. `login`) — keys locator cache |
| `test_name`, `objective`, `expected_outcome` | Human context for planner LLM |
| `environment`, `owner_team` | Routing and metadata |
| `steps[]` | Ordered English step lines |

Validated by Pydantic and JSON Schema before any browser run.

### 2.2 Sep 2026 Dassault action items

| Action item | Implementation | Primary modules |
|---|---|---|
| Locator / page-object cache | `LocatorStore` — label → selector JSON per site + feature | `src/agents/artifact_store.py`, `discovery_agent.py` |
| Store Playwright script for replay | `SuiteStore` — full `TestSuite` JSON per `test_id` | `artifact_store.py`, `orchestrator.py` |
| LLM token + latency tracking | Per-call metrics on report; optional LangSmith export | `llm_client.py`, `llm_observability.py` |
| Phase timing / performance | `PhaseTiming` on report + detailed log breakdown | `orchestrator.py`, `performance_summary.py` |
| Reduce execution time | Locator cache skip; single browser across discovery URLs; capped waits | `discovery_agent.py`, `runner.py` |
| Cookie / session isolation | `CLEAR_COOKIES`, `CLEAR_STORAGE`; clear state before each run | `parser.py`, `runner.py`, `settings.py` |
| Healer trace accumulation | Healer traces append to pipeline audit (no per-call reset leak) | `healer.py`, `test_report_agent.py` |
| Excel import | **Deferred** — awaiting Dassault template | — |

---

## 3. High-level architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         INTERFACES                                        │
│  Web UI (/) · FastAPI REST · CLI (run_suite.py) · Streamlit (legacy)     │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
                    StructuredTestPrompt  +  flags
                    (use_llm, use_discovery, use_healer, use_replay)
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    AgentOrchestrator                                      │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────────────────────┐  │
│  │  REPLAY?    │   │  FULL RUN    │   │  Agent 3 — Test & Report    │  │
│  │  Load suite │   │  Agent 1 → 2 │   │  Playwright · Healer · Notify│  │
│  │  from disk  │   │              │   │  Reports · LLM metrics       │  │
│  └──────┬──────┘   └──────┬───────┘   └──────────────┬──────────────┘  │
│         │                 │                           │                  │
│         └─────────────────┴───────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
   data/locators/           data/suites/           data/reports/
   (selector maps)          (TestSuite JSON)       data/logs/
                                                    data/screenshots/
```

### 3.1 Two execution modes

| Mode | Agent 1 (Step) | Agent 2 (Discovery) | Agent 3 (Execute) | Saves suite |
|---|---|---|---|---|
| **Full pipeline** | ✅ LLM or rule parser | ✅ scan or cache hit | ✅ + healer | ✅ `{test_id}_latest.json` |
| **Replay** (`use_replay=true`) | ❌ skipped | ❌ skipped | ✅ + healer | ❌ read-only |

Replay loads `data/suites/{test_id}_latest.json` by `test_id`. Values and selectors in that file are executed as-is (form edits are ignored except `test_id`).

---

## 4. Agent 1 — Test Step Agent

**Module:** `src/agents/step_agent.py`

| Phase | Description |
|---|---|
| **validate** | Pydantic validation of `StructuredTestPrompt` |
| **planner** | LLM refines natural-language step lines (Groq / OpenAI / Ollama) |
| **generator** | LLM or rule fallback → `TestSuite` JSON with typed steps |
| **normalize** | Fixes common LLM mistakes (`contains zoho.com` → `zoho.com`) |

**Output:** `TestSuite` — list of `Step` objects:

```json
{
  "id": "s2",
  "action": "fill",
  "selector": "input[name='email']",
  "value": "user@example.com",
  "description": "Fill email with user@example.com"
}
```

**Supported actions:** `goto`, `fill`, `click`, `select`, `assert_text`, `assert_url`, `clear_cookies`, `clear_storage`, and others defined in `StepAction`.

**Fallback:** If no LLM API key, `flexible_steps.py` + `parser.py` parse English lines with regex rules.

---

## 5. Agent 2 — Module Discovery Agent

**Module:** `src/agents/discovery_agent.py`

Discovery bridges **human step hints** and **Playwright selectors**. It does **not** cache the full DOM — it caches a **ModuleMap** (page-object-style dictionary).

### 5.1 Scan behaviour (cache miss)

1. Collect all `goto` URLs from the suite (multi-URL flows supported).
2. Launch headless Chromium once; reuse browser across URLs.
3. For each page: wait for `input, button, a`; enumerate inputs and buttons.
4. Build keys from labels, placeholders, `aria-label`, `id`, `name`, button text.
5. For login/auth features, merge known guesses (e.g. Zoho `#login_id`, `#password`, `#nextbtn`).
6. Save `ModuleMap` to disk.

### 5.2 Enrichment

For each `fill` / `click` / `select` step, extract a hint from the description:

- `"Fill email with …"` → hint `email`
- `"Click Sign in"` → hint `sign in`

Look up hint in `ModuleMap.elements` and patch `step.selector`.

### 5.3 Locator cache

| Property | Value |
|---|---|
| **Class** | `LocatorStore` |
| **Path** | `data/locators/{host}_{feature}.json` |
| **Example** | `accounts_zoho_com_login.json` |
| **Key** | `urlparse(site_url).netloc` + `feature` |
| **Content** | `{ "site_url", "feature", "elements": { "email": "#login_id", ... } }` |

**Cache hit:** Discovery skips browser entirely; traces show `discovery_agent · cache_hit`.

**Healer merge:** Successful heals in Agent 3 are merged back into the locator cache via `LocatorStore.merge_elements()`.

---

## 6. Agent 3 — Test & Report Agent

**Module:** `src/agents/test_report_agent.py`

| Phase | Description |
|---|---|
| **execute** | `PlaywrightExecutor.run(suite)` — step loop with optional healer |
| **notify** | `NotifyAgent` — ticket + team on failure (`config/team_ownership.yaml`) |
| **report** | JSON, Markdown, detailed timestamped `.log` |

### 6.1 Playwright executor

**Module:** `src/executor/runner.py`

- Clears cookies + storage before run when `CLEAR_BROWSER_STATE_ON_RUN=true`.
- Dispatches each `StepAction` to Playwright APIs.
- Post-auth clicks wait for URL change (timeout swallowed if no redirect — known limitation).
- URL asserts use redirect-aware matching (`url_assertions.py`).
- Failure → full-page screenshot → `data/screenshots/{run_id}_{step_id}.png`.

### 6.2 Healer

**Module:** `src/agents/healer.py`

On step failure (fill / click / select):

1. **Rule heal** — login field candidates, `get_by_label`, `text=` selectors.
2. **LLM heal** — send failed step + page element list to LLM; parse JSON selector.
3. Retry step once; append trace; update locator cache on success.

Inspired by [Playwright Test Agents — Healer](https://playwright.dev/docs/test-agents).

### 6.3 Suite cache (replay script)

| Property | Value |
|---|---|
| **Class** | `SuiteStore` |
| **Latest path** | `data/suites/{test_id}_latest.json` |
| **Per-run copy** | `data/suites/{test_id}_{run_id}.json` |
| **Saved when** | Full pipeline run completes (`save_artifacts && !use_replay`) |
| **Used when** | `use_replay=true` or `POST /api/v1/replay/{test_id}` |

The cached suite is the **complete executable script** — actions, selectors, values, and assertions — not just locators.

**Download:** UI fetches `GET /api/v1/suites/{test_id}/latest` after a full run. This is an **export** for audit/local use; the app does not re-import uploaded JSON yet (use `POST /api/v1/run/json` manually).

---

## 7. Observability & performance

### 7.1 In-run metrics

Each `TestReport` includes:

| Field | Content |
|---|---|
| `llm_calls[]` | Per caller (`planner`, `generator`, `healer`): tokens, latency, model |
| `phase_timings[]` | Wall-clock ms for `step_agent`, `discovery_agent`, `execute`, `notify`, `report`, `replay` |
| `agent_traces[]` | Audit log lines per agent phase |
| `steps[]` | Per-step `started_at`, `finished_at`, `duration_ms` |

Surfaces in: web UI **Performance & LLM Usage** panel, JSON report, Markdown report, `data/logs/{run_id}.log`.

**Module:** `src/reporting/performance_summary.py`

### 7.2 LangSmith (optional)

**Module:** `src/agents/llm_observability.py`

When `LANGSMITH_TRACING_ENABLED=true` and `LANGSMITH_API_KEY` is set, each LLM call exports a trace to LangSmith with OpenAI-style messages, token counts, and timestamps.

| Env var | Purpose |
|---|---|
| `LANGSMITH_API_KEY` | API authentication |
| `LANGSMITH_PROJECT` | Project name (default: `agentic-test-executor`) |
| `LANGSMITH_TRACING_ENABLED` | `true` to export |

### 7.3 Typical phase breakdown

| Phase | Typical cost | Notes |
|---|---|---|
| `execute` | 15–40 s | Playwright + network + healer retries |
| `step_agent` | 2–20 s | LLM planner + generator |
| `discovery_agent` | 0–20 s | 0 ms on locator cache hit |
| `replay` | &lt; 1 ms | JSON load only |

---

## 8. Data model

**Module:** `src/common/models.py`

```
StructuredTestPrompt
        │
        ▼
    TestSuite ──────────────► ModuleMap (discovery cache)
        │
        ▼
    TestReport
        ├── StepResult[] (per-step pass/fail)
        ├── AgentTrace[] (pipeline audit)
        ├── LLMCallMetrics[]
        ├── PhaseTiming[]
        ├── NotifyInfo
        ├── replay_mode: bool
        └── suite_snapshot_path: str | null
```

**Schemas (frozen contracts):**

- `schemas/structured_test_prompt.v1.json`
- `schemas/step_schema.v1.json`
- `schemas/report_schema.v1.json`

---

## 9. API surface

**Module:** `src/backend/app.py` · **Base URL:** `/`

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Web dashboard |
| `GET` | `/health`, `/ping` | Liveness (Cloud Run / UptimeRobot) |
| `GET` | `/api/v1/samples` | List loadable sample cases |
| `GET` | `/api/v1/samples/{id}` | Load sample YAML as JSON |
| `POST` | `/api/v1/run/agents` | Full 3-agent pipeline (+ replay flag) |
| `POST` | `/api/v1/run/structured` | Rule parser only (no agents) |
| `POST` | `/api/v1/run/json` | Execute raw `TestSuite` JSON |
| `GET` | `/api/v1/suites/{test_id}/latest` | Download cached suite |
| `GET` | `/api/v1/suites/{test_id}/exists` | Check if replay cache exists |
| `GET` | `/api/v1/locators?site_url=&feature=` | Download locator cache (`ModuleMap` JSON) |
| `GET` | `/api/v1/locators/exists?site_url=&feature=` | Check if locator cache exists |
| `POST` | `/api/v1/replay/{test_id}` | Replay cached suite directly |
| `GET` | `/api/v1/reports/{run_id}` | Fetch JSON report |
| `GET` | `/api/v1/reports/{run_id}/markdown` | Fetch Markdown report |
| `GET` | `/api/v1/reports/{run_id}/log` | Fetch detailed log |
| `GET` | `/api/v1/screenshots/{filename}` | Failure screenshot |

### 9.1 Agent run request body

```json
{
  "prompt": { "test_id": "...", "site_url": "...", "feature": "...", "steps": ["..."] },
  "headless": true,
  "use_llm": true,
  "use_discovery": true,
  "use_healer": true,
  "use_replay": false
}
```

When `use_replay=true`, the orchestrator forces LLM and discovery off regardless of other flags.

---

## 10. Frontend

**Paths:** `frontend/index.html`, `frontend/static/js/app.js`, `frontend/static/css/styles.css`

| Feature | Behaviour |
|---|---|
| Structured form | All mentor-required fields |
| Load sample | Sauce Demo, Campus Voice, Zoho TC01–TC06 |
| Pipeline toggles | LLM, discovery, healer, replay, headless |
| Results panel | Step timings, agent traces, performance + LLM table |
| Downloads | JSON report, Markdown, detailed log, cached suite JSON |

---

## 11. Deployment architecture

### 11.1 Google Cloud Run (production)

| Setting | Value |
|---|---|
| **Region** | `us-central1` |
| **Memory** | 2 GiB (Chromium) |
| **Timeout** | 900 s |
| **Container** | Root `Dockerfile` — Python + Playwright Chromium |
| **Sandbox** | `PLAYWRIGHT_NO_SANDBOX=true` when `K_SERVICE` set |

**Module:** `src/executor/browser_launch.py` detects Cloud Run via `K_SERVICE`.

See [DEPLOY_CLOUD_RUN.md](./DEPLOY_CLOUD_RUN.md).

### 11.2 Ephemeral storage on Cloud Run

All artifacts write to the **container filesystem**:

```
data/
├── locators/      # selector maps — lost on redeploy / new instance
├── suites/        # replay scripts — lost on redeploy / new instance
├── reports/       # run reports
├── logs/          # detailed logs
└── screenshots/   # failure PNGs
```

| Scenario | Cache behaviour |
|---|---|
| Two runs, same warm instance | Locator + suite cache available; replay works |
| Redeploy or cold start | Cache empty; must re-run full pipeline |
| Multiple Cloud Run instances | Cache not shared between instances |
| Downloaded suite JSON | Persists on user's machine; re-run via `POST /api/v1/run/json` locally |

**Planned (Phase-3):** GCS-backed `LocatorStore` / `SuiteStore` or SQLite run history.

---

## 12. Sample corpus (Zoho demo set)

| Sample ID | Purpose |
|---|---|
| `ZOHO_TC01` | Homepage + observability |
| `ZOHO_TC02` | Redirect-aware URL assert |
| `ZOHO_TC03` | Discovery + locator cache demo (run twice) |
| `ZOHO_TC04` | Login flow |
| `ZOHO_TC05` | Multi-URL + suite cache + replay demo |
| `ZOHO_TC06` | Cookie clearance step |

Located in `tests/samples/structured/ZOHO_TC*.yaml`.

---

## 13. Module map

| Package / file | Responsibility |
|---|---|
| `src/agents/orchestrator.py` | Pipeline coordination; replay vs full run |
| `src/agents/step_agent.py` | Agent 1 — validate, plan, generate |
| `src/agents/discovery_agent.py` | Agent 2 — scan, enrich, locator cache |
| `src/agents/test_report_agent.py` | Agent 3 — execute, heal, report, notify |
| `src/agents/healer.py` | Locator recovery on failure |
| `src/agents/artifact_store.py` | `LocatorStore`, `SuiteStore` |
| `src/agents/llm_client.py` | LLM providers + call logging |
| `src/agents/llm_observability.py` | LangSmith export, token parsing |
| `src/agent/parser.py` | Rule-based step parser |
| `src/agent/flexible_steps.py` | Natural-language parser + LLM normalizer |
| `src/agent/structured_prompt.py` | Prompt → suite (non-LLM path) |
| `src/agent/selectors.py` | Login field selector candidates |
| `src/executor/runner.py` | Playwright step loop |
| `src/executor/url_assertions.py` | Redirect-aware URL matching |
| `src/executor/navigation.py` | SPA-aware goto |
| `src/executor/browser_launch.py` | Chromium launch (local / Cloud Run) |
| `src/reporting/writer.py` | JSON + Markdown reports |
| `src/reporting/detailed_log.py` | Timestamped step log |
| `src/reporting/performance_summary.py` | Phase + LLM summary tables |
| `src/notify/agent.py` | Failure routing + ticket ID |
| `src/backend/app.py` | FastAPI + static UI |
| `config/team_ownership.yaml` | Feature → team map for notify |

---

## 14. CLI entry points

```bash
# Full 3-agent pipeline
python scripts/run_suite.py --structured tests/samples/structured/ZOHO_TC05_projects_after_login.yaml --agents

# With LLM + replay
python scripts/run_suite.py --structured ... --agents --llm --replay

# Execute downloaded suite JSON directly
python scripts/run_suite.py --json path/to/suite.json
```

---

## 15. Known limitations (Phase-2)

| Limitation | Impact |
|---|---|
| Cloud Run ephemeral disk | Locator + suite cache lost on redeploy; replay fails until full run |
| No suite upload API | Downloaded JSON cannot be re-imported via UI |
| Action steps ≠ auth proof | Fill/click pass without verifying login succeeded |
| Post-auth wait swallows timeout | Sign-in step may pass while still on login page |
| Zoho regional TLD | `zoho.com` assert fails on `zoho.in` |
| Zoho two-step login | Requires `Click Next` before password fill |
| Public marketing URLs | TC05 asserts public page — passes without login |
| Excel import | Not implemented — awaiting Dassault template |
| Captcha / MFA | Headless login may fail — documented out of scope |

---

## 16. Testing

Unit tests under `tests/unit/` cover parser, artifact stores, discovery cache, replay orchestrator, URL assertions, LLM observability, cookie clearance, and agent wiring.

```bash
pytest tests/unit -q
```

---

## 17. Phase-3 roadmap

| Item | Description |
|---|---|
| Persistent cache | GCS or SQLite for locators, suites, run history |
| Suite upload | `POST /api/v1/suites/upload` for replay after redeploy |
| Auth assertions | Post-login checks; fail if still on `/signin` |
| Excel import | When Dassault template arrives |
| CI GitHub Action | Run sample suite on push |
| Slack notify | Wire `SLACK_WEBHOOK_URL` in production |

---

## 18. Related documents

| Document | Content |
|---|---|
| [PHASE2_SPECIFICATION.md](./PHASE2_SPECIFICATION.md) | Feature spec and demo script |
| [STRUCTURED_PROMPT.md](./STRUCTURED_PROMPT.md) | Input contract for testers |
| [DEPLOY_CLOUD_RUN.md](./DEPLOY_CLOUD_RUN.md) | GCP deploy guide |
| [DEMO_PREP.md](./DEMO_PREP.md) | Mentor demo Q&A |
| [MVP_SPECIFICATION.md](./MVP_SPECIFICATION.md) | Phase-1 baseline |

---

*Last updated: September 2026 — reflects Sep 3 mentor action items, Cloud Run deployment, Zoho sample corpus, and two-tier caching architecture.*
