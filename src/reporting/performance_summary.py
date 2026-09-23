"""Aggregate phase timings and LLM usage for performance analysis."""

from __future__ import annotations

from src.common.models import LLMCallMetrics, PhaseTiming, TestReport


def build_phase_timings_from_traces(report: TestReport) -> list[PhaseTiming]:
    """Derive phase timings from agent traces that recorded duration_ms."""
    timings: list[PhaseTiming] = []
    for trace in report.agent_traces:
        if trace.duration_ms is None:
            continue
        key = f"{trace.agent}.{trace.phase}"
        timings.append(
            PhaseTiming(
                phase=key,
                duration_ms=trace.duration_ms,
                detail=trace.detail[:120] if trace.detail else None,
            )
        )
    return timings


def merge_phase_timings(report: TestReport) -> list[PhaseTiming]:
    explicit = list(report.phase_timings)
    if explicit:
        return explicit
    return build_phase_timings_from_traces(report)


def render_performance_summary(report: TestReport) -> list[str]:
    """Human-readable performance breakdown for detailed logs."""
    lines: list[str] = ["--- Performance Breakdown ---", ""]
    timings = merge_phase_timings(report)
    if timings:
        sorted_phases = sorted(timings, key=lambda p: p.duration_ms, reverse=True)
        lines.append(f"{'Phase':<40} {'Duration (ms)':>14} {'% of run':>10}")
        lines.append("-" * 66)
        total_run = max(report.duration_ms, 1)
        for pt in sorted_phases:
            pct = (pt.duration_ms / total_run) * 100
            lines.append(f"{pt.phase:<40} {pt.duration_ms:>14} {pct:>9.1f}%")
        lines.append("")
        slowest = sorted_phases[0]
        lines.append(
            f"Slowest phase: {slowest.phase} ({slowest.duration_ms} ms, "
            f"{(slowest.duration_ms / total_run) * 100:.1f}% of total run time)"
        )
    else:
        lines.append("No per-phase timing recorded.")

    lines.extend(["", "--- LLM Token Usage ---", ""])
    if report.llm_calls:
        lines.append(
            f"{'Caller':<14} {'Prompt':>8} {'Completion':>12} {'Total':>8} {'Latency (ms)':>14}"
        )
        lines.append("-" * 60)
        for call in report.llm_calls:
            lines.append(
                f"{call.caller:<14} {call.prompt_tokens:>8} {call.completion_tokens:>12} "
                f"{call.total_tokens:>8} {call.latency_ms:>14}"
            )
        total_p = sum(c.prompt_tokens for c in report.llm_calls)
        total_c = sum(c.completion_tokens for c in report.llm_calls)
        total_t = sum(c.total_tokens for c in report.llm_calls)
        total_l = sum(c.latency_ms for c in report.llm_calls)
        lines.append("-" * 60)
        lines.append(
            f"{'TOTAL':<14} {total_p:>8} {total_c:>12} {total_t:>8} {total_l:>14}"
        )
    else:
        lines.append("No LLM calls recorded (rule-only run or LLM disabled).")

    slow_steps = sorted(
        [s for s in report.steps if s.duration_ms > 0],
        key=lambda s: s.duration_ms,
        reverse=True,
    )[:5]
    if slow_steps:
        lines.extend(["", "--- Slowest Playwright Steps ---", ""])
        for step in slow_steps:
            lines.append(
                f"  {step.step_id} ({step.action}): {step.duration_ms} ms — "
                f"{step.description or step.status.value}"
            )

    lines.append("")
    return lines
