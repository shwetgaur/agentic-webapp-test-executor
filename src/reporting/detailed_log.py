"""Human-readable detailed execution logs with per-step timestamps."""

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


def render_detailed_log(report: TestReport) -> str:
    """Build a mentor-friendly text log with timestamps and step durations."""
    lines = [
        "=" * 80,
        f"TEST RUN LOG — {report.run_id}",
        f"Suite: {report.suite_name or report.suite_id} ({report.suite_id})",
        f"Module / Feature: {report.module or 'n/a'}",
        f"Site URL: {report.site_url or 'n/a'}",
        f"Environment: {report.environment or 'n/a'}",
        f"Objective: {report.objective or 'n/a'}",
        f"Expected Outcome: {report.expected_outcome or 'n/a'}",
        f"Status: {report.status.value.upper()}",
        f"Run started:  {_fmt_ts(report.started_at)}",
        f"Run finished: {_fmt_ts(report.finished_at)}",
        f"Total duration: {report.duration_ms} ms",
        f"Summary: {report.summary.passed} passed / {report.summary.failed} failed / "
        f"{report.summary.skipped} skipped (total {report.summary.total})",
        "=" * 80,
        "",
    ]

    if report.agent_traces:
        lines.extend(["--- Agent Pipeline ---", ""])
        for trace in report.agent_traces:
            lines.append(
                f"[{_fmt_ts(trace.timestamp)}] {trace.agent}.{trace.phase} — {trace.detail}"
            )
        lines.append("")

    lines.extend(["--- Step Execution (timestamped) ---", ""])
    for step in report.steps:
        lines.append(
            f"[{_fmt_ts(step.started_at)}] STEP {step.step_id} START  "
            f"{step.action}  {step.description or ''}".rstrip()
        )
        detail_parts = [
            f"status={step.status.value}",
            f"duration={step.duration_ms}ms",
            f"finished={_fmt_ts(step.finished_at)}",
        ]
        if step.expected:
            detail_parts.append(f"expected={step.expected}")
        if step.actual:
            detail_parts.append(f"actual={step.actual}")
        if step.error:
            detail_parts.append(f"error={step.error}")
        if step.screenshot_path:
            detail_parts.append(f"screenshot={step.screenshot_path}")
        lines.append(f"[{_fmt_ts(step.finished_at)}] STEP {step.step_id} END    " + " | ".join(detail_parts))
        lines.append("")

    notify = report.notify
    lines.extend(
        [
            "--- Notification ---",
            f"Triggered: {notify.triggered}",
            f"Team: {notify.team or 'n/a'}",
            f"Channel: {notify.channel or 'n/a'}",
            f"Ticket: {notify.ticket_id or 'n/a'}",
            "",
            "=" * 80,
            f"END OF LOG — {report.run_id}",
            "=" * 80,
            "",
        ]
    )
    return "\n".join(lines)


def save_detailed_log(report: TestReport, out_dir: str | Path = "data/logs") -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{report.run_id}.log"
    path.write_text(render_detailed_log(report), encoding="utf-8")
    return path
