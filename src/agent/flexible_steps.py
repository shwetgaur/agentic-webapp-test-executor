"""Flexible natural-language step parsing and LLM output cleanup."""

from __future__ import annotations

import re

from src.agent.parser import _guess_selector
from src.common.models import Step, StepAction, StructuredTestPrompt, TestSuite

_FILL_RE = re.compile(r"^(?:fill|enter|type)\s+(.+?)\s+with\s+(.+)$", re.I)
_CLICK_RE = re.compile(r"^(?:click|press)\s+(?:the\s+)?(.+?)(?:\s+button|\s+link)?$", re.I)
_OPEN_RE = re.compile(r"^(?:open|go to|navigate to|goto)\s+(.+)$", re.I)
_SELECT_RE = re.compile(r"^select\s+(.+?)\s+from\s+(?:the\s+)?(.+)$", re.I)

_ASSERT_URL_RES = (
    re.compile(r"^verify(?:\s+that)?\s+(?:the\s+)?url\s+(?:contains|is)\s+(.+)$", re.I),
    re.compile(r"(?:url|URL)\s+(?:contains|is)\s+['\"]?([^'\"]+)['\"]?", re.I),
)

_ASSERT_TEXT_RES = (
    re.compile(r"^verify(?:\s+that)?\s+text\s+(.+?)\s+is\s+visible$", re.I),
    re.compile(r"^verify(?:\s+that)?\s+(?:the\s+)?(.+?)\s+text\s+is\s+visible$", re.I),
    re.compile(r"^verify(?:\s+that)?\s+(?:the\s+)?(.+?)\s+is\s+visible$", re.I),
    re.compile(r"(?:the\s+)?text\s+['\"]?([^'\"]+)['\"]?\s+is\s+visible", re.I),
)


def _clean(text: str) -> str:
    return text.strip().strip('"').strip("'")


def clean_url_fragment(value: str) -> str:
    """Strip wrapper words LLMs often put in assert_url expected values."""
    fragment = _clean(value)
    lowered = fragment.lower()
    for prefix in (
        "the url contains ",
        "url contains ",
        "contains ",
        "the url is ",
        "url is ",
        "is ",
    ):
        if lowered.startswith(prefix):
            fragment = fragment[len(prefix) :].strip()
            lowered = fragment.lower()
    return _clean(fragment)


def parse_flexible_line(step_id: str, raw: str) -> Step | None:
    """Parse a natural-language step line into a Step, or None if unrecognized."""
    raw = raw.strip()
    if not raw:
        return None

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

    for pattern in _ASSERT_TEXT_RES:
        if m := pattern.match(raw):
            return Step(
                id=step_id,
                action=StepAction.ASSERT_TEXT,
                expected=_clean(m.group(1)),
                description=raw,
            )

    for pattern in _ASSERT_URL_RES:
        if m := pattern.search(raw):
            return Step(
                id=step_id,
                action=StepAction.ASSERT_URL,
                expected=clean_url_fragment(m.group(1)),
                description=raw,
            )

    return None


def _align_source_lines(steps: list[Step], lines: list[str]) -> list[str | None]:
    """Align user step lines to generated steps (LLM may insert goto)."""
    pending = list(lines)
    aligned: list[str | None] = []
    for step in steps:
        if step.action == StepAction.GOTO:
            if pending and pending[0].lower().startswith(("open ", "go to ", "navigate to ", "goto ")):
                aligned.append(pending.pop(0))
            else:
                aligned.append(None)
            continue
        aligned.append(pending.pop(0) if pending else None)
    return aligned


def normalize_step(step: Step, *, source_line: str | None = None) -> Step:
    """Fix common LLM mistakes using the original step line or step description."""
    hints = [h for h in (source_line, step.description) if h]
    parsed: Step | None = None
    for hint in hints:
        candidate = parse_flexible_line(step.id, hint)
        if not candidate:
            continue
        if candidate.action == step.action:
            parsed = candidate
            break
        if step.action in (StepAction.ASSERT_URL, StepAction.ASSERT_TEXT):
            parsed = candidate
            break

    updates: dict = {}

    if step.action == StepAction.ASSERT_URL:
        expected = step.expected or ""
        if parsed and parsed.action == StepAction.ASSERT_URL and parsed.expected:
            expected = parsed.expected
        updates["expected"] = clean_url_fragment(expected)

    elif step.action == StepAction.ASSERT_TEXT:
        expected = step.expected or ""
        if parsed and parsed.action == StepAction.ASSERT_TEXT and parsed.expected:
            expected = parsed.expected
        updates["expected"] = _clean(expected)

    elif parsed and parsed.action == step.action:
        if parsed.selector and not step.selector:
            updates["selector"] = parsed.selector
        if parsed.value is not None and step.value is None:
            updates["value"] = parsed.value
        if parsed.url and not step.url:
            updates["url"] = parsed.url
        if parsed.expected and not step.expected:
            updates["expected"] = parsed.expected

    if updates:
        return step.model_copy(update=updates)
    return step


def ensure_opens_site(steps: list[Step], site_url: str) -> list[Step]:
    if not steps:
        return steps
    if steps[0].action == StepAction.GOTO:
        return steps
    return [
        Step(
            id="s0",
            action=StepAction.GOTO,
            url=site_url,
            description=f"Open {site_url}",
        ),
        *[step.model_copy(update={"id": f"s{idx}"}) for idx, step in enumerate(steps, start=1)],
    ]


def normalize_llm_suite(
    suite: TestSuite,
    prompt: StructuredTestPrompt,
    *,
    source_lines: list[str] | None = None,
) -> TestSuite:
    """Reconcile LLM-generated steps with natural-language intent."""
    lines = source_lines or list(prompt.steps)
    aligned = _align_source_lines(suite.steps, lines)
    normalized: list[Step] = []
    for step, source in zip(suite.steps, aligned):
        normalized.append(normalize_step(step, source_line=source))

    normalized = ensure_opens_site(normalized, prompt.site_url.strip())
    return suite.model_copy(update={"steps": normalized})


def suite_from_natural_steps(prompt: StructuredTestPrompt, step_lines: list[str]) -> TestSuite:
    """Build a TestSuite directly from flexible natural-language lines."""
    cleaned = [line.strip() for line in step_lines if line.strip()]
    if not cleaned:
        raise ValueError("At least one step is required")

    first_lower = cleaned[0].lower()
    if not any(first_lower.startswith(p) for p in ("open ", "go to ", "navigate to ", "goto ")):
        cleaned.insert(0, f"Open {prompt.site_url}")

    steps: list[Step] = []
    for idx, line in enumerate(cleaned, start=1):
        step = parse_flexible_line(f"s{idx}", line)
        if not step:
            raise ValueError(
                f"Unrecognized step format: '{line}'. "
                "Use natural phrases like verify url contains …, verify that the X text is visible, Fill … with …"
            )
        steps.append(step)

    module = prompt.feature.strip().lower()
    return TestSuite(
        suite_id=prompt.test_id.strip(),
        name=prompt.test_name.strip(),
        module=module,
        base_url=prompt.site_url.strip(),
        objective=prompt.objective.strip(),
        expected_outcome=prompt.expected_outcome.strip(),
        environment=prompt.environment.value,
        steps=steps,
    )
