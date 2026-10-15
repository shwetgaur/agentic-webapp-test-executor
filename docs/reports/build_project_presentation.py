"""Generate DS-1 complete project PPT (CA-1 college template format).

Uses the college slide masters for layout only. Removes leftover pictures/tables
from the sample deck (other groups' projects) and inserts figures generated from
this repository (docs/reports/ds1_figures.py).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

REPORT_DIR = Path(__file__).resolve().parent
if str(REPORT_DIR) not in sys.path:
    sys.path.insert(0, str(REPORT_DIR))

from ds1_figures import FIG_ARCH, FIG_REPO, build_all  # noqa: E402
TEMPLATE = Path(
    r"C:\Users\shwet\Downloads\PBL-2 Review Presentation (CA-1)Template_CA (2).pptx"
)
OUT = REPORT_DIR / "DS1_Agentic_Test_Executor_Complete_Presentation_October_2026.pptx"
DOWNLOADS = Path.home() / "Downloads" / OUT.name

DATE = "15-10-2026"
TEAM = (
    "Group Members:\n"
    "Shwet Gaur (23070126126)\n"
    "Sahishnu Raut (23070126118)\n"
    "Eesha Barad (23070126161)\n"
    "Saksham Sharma (23070126113)"
)


def scrub_slide(
    slide,
    *,
    drop_pictures: bool = True,
    drop_tables: bool = False,
    drop_groups: bool = False,
) -> None:
    """Remove embedded media from the filled CA-1 sample deck (other projects)."""
    sp_tree = slide.shapes._spTree
    for shape in list(slide.shapes):
        st = shape.shape_type
        if drop_pictures and st == MSO_SHAPE_TYPE.PICTURE:
            sp_tree.remove(shape.element)
        elif drop_tables and st == MSO_SHAPE_TYPE.TABLE:
            sp_tree.remove(shape.element)
        elif drop_groups and st == MSO_SHAPE_TYPE.GROUP:
            sp_tree.remove(shape.element)


def _is_page_number(text: str) -> bool:
    return text.isdigit() and len(text) <= 2


def _patch_footers(shape, date: str) -> bool:
    """Return True if shape was footer-only and should not receive body text."""
    if not shape.has_text_frame:
        return True
    raw = shape.text_frame.text.strip()
    if _is_page_number(raw):
        return True
    if "Department of Artificial Intelligence" in raw:
        for para in shape.text_frame.paragraphs:
            if "17-01-2025" in para.text:
                para.text = para.text.replace("17-01-2025", date)
        return True
    if raw in ("17-01-2025", "Date"):
        shape.text_frame.text = date
        return True
    return False


def _set_shape_text(shape, text: str) -> None:
    tf = shape.text_frame
    tf.clear()
    lines = text.split("\n")
    tf.paragraphs[0].text = lines[0]
    for line in lines[1:]:
        tf.add_paragraph().text = line


def replace_slide_body(slide, texts: list[str], date: str = DATE) -> None:
    body_shapes = []
    for sh in slide.shapes:
        if _patch_footers(sh, date):
            continue
        if sh.has_text_frame and sh.text_frame.text.strip():
            body_shapes.append(sh)
    for sh, txt in zip(body_shapes, texts):
        _set_shape_text(sh, txt)


def add_picture(slide, path: Path, top: float = 1.35, width: float = 9.1) -> None:
    if path.exists():
        slide.shapes.add_picture(str(path), Inches(0.45), Inches(top), width=Inches(width))


SLIDE_TEXTS: list[list[str]] = [
    [
        "Project Based Learning-2\nSemester: VII  Batch: 2023-27",
        "PBL-2 Review Presentation (Complete Project — October 2026)",
        "Title of the Project: Agentic Web-App Test Executor\n(Domain: Quality Engineering — Dassault DS 1)",
        TEAM,
        "Name of the Guide: Prof. Mayur Gaikwad",
        DATE,
        "GroupID: DS-1",
    ],
    [
        "Outline of the Presentation",
        "Names of all the group members and their work distribution\nIntroduction\nProblem Statement\nObjectives of the Project\nProject plan with timeline\nLiterature Review\nGap in the Research / Technology / Methodology\nProposed Solution & Architecture\nTechnology Stack\nWork done till now (Phase-1, Phase-2, Sep 2026 mentor items)\nDeployment on Google Cloud Run\nConclusion & References",
    ],
    [
        "Name of all the group members and their work distribution",
        "Shwet Gaur — Orchestrator, Playwright executor, Cloud Run deploy, integration\n"
        "Sahishnu Raut — Step schema, LLM contracts, parser & flexible NL steps\n"
        "Eesha Barad — FastAPI, web UI, reports (JSON/MD), Excel import API\n"
        "Saksham Sharma — Notify agent, sample suites, documentation & QA",
    ],
    [
        "Introduction",
        "Manual UI regression is slow; scripted automation breaks when locators change.",
        "Dassault DS 1 asks for text-based steps -> browser replay -> pass/fail evidence -> team alert on failure.",
        "We deliver a structured prompt (not free-form-only) with a 3-agent AI pipeline on Playwright.",
        "Phase-1 proved the vertical slice; Phase-2 adds LLM planning, discovery, healing, web UI, and cloud hosting.",
    ],
    [
        "Problem Statement",
        "Build an agentic test executor that accepts structured test prompts, maps steps to Playwright actions, "
        "executes flows on live web apps (Sauce Demo, Zoho, Campus Voice), documents pass/fail with screenshots, "
        "and notifies the owning team when a case fails — with caching and replay for industrial QA efficiency.",
    ],
    [
        "Objectives of the project",
        "O1 — Structured input validation and step generation (LLM + rule fallback).\n\n"
        "O2 — Module discovery and locator cache per site URL + feature.\n\n"
        "O3 — Execute, heal on failure, and produce JSON/Markdown reports with phase timings.\n\n"
        "O4 — Notify mapped team on failure; optional Slack hook.\n\n"
        "O5 — Observability (LLM tokens, LangSmith); deploy demo on Cloud Run; Excel import & GCS artifacts.",
    ],
    [
        "Project plan with timeline",
        "Jul–Aug 2026: CA-1 ideation, schemas, Phase-1 MVP (parser → Playwright → report → notify).\n"
        "Sep 2026: Phase-2 — 3 agents, healer, web UI, Google Cloud Run, Zoho and Campus Voice YAML cases.\n"
        "Sep 3 mentor: locator cache, suite replay, LangSmith, cookie clearance.\n"
        "Sep 24 mentor: GCS persistence, Excel import, suite upload after redeploy.\n"
        "Oct 2026: Production hardening (python-multipart), docs, unit tests, industry demo readiness.",
    ],
    [
        "Literature Review",
        "Microsoft Playwright Test Agents (planner / generator / healer) — closest industrial pattern to DS 1.\n"
        "Tricentis Testim — smart locators & NL authoring (commercial reference).\n"
        "Nass et al. (2024) — LLM-based element localisation when selectors break.\n"
        "ICECIT 2025 — self-healing Selenium with generative AI (latency vs success trade-off).\n"
        "Robula+ — pre-AI robust locator baseline cited in our parser heuristics.",
    ],
    [
        "Gaps in Research",
        "Limited open, schema-first QE pipelines",
        "Missing unified cache + replay",
        "Fragmented observability",
        "Enterprise storage on serverless",
        "NL steps without audit trail",
        "Few student-accessible stacks combine structured prompts, 3-agent flow, step-level reports, team routing, and downloadable locator/suite artifacts in one repo.",
        "Industry tools cache internally; we expose locator JSON and suite JSON with replay API for mentor review.",
        "Token and phase timing are often hidden; we attach LLM usage and timings to every run report.",
        "Cloud Run ephemeral disk loses cache unless GCS dual-write is configured — addressed in Sep 24 work.",
        "Free-form LLM prompts are hard to validate; we require fixed metadata fields before any browser launch.",
    ],
    [
        "Proposed Solution",
        "Structured prompt -> Agent 1 (plan and generate TestSuite JSON).",
        "Agent 2 scans pages or loads locator cache -> enriches selectors.",
        "Agent 3 runs Playwright, heals failures, writes reports, notifies on fail.",
        "Replay mode skips Agents 1-2; Excel import via src/importers/excel_importer.py.",
    ],
    [
        "Architectural Diagram",
    ],
    [
        "Technology Stack",
        "Core: Python 3.11+, Playwright, Pydantic v2, FastAPI, Uvicorn, Jinja2 web UI.\n\n"
        "AI: Groq / OpenAI / Ollama via llm_client; optional LangSmith tracing.\n\n"
        "Data: YAML structured cases, JSON schemas, openpyxl Excel import.\n\n"
        "Cloud: Docker, Google Cloud Run, optional GCS (google-cloud-storage).\n\n"
        "Quality: pytest unit suite, GitHub CI, rich CLI (run_suite.py --agents).",
    ],
    [
        "Work done till now",
        "Phase-1 (Aug 2026):\n"
        "StructuredTestPrompt + rule parser; Playwright executor; JSON/MD reports; failure screenshots.\n"
        "Notify agent with team_ownership.yaml and ticket IDs; Streamlit + CLI + FastAPI /health.\n"
        "Sample cases: Sauce Demo PASS/FAIL, ten documented text scenarios.",
    ],
    [
        "Work done till now",
        "Phase-2 agents (Sep 2026):\n"
        "Step Agent — LLM planner + generator with normalizer and flexible NL parser fallback.\n"
        "Discovery Agent — multi-URL scan, Zoho login hints, locator cache under data/locators/.\n"
        "Test & Report Agent — healer (rule + LLM), detailed logs, performance summary panel in UI.\n"
        "Sep mentor items: locator/suite cache, LangSmith, GCS + Excel import (docs/SEP3_ACTION_ITEMS.md).",
    ],
    [
        "Sample test corpus (this repository)",
        "tests/samples/structured/TC01_login_success.yaml — Sauce Demo PASS\n"
        "tests/samples/structured/TC10_intentional_fail.yaml — notify demo\n"
        "tests/samples/structured/ZOHO_TC01..ZOHO_TC06 — Zoho flows\n"
        "tests/samples/structured/CV_test_login_1.yaml — Campus Voice\n"
        "tests/samples/text/ and json/ — legacy formats for parser tests",
    ],
    [
        "Schemas, config, and docs (this repository)",
        "schemas/step_schema.v1.json and report_schema.v1.json\n"
        "config/team_ownership.yaml — module to team map for notify/agent.py\n"
        "docs/ARCHITECTURE.md, PHASE2_SPECIFICATION.md, DEPLOY_CLOUD_RUN.md\n"
        "docs/SEP3_ACTION_ITEMS.md — Dassault mentor checklist status",
    ],
    [
        "Work done till now",
        "Testing & engineering:\n"
        "Unit tests for parser, agents, discovery cache, replay orchestrator, Excel importer, GCS storage.\n"
        "Docs: ARCHITECTURE.md, PHASE2_SPECIFICATION.md, DEPLOY_CLOUD_RUN.md, SEP3_ACTION_ITEMS.md.\n"
        "Repository: github.com/shwetgaur/agentic-webapp-test-executor (develop branch).",
    ],
    [
        "Deployment (this repository)",
        "Dockerfile + scripts/deploy_cloud_run.ps1 (see docs/DEPLOY_CLOUD_RUN.md).\n"
        "Live URL in README.md — FastAPI dashboard at /.\n"
        "APIs in src/backend/app.py: run, replay, locators, suites, Excel import.\n"
        "Optional GCS persistence: src/agents/artifact_storage.py (ARTIFACT_STORAGE=gcs).",
    ],
    [
        "Conclusion From Evaluation",
        "Phase-1 objectives O1–O5 are met; O6 (AI resilience) is partially met via discovery + healer.\n"
        "Structured prompts satisfy mentor input rules; replay cuts re-run time when cache exists.\n"
        "Remaining: stronger post-login asserts (Zoho TC04/TC05), production Slack/Jira, ClickUp when access granted.\n"
        "The system is demo-ready for Dassault Quality Engineering review with auditable artifacts per run.",
    ],
    [
        "References",
        "Microsoft. (2025–26). Playwright Test Agents documentation. https://playwright.dev/docs/test-agents\n"
        "Dassault Systèmes. (2026). DS 1 Agentic Web-App Test Executor — industry problem brief.\n"
        "Nass, A., Alégroth, E., & Feldt, R. (2024). LLM-based web element localisation (cited in project docs).\n"
        "Tricentis Testim product documentation — smart locator reference.\n"
        "In-repo documentation: docs/ARCHITECTURE.md, docs/MVP_SPECIFICATION.md.",
    ],
    [
        "A photograph of the DS-1 project presentation after due permission from the guide.",
    ],
]

# Slides that still had other groups' tables/icons in the college sample file.
SCRUB_TABLES = {2}
SCRUB_GROUPS = {2, 6, 12, 13, 14, 15, 16, 17}  # old dataset / SHAP / timeline graphics


def build() -> None:
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"CA-1 template not found: {TEMPLATE}")

    build_all()
    shutil.copy2(TEMPLATE, OUT)
    prs = Presentation(str(OUT))

    if len(prs.slides) != len(SLIDE_TEXTS):
        raise RuntimeError(
            f"Template has {len(prs.slides)} slides; content has {len(SLIDE_TEXTS)} entries."
        )

    for idx, (slide, texts) in enumerate(zip(prs.slides, SLIDE_TEXTS)):
        scrub_slide(
            slide,
            drop_pictures=True,
            drop_tables=idx in SCRUB_TABLES,
            drop_groups=idx in SCRUB_GROUPS,
        )
        replace_slide_body(slide, texts, date=DATE)
        if idx == 10:
            add_picture(slide, FIG_ARCH)
        if idx == 17:
            add_picture(slide, FIG_REPO, top=2.05, width=8.5)

    prs.save(str(OUT))
    shutil.copy2(OUT, DOWNLOADS)
    print(f"Wrote: {OUT}")
    print(f"Copied: {DOWNLOADS}")


if __name__ == "__main__":
    build()
