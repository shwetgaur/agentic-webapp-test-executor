# Structured Test Prompt (Mentor Requirement)

Testers **cannot** submit free-form text only. Every run must use this fixed structure.

## Required fields

| Field | Description |
|---|---|
| `test_id` | Unique ID e.g. `TC01_login_success` |
| `site_url` | Application URL under test |
| `feature` | Module/feature e.g. `login`, `checkout` |
| `test_name` | Short title |
| `objective` | What the test validates |
| `expected_outcome` | Overall expected result |
| `steps` | Ordered list of actions |

## Optional fields

| Field | Description |
|---|---|
| `environment` | e.g. `demo`, `staging` |
| `owner_team` | Team to notify on failure |

## Example (YAML)

```yaml
test_id: TC01_login_success
site_url: https://www.saucedemo.com/
feature: login
test_name: Valid user login
objective: Verify standard user can log in
expected_outcome: Products page is visible
environment: demo
owner_team: auth-frontend
steps:
  - Fill username with standard_user
  - Fill password with secret_sauce
  - Click Login
  - Verify URL contains inventory.html
  - Verify text Products is visible
```

## Allowed step verbs

- `Open https://...` (auto-added from `site_url` if missing)
- `Fill <field> with <value>`
- `Click <button/link>`
- `Select <option> from <dropdown>`
- `Verify text <text> is visible`
- `Verify URL contains <fragment>`

## CLI

```bash
python scripts/run_suite.py --structured tests/samples/structured/TC01_login_success.yaml
```

## API

`POST /api/v1/run/structured` with JSON body `{ "prompt": { ...StructuredTestPrompt }, "headless": true }`
