"""Build CA-2 submission report (Resource / Dataset / Modalities / EDA) as .docx."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.shared import Cm, Inches, Pt, RGBColor

OUT = Path(__file__).resolve().parent / "CA2_Report_DS1_Agentic_Test_Executor.docx"
FIG = Path(__file__).resolve().parent / "fig_architecture.png"


def set_run_font(run, name="Times New Roman", size=12, bold=False, italic=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def body(doc, text, first_line_indent=True):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_after = Pt(8)
    if first_line_indent:
        p.paragraph_format.first_line_indent = Cm(1.25)
    run = p.add_run(text)
    set_run_font(run)
    return p


def heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        set_run_font(run, size=14 if level == 1 else 13, bold=True)
        run.font.color.rgb = RGBColor(31, 78, 121)
    return p


def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            for run in p.runs:
                set_run_font(run, size=10, bold=True)
    for r_i, row in enumerate(rows, 1):
        for c, val in enumerate(row):
            table.rows[r_i].cells[c].text = str(val)
            for p in table.rows[r_i].cells[c].paragraphs:
                for run in p.runs:
                    set_run_font(run, size=10)
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph()
    return table


def build():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)

    # ---- COVER ----
    for text, size, bold in [
        ("SYMBIOSIS INSTITUTE OF TECHNOLOGY, PUNE", 14, True),
        ("Department of Artificial Intelligence and Machine Learning", 12, True),
        ("B. Tech. Project — CA-2 Report", 16, True),
        ("Agentic Web-App Test Executor", 18, True),
        ("(Industry Problem DS 1 — Dassault Systèmes, Quality Engineering)", 12, False),
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(p.add_run(text), size=size, bold=bold)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run("Group Number: _______________  (fill before upload)"), size=12, bold=True)

    heading(doc, "Group Members", level=2)
    add_table(
        doc,
        ["Sr.", "Name", "PRN"],
        [
            ["1", "Shwet Gaur", "23070126126"],
            ["2", "Sahishnu Raut", "23070126118"],
            ["3", "Eesha Barad", "23070126161"],
            ["4", "Saksham Sharma", "23070126113"],
        ],
        [0.6, 3.2, 2.5],
    )

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run("Faculty Guide: Prof. Mayur Gaikwad"), size=12)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run("Submission Date: September 2026"), size=12)

    doc.add_page_break()

    # ---- 1 INTRO (from CA-1, brief) ----
    heading(doc, "1. Introduction")
    body(
        doc,
        "This CA-2 report extends the CA-1 ideation review for DS 1 — Agentic Web-App Test Executor. "
        "The project accepts structured test prompts (site URL, feature, objective, expected outcome, and ordered steps), "
        "runs them through a three-agent pipeline, executes browser tests with Playwright, and produces pass/fail evidence with team notification on failure. "
        "CA-1 fixed the problem statement, literature gap, and Phase-1 architecture. CA-2 documents resource planning, the project data corpus, modalities, and exploratory analysis carried out before and during implementation.",
    )

    # ---- 2 RESOURCE ALLOCATION ----
    heading(doc, "2. Resource Allocation and Risk Analysis")

    heading(doc, "2.1 Human resource allocation", level=2)
    add_table(
        doc,
        ["Member", "Primary responsibility", "Tools / modules owned"],
        [
            ["Shwet Gaur", "Integration, executor, deployment", "Playwright runner, Render deploy, end-to-end wiring"],
            ["Sahishnu Raut", "Step agent, parser, LLM contracts", "Agent 1, flexible_steps, sample YAML cases"],
            ["Eesha Barad", "API, reports, web UI backend", "FastAPI, JSON/MD/log writers, Pydantic models"],
            ["Saksham Sharma", "Notify agent, QA samples, documentation", "team_ownership.yaml, test cases, CA reports"],
        ],
        [1.5, 2.0, 3.0],
    )

    heading(doc, "2.2 Compute and software resources", level=2)
    add_table(
        doc,
        ["Resource", "Purpose", "Allocation"],
        [
            ["Developer laptops (4)", "Local Playwright runs, unit tests", "Shared during lab slots"],
            ["Groq API (LLM)", "Step planner/generator and healer", "Free tier; GROQ_API_KEY in .env"],
            ["Render Starter (Docker)", "Public demo URL + UptimeRobot", "One web service instance"],
            ["GitHub repository", "Version control, dissemination", "Public repo, develop branch"],
            ["Target web apps (public)", "Test execution targets", "Sauce Demo, Zoho, Campus Voice (Vercel)"],
        ],
        [1.8, 2.5, 2.2],
    )

    heading(doc, "2.3 Risk analysis and mitigation", level=2)
    add_table(
        doc,
        ["Risk", "Impact", "Likelihood", "Mitigation"],
        [
            ["LLM output varies between runs", "Wrong selectors or assert values", "Medium", "Rule parser fallback; flexible_steps normalizer; fixed JSON schema"],
            ["Locator breakage on real sites (Zoho, SPA apps)", "Test failures", "High", "Discovery agent + healer; redirect-aware URL asserts"],
            ["Slow execution (~30–50 s per run)", "Poor demo experience", "Medium", "Skip discovery for assert-only cases; cache locators (planned); profile step logs"],
            ["Render ephemeral disk", "Reports lost on redeploy", "Medium", "Download JSON/MD/log from UI; future SQLite history"],
            ["No Excel template yet from Dassault", "Cannot import 20–30 step cases", "Medium", "Manual structured prompts; wait for Ajay KR template"],
            ["Captcha / MFA on login sites", "Headless login fails", "Low–Med", "Use dummy test accounts; document limitation"],
            ["Plagiarism / AI report rejection", "CA-2 not accepted", "Low", "Original prose from repo + meetings; Guide generates similarity reports"],
        ],
        [1.8, 1.5, 1.0, 2.2],
    )

    # ---- 3 DATASET ----
    heading(doc, "3. Description of the Selected Dataset")
    body(
        doc,
        "DS 1 is a software Quality Engineering project, not a classical tabular ML dataset. "
        "For CA-2 we define the project dataset as the structured test corpus used to drive and evaluate the executor. "
        "This corpus is the equivalent of a labelled dataset: each item has metadata, ordered steps, expected outcomes, and observed run results.",
    )

    heading(doc, "3.1 Dataset composition", level=2)
    add_table(
        doc,
        ["Dataset partition", "Location in repo", "Count / size", "Role"],
        [
            ["Structured YAML cases", "tests/samples/structured/", "3 primary (TC01, TC10, CV_test_login_1)", "Demo and regression"],
            ["Plain-text case bank", "tests/samples/plain_text_cases.md", "10 documented flows", "Future YAML conversion"],
            ["JSON suite (Phase-1)", "tests/samples/json/TC01_login_success.json", "1 machine-ready suite", "CLI smoke test"],
            ["JSON schemas (contracts)", "schemas/*.json", "3 schemas", "Validation of prompt, steps, report"],
            ["Team ownership map", "config/team_ownership.yaml", "Module → team routing", "Notify agent input"],
            ["Run artifacts (generated)", "data/reports/, data/logs/, data/screenshots/", "Per run_id", "Ground truth for pass/fail analysis"],
        ],
        [1.6, 2.2, 1.4, 2.3],
    )

    heading(doc, "3.2 Target application domains in the corpus", level=2)
    add_table(
        doc,
        ["Application", "URL", "Feature covered", "Why included"],
        [
            ["Sauce Demo", "https://www.saucedemo.com/", "Login, inventory", "Stable public baseline; CA-1 target"],
            ["Zoho (marketing + accounts)", "zoho.com, accounts.zoho.com", "Navigation, login", "Industry-relevant; Dassault note"],
            ["Campus Voice", "https://fs-blind.vercel.app/", "SPA login → feed", "Team-deployed real app"],
        ],
        [1.4, 2.2, 1.6, 2.3],
    )

    heading(doc, "3.3 Structured prompt fields (dataset record schema)", level=2)
    body(
        doc,
        "Each test case record in the corpus follows a fixed schema (StructuredTestPrompt): test_id, site_url, feature, test_name, objective, expected_outcome, environment, optional owner_team, and steps[] (one natural-language or template line per step). "
        "This schema was frozen after faculty and industry mentor feedback in CA-1 and is validated with Pydantic before any browser run.",
        first_line_indent=False,
    )

    # ---- 4 MODALITIES ----
    heading(doc, "4. Modalities Chosen for the Project")
    body(
        doc,
        "In AIML projects, modalities usually mean image, text, or audio. For DS 1 we map modalities to the types of data the agents consume and produce:",
    )
    add_table(
        doc,
        ["Modality", "Format", "Producer", "Consumer"],
        [
            ["Text — structured prompt", "YAML / web form / JSON", "Human tester", "Agent 1 (Step Agent)"],
            ["Text — natural-language steps", "Plain English lines", "Human tester / LLM planner", "Parser + LLM generator"],
            ["DOM / UI structure", "Live HTML from target site", "Target web app", "Agent 2 (Discovery Agent)"],
            ["Browser actions", "Playwright commands (goto, fill, click, assert)", "Agent 3 executor", "Chromium headless"],
            ["Visual evidence", "PNG screenshots on failure", "Playwright", "Reports + mentor review"],
            ["Structured run output", "JSON + Markdown + .log", "Report writer", "Tester, guide, Dassault demo"],
            ["Alert text", "Console / optional Slack", "Notify agent", "Owning QA team"],
        ],
        [1.5, 1.8, 1.5, 2.7],
    )
    body(
        doc,
        "The primary modality pair is text-in → browser-out → structured-report-out. "
        "LLM calls add a secondary modality (natural language ↔ JSON TestSuite). "
        "Discovery adds DOM-derived selector maps as an intermediate representation between text steps and Playwright execution.",
    )

    # ---- 5 EDA ----
    heading(doc, "5. Exploratory Data Analysis and Preliminary Work")
    body(
        doc,
        "Classical EDA (histograms, correlation on CSV features) does not apply directly because our corpus is test cases and run logs, not numeric training data. "
        "Instead we performed exploratory analysis on (a) test case coverage, (b) target site behaviour, and (c) early run logs. "
        "This section satisfies the CA-2 requirement for data exploration where conventional EDA is not applicable.",
    )

    heading(doc, "5.1 Test corpus exploration", level=2)
    body(
        doc,
        "We reviewed all sample cases for action type distribution. Most flows use six core actions: goto, fill, click, select, assert_text, assert_url. "
        "Login flows dominate (Sauce Demo TC01, Campus Voice CV_test_login_1, Zoho flows in plain-text bank). TC10 is an intentional negative case to validate failure reporting and notify routing. "
        "Plain-text cases in plain_text_cases.md were scanned to ensure the parser verb list covers Fill/Click/Open/Verify patterns used in industry-style steps.",
    )

    heading(doc, "5.2 Target site reconnaissance (manual + automated discovery)", level=2)
    body(
        doc,
        "Before automating Zoho and Campus Voice, we manually opened each URL in Chromium and noted: page load time, redirect chains, login field ids (#login_id vs #user-name), and SPA navigation after sign-in. "
        "Discovery Agent automates this reconnaissance by scanning every goto URL in a suite and building a label→selector map. "
        "Key finding: projects.zoho.com redirects to www.zoho.com/projects/, so URL assertions must be redirect-aware. "
        "Campus Voice redirects from /login to /feed after authentication, requiring post-login wait logic.",
    )

    heading(doc, "5.3 Run log analysis (timing exploration)", level=2)
    add_table(
        doc,
        ["Observation from early runs", "Typical value", "Implication"],
        [
            ["Full 3-agent run (LLM + discovery + execute)", "40–60 seconds", "Acceptable for demo; optimization needed"],
            ["LLM planner + generator", "10–20 seconds", "Dominates when API cold"],
            ["Discovery scan (per URL)", "10–20 seconds", "Skipped when suite is assert-only"],
            ["Single fill step on slow sites", "Up to 30 s reported", "Healer retries + page load; mentor feedback Sep 2026"],
            ["Sauce Demo TC01 (stable site)", "Under 25 s locally", "Baseline for comparison"],
        ],
        [2.5, 1.5, 2.5],
    )
    body(
        doc,
        "Phase-2 added per-step timestamps and detailed .log files so future analysis can plot duration_ms per step_id across runs. "
        "Token usage per LLM call is not yet logged; this is planned using LangSmith or custom tracing (Dassault mentor action item, Sep 2026).",
    )

    heading(doc, "5.4 Failure pattern exploration", level=2)
    add_table(
        doc,
        ["Failure mode observed", "Example", "Fix applied"],
        [
            ["LLM assert_url includes word 'contains'", "expected: 'contains zoho.com'", "flexible_steps normalizer"],
            ["Wrong assert_text parse", "'text Projects' instead of 'Projects'", "Regex fix in flexible_steps.py"],
            ["Discovery scanned wrong URL for login", "site_url ≠ sign-in page", "Multi-URL discovery scan"],
            ["URL assert after redirect", "projects.zoho.com vs www.zoho.com/projects/", "url_assertions.py redirect matching"],
            ["SPA login not waited", "Campus Voice /feed assert too early", "Post-auth navigation wait in runner"],
        ],
        [2.0, 2.5, 2.0],
    )

    if FIG.exists():
        heading(doc, "5.5 System architecture (from CA-1, updated Phase-2)", level=2)
        doc.add_picture(str(FIG), width=Inches(5.8))
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(p.add_run("Figure 1. Pipeline architecture (Phase-1 MVP; extended in Phase-2 with 3-agent LLM pipeline)."), size=10, italic=True)

    # ---- 6 PROGRESS ----
    heading(doc, "6. Progress Since CA-1 (Summary)")
    add_table(
        doc,
        ["CA-1 baseline (Jul–Aug 2026)", "CA-2 period addition (Aug–Sep 2026)"],
        [
            ["Rule-based parser + Playwright MVP", "3-agent pipeline (Step, Discovery, Test & Report)"],
            ["Streamlit demo", "Production web UI + Render cloud deploy"],
            ["JSON + Markdown reports", "Detailed timestamped logs + screenshot API"],
            ["Sauce Demo only", "Zoho + Campus Voice validation"],
            ["Console notify", "Agent trace audit + failure screenshot view"],
        ],
        [3.5, 3.5],
    )

    # ---- 7 CONCLUSION ----
    heading(doc, "7. Conclusion")
    body(
        doc,
        "CA-2 documents how DS 1 allocates team and compute resources, identifies risks, and defines its dataset as a structured test corpus rather than a classical ML table. "
        "Three modalities dominate: structured text prompts, live DOM/browser interaction, and structured run artifacts. "
        "Exploratory work covered test coverage, target-site behaviour, timing patterns, and failure modes—leading to Phase-2 delivery of a hosted demo and industry review on 3 September 2026. "
        "Next steps include locator caching, Playwright script storage, token/latency observability, and Excel import once the Dassault template arrives.",
    )

    heading(doc, "References")
    refs = [
        "Dassault Systèmes. (2026). AI/ML projects with SIT – ENOVIA 2026 (DS 1 problem brief).",
        "Microsoft. (2025). Playwright Test Agents. https://playwright.dev/docs/test-agents",
        "Symbiosis Institute of Technology. (2026). B.Tech project CA-2 submission notice, Department of AIML.",
        "Project repository: https://github.com/shwetgaur/agentic-webapp-test-executor",
        "Live demo: https://agentic-webapp-test-executor.onrender.com",
    ]
    for ref in refs:
        p = doc.add_paragraph(ref, style="List Number")

    heading(doc, "Appendix — Similarity and AI Reports")
    body(
        doc,
        "As per department instructions: attach Guide-generated Similarity Report (target <10%) and AI plagiarism report (target 0% AI content) before final Moodle upload.",
        first_line_indent=False,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    downloads = Path.home() / "Downloads" / OUT.name
    doc.save(downloads)
    print("Wrote", OUT)
    print("Wrote", downloads)


if __name__ == "__main__":
    build()
