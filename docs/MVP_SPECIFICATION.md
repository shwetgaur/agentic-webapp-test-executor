# MVP Specification — Agentic Web-App Test Executor (DS 1)

| Field | Value |
|---|---|
| **Document ID** | DS1-MVP-001 |
| **Version** | 1.0 |
| **Status** | Demo-ready (Phase-1) |
| **Date** | 12 August 2026 |
| **Project** | B.Tech AIML Major Project · AY 2026–27 |
| **Industry Partner** | Dassault Systèmes (ENOVIA) · Quality Engineering |
| **Team** | Shwet Gaur · Sahishnu Raut · Eesha Barad · Saksham Sharma |
| **Guide** | Mayur Gaikwad |
| **Repository** | https://github.com/shwetgaur/agentic-webapp-test-executor |

---

## 1. Executive Summary

The **Agentic Web-App Test Executor** is a Quality Engineering automation system that accepts human-readable test instructions, executes them against a live web application using Playwright, produces auditable pass/fail evidence, and routes failure alerts to the owning product team.

This MVP delivers an **end-to-end, demoable pipeline** aligned with Dassault DS 1 objectives. It prioritizes a working vertical slice over advanced AI features so mentors and reviewers can validate architecture, contracts, and workflow before Phase-2 intelligence is added.

**One-line value proposition:**  
*Structured test intent → automated browser execution → evidence-backed report → team notification on failure.*

---

## 2. Problem Statement

Quality teams often maintain test cases as plain-language steps while automation lives in separate Playwright/Selenium scripts. When UI changes or ownership is unclear, failures are hard to trace and slow to assign.

DS 1 asks for a system that:
1. Takes **text-based test steps** as input.
2. **Replays user actions** on a web app automatically.
3. **Verifies** expected behaviour via UI assertions.
4. **Documents** each run with pass/fail status and evidence.
5. **Notifies** the responsible team when a test fails (scrum-master style).

**Mentor refinement (Aug 2026):** Testers must submit a **structured prompt** with fixed fields (site URL, feature, objective, expected outcome, steps) — not arbitrary free-form text alone.

---

## 3. MVP Goals & Success Criteria

| Goal | MVP Status |
|---|---|
| Accept structured test input and reject invalid/incomplete prompts | ✅ Done |
| Parse steps into executable JSON `TestSuite` | ✅ Done (rule-based) |
| Execute actions + assertions via Playwright | ✅ Done |
| Generate JSON + Markdown reports per run | ✅ Done |
| Capture failure screenshots | ✅ Done |
| Notify owning team on failure with ticket ID | ✅ Done (console; Slack hook ready) |
| Demo via UI + CLI + API | ✅ Done |
| Show ≥1 passing flow + 1 intentional failure | ✅ Done (TC01, TC10) |

---

## 4. Scope

### 4.1 In Scope (MVP / Phase-1)

| Area | Deliverable |
|---|---|
| **Input** | Structured test prompt (YAML/JSON/form) with validation |
| **Parser** | Rule-based natural-language step parser → `TestSuite` |
| **Executor** | Playwright sync runner: goto, fill, click, select, assert text/URL |
| **Reporting** | Per-run JSON + Markdown reports; step-level status and timing |
| **Evidence** | Screenshot on failed steps |
| **Notification** | Module → team mapping; console alert + optional Slack webhook |
| **Interfaces** | Streamlit demo UI, CLI (`run_suite.py`), FastAPI REST |
| **Contracts** | JSON schemas for steps, reports, structured prompts |
| **Config** | Team ownership map (`config/team_ownership.yaml`) |
| **Environments** | `develop`, `stage`, `prod` labels on test prompts |
| **Target app** | Sauce Demo (public, no credentials required) |
| **Tests** | Unit tests for parser + structured prompt validation |

### 4.2 Out of Scope (Post-MVP)

| Item | Planned Phase |
|---|---|
| LLM-based step parsing | Phase-2 |
| Self-healing / locator recovery (LLM or RL) | Phase-3 |
| Production Slack/email without manual config | Phase-4 |
| ClickUp / Zoho / Jira ticket creation | Phase-4 (if mentor approves) |
| Persistent run history database | Phase-2 |
| Full web dashboard (beyond Streamlit MVP) | Phase-2 |
| Batch suite orchestration + CI/CD plugin | Phase-3 |
| Multi-browser matrix (Firefox, WebKit) | Phase-3 |
| Evaluation paper / benchmark metrics | Phase-4 |

---

## 5. Stakeholders & Users

| Stakeholder | Role | MVP interaction |
|---|---|---|
| **Manual QA / tester** | Authors structured test prompts | Streamlit form or YAML files |
| **Automation engineer** | Reviews reports, extends parser mappings | CLI, JSON reports, schemas |
| **Scrum master / team lead** | Receives failure alerts | Console notify + future Slack |
| **Product team (auth, catalog, etc.)** | Owns failures by module | Mapped via `team_ownership.yaml` |
| **Mentor / reviewer** | Validates DS 1 alignment | Live demo + this document |
| **College guide** | Tracks progress vs proposal | GitHub, docs, presentation |

