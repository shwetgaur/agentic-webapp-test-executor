# Demo Preparation Guide — Q&A, Script & Talking Points

Use this before presenting to mentors, guide, or industry reviewers.

---

## Part 1 — Five-Minute Demo Script

### Before you start (30 sec)

> "We are building DS 1 — an Agentic Web-App Test Executor for Dassault Quality Engineering. Testers submit a **structured test prompt** — not free-form text — with site URL, feature, objective, expected outcome, and steps. The system runs Playwright, documents pass/fail with evidence, and notifies the owning team on failure."

### Live demo (3 min)

1. **Open Streamlit** (`streamlit run demo/streamlit_app.py`)
2. **Point at the form** — walk through each field; mention mentor requirement for structure.
3. **Load TC01 Login PASS** → Run Test → show green status, step table, report paths.
4. **Load TC10 Intentional FAIL** → Run Test → show red status, failure screenshot, notify ticket (`TKT-...` → QA Platform Team).
5. **Optional:** open `data/reports/run_*.json` or Markdown report to show audit trail.

### Close (1 min)

> "This MVP covers Phase-1 of our 12-week plan: the full vertical slice from structured input to execution to report to notify. Phase-2 adds LLM parsing; Phase-3 adds self-healing; Phase-4 adds production notifications and evaluation. Code is on GitHub."

### Backup if Streamlit fails

```powershell
python scripts/run_suite.py --structured tests/samples/structured/TC01_login_success.yaml
python scripts/run_suite.py --structured tests/samples/structured/TC10_intentional_fail.yaml
```

Show the console notify block and files in `data/reports/`.

---

## Part 2 — How Close Is the MVP to the PPT Proposal?

| What we proposed (PPT) | MVP today | Gap |
|---|---|---|
| Text steps → auto execution | ✅ Structured prompt + rule parser | LLM not yet; mentor wanted structure anyway |
| Playwright automation | ✅ Full pipeline | Only 6 action types so far |
| Pass/fail reports + evidence | ✅ JSON, Markdown, screenshots | No DB history yet |
| Notify team on failure | ✅ Ticket ID + team routing | Console only by default |
| AI-assisted parsing | ❌ Phase-2 | By design — not slipped, scheduled |
| Self-healing locators | ❌ Phase-3 | Literature reviewed, not built |
| Dashboard | ⚠️ Streamlit MVP | Production UI in Phase-2 |
| ClickUp / Zoho | ❌ Phase-4 | Needs mentor access |
| Sauce Demo evaluation | ⚠️ 2 structured + 10 documented cases | More cases to convert |
| Modular architecture + schemas | ✅ Complete | Matches slide 11 architecture |

**Soundbite:** *"We delivered ~95% of Phase-1 and ~55% of the full year vision — exactly where our Gantt said we should be at the first executable demo."*

---

## Part 3 — What's Left (Be Honest, Show Roadmap)

### Done now ✅
- Structured test prompt validation
- Rule-based parser
- Playwright executor
- Reports + failure screenshots
- Notify agent with team mapping
- Streamlit + CLI + FastAPI
- GitHub repo + unit tests

### Next (Phase-2, weeks 7–9)
- LLM parser (Groq/OpenAI/Ollama) wrapping same `TestSuite` schema
- SQLite run history and report browser
- Convert remaining 8 plain-text cases to structured YAML
- Richer dashboard (or keep Streamlit with history tab)

### Later (Phase-3–4)
- Self-healing when selectors break (LLM or heuristic fallback)
- Batch suite runner + CI integration
- Real Slack/email/Jira/ClickUp notify
- Evaluation metrics for paper / black book
- Multi-environment URL mapping (develop/stage/prod → different base URLs)

---

## Part 4 — Why We Chose What We Chose (MVP Rationale)

Use these when asked **"Why not X?"**

### Why structured prompt instead of free-form text?
- **Mentor feedback:** testers must not submit arbitrary prompts.
- **Engineering:** validation catches missing fields before a browser launches.
- **Industry parallel:** test management tools use fixed templates (TestRail, Zephyr).

### Why rule-based parser first, not LLM?
- **Deterministic demos** — same input always produces same steps; no API key needed in the lab.
- **Architecture first** — LLM plugs into the same `TestSuite` model later without rewriting executor.
- **Proposal alignment** — PPT always listed LLM for Phase-2, not week-1.

### Why Playwright?
- Official Microsoft direction includes **test agents** (planner/generator/healer).
- Better auto-wait and modern API than Selenium for new projects.
- Named in literature review and industry baseline.

### Why Streamlit instead of React dashboard?
- **Speed** — demo-ready UI in one file for tomorrow.
- **Honest scope** — dashboard polish is Phase-2; architecture doesn't depend on UI framework.

### Why Sauce Demo?
- Public, stable, no VPN or Dassault credentials.
- Standard QA training app; selectors are well-known.
- Proposal explicitly listed Sauce Demo for Phase-1.

