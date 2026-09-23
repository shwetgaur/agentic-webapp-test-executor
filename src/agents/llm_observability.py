"""LLM call metrics and optional LangSmith-compatible tracing."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from src.common.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMCallRecord:
    """One LLM API invocation (Planner, Generator, Healer, etc.)."""

    caller: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "caller": self.caller,
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class LLMUsageSummary:
    """Aggregated token/latency totals for a run."""

    calls: list[LLMCallRecord] = field(default_factory=list)

    @property
    def total_prompt_tokens(self) -> int:
        return sum(c.prompt_tokens for c in self.calls)

    @property
    def total_completion_tokens(self) -> int:
        return sum(c.completion_tokens for c in self.calls)

    @property
    def total_tokens(self) -> int:
        return sum(c.total_tokens for c in self.calls)

    @property
    def total_latency_ms(self) -> int:
        return sum(c.latency_ms for c in self.calls)

    def by_caller(self) -> dict[str, list[LLMCallRecord]]:
        grouped: dict[str, list[LLMCallRecord]] = {}
        for call in self.calls:
            grouped.setdefault(call.caller, []).append(call)
        return grouped


def parse_openai_usage(body: dict[str, Any]) -> tuple[int, int, int]:
    usage = body.get("usage") or {}
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    total = int(usage.get("total_tokens") or prompt + completion)
    return prompt, completion, total


def parse_ollama_usage(body: dict[str, Any]) -> tuple[int, int, int]:
    prompt = int(body.get("prompt_eval_count") or 0)
    completion = int(body.get("eval_count") or 0)
    return prompt, completion, prompt + completion


def maybe_export_langsmith(record: LLMCallRecord, *, run_id: str | None = None) -> None:
    """Best-effort LangSmith run export when API key is configured (no SDK required)."""
    if not settings.langsmith_tracing_enabled or not settings.langsmith_api_key:
        return
    payload = {
        "name": f"llm.{record.caller}",
        "run_type": "llm",
        "inputs": {"caller": record.caller},
        "outputs": {"success": record.success},
        "extra": {
            "metadata": {
                "provider": record.provider,
                "model": record.model,
                "run_id": run_id,
            }
        },
        "session_name": settings.langsmith_project,
        "start_time": None,
        "end_time": None,
        "prompt_tokens": record.prompt_tokens,
        "completion_tokens": record.completion_tokens,
        "total_tokens": record.total_tokens,
    }
    try:
        httpx.post(
            "https://api.smith.langchain.com/runs",
            headers={
                "x-api-key": settings.langsmith_api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=5.0,
        )
    except Exception as exc:
        logger.debug("LangSmith export skipped: %s", exc)
