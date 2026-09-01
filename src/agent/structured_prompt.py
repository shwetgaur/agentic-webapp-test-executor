"""Validate structured test prompts and convert to executable TestSuite."""

from __future__ import annotations

from typing import Optional

from pydantic import ValidationError

from src.agent.flexible_steps import parse_flexible_line, suite_from_natural_steps
from src.common.models import StructuredTestPrompt, TestSuite


def _parse_single_step(step_id: str, raw: str):
    step = parse_flexible_line(step_id, raw)
    if not step:
        raise ValueError(
            f"Unrecognized step format: '{raw}'. "
            "Use: Open/Fill/Click/Select/Verify text/Verify URL ..."
        )
    return step


def structured_prompt_to_suite(prompt: StructuredTestPrompt) -> TestSuite:
    """Convert validated structured prompt into TestSuite for Playwright."""
    step_lines = [s.strip() for s in prompt.steps if s.strip()]
    if not step_lines:
        raise ValueError("At least one step is required")
    return suite_from_natural_steps(prompt, step_lines)


def parse_structured_dict(data: dict) -> TestSuite:
    try:
        prompt = StructuredTestPrompt.model_validate(data)
    except ValidationError as exc:
        missing = [e["loc"][0] for e in exc.errors() if e["type"] == "missing"]
        if missing:
            raise ValueError(
                f"Structured prompt incomplete. Missing required fields: {', '.join(map(str, missing))}"
            ) from exc
        raise ValueError(f"Invalid structured prompt: {exc}") from exc
    return structured_prompt_to_suite(prompt)


def parse_structured_yaml_or_json(text: str, *, format_hint: Optional[str] = None) -> TestSuite:
    import json

    import yaml

    text = text.strip()
    if format_hint == "json" or text.startswith("{"):
        return parse_structured_dict(json.loads(text))
    return parse_structured_dict(yaml.safe_load(text))


def build_demo_text_from_structured(prompt: StructuredTestPrompt) -> str:
    """Legacy plain-text block for debugging."""
    step_lines = [s.strip() for s in prompt.steps if s.strip()]
    if step_lines and not step_lines[0].lower().startswith(("open ", "go to ", "navigate to ", "goto ")):
        step_lines.insert(0, f"Open {prompt.site_url}")
    lines = [
        f"## {prompt.test_id}",
        f"Module: {prompt.feature}",
        f"Site: {prompt.site_url}",
        f"Objective: {prompt.objective}",
        f"Expected: {prompt.expected_outcome}",
    ]
    for i, step in enumerate(step_lines, start=1):
        lines.append(f"{i}. {step}")
    return "\n".join(lines)
