"""Pass/fail report writers (JSON + Markdown)."""

from __future__ import annotations

from pathlib import Path

from src.common.models import TestReport


def save_json_report(report: TestReport, out_dir: str | Path = "data/reports") -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{report.run_id}.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return path


def save_markdown_report(report: TestReport, out_dir: str | Path = "data/reports") -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{report.run_id}.md"

    lines = [
        f"# Test Run Report — {report.suite_name or report.suite_id}",
        "",
        f"- **Run ID:** `{report.run_id}`",
        f"- **Suite ID:** `{report.suite_id}`",
        f"- **Module / Feature:** `{report.module}`",
        f"- **Site URL:** `{report.site_url or 'n/a'}`",
        f"- **Environment:** `{report.environment or 'n/a'}`",
        f"- **Objective:** {report.objective or 'n/a'}",
        f"- **Expected Outcome:** {report.expected_outcome or 'n/a'}",
        f"- **Status:** **{report.status.value.upper()}**",
        f"- **Started:** {report.started_at.isoformat()}",
        f"- **Finished:** {report.finished_at.isoformat()}",
        f"- **Duration:** {report.duration_ms} ms",
        "",
        "## Summary",
        "",
        f"| Total | Passed | Failed | Skipped |",
        f"|------:|-------:|-------:|--------:|",
        f"| {report.summary.total} | {report.summary.passed} | {report.summary.failed} | {report.summary.skipped} |",
        "",
        "## Step Results",
        "",
        "| Step | Action | Status | Expected | Actual / Error | Screenshot |",
        "|------|--------|--------|----------|----------------|------------|",
    ]
    for s in report.steps:
        err = s.error or s.actual or ""
        err = err.replace("|", "\\|")
        shot = s.screenshot_path or ""
        lines.append(
            f"| {s.step_id} | {s.action} | {s.status.value} | {s.expected or ''} | {err} | {shot} |"
        )

    lines.extend(["", "## Notification", ""])
    n = report.notify
    lines.append(f"- Triggered: `{n.triggered}`")
    lines.append(f"- Team: `{n.team}`")
    lines.append(f"- Channel: `{n.channel}`")
    lines.append(f"- Ticket: `{n.ticket_id}`")

    if report.agent_traces:
        lines.extend(["", "## Agent Pipeline", ""])
        lines.append("| Agent | Phase | Detail |")
        lines.append("|-------|-------|--------|")
        for t in report.agent_traces:
            detail = (t.detail or "").replace("|", "\\|")
            lines.append(f"| {t.agent} | {t.phase} | {detail} |")

    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
