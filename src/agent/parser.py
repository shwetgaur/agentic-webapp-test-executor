"""Rule-based text -> JSON step parser (Phase-1 baseline before LLM).

This gives an end-to-end path without requiring API keys.
LLM-backed parsing will wrap the same TestSuite model in Phase-2.
"""

from __future__ import annotations

import re
from typing import Optional

from src.common.models import Step, StepAction, TestSuite


_FILL_RE = re.compile(r"^(?:fill|enter|type)\s+(.+?)\s+with\s+(.+)$", re.I)
_CLICK_RE = re.compile(r"^(?:click|press)\s+(?:the\s+)?(.+?)(?:\s+button|\s+link)?$", re.I)
_OPEN_RE = re.compile(r"^(?:open|go to|navigate to|goto)\s+(.+)$", re.I)
_ASSERT_TEXT_RE = re.compile(
    r"^verify(?:\s+that)?\s+text\s+(.+?)\s+is\s+visible$",
    re.I,
)
_ASSERT_URL_RE = re.compile(
    r"^verify(?:\s+that)?\s+url\s+(?:contains|is)\s+(.+)$",
    re.I,
)
_SELECT_RE = re.compile(r"^select\s+(.+?)\s+from\s+(?:the\s+)?(.+)$", re.I)


def _clean(text: str) -> str:
    return text.strip().strip('"').strip("'")


from src.agent.selectors import best_guess_selector as _guess_selector


def parse_plain_text_case(
    text: str,
    *,
    suite_id: Optional[str] = None,
    name: Optional[str] = None,
    module: Optional[str] = None,
) -> TestSuite:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    meta_module = module
    title = name
    sid = suite_id
    step_lines: list[str] = []

    for ln in lines:
        lower = ln.lower()
        if lower.startswith("## "):
            sid = sid or ln[3:].strip().replace(" ", "_")
            title = title or ln[3:].strip()
            continue
        if lower.startswith("module:"):
            meta_module = ln.split(":", 1)[1].strip()
            continue
        if lower.startswith("owner team:") or lower.startswith("purpose:"):
            continue
        # numbered steps: "1. Do something"
        m = re.match(r"^\d+\.\s*(.+)$", ln)
        if m:
            step_lines.append(m.group(1).strip())

    if not step_lines:
        raise ValueError("No numbered steps found in plain-text case")

    steps: list[Step] = []
    for idx, raw in enumerate(step_lines, start=1):
        step_id = f"s{idx}"
        if (m := _OPEN_RE.match(raw)):
            url = _clean(m.group(1))
            steps.append(Step(id=step_id, action=StepAction.GOTO, url=url, description=raw))
            continue
        if (m := _FILL_RE.match(raw)):
            field, value = _clean(m.group(1)), _clean(m.group(2))
            steps.append(
                Step(
                    id=step_id,
                    action=StepAction.FILL,
                    selector=_guess_selector(field),
                    value=value,
                    description=raw,
                )
            )
            continue
        if (m := _SELECT_RE.match(raw)):
            value, control = _clean(m.group(1)), _clean(m.group(2))
            steps.append(
                Step(
                    id=step_id,
                    action=StepAction.SELECT,
                    selector=_guess_selector(control),
                    value=value,
                    description=raw,
                )
            )
            continue
        if (m := _CLICK_RE.match(raw)):
            target = _clean(m.group(1))
            steps.append(
                Step(
                    id=step_id,
                    action=StepAction.CLICK,
                    selector=_guess_selector(target),
                    description=raw,
                )
            )
            continue
        if (m := _ASSERT_TEXT_RE.match(raw)):
            expected = _clean(m.group(1))
            steps.append(
                Step(
                    id=step_id,
                    action=StepAction.ASSERT_TEXT,
                    expected=expected,
                    description=raw,
                )
            )
            continue
        if (m := _ASSERT_URL_RE.match(raw)):
            expected = _clean(m.group(1))
            steps.append(
                Step(
                    id=step_id,
                    action=StepAction.ASSERT_URL,
                    expected=expected,
                    description=raw,
                )
            )
            continue
        # Fallback: treat as assert_text of whole sentence remnant
        steps.append(
            Step(
                id=step_id,
                action=StepAction.ASSERT_TEXT,
                expected=raw,
                description=f"Unrecognized step parsed as assert_text: {raw}",
            )
        )

    return TestSuite(
        suite_id=sid or "unnamed_suite",
        name=title or sid or "unnamed_suite",
        module=meta_module or "validation",
        steps=steps,
    )