---

## 6. System Architecture

```
Structured Test Prompt (YAML / JSON / UI form)
        │
        ▼
┌───────────────────┐
│  Prompt Validator │  ← Pydantic + JSON Schema
│  + Step Parser    │  ← Rule-based (Phase-1)
└─────────┬─────────┘
          │ TestSuite (JSON)
          ▼
┌───────────────────┐
│ Playwright        │  ← goto · fill · click · select · assert
│ Executor          │
└─────────┬─────────┘
          │ TestReport
          ├──────────────────────┐
          ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│ Report Writer   │    │ Notify Agent    │
│ JSON + Markdown │    │ team map → alert│
└─────────────────┘    └─────────────────┘
          │
          ▼
   data/reports/ · data/screenshots/
```

### Module map

| Package | Responsibility |
|---|---|
| `src/agent/` | Structured prompt validation; text → `Step` conversion |
| `src/executor/` | Playwright browser lifecycle and step execution |
| `src/reporting/` | Serialize reports to JSON and Markdown |
| `src/notify/` | Resolve team from module; emit failure alert |
| `src/backend/` | FastAPI HTTP surface |
| `demo/` | Streamlit presentation UI |
| `schemas/` | Versioned JSON contracts |
| `config/` | Team ownership and notification defaults |

---

## 7. Structured Test Prompt Contract

Every test run requires the following fields. Incomplete prompts are rejected at validation time.

| Field | Required | Description |
|---|---|---|
| `test_id` | Yes | Unique identifier e.g. `TC01_login_success` |
| `site_url` | Yes | Application URL under test |
| `feature` | Yes | Module/feature e.g. `login`, `checkout` |
| `test_name` | Yes | Short human-readable title |
| `objective` | Yes | What the test validates |
| `expected_outcome` | Yes | Overall success criteria |
| `steps` | Yes | Ordered action lines (min. 1) |
| `environment` | No | `develop` \| `stage` \| `prod` (default: `develop`) |
| `owner_team` | No | Override for notification routing |

**Supported step verbs:** Open · Fill · Click · Select · Verify text · Verify URL

Schema: `schemas/structured_test_prompt.v1.json`  
Full reference: [STRUCTURED_PROMPT.md](./STRUCTURED_PROMPT.md)

---

## 8. Technology Choices & Rationale

| Choice | Why this (MVP) | Why not alternatives (yet) |
|---|---|---|
| **Python 3.12+** | Team AIML stack; rich QA/ML ecosystem | Node-only stack splits AI + browser tooling |
| **Playwright** | Modern, reliable; official test-agent direction from Microsoft; strong assertions | Selenium: slower ecosystem shift; Cypress: less suited to general Python backend |
| **Rule-based parser (Phase-1)** | Zero API keys; deterministic demos; proves pipeline before AI variability | LLM-first: non-deterministic, needs keys, harder to debug in week-1 demo |
| **Pydantic + JSON Schema** | Strict contracts; mentor requirement for structured input | Free-form only: rejected by mentor; no validation |
| **FastAPI** | Lightweight REST for integration tests and future UI | Django: heavier than needed for executor API |
| **Streamlit** | Fast demo UI without front-end sprint | React dashboard: planned Phase-2; too slow for first demo |
| **YAML samples** | Readable for QA authors; easy mentor review | Excel/CSV: poor fit for nested steps |
| **Console notify (default)** | Works offline in college demo; proves routing logic | Real Slack: needs webhook secrets in demo room |
| **Sauce Demo target app** | Public, stable, no VPN; industry-standard demo app | Dassault internal apps: access blocked for college MVP |

---

## 9. API Surface (MVP)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/api/v1/run/structured` | Run from structured prompt body |
| `POST` | `/api/v1/run/text` | Run from legacy plain-text steps |
| `POST` | `/api/v1/run/json` | Run from pre-built `TestSuite` JSON |
| `GET` | `/api/v1/reports/{run_id}` | Fetch saved report |

---

## 10. Sample Test Cases (MVP)

| ID | Type | Expected result | Purpose |
|---|---|---|---|
| `TC01_login_success` | PASS | All steps green | Happy-path login on Sauce Demo |
| `TC10_intentional_fail` | FAIL | Assert step fails | Demonstrate report + notify |

Additional plain-text cases (TC02–TC09) exist in `tests/samples/plain_text_cases.md` for Phase-2 conversion to structured YAML.

---

## 11. Alignment with CA-1 / PPT Proposal

