"""Pass/fail report writers (JSON + Markdown)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.common.models import TestReport


def _fmt_ts(dt: datetime | None) -> str:
    if not dt:
        return "n/a"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


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
    ]
    if report.replay_mode:
        lines.append("- **Replay mode:** yes (cached suite)")
    if report.suite_snapshot_path:
        lines.append(f"- **Cached suite:** `{report.suite_snapshot_path}`")
    lines.extend([
        "",
        "## Summary",
        "",
        f"| Total | Passed | Failed | Skipped |",
        f"|------:|-------:|-------:|--------:|",
        f"| {report.summary.total} | {report.summary.passed} | {report.summary.failed} | {report.summary.skipped} |",
        "",
        "## Step Results",
        "",
        "| Step | Action | Status | Started | Finished | Duration (ms) | Expected | Actual / Error | Screenshot |",
        "|------|--------|--------|---------|----------|--------------:|----------|----------------|------------|",
    ])
    for s in report.steps:
        err = s.error or s.actual or ""
        err = err.replace("|", "\\|")
        shot = s.screenshot_path or ""
        lines.append(
            f"| {s.step_id} | {s.action} | {s.status.value} | {_fmt_ts(s.started_at)} | "
            f"{_fmt_ts(s.finished_at)} | {s.duration_ms} | {s.expected or ''} | {err} | {shot} |"
        )

    lines.extend(["", "## Notification", ""])
    n = report.notify
    lines.append(f"- Triggered: `{n.triggered}`")
    lines.append(f"- Team: `{n.team}`")
    lines.append(f"- Channel: `{n.channel}`")
    lines.append(f"- Ticket: `{n.ticket_id}`")

    if report.agent_traces:
        lines.extend(["", "## Agent Pipeline", ""])
        lines.append("| Timestamp | Agent | Phase | Duration (ms) | Tokens | Detail |")
        lines.append("|-----------|-------|-------|--------------:|--------|--------|")
        for t in report.agent_traces:
            detail = (t.detail or "").replace("|", "\\|")
            tokens = ""
            if t.tokens_prompt is not None or t.tokens_completion is not None:
                tokens = f"{t.tokens_prompt or 0}/{t.tokens_completion or 0}"
            dur = t.duration_ms if t.duration_ms is not None else ""
            lines.append(
                f"| {_fmt_ts(t.timestamp)} | {t.agent} | {t.phase} | {dur} | {tokens} | {detail} |"
            )

    if report.llm_calls:
        lines.extend(["", "## LLM Usage", ""])
        lines.append("| Caller | Provider | Model | Prompt | Completion | Total | Latency (ms) |")
        lines.append("|--------|----------|-------|-------:|-----------:|------:|-------------:|")
        for c in report.llm_calls:
            lines.append(
                f"| {c.caller} | {c.provider} | {c.model} | {c.prompt_tokens} | "
                f"{c.completion_tokens} | {c.total_tokens} | {c.latency_ms} |"
            )

    if report.phase_timings:
        lines.extend(["", "## Phase Timings", ""])
        lines.append("| Phase | Duration (ms) | Detail |")
        lines.append("|-------|--------------:|--------|")
        for pt in sorted(report.phase_timings, key=lambda p: p.duration_ms, reverse=True):
            detail = (pt.detail or "").replace("|", "\\|")
            lines.append(f"| {pt.phase} | {pt.duration_ms} | {detail} |")

    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
