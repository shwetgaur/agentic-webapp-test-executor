# System Architecture (Phase-1)

```
Plain-text steps  ──►  Step Parser (rules now / LLM later)
                              │
                              ▼
                         JSON TestSuite
                              │
                              ▼
                    Playwright Executor
                     (actions+asserts)
                              │
                              ▼
                      TestReport (pass/fail)
                         │            │
                         ▼            ▼
                 Report Writer    Notify Agent
               (JSON + Markdown) (team map → alert)
                         │
                         ▼
                 data/reports + API/CLI
```

## Modules
| Package | Responsibility |
|---|---|
| `src/agent` | Text → structured steps |
| `src/executor` | Playwright run + assertions + failure screenshots |
| `src/reporting` | Pass/fail documentation artifacts |
| `src/notify` | Scrum-style failure routing |
| `src/backend` | FastAPI endpoints |
| `schemas/` | Locked JSON schemas |
| `config/` | Team ownership map |

## Fixed contracts
- Step schema: `schemas/step_schema.v1.json`
- Report schema: `schemas/report_schema.v1.json`
- Ownership map: `config/team_ownership.yaml`