| PPT / Proposal Item | MVP Coverage | Notes |
|---|---|---|
| Text steps → automated execution | ✅ ~90% | Structured prompt supersedes free-form (mentor ask) |
| Playwright executor | ✅ 100% | Core actions + assertions implemented |
| Pass/fail documentation | ✅ 100% | JSON + Markdown + screenshots |
| Team notify on failure | ✅ ~80% | Logic complete; delivery is console/Slack-ready |
| AI / LLM parser | ⏳ 0% | Explicitly Phase-2 in proposal timeline |
| Self-healing locators | ⏳ 0% | Phase-3 per Gantt |
| Dashboard UI | ✅ ~40% | Streamlit MVP, not production dashboard |
| ClickUp / Zoho integration | ⏳ 0% | Conditional on mentor access |
| Evaluation on sample apps | ✅ ~30% | Sauce Demo; 2 structured cases runnable |
| JSON schemas + modular architecture | ✅ 100% | Matches proposed design |
| 12-week phased timeline | ✅ On track | Week 4–6 demo milestone met early |

**Overall MVP vs full proposal: ~55–60% of final vision, ~95% of Phase-1 foundation.**

The MVP intentionally delivers the **vertical slice** proposed for early weeks: parse → execute → report → notify. AI and resilience layers were always scheduled later in the Gantt.

---

## 12. Known Limitations

1. **Parser coverage** — Limited verb patterns and Sauce-Demo-biased selector guessing; unknown steps raise validation errors.
2. **No LLM** — Cannot interpret arbitrary natural language beyond defined patterns.
3. **Single browser** — Chromium only in MVP.
4. **No run database** — Reports are files on disk; `DATABASE_URL` in settings is reserved for Phase-2.
5. **Notification** — Default channel is console; Slack requires `SLACK_WEBHOOK_URL` in `.env`.
6. **No authentication** — API has no auth (local demo only).
7. **Sequential execution** — One test suite per run; no parallel batch runner yet.
8. **Environment label** — Metadata only; does not switch URLs automatically per environment.

---

## 13. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Demo network failure | Cannot reach Sauce Demo | Pre-run tests; keep last JSON report as backup |
| Playwright not installed | Browser launch fails | Document `playwright install chromium` in README |
| Mentor asks about AI | MVP has no LLM | Explain Phase-1 = prove pipeline; LLM wraps same schema in Phase-2 |
| Selector breakage on Sauce Demo | Test fails unexpectedly | Pin to known stable flows (TC01); show TC10 for intentional fail |
| Over-promising scope | Credibility loss | Use this doc's scope table; reference 12-week Gantt |

---

## 14. Roadmap (Post-MVP)

| Phase | Timeline (proposal) | Deliverables |
|---|---|---|
| **Phase-1** ✅ | Weeks 1–6 | Parser, executor, reports, notify, demo UI ← **current** |
| **Phase-2** | Weeks 7–9 | LLM step parser; SQLite run history; improved dashboard |
| **Phase-3** | Weeks 10–11 | Self-healing locators; batch suites; CI hook |
| **Phase-4** | Week 12 | Slack/email production notify; evaluation metrics; demo freeze |

---

## 15. How to Run (Demo)

```powershell
cd agentic-webapp-test-executor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
streamlit run demo/streamlit_app.py
```

**Demo sequence:** TC01 Login PASS → TC10 Intentional FAIL (show notify ticket).

CLI backup:

```powershell
python scripts/run_suite.py --structured tests/samples/structured/TC01_login_success.yaml
python scripts/run_suite.py --structured tests/samples/structured/TC10_intentional_fail.yaml
```

---

## 16. Metrics (MVP)

| Metric | Value |
|---|---|
| Unit tests | 4 passing |
| Supported step actions | 6 (goto, fill, click, select, assert_text, assert_url) |
| API endpoints | 5 |
| Structured sample cases | 2 runnable |
| Plain-text sample cases documented | 10 |
| Report formats | JSON, Markdown |
| Notification channels | Console (+ Slack optional) |
| Lines of application code (excl. deleted PPT scripts) | ~1,200 |

---

## 17. Document History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 12 Aug 2026 | Team DS1 | Initial MVP specification for demo |

---

## Appendix A — File Index

```
demo/streamlit_app.py          Demo UI
scripts/run_suite.py           CLI entrypoint
src/agent/structured_prompt.py Structured prompt → TestSuite
src/agent/parser.py            Rule-based plain-text parser
src/executor/runner.py         Playwright executor
src/reporting/writer.py        Report persistence
src/notify/agent.py            Failure notification
src/backend/app.py             FastAPI server
schemas/                       JSON contracts
config/team_ownership.yaml     Module → team map
tests/samples/structured/      Runnable YAML cases
```

## Appendix B — Related Documents

- [OBJECTIVES.md](./OBJECTIVES.md) — Project objectives
- [ARCHITECTURE.md](./ARCHITECTURE.md) — Architecture diagram
- [STRUCTURED_PROMPT.md](./STRUCTURED_PROMPT.md) — Prompt format reference
- [LITERATURE_REVIEW.md](./LITERATURE_REVIEW.md) — Research baseline
- [DEMO_PREP.md](./DEMO_PREP.md) — Demo script and Q&A
