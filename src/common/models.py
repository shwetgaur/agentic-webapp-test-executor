"""Shared Pydantic models for step + report schemas (Phase-1 locked)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StepAction(str, Enum):
    GOTO = "goto"
    FILL = "fill"
    CLICK = "click"
    SELECT = "select"
    HOVER = "hover"
    PRESS_KEY = "press_key"
    WAIT = "wait"
    ASSERT_TEXT = "assert_text"
    ASSERT_URL = "assert_url"
    ASSERT_VISIBLE = "assert_visible"
    SCREENSHOT = "screenshot"


class StepStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class RunStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class Step(BaseModel):
    id: str
    action: StepAction
    url: Optional[str] = None
    selector: Optional[str] = None
    value: Optional[str] = None
    key: Optional[str] = None
    timeout_ms: Optional[int] = None
    expected: Optional[str] = None
    description: Optional[str] = None


class StructuredTestPrompt(BaseModel):
    """Fixed-format test input (mentor requirement). No free-form-only prompts."""

    test_id: str = Field(..., min_length=1, description="Unique test case ID")
    site_url: str = Field(..., min_length=1, description="Application URL under test")
    feature: str = Field(..., min_length=1, description="Feature/module e.g. login, checkout")
    test_name: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    expected_outcome: str = Field(..., min_length=1)
    environment: str = Field(default="demo")
    owner_team: Optional[str] = None
    steps: list[str] = Field(..., min_length=1, description="Ordered test step lines")


class TestSuite(BaseModel):
    suite_id: str
    name: str
    module: Optional[str] = "validation"
    base_url: Optional[str] = None
    objective: Optional[str] = None
    expected_outcome: Optional[str] = None
    environment: Optional[str] = None
    steps: list[Step] = Field(min_length=1)


class StepResult(BaseModel):
    step_id: str
    action: str
    description: Optional[str] = None
    status: StepStatus
    expected: Optional[str] = None
    actual: Optional[str] = None
    duration_ms: int = 0
    screenshot_path: Optional[str] = None
    error: Optional[str] = None


class RunSummary(BaseModel):
    total: int
    passed: int
    failed: int
    skipped: int


class NotifyInfo(BaseModel):
    triggered: bool = False
    team: Optional[str] = None
    channel: Optional[str] = None
    ticket_id: Optional[str] = None


class TestReport(BaseModel):
    run_id: str
    suite_id: str
    suite_name: Optional[str] = None
    module: Optional[str] = None
    site_url: Optional[str] = None
    objective: Optional[str] = None
    expected_outcome: Optional[str] = None
    environment: Optional[str] = None
    status: RunStatus
    started_at: datetime
    finished_at: datetime
    duration_ms: int = 0
    summary: RunSummary
    steps: list[StepResult]
    notify: NotifyInfo = Field(default_factory=NotifyInfo)
