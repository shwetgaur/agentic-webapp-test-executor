"""Build complete DS-1 project report (Aug–Oct 2026) as .docx.

All figures and tables describe files in agentic-webapp-test-executor only.
"""

import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

REPORT_DIR = Path(__file__).resolve().parent
if str(REPORT_DIR) not in sys.path:
    sys.path.insert(0, str(REPORT_DIR))

from ds1_figures import FIG_ARCH, FIG_REPO, build_all  # noqa: E402

OUT = REPORT_DIR / "DS1_Complete_Project_Report_October_2026.docx"
DOWNLOADS = Path.home() / "Downloads" / OUT.name


def set_run_font(run, name="Times New Roman", size=12, bold=False, italic=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), name)
    rFonts.set(qn("w:hAnsi"), name)
    rFonts.set(qn("w:eastAsia"), name)


def add_page_number(paragraph):
    run = paragraph.add_run()
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)
    set_run_font(run, size=10)


def shade_header_row(row):
    for cell in row.cells:
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "1F4E79")
        shd.set(qn("w:val"), "clear")
        tcPr.append(shd)
        for p in cell.paragraphs:
            for run in p.runs:
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.bold = True
                set_run_font(run, size=10, bold=True)


def set_cell_text(cell, text, bold=False, size=10, align="left"):
    cell.text = ""
    p = cell.paragraphs[0]
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold)


def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for i, h in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], h, bold=True, size=10, align="center")
    shade_header_row(table.rows[0])
    for r_i, row in enumerate(rows, 1):
        for c, val in enumerate(row):
            set_cell_text(table.rows[r_i].cells[c], str(val), size=10)
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph()
    return table


def body(doc, text, first_line_indent=True):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_after = Pt(8)
    if first_line_indent:
        p.paragraph_format.first_line_indent = Cm(1.25)
    set_run_font(p.add_run(text))
    return p


def heading(doc, text):
    p = doc.add_heading(text, level=1)
    for run in p.runs:
        set_run_font(run, size=14, bold=True)
        run.font.color.rgb = RGBColor(31, 78, 121)
    return p


def heading2(doc, text):
    p = doc.add_heading(text, level=2)
    for run in p.runs:
        set_run_font(run, size=13, bold=True)
        run.font.color.rgb = RGBColor(31, 78, 121)
    return p


def caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run(text), size=10, italic=True)


