"""Streamlit demo MVP — structured prompt → run → report → notify."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.orchestrator import AgentOrchestrator
from src.common.models import StructuredTestPrompt
from src.reporting.writer import save_json_report, save_markdown_report

SAMPLES = ROOT / "tests" / "samples" / "structured"

st.set_page_config(
    page_title="Agentic Web-App Test Executor",
    page_icon="🎭",
    layout="wide",
)

st.title("Agentic Web-App Test Executor")
st.caption("DS 1 · Dassault Systemes · Quality Engineering · Structured test prompt MVP")

st.info(
    "**Structured prompt only:** testers must specify site, feature, objective, expected outcome, "
    "and numbered steps. Free-form prompts are not accepted."
)

col_form, col_result = st.columns([1, 1])

with col_form:
    st.subheader("Structured Test Prompt")

    sample_choice = st.selectbox(
        "Load sample",
        ["(none)", "TC01 Login PASS", "TC10 Intentional FAIL"],
    )

    defaults = {
        "test_id": "TC01_login_success",
        "site_url": "https://www.saucedemo.com/",
        "feature": "login",
        "test_name": "Valid user login",
        "objective": "Verify standard user can log in and see products page",
        "expected_outcome": "Products page is visible after login",
        "environment": "develop",
        "owner_team": "auth-frontend",
        "steps_text": "\n".join(
            [
                "Fill username with standard_user",
                "Fill password with secret_sauce",
                "Click Login",
                "Verify URL contains inventory.html",
                "Verify text Products is visible",
            ]
        ),
    }

    if sample_choice == "TC01 Login PASS" and SAMPLES.joinpath("TC01_login_success.yaml").exists():
        data = yaml.safe_load(SAMPLES.joinpath("TC01_login_success.yaml").read_text(encoding="utf-8"))
        defaults["steps_text"] = "\n".join(data["steps"])
        defaults.update({k: data[k] for k in defaults if k in data and k != "steps_text"})
    elif sample_choice == "TC10 Intentional FAIL" and SAMPLES.joinpath("TC10_intentional_fail.yaml").exists():
        data = yaml.safe_load(SAMPLES.joinpath("TC10_intentional_fail.yaml").read_text(encoding="utf-8"))
        defaults["steps_text"] = "\n".join(data["steps"])
        defaults.update({k: data[k] for k in defaults if k in data and k != "steps_text"})

    test_id = st.text_input("Test ID *", value=defaults["test_id"])
    site_url = st.text_input("Site URL under test *", value=defaults["site_url"])
    feature = st.text_input("Feature / Module *", value=defaults["feature"])
    test_name = st.text_input("Test Name *", value=defaults["test_name"])
    objective = st.text_area("Test Objective *", value=defaults["objective"], height=68)
    expected_outcome = st.text_area("Expected Outcome *", value=defaults["expected_outcome"], height=68)
    environment = st.selectbox(
        "Environment",
        options=["develop", "stage", "prod"],
        index=["develop", "stage", "prod"].index(defaults["environment"])
        if defaults["environment"] in ("develop", "stage", "prod")
        else 0,
    )
    owner_team = st.text_input("Owner Team (for notify)", value=defaults["owner_team"])
    steps_text = st.text_area(
        "Test Steps (one action per line) *",
        value=defaults["steps_text"],
        height=180,
        help="Examples: Fill username with X | Click Login | Verify text Products is visible",
    )
    headless = st.checkbox("Headless browser", value=True)
    use_agents = st.checkbox(
        "Run 3-agent pipeline (Step → Discovery → Test & Report)",
        value=True,
        help="Agent 1: plan/parse steps · Agent 2: discover modules · Agent 3: run, heal, report, notify",
    )
    use_llm = st.checkbox("Use LLM in Step Agent (if API key set)", value=False)
    use_healer = st.checkbox("Enable Healer on step failure", value=True)

    run_btn = st.button("Run Test", type="primary", use_container_width=True)

with col_result:
    st.subheader("Execution Result")

    if run_btn:
        steps = [ln.strip() for ln in steps_text.splitlines() if ln.strip()]
        try:
            prompt = StructuredTestPrompt(
                test_id=test_id,
                site_url=site_url,
                feature=feature,
                test_name=test_name,
                objective=objective,
                expected_outcome=expected_outcome,
                environment=environment,
                owner_team=owner_team or None,
                steps=steps,
            )
        except Exception as exc:
            st.error(f"Validation error: {exc}")
            st.stop()

        with st.spinner("Running 3-agent pipeline..." if use_agents else "Running Playwright executor..."):
            try:
                if use_agents:
                    result = AgentOrchestrator(
                        headless=headless,
                        use_llm=use_llm,
                        use_discovery=True,
                        use_healer=use_healer,
                    ).run(prompt)
                    report = result.report
                else:
                    from src.agent.structured_prompt import structured_prompt_to_suite
                    from src.executor.runner import PlaywrightExecutor
                    from src.notify.agent import NotifyAgent

                    suite = structured_prompt_to_suite(prompt)
                    report = PlaywrightExecutor(headless=headless).run(suite)
                    report = NotifyAgent().maybe_notify(report)
                    json_path = save_json_report(report)
                    md_path = save_markdown_report(report)
            except Exception as exc:
                st.error(f"Execution failed: {exc}")
                st.stop()

        if use_agents:
            json_path = Path("data/reports") / f"{report.run_id}.json"
            md_path = Path("data/reports") / f"{report.run_id}.md"

        status_color = "green" if report.status.value == "passed" else "red"
        st.markdown(f"### Status: :{status_color}[{report.status.value.upper()}]")
        st.write(f"**Run ID:** `{report.run_id}`")
        st.write(f"**Duration:** {report.duration_ms} ms")
        st.write(
            f"**Summary:** {report.summary.passed} passed / "
            f"{report.summary.failed} failed / {report.summary.skipped} skipped"
        )

        st.markdown("#### Step Results")
        for step in report.steps:
            icon = "✅" if step.status.value == "passed" else "❌" if step.status.value == "failed" else "⏭️"
            st.write(f"{icon} **{step.step_id}** — {step.action}: {step.description or ''}")
            if step.error:
                st.caption(f"Error: {step.error}")
            if step.screenshot_path and Path(step.screenshot_path).exists():
                st.image(step.screenshot_path, caption=f"Screenshot {step.step_id}", width=400)

        st.markdown("#### Agent Pipeline")
        if report.agent_traces:
            for t in report.agent_traces:
                st.write(f"**{t.agent}** · `{t.phase}` — {t.detail}")
        else:
            st.caption("_Legacy run (single executor, no agent traces)._")

        st.markdown("#### Notification")
        if report.notify.triggered:
            st.warning(
                f"Alert sent → **{report.notify.team}** | Ticket: `{report.notify.ticket_id}`"
            )
        else:
            st.success("No failure notification (test passed).")

        st.markdown("#### Reports saved")
        st.code(f"{json_path}\n{md_path}")

        with open(json_path, encoding="utf-8") as f:
            st.download_button("Download JSON report", f.read(), file_name=json_path.name)
        with open(md_path, encoding="utf-8") as f:
            st.download_button("Download Markdown report", f.read(), file_name=md_path.name)
    else:
        st.markdown(
            "_Fill the structured prompt on the left and click **Run Test** to execute the demo._"
        )

st.divider()
st.markdown(
    "**Demo flow for presentation:** load TC01 → Run (PASS) → load TC10 → Run (FAIL + notify)."
)
