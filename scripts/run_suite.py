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
from src.agents.orchestrator import AgentOrchestrator
from src.common.models import StructuredTestPrompt, TestSuite
from src.executor.runner import PlaywrightExecutor
from src.notify.agent import NotifyAgent
from src.reporting.writer import save_json_report, save_markdown_report
from src.reuse.replay import load_replay_source, replay_stored_suite


def _load_structured_prompt(path: Path) -> StructuredTestPrompt:
    raw = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(raw)
        return StructuredTestPrompt.model_validate(data)
    data = json.loads(raw)
    return StructuredTestPrompt.model_validate(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic Web-App Test Executor CLI")
    parser.add_argument("--text", type=str, help="Path to plain-text test case (.md/.txt)")
    parser.add_argument("--json", type=str, help="Path to JSON suite file")
    parser.add_argument("--structured", type=str, help="Path to structured YAML/JSON prompt")
    parser.add_argument(
        "--replay",
        type=str,
        help="Replay a stored suite_id or path to data/scripts/*.json (skips agents)",
    )
    parser.add_argument("--agents", action="store_true", help="Run combined 3-agent pipeline")
    parser.add_argument(
        "--replay-if-stored",
        action="store_true",
        help="With --agents, skip Step+Discovery when a stored script exists",
    )
    parser.add_argument(
        "--refresh-locators",
        action="store_true",
        help="Force Discovery to re-scan even if locators are cached",
    )
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM in step agent")
    parser.add_argument("--no-discovery", action="store_true", help="Disable module discovery agent")
    parser.add_argument("--no-healer", action="store_true", help="Disable healer in test agent")
    parser.add_argument("--headed", action="store_true", help="Run browser headed (not headless)")
    args = parser.parse_args()

    if sum(bool(x) for x in (args.text, args.json, args.structured, args.replay)) != 1:
        parser.error("Provide exactly one of --text, --json, --structured, or --replay")

    headless = not args.headed

    if args.replay:
        artifact = load_replay_source(args.replay)
        report = replay_stored_suite(
            artifact.suite,
            headless=headless,
            use_healer=not args.no_healer,
        )
    elif args.structured and args.agents:
        prompt = _load_structured_prompt(Path(args.structured))
        result = AgentOrchestrator(
            headless=headless,
            use_llm=not args.no_llm,
            use_discovery=not args.no_discovery,
            use_healer=not args.no_healer,
            prefer_replay=args.replay_if_stored,
            refresh_locators=args.refresh_locators,
        ).run(prompt)
        report = result.report
    elif args.json:
        data = json.loads(Path(args.json).read_text(encoding="utf-8"))
        if isinstance(data, dict) and "suite" in data:
            suite = TestSuite.model_validate(data["suite"])
        else:
            suite = TestSuite.model_validate(data)
        report = PlaywrightExecutor(headless=headless).run(suite)
        report = NotifyAgent().maybe_notify(report)
        save_json_report(report)
        save_markdown_report(report)
    elif args.structured:
        raw = Path(args.structured).read_text(encoding="utf-8")
        suffix = Path(args.structured).suffix.lower()
        hint = "json" if suffix == ".json" else "yaml"
        suite = parse_structured_yaml_or_json(raw, format_hint=hint)
        report = PlaywrightExecutor(headless=headless).run(suite)
        report = NotifyAgent().maybe_notify(report)
        save_json_report(report)
        save_markdown_report(report)
    else:
        suite = parse_plain_text_case(Path(args.text).read_text(encoding="utf-8"))
        report = PlaywrightExecutor(headless=headless).run(suite)
        report = NotifyAgent().maybe_notify(report)
        save_json_report(report)
        save_markdown_report(report)

    print(f"Status: {report.status.value}")
    print(f"Summary: {report.summary.model_dump()}")
    json_path = Path("data/reports") / f"{report.run_id}.json"
    md_path = Path("data/reports") / f"{report.run_id}.md"
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")
    arts = report.artifacts
    if arts.script_json_path or arts.locator_path:
        print(f"Replay script: {arts.script_json_path or 'n/a'}")
        print(f"Playwright py: {arts.script_py_path or 'n/a'}")
        print(f"Locator cache: {arts.locator_path or 'n/a'}")
        print(f"Replayed: {arts.replayed}")
    if report.notify.triggered:
        print(f"Notify ticket: {report.notify.ticket_id} -> {report.notify.team}")
    if report.agent_traces:
        print("\nAgent pipeline:")
        for t in report.agent_traces:
            print(f"  [{t.agent}] {t.phase}: {t.detail}")


if __name__ == "__main__":
    main()
