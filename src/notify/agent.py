"""Scrum-style failure notification agent."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from src.common.models import NotifyInfo, RunStatus, TestReport
from src.common.settings import settings


@dataclass
class TeamTarget:
    key: str
    display_name: str
    email: Optional[str]
    slack_channel: Optional[str]


class NotifyAgent:
    def __init__(self, ownership_path: str | Path = "config/team_ownership.yaml") -> None:
        self.ownership_path = Path(ownership_path)
        self.config = self._load()

    def _load(self) -> dict[str, Any]:
        with self.ownership_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def resolve_team(self, module: Optional[str]) -> TeamTarget:
        module_owners = self.config.get("module_owners", {})
        teams = self.config.get("teams", {})
        team_key = module_owners.get(module or "", self.config.get("default_team", "qa-platform"))
        team = teams.get(team_key, {})
        return TeamTarget(
            key=team_key,
            display_name=team.get("display_name", team_key),
            email=team.get("email"),
            slack_channel=team.get("slack_channel"),
        )

    def maybe_notify(self, report: TestReport) -> TestReport:
        if not settings.notify_enabled:
            return report
        if report.status == RunStatus.PASSED:
            report.notify = NotifyInfo(triggered=False)
            return report

        team = self.resolve_team(report.module)
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        failed_steps = [s for s in report.steps if s.status.value in ("failed", "error")]
        first = failed_steps[0] if failed_steps else None

        message = self._format_message(report, team, ticket_id, first)
        channel = settings.notify_channel
        self._dispatch(channel, message, team)

        report.notify = NotifyInfo(
            triggered=True,
            team=team.display_name,
            channel=channel,
            ticket_id=ticket_id,
        )
        return report

    def _format_message(self, report: TestReport, team: TeamTarget, ticket_id: str, first) -> str:
        step_line = "n/a"
        if first:
            step_line = f"{first.step_id} ({first.action}): {first.error or first.actual or 'failed'}"
        return (
            f"[QA FAILURE] {ticket_id}\n"
            f"Suite: {report.suite_id} — {report.suite_name}\n"
            f"Module: {report.module}\n"
            f"Owner team: {team.display_name}\n"
            f"Run: {report.run_id} | Status: {report.status.value}\n"
            f"Failed step: {step_line}\n"
            f"Summary: {report.summary.passed} passed / {report.summary.failed} failed / "
            f"{report.summary.skipped} skipped (total {report.summary.total})\n"
            f"Contact: {team.email or 'n/a'} | Slack: {team.slack_channel or 'n/a'}"
        )

    def _dispatch(self, channel: str, message: str, team: TeamTarget) -> None:
        # Phase-1: console channel is enough for demos / mentor review.
        # Slack/email hooks land in Phase-4 without changing this interface.
        print("\n===== NOTIFY AGENT =====")
        print(message)
        print("========================\n")
        if channel == "slack" and settings.slack_webhook_url:
            try:
                import httpx

                httpx.post(settings.slack_webhook_url, json={"text": message}, timeout=10)
            except Exception as exc:  # noqa: BLE001
                print(f"[notify] Slack send failed: {exc}")
