"""Validate structured test prompts and convert to executable TestSuite."""

from __future__ import annotations

import re
from typing import Optional

from pydantic import ValidationError

from src.agent.parser import _guess_selector
from src.common.models import Step, StepAction, StructuredTestPrompt, TestSuite

_FILL_RE = re.compile(r"^(?:fill|enter|type)\s+(.+?)\s+with\s+(.+)$", re.I)
_CLICK_RE = re.compile(r"^(?:click|press)\s+(?:the\s+)?(.+?)(?:\s+button|\s+link)?$", re.I)
_OPEN_RE = re.compile(r"^(?:open|go to|navigate to|goto)\s+(.+)$", re.I)
_ASSERT_TEXT_RE = re.compile(r"^verify(?:\s+that)?\s+text\s+(.+?)\s+is\s+visible$", re.I)
_ASSERT_URL_RE = re.compile(r"^verify(?:\s+that)?\s+url\s+(?:contains|is)\s+(.+)$", re.I)
_SELECT_RE = re.compile(r"^select\s+(.+?)\s+from\s+(?:the\s+)?(.+)$", re.I)


def _clean(text: str) -> str:
    return text.strip().strip('"').strip("'")


def _parse_single_step(step_id: str, raw: str) -> Step:
    raw = raw.strip()
    if not raw:
        raise ValueError(f"Step {step_id} is empty")

    if m := _OPEN_RE.match(raw):
        return Step(id=step_id, action=StepAction.GOTO, url=_clean(m.group(1)), description=raw)
    if m := _FILL_RE.match(raw):
        field, value = _clean(m.group(1)), _clean(m.group(2))
        return Step(
            id=step_id,
            action=StepAction.FILL,
            selector=_guess_selector(field),
            value=value,
            description=raw,
        )
    if m := _SELECT_RE.match(raw):
        value, control = _clean(m.group(1)), _clean(m.group(2))
        return Step(
            id=step_id,
            action=StepAction.SELECT,
            selector=_guess_selector(control),
            value=value,
            description=raw,
        )
    if m := _CLICK_RE.match(raw):
        target = _clean(m.group(1))
        return Step(
            id=step_id,
            action=StepAction.CLICK,
            selector=_guess_selector(target),
            description=raw,
        )
    if m := _ASSERT_TEXT_RE.match(raw):
        return Step(
            id=step_id,
            action=StepAction.ASSERT_TEXT,
            expected=_clean(m.group(1)),
            description=raw,
        )
    if m := _ASSERT_URL_RE.match(raw):
        return Step(
            id=step_id,
            action=StepAction.ASSERT_URL,
            expected=_clean(m.group(1)),
            description=raw,
        )
    raise ValueError(
        f"Unrecognized step format: '{raw}'. "
        "Use: Open/Fill/Click/Select/Verify text/Verify URL ..."
    )


def _normalize_steps(raw_steps: list[str], site_url: str) -> list[str]:
    cleaned = [s.strip() for s in raw_steps if s.strip()]
    if not cleaned:
        raise ValueError("At least one step is required")

    first_lower = cleaned[0].lower()
    if not any(first_lower.startswith(p) for p in ("open ", "go to ", "navigate to ", "goto ")):
        cleaned.insert(0, f"Open {site_url}")
    return cleaned


def structured_prompt_to_suite(prompt: StructuredTestPrompt) -> TestSuite:
    """Convert validated structured prompt into TestSuite for Playwright."""
    step_lines = _normalize_steps(prompt.steps, prompt.site_url)
    steps: list[Step] = []
    for idx, line in enumerate(step_lines, start=1):
        steps.append(_parse_single_step(f"s{idx}", line))

    module = prompt.feature.strip().lower()
    return TestSuite(
        suite_id=prompt.test_id.strip(),
        name=prompt.test_name.strip(),
        module=module,
        base_url=prompt.site_url.strip(),
        objective=prompt.objective.strip(),
        expected_outcome=prompt.expected_outcome.strip(),
        environment=prompt.environment.strip(),
        steps=steps,
    )


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
    lines = [
        f"## {prompt.test_id}",
        f"Module: {prompt.feature}",
        f"Site: {prompt.site_url}",
        f"Objective: {prompt.objective}",
        f"Expected: {prompt.expected_outcome}",
    ]
    for i, step in enumerate(_normalize_steps(prompt.steps, prompt.site_url), start=1):
        lines.append(f"{i}. {step}")
    return "\n".join(lines)