def build():
    build_all()
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    for attr in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(section, attr, Cm(2.54))

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(
        header.add_run(
            "Department of Artificial Intelligence & Machine Learning, SIT Pune  |  "
            "B.Tech Project DS-1  |  AY 2026-27"
        ),
        size=9,
    )
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(footer.add_run("Complete Project Report  •  October 2026  •  Page "), size=10)
    add_page_number(footer)

    # Cover
    for text, size, bold in [
        ("Project ID: DS-1 (Dassault Systèmes — Quality Engineering)", 12, True),
        ("SYMBIOSIS INSTITUTE OF TECHNOLOGY, PUNE", 14, True),
        ("Department of Artificial Intelligence and Machine Learning", 12, True),
        ("B. Tech. Project — Consolidated Report", 16, True),
        ("Agentic Web-App Test Executor", 20, True),
        ("August 2026 – October 2026 (Phase-1 MVP + Phase-2 + Mentor Action Items)", 12, False),
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(p.add_run(text), size=size, bold=bold)

    doc.add_paragraph()
    add_table(
        doc,
        ["Sr.", "Name of Student", "PRN"],
        [
            ["1", "Shwet Gaur", "23070126126"],
            ["2", "Sahishnu Raut", "23070126118"],
            ["3", "Eesha Barad", "23070126161"],
            ["4", "Saksham Sharma", "23070126113"],
        ],
        [0.7, 3.5, 2.5],
    )
    for line in ("Faculty Guide: Prof. Mayur Gaikwad", "Industry Partner: Dassault Systèmes (ENOVIA)", "Submission: October 2026"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(p.add_run(line), size=12)

    doc.add_page_break()

    heading(doc, "Executive Summary")
    body(
        doc,
        "The Agentic Web-App Test Executor (DS 1) automates structured UI test cases for Dassault Quality Engineering. "
        "Testers supply a fixed-form prompt (site URL, feature, objective, expected outcome, ordered steps). "
        "The system runs a three-agent pipeline—step planning, module discovery, execution with healing—using Playwright, "
        "writes JSON and Markdown reports with screenshots on failure, and notifies the mapped owning team. "
        "Phase-1 (August 2026) delivered the rule-based vertical slice. Phase-2 (September 2026) added LLM agents, "
        "locator and suite caching, replay, observability, a production web UI, and cloud deployment. "
        "September mentor meetings added GCS-backed artifact storage, Excel bulk import, and suite upload for Cloud Run redeploys.",
    )
    body(
        doc,
        "Live demo URL: https://agentic-webapp-test-executor-275092957818.us-central1.run.app "
        "(Google Cloud Run). Source: https://github.com/shwetgaur/agentic-webapp-test-executor.",
        first_line_indent=False,
    )

    heading(doc, "1. Introduction")
    body(
        doc,
        "Web applications are released frequently; regression testing remains largely manual or dependent on brittle automation scripts. "
        "Dassault DS 1 asks for an agentic executor that reads basic text steps, replays user actions, and verifies behaviour. "
        "Faculty guidance requires structured input (not arbitrary free-form prompts), auditable reports, and team notification on failure.",
    )

    heading(doc, "2. Problem Statement")
    body(
        doc,
        "Design and implement a Quality Engineering automation platform that: (1) validates structured test prompts, "
        "(2) converts natural-language step lines into executable Playwright actions, (3) discovers or reuses UI selectors, "
        "(4) executes flows with optional self-healing, (5) documents pass/fail with evidence, and (6) routes failures to the correct team.",
    )

    heading(doc, "3. Objectives and Status")
    add_table(
        doc,
        ["ID", "Objective", "Status (Oct 2026)"],
        [
            ["O1", "Structured prompt validation and TestSuite generation", "Done (LLM + rules)"],
            ["O2", "Playwright execution on Chromium", "Done"],
            ["O3", "Assertions (text, URL, visibility)", "Done"],
            ["O4", "JSON/MD reports + failure screenshots", "Done"],
            ["O5", "Notify team with ticket ID", "Done (console; Slack optional)"],
            ["O6", "AI-assisted parsing and locator recovery", "Partial (healer + discovery)"],
            ["O7", "Cloud demo and industry-ready UI", "Done (Cloud Run + web UI)"],
            ["O8", "Persistent cache and bulk import", "Done (GCS + Excel; GCS optional on deploy)"],
        ],
        [0.6, 4.2, 2.6],
    )

    heading(doc, "4. Literature Review (Summary)")
    body(
        doc,
        "Microsoft Playwright Test Agents (planner, generator, healer) inform our three-agent split. "
        "Commercial tools such as Tricentis Testim demonstrate smart locators. Academic work (Nass et al., 2024; ICECIT 2025) "
        "covers LLM localisation and self-healing trade-offs. Robula+ remains the pre-AI locator baseline. "
        "Summaries match docs/MVP_SPECIFICATION.md and docs/DEMO_PREP.md in this repository. "
        "Full APA references appear in Section 13.",
    )

    heading(doc, "5. Research and Technology Gap")
    body(
        doc,
        "Open, schema-first pipelines that combine structured prompts, multi-agent orchestration, downloadable locator/suite artifacts, "
        "LLM observability, and team routing are rare in academic prototypes. DS 1 targets that integrated gap for ENOVIA-style QE workflows.",
    )

    heading(doc, "6. Proposed Solution and Architecture")
    body(
        doc,
        "StructuredTestPrompt enters src/agents/orchestrator.py (AgentOrchestrator). Full runs invoke step_agent.py, "
        "discovery_agent.py, and test_report_agent.py with src/executor/runner.py. "
        "Replay mode loads data/suites/{test_id}_latest.json and skips Agents 1 and 2. "
        "Locator maps persist under data/locators/ or GCS via src/agents/artifact_storage.py when ARTIFACT_STORAGE=gcs.",
    )
    if FIG_ARCH.exists():
        doc.add_picture(str(FIG_ARCH), width=Inches(6.2))
        caption(doc, "Figure 1. DS-1 pipeline (file names from docs/ARCHITECTURE.md).")

    heading2(doc, "6.1 Mentor action items (Sep 2026)")
    add_table(
        doc,
        ["Item", "Implementation"],
        [
            ["Locator cache + API download", "src/agents/artifact_store.py; GET /api/v1/locators in src/backend/app.py"],
            ["Suite JSON replay", "SuiteStore; frontend replay control; POST /api/v1/replay/{test_id}"],
            ["LLM tokens + LangSmith", "src/agents/llm_client.py, llm_observability.py"],
            ["Phase timings", "src/reporting/performance_summary.py"],
            ["Cookie/session isolation", "tests/samples/structured/ZOHO_TC06_cookie_clear_homepage.yaml; runner settings"],
            ["GCS persistence", "src/agents/artifact_storage.py"],
            ["Excel import", "src/importers/excel_importer.py"],
            ["Restore suite after redeploy", "POST /api/v1/suites/upload"],
        ],
        [2.5, 4.8],
    )

    heading(doc, "7. Technology Stack")
    add_table(
        doc,
        ["Layer", "Technologies"],
        [
            ["Language / runtime", "Python 3.11+"],
            ["Browser automation", "Playwright (Chromium)"],
            ["API & UI", "FastAPI, Uvicorn, HTML/CSS/JS frontend, Streamlit (legacy local)"],
            ["AI", "Groq / OpenAI / Ollama; optional LangSmith"],
            ["Data", "Pydantic models, JSON Schema, YAML samples, openpyxl"],
            ["Cloud", "Docker, Google Cloud Run, optional GCS"],
            ["Quality", "pytest, GitHub Actions"],
        ],
        [2.0, 5.2],
    )

    heading(doc, "8. Implementation Summary")
    heading2(doc, "8.1 Phase-1 (August 2026)")
    body(
        doc,
        "Packages src/agent, src/executor, src/reporting, src/notify; rule parser; Sauce Demo structured cases; "
        "Streamlit demo; FastAPI endpoints; team_ownership.yaml; console notify with ticket IDs.",
    )
    heading2(doc, "8.2 Phase-2 (September 2026)")
    body(
        doc,
        "src/agents: step_agent, discovery_agent, test_report_agent, healer, orchestrator. "
        "Flexible NL parser and LLM normalizer. Multi-URL discovery and Zoho login hints. "
        "Web dashboard at /. Deployment on Cloud Run with Playwright Docker image.",
    )
    heading2(doc, "8.3 Sample files in tests/samples/")
    add_table(
        doc,
        ["Path", "Role"],
        [
            ["tests/samples/structured/TC01_login_success.yaml", "Sauce Demo PASS baseline"],
            ["tests/samples/structured/TC10_intentional_fail.yaml", "Failure + notify demo"],
            ["tests/samples/structured/ZOHO_TC01_homepage.yaml … ZOHO_TC06_*.yaml", "Zoho flows"],
            ["tests/samples/structured/CV_test_login_1.yaml", "Campus Voice case"],
            ["tests/samples/text/*.txt, tests/samples/json/*.json", "Legacy parser inputs"],
        ],
        [3.4, 3.4],
    )

    heading2(doc, "8.4 Repository layout")
    if FIG_REPO.exists():
        doc.add_picture(str(FIG_REPO), width=Inches(5.8))
        caption(doc, "Figure 2. Top-level packages in agentic-webapp-test-executor (README.md).")

    heading(doc, "9. Testing and Quality Assurance")
    body(
        doc,
        "Unit tests under tests/unit/ cover structured prompt validation, parser, flexible steps, agents, discovery cache, "
        "replay orchestrator, URL assertions, Excel importer (test_excel_importer.py), artifact storage, and locator API. "
        "Manual demo scripts are in docs/DEMO_PREP.md.",
    )

    heading(doc, "10. Deployment and Operations")
    body(
        doc,
        "Production deploy uses scripts/deploy_cloud_run.ps1 and docs/DEPLOY_CLOUD_RUN.md. "
        "Health endpoints: GET /health and GET /ping. Environment variables include GROQ_API_KEY, LANGSMITH_*, "
        "ARTIFACT_STORAGE, GCS_BUCKET, and GCS_PREFIX. Cloud Run uses ephemeral disk by default; "
        "configure GCS for durable locator and suite cache. Revision 00012 addressed FastAPI multipart dependency for Excel upload.",
    )

    heading(doc, "11. Work Distribution")
    add_table(
        doc,
        ["Member", "Primary ownership"],
        [
            ["Shwet Gaur", "Executor, orchestration integration, Cloud Run, end-to-end demos"],
            ["Sahishnu Raut", "Schemas, parser, LLM step contracts, architecture documentation"],
            ["Eesha Barad", "FastAPI, web UI, reporting formats, Excel import API"],
            ["Saksham Sharma", "Notify agent, sample corpus, logbook, report drafting"],
        ],
        [1.8, 5.0],
    )

    heading(doc, "12. Conclusion and Future Work")
    body(
        doc,
        "The project meets the DS 1 brief for an agentic structured test executor with industry-aligned agent architecture, "
        "auditable outputs, and a hosted demo. Remaining work includes stronger post-login assertions on complex apps (Zoho), "
        "production integrations (Slack/Jira/ClickUp when credentials are available), expanded evaluation metrics, and enabling GCS on the live service for persistent cache.",
    )

    heading(doc, "13. References (APA style)")
    refs = [
        "Dassault Systèmes. (2026). AI/ML projects with SIT — DS 1 Agentic Web-App Test Executor (industry brief).",
        "Microsoft. (2025–26). Playwright test agents. https://playwright.dev/docs/test-agents",
        "Nass, A., Alégroth, E., & Feldt, R. (2024). On LLM-based web element localisation (as cited in project literature review).",
        "Tricentis. (n.d.). Testim documentation — smart locators and NL testing.",
        "Shwet Gaur et al. (2026). agentic-webapp-test-executor [Source code]. GitHub. https://github.com/shwetgaur/agentic-webapp-test-executor",
    ]
    for r in refs:
        p = doc.add_paragraph(r, style="List Bullet")
        for run in p.runs:
            set_run_font(run, size=11)

    doc.save(str(OUT))
    shutil_copy = __import__("shutil")
    shutil_copy.copy2(OUT, DOWNLOADS)
    print(f"Wrote: {OUT}")
    print(f"Copied: {DOWNLOADS}")


if __name__ == "__main__":
    build()
