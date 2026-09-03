"""Playwright-based step executor."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from src.executor.browser_launch import chromium_launch_kwargs
from src.executor.navigation import navigate
from src.executor.url_assertions import url_matches
from src.common.models import (
    RunStatus,
    RunSummary,
    Step,
    StepAction,
    StepResult,
    StepStatus,
    TestReport,
    TestSuite,
)
from src.common.settings import settings


def _is_auth_submit_click(step: Step) -> bool:
    desc = (step.description or "").lower()
    sel = (step.selector or "").lower()
    return any(token in desc for token in ("sign in", "log in", "login")) or "signin" in sel or sel in {
        "#nextbtn",
        "#login-button",
        "button[type='submit']",
    }


def _wait_for_auth_navigation(page, prior_url: str, timeout_ms: int) -> None:
    """Wait for SPA login redirects (e.g. /login -> /feed)."""
    normalized_prior = prior_url.rstrip("/")
    try:
        page.wait_for_url(
            lambda url: url.rstrip("/") != normalized_prior,
            timeout=timeout_ms,
        )
    except PlaywrightTimeoutError:
        pass
    try:
        page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
    except PlaywrightTimeoutError:
        pass


def _wait_for_url_match(page, expected: str, timeout_ms: int) -> str:
    """Poll until page URL matches expected fragment or timeout."""
    deadline = time.perf_counter() + (timeout_ms / 1000)
    last_url = page.url
    while time.perf_counter() < deadline:
        last_url = page.url
        if url_matches(last_url, expected):
            return last_url
        page.wait_for_timeout(300)
    if not url_matches(last_url, expected):
        raise AssertionError(f"URL '{last_url}' does not contain '{expected}'")
    return last_url


class PlaywrightExecutor:
    def __init__(
        self,
        *,
        headless: Optional[bool] = None,
        screenshot_dir: str | Path = "data/screenshots",
        timeout_ms: Optional[int] = None,
    ) -> None:
        self.headless = settings.headless if headless is None else headless
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.timeout_ms = timeout_ms or settings.default_timeout_ms

    def run(
        self,
        suite: TestSuite,
        *,
        healer: Callable[[Step, object, str], Step | None] | None = None,
    ) -> TestReport:
        run_id = f"run_{uuid.uuid4().hex[:10]}"
        started = datetime.now(timezone.utc)
        results: list[StepResult] = []
        failed = False

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(**chromium_launch_kwargs(headless=self.headless))
                context = browser.new_context()
                page = context.new_page()
                page.set_default_timeout(self.timeout_ms)

                for step in suite.steps:
                    if failed:
                        skip_at = datetime.now(timezone.utc)
                        results.append(
                            StepResult(
                                step_id=step.id,
                                action=step.action.value,
                                description=step.description,
                                status=StepStatus.SKIPPED,
                                expected=step.expected,
                                started_at=skip_at,
                                finished_at=skip_at,
                                duration_ms=0,
                            )
                        )
                        continue

                    step_result = self._execute_step(page, run_id, step, healer=healer)
                    results.append(step_result)
                    if step_result.status in (StepStatus.FAILED, StepStatus.ERROR):
                        failed = True

                context.close()
                browser.close()
        except (PlaywrightError, OSError, RuntimeError) as exc:
            finished = datetime.now(timezone.utc)
            return TestReport(
                run_id=run_id,
                suite_id=suite.suite_id,
                suite_name=suite.name,
                module=suite.module,
                site_url=suite.base_url,
                objective=suite.objective,
                expected_outcome=suite.expected_outcome,
                environment=suite.environment,
                status=RunStatus.ERROR,
                started_at=started,
                finished_at=finished,
                duration_ms=int((finished - started).total_seconds() * 1000),
                summary=RunSummary(total=1, passed=0, failed=0, skipped=0),
                steps=[
                    StepResult(
                        step_id="browser",
                        action="launch",
                        description="Browser launch or session setup",
                        status=StepStatus.ERROR,
                        started_at=started,
                        finished_at=finished,
                        duration_ms=int((finished - started).total_seconds() * 1000),
                        error=str(exc),
                    )
                ],
            )

        finished = datetime.now(timezone.utc)
        passed = sum(1 for r in results if r.status == StepStatus.PASSED)
        failed_n = sum(1 for r in results if r.status in (StepStatus.FAILED, StepStatus.ERROR))
        skipped = sum(1 for r in results if r.status == StepStatus.SKIPPED)

        status = RunStatus.PASSED if failed_n == 0 else RunStatus.FAILED
        return TestReport(
            run_id=run_id,
            suite_id=suite.suite_id,
            suite_name=suite.name,
            module=suite.module,
            site_url=suite.base_url,
            objective=suite.objective,
            expected_outcome=suite.expected_outcome,
            environment=suite.environment,
            status=status,
            started_at=started,
            finished_at=finished,
            duration_ms=int((finished - started).total_seconds() * 1000),
            summary=RunSummary(
                total=len(results),
                passed=passed,
                failed=failed_n,
                skipped=skipped,
            ),
            steps=results,
        )

    def _execute_step(
        self,
        page,
        run_id: str,
        step: Step,
        *,
        healer: Callable[[Step, object, str], Step | None] | None = None,
    ) -> StepResult:
        started_at = datetime.now(timezone.utc)
        t0 = time.perf_counter()
        screenshot_path = None
        current = step
        healed = False

        def _finish(**kwargs) -> StepResult:
            finished_at = datetime.now(timezone.utc)
            duration = kwargs.pop("duration_ms", int((time.perf_counter() - t0) * 1000))
            return StepResult(
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration,
                **kwargs,
            )

        try:
            actual = self._dispatch(page, current)
            desc = current.description
            if healed and desc:
                desc = f"{desc} [healed]"
            elif healed:
                desc = "[healed]"
            return _finish(
                step_id=step.id,
                action=current.action.value,
                description=desc,
                status=StepStatus.PASSED,
                expected=current.expected,
                actual=actual,
            )
        except Exception as exc:  # noqa: BLE001 - collect any step failure
            err_str = str(exc)
            if healer and not healed:
                alt = healer(step, page, err_str)
                if alt:
                    healed = True
                    current = alt
                    try:
                        actual = self._dispatch(page, current)
                        desc = f"{(current.description or step.description or '')} [healed]".strip()
                        return _finish(
                            step_id=step.id,
                            action=current.action.value,
                            description=desc or "[healed]",
                            status=StepStatus.PASSED,
                            expected=current.expected,
                            actual=actual,
                        )
                    except Exception as retry_exc:
                        exc = retry_exc

            try:
                path = self.screenshot_dir / f"{run_id}_{step.id}.png"
                page.screenshot(path=str(path), full_page=True)
                screenshot_path = str(path)
            except Exception:  # noqa: BLE001
                screenshot_path = None
            return _finish(
                step_id=step.id,
                action=step.action.value,
                description=step.description,
                status=StepStatus.FAILED if isinstance(exc, (AssertionError, PlaywrightTimeoutError)) else StepStatus.ERROR,
                expected=step.expected,
                actual=None,
                screenshot_path=screenshot_path,
                error=str(exc),
            )

    def _dispatch(self, page, step: Step) -> str:
        action = step.action
        if action == StepAction.GOTO:
            if not step.url:
                raise ValueError("goto requires url")
            navigate(page, step.url)
            return page.url
        if action == StepAction.FILL:
            if not step.selector:
                raise ValueError("fill requires selector")
            page.fill(step.selector, step.value or "")
            return step.value or ""
        if action == StepAction.CLICK:
            if not step.selector:
                raise ValueError("click requires selector")
            prior_url = page.url
            page.click(step.selector)
            if _is_auth_submit_click(step):
                _wait_for_auth_navigation(page, prior_url, self.timeout_ms)
            return f"clicked:{step.selector}"
        if action == StepAction.SELECT:
            if not step.selector:
                raise ValueError("select requires selector")
            page.select_option(step.selector, label=step.value)
            return step.value or ""
        if action == StepAction.HOVER:
            if not step.selector:
                raise ValueError("hover requires selector")
            page.hover(step.selector)
            return f"hovered:{step.selector}"
        if action == StepAction.PRESS_KEY:
            page.keyboard.press(step.key or "Enter")
            return step.key or "Enter"
        if action == StepAction.WAIT:
            page.wait_for_timeout(step.timeout_ms or 1000)
            return f"waited:{step.timeout_ms or 1000}ms"
        if action == StepAction.ASSERT_TEXT:
            expected = step.expected or ""
            locator = page.get_by_text(expected, exact=False)
            try:
                locator.first.wait_for(state="visible", timeout=self.timeout_ms)
            except PlaywrightTimeoutError as exc:
                if locator.count() == 0:
                    raise AssertionError(f"Text not found: {expected}") from exc
            return expected
        if action == StepAction.ASSERT_URL:
            expected = step.expected or ""
            return _wait_for_url_match(page, expected, self.timeout_ms)
        if action == StepAction.ASSERT_VISIBLE:
            if not step.selector:
                raise ValueError("assert_visible requires selector")
            locator = page.locator(step.selector)
            if not locator.is_visible():
                raise AssertionError(f"Element not visible: {step.selector}")
            return step.selector
        if action == StepAction.SCREENSHOT:
            # handled as success marker; caller may also screenshot on failure
            return "screenshot-ok"
        raise ValueError(f"Unsupported action: {action}")
