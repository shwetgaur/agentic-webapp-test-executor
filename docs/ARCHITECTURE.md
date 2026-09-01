# System Architecture (Phase-2 — 3-Agent Pipeline)

```
Structured Test Prompt
         │
         ▼
┌─────────────────────────────────────┐
│  AGENT 1 — Test Step Agent           │
│  Planner (LLM refine steps)          │
│  Generator (LLM or rule → TestSuite) │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  AGENT 2 — Module Discovery Agent  │
│  Scan site · map feature → selectors│
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  AGENT 3 — Test & Report Agent     │
│  Playwright execute · Healer retry │
│  JSON/MD report · team notify      │
└─────────────────────────────────────┘
```

## Modules
| Package | Responsibility |
|---|---|
| `src/agents/step_agent.py` | Agent 1 — validate, plan, generate TestSuite |
| `src/agents/discovery_agent.py` | Agent 2 — discover UI modules on target site |
| `src/agents/test_report_agent.py` | Agent 3 — run, heal, report, notify |
| `src/agents/healer.py` | Locator recovery (Playwright Healer-inspired) |
| `src/agents/orchestrator.py` | Runs Agent 1 → 2 → 3 |
| `src/agents/llm_client.py` | Groq / OpenAI / Ollama (optional) |
| `src/executor/` | Playwright runner (used by Agent 3) |
| `src/reporting/` | Pass/fail documentation |
| `src/notify/` | Scrum-style failure routing |

## Run commands

```bash
# 3-agent pipeline (LLM off by default if no API key)
python scripts/run_suite.py --structured tests/samples/structured/TC01_login_success.yaml --agents

# API
POST /api/v1/run/agents
```

## Fixed contracts
- Step schema: `schemas/step_schema.v1.json`
- Report schema: `schemas/report_schema.v1.json`
- Structured prompt: `schemas/structured_test_prompt.v1.json`
- Ownership map: `config/team_ownership.yaml`