### Why console notification instead of real Slack?
- Proves **routing logic** (module → team → ticket ID) without depending on webhook setup in demo room.
- Slack hook already wired in `NotifyAgent` — flip `NOTIFY_CHANNEL=slack` in `.env`.

### Why Python / FastAPI?
- AIML program stack; same language for future LLM and RL experiments.
- FastAPI gives OpenAPI docs for free when mentors ask about integration.

### Why not Selenium + Testim + buy a product?
- DS 1 is an **academic + open prototype** — we need explainable modules, schemas, and research contribution (report + notify in one workflow).
- Literature gap: commercial tools don't combine all three in one open system.

---

## Part 5 — Likely Questions & Answers

### "What problem does this solve?"
Manual QA writes steps in English; automation engineers rewrite them in code. We close that gap and add automatic failure routing so the right team is pinged without manual triage.

### "Is this agentic / where is the AI?"
Phase-1 proves the **agent loop**: perceive (parse prompt) → act (Playwright) → verify (assertions) → communicate (report + notify). LLM intelligence lands in Phase-2 on the parser; self-heal in Phase-3. The architecture is agent-ready.

### "How is this different from Playwright Codegen or Testim?"
We unify **structured text input + execution + auditable report + scrum-style notify** in one open pipeline. Codegen produces scripts, not team alerts. Testim is closed-source and doesn't expose our notify/ownership module.

### "What if the step text doesn't match your patterns?"
The validator returns a clear error listing allowed verbs. Phase-2 LLM handles broader language; Phase-3 self-heal handles broken selectors.

### "Can it run on our internal Dassault app?"
Architecturally yes — change `site_url` and extend selector mappings. MVP uses Sauce Demo because we don't have internal app access yet.

### "How do you know which team to notify?"
`config/team_ownership.yaml` maps module (`login`, `checkout`, etc.) to team. On failure, `NotifyAgent` resolves the owner and generates a ticket ID.

### "What about develop vs stage vs prod?"
Environment is captured in the prompt and report metadata today. Phase-2 will map each label to a different base URL config.

### "Is it secure?"
MVP is local demo only — no API auth. Production hardening (auth, secrets, rate limits) is post-college or Phase-4 if deployed.

### "How do you test the parser?"
Unit tests in `tests/unit/` — 4 tests covering parser and structured prompt validation. Integration tests are the live Playwright runs.

### "What happens on pass?"
Report saved; notify agent does **not** fire. Only failures trigger alerts — avoids alert fatigue.

### "Can testers still use plain text?"
Legacy path exists (`--text`, `/run/text`) for development, but **mentor direction** is structured prompt for official runs.

### "What's your research contribution?"
Combining plain-language step execution, evidence-backed documentation, and team-scoped failure notification in one open QE workflow — gap identified in literature review vs Playwright agents (code focus) and Testim (closed product).

### "Timeline — are you behind?"
No. Phase-1 demo was weeks 4–6 on the Gantt; we have a working vertical slice with GitHub, docs, and tests.

### "Who built what?"
Be ready with team role split from PPT (parser, executor, reporting, notify) even if one person built MVP — explain planned ownership going forward.

---

## Part 6 — One-Page Cheat Sheet (Print This)

```
PROBLEM:  Text steps → auto test → report → notify team
MVP:      Structured prompt → Playwright → JSON/MD report → console/Slack notify
DEMO:     TC01 PASS · TC10 FAIL + ticket
STACK:    Python · Playwright · FastAPI · Streamlit · Pydantic
TARGET:   Sauce Demo (public)
GITHUB:   github.com/shwetgaur/agentic-webapp-test-executor

PHASE-1 ✅  Parser + executor + report + notify + demo UI
PHASE-2 ⏳  LLM parser + DB + dashboard
PHASE-3 ⏳  Self-heal + batch + CI
PHASE-4 ⏳  Prod notify + evaluation + freeze

WHY RULES NOT LLM?   Deterministic demo, no API keys, Phase-2 planned
WHY STRUCTURED?      Mentor requirement + validation
WHY PLAYWRIGHT?      Industry baseline + test agents direction
WHY NOT TESTIM?      Open, explainable, research contribution
```

---

## Part 7 — Anticipated Tough Questions

**"This looks like a script runner, not agentic AI."**  
→ Agentic = autonomous loop with feedback. We have parse → act → verify → notify. AI enhances parsing/healing in later phases; the orchestration is already agent-shaped.

**"Only two test cases?"**  
→ Two are fully structured and runnable for demo; ten more are documented in plain text ready for YAML conversion — deliberate scope control for first demo.

**"Console notify isn't real notification."**  
→ Interface is production-shaped (team, ticket, channel). Console proves routing; Slack is one env var away. Same pattern as stub → real in enterprise MVPs.

**"Selector guessing seems brittle."**  
→ Correct — that's why Phase-3 self-healing is in the proposal and literature review. MVP uses known Sauce Demo mappings to prove the executor path.

---

Good luck with the demo. Run TC01 once the night before to confirm network and Playwright are working.
