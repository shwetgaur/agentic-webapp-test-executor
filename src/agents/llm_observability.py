"""LLM call metrics and optional LangSmith-compatible tracing."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from src.common.settings import settings

logger = logging.getLogger(__name__)

_LANGSMITH_BASE = "https://api.smith.langchain.com"


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


def _truncate(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _langsmith_headers() -> dict[str, str]:
    return {
        "x-api-key": settings.langsmith_api_key or "",
        "Content-Type": "application/json",
    }


def maybe_export_langsmith(
    record: LLMCallRecord,
    *,
    run_id: str | None = None,
    system: str = "",
    user: str = "",
    assistant_content: str | None = None,
) -> None:
    """
    Export one LLM call to LangSmith using POST + PATCH (REST cookbook pattern).

    LangSmith shows token counts and latency only when:
    - run_type is \"llm\" with OpenAI-style messages in inputs/outputs
    - start_time and end_time are set (latency derived from these)
    - prompt_tokens / completion_tokens / total_tokens are on the PATCH body
    """
    if not settings.langsmith_tracing_enabled or not settings.langsmith_api_key:
        return

    ls_run_id = str(uuid.uuid4())
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(milliseconds=max(record.latency_ms, 1))

    messages = []
    if system.strip():
        messages.append({"role": "system", "content": _truncate(system)})
    if user.strip():
        messages.append({"role": "user", "content": _truncate(user)})

    create_payload = {
        "id": ls_run_id,
        "name": f"llm.{record.caller}",
        "run_type": "llm",
        "session_name": settings.langsmith_project,
        "start_time": start_time.isoformat(),
        "inputs": {
            "messages": messages or [{"role": "user", "content": f"caller={record.caller}"}],
            "model": record.model,
            "provider": record.provider,
        },
        "extra": {
            "metadata": {
                "caller": record.caller,
                "provider": record.provider,
                "model": record.model,
                "pipeline_run_id": run_id,
            }
        },
        "tags": [record.caller, record.provider],
    }

    patch_payload: dict[str, Any] = {
        "end_time": end_time.isoformat(),
        "prompt_tokens": record.prompt_tokens,
        "completion_tokens": record.completion_tokens,
        "total_tokens": record.total_tokens or (record.prompt_tokens + record.completion_tokens),
    }

    if record.success and assistant_content is not None:
        patch_payload["outputs"] = {
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": _truncate(assistant_content),
                    },
                    "finish_reason": "stop",
                }
            ]
        }
    elif record.error:
        patch_payload["error"] = record.error
        patch_payload["outputs"] = {"success": False, "error": record.error}
    else:
        patch_payload["outputs"] = {"success": record.success}

    try:
        create_resp = httpx.post(
            f"{_LANGSMITH_BASE}/runs",
            headers=_langsmith_headers(),
            json=create_payload,
            timeout=10.0,
        )
        if create_resp.status_code >= 400:
            logger.warning(
                "LangSmith create run failed (%s): %s",
                create_resp.status_code,
                create_resp.text[:300],
            )
            return

        patch_resp = httpx.patch(
            f"{_LANGSMITH_BASE}/runs/{ls_run_id}",
            headers=_langsmith_headers(),
            json=patch_payload,
            timeout=10.0,
        )
        if patch_resp.status_code >= 400:
            logger.warning(
                "LangSmith patch run failed (%s): %s",
                patch_resp.status_code,
                patch_resp.text[:300],
            )
    except Exception as exc:
        logger.warning("LangSmith export skipped: %s", exc)
