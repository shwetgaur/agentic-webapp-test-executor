"""CLI entrypoint for local runs without the API server."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent.parser import parse_plain_text_case
from src.agent.structured_prompt import parse_structured_yaml_or_json
from src.common.models import TestSuite
from src.executor.runner import PlaywrightExecutor
from src.notify.agent import NotifyAgent
from src.reporting.writer import save_json_report, save_markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic Web-App Test Executor CLI")
    parser.add_argument("--text", type=str, help="Path to plain-text test case (.md/.txt)")
    parser.add_argument("--json", type=str, help="Path to JSON suite file")
    parser.add_argument("--structured", type=str, help="Path to structured YAML/JSON prompt")
    parser.add_argument("--headed", action="store_true", help="Run browser headed (not headless)")
    args = parser.parse_args()

    if sum(bool(x) for x in (args.text, args.json, args.structured)) != 1:
        parser.error("Provide exactly one of --text, --json, or --structured")

    if args.json:
        data = json.loads(Path(args.json).read_text(encoding="utf-8"))
        suite = TestSuite.model_validate(data)
    elif args.structured:
        raw = Path(args.structured).read_text(encoding="utf-8")
        suffix = Path(args.structured).suffix.lower()
        hint = "json" if suffix == ".json" else "yaml"
        suite = parse_structured_yaml_or_json(raw, format_hint=hint)
    else:
        suite = parse_plain_text_case(Path(args.text).read_text(encoding="utf-8"))

    report = PlaywrightExecutor(headless=not args.headed).run(suite)
    report = NotifyAgent().maybe_notify(report)
    json_path = save_json_report(report)
    md_path = save_markdown_report(report)

    print(f"Status: {report.status.value}")
    print(f"Summary: {report.summary.model_dump()}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")
    if report.notify.triggered:
        print(f"Notify ticket: {report.notify.ticket_id} -> {report.notify.team}")


if __name__ == "__main__":
    main()
