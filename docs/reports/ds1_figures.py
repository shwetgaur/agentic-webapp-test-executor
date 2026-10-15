"""Matplotlib figures derived from this repository only (no external project assets)."""

from pathlib import Path

REPORT_DIR = Path(__file__).resolve().parent
FIG_ARCH = REPORT_DIR / "fig_phase2_architecture.png"
FIG_REPO = REPORT_DIR / "fig_repo_layout.png"

# Module layout matches README / docs/ARCHITECTURE.md in agentic-webapp-test-executor.
REPO_BOXES = [
    "frontend/  Web UI",
    "src/backend/  FastAPI app.py",
    "src/agents/  step, discovery, test_report, healer",
    "src/executor/  Playwright runner",
    "src/reporting/  JSON + Markdown reports",
    "src/notify/  failure alerts",
    "tests/samples/structured/  YAML cases",
    "data/locators/  selector cache",
    "data/suites/  replay JSON",
    "schemas/  JSON Schema contracts",
]


def make_phase2_architecture_fig() -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=(10.2, 5.8))
    ax.set_xlim(0, 10.2)
    ax.set_ylim(0, 5.8)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    boxes = [
        (0.2, 2.35, 1.55, 1.25, "StructuredTestPrompt\n(form / YAML)", "#D6EAF8"),
        (2.0, 2.35, 1.55, 1.25, "step_agent.py\nAgent 1", "#D5F5E3"),
        (3.8, 2.35, 1.55, 1.25, "discovery_agent.py\nAgent 2", "#FCF3CF"),
        (5.6, 2.35, 1.55, 1.25, "test_report_agent.py\n+ runner.py", "#FAD7A0"),
        (7.4, 3.55, 1.65, 1.0, "notify/agent.py", "#F5B7B1"),
        (7.4, 1.15, 1.65, 1.0, "frontend/\n+ Cloud Run", "#E8DAEF"),
        (0.2, 0.55, 2.8, 0.85, "SuiteStore: data/suites/", "#EBF5FB"),
        (3.2, 0.55, 2.8, 0.85, "LocatorStore: data/locators/", "#EBF5FB"),
    ]
    for x, y, w, h, label, color in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.03,rounding_size=0.12",
                facecolor=color,
                edgecolor="#1F4E79",
                linewidth=1.3,
            )
        )
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=8, color="#1F1F1F")

    for (x1, y1), (x2, y2) in [
        ((1.75, 2.95), (2.0, 2.95)),
        ((3.55, 2.95), (3.8, 2.95)),
        ((5.35, 2.95), (5.6, 2.95)),
        ((7.15, 3.2), (7.4, 3.85)),
        ((7.15, 2.7), (7.4, 1.65)),
    ]:
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", color="#1F4E79", lw=1.2),
        )

    ax.set_title(
        "DS-1 repo: orchestrator.py pipeline (see docs/ARCHITECTURE.md)",
        fontsize=10,
        pad=8,
        color="#1F4E79",
    )
    fig.tight_layout()
    fig.savefig(FIG_ARCH, dpi=180, bbox_inches="tight")
    plt.close()
    return FIG_ARCH


def make_repo_layout_fig() -> Path:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(REPO_BOXES) + 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    for i, line in enumerate(REPO_BOXES):
        y = len(REPO_BOXES) - i
        ax.text(0.3, y, line, fontsize=10, va="center", family="monospace", color="#1F1F1F")
        ax.plot([0.2, 9.8], [y - 0.35, y - 0.35], color="#D5D8DC", linewidth=0.8)

    ax.set_title(
        "Repository layout (agentic-webapp-test-executor)",
        fontsize=11,
        color="#1F4E79",
        pad=12,
    )
    fig.tight_layout()
    fig.savefig(FIG_REPO, dpi=180, bbox_inches="tight")
    plt.close()
    return FIG_REPO


def build_all() -> None:
    make_phase2_architecture_fig()
    make_repo_layout_fig()
