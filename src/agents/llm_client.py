"""Thin LLM client for Groq, OpenAI, and Ollama (optional — rule fallback when unavailable)."""

from __future__ import annotations

import json
import time
from typing import Any, Optional

import httpx

from src.agents.llm_observability import (
    LLMCallRecord,
    LLMUsageSummary,
    maybe_export_langsmith,
    parse_ollama_usage,
    parse_openai_usage,
)
from src.common.settings import settings


class LLMClient:
    """Chat completion wrapper with per-call token and latency tracking."""

    def __init__(
        self,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        timeout_s: float = 60.0,
        run_id: str | None = None,
    ) -> None:
        self.provider = (provider or settings.llm_provider).lower()
        self.model = model or settings.llm_model
        self.timeout_s = timeout_s
        self.run_id = run_id
        self.call_log: list[LLMCallRecord] = []
        self.last_call: LLMCallRecord | None = None

    def is_available(self) -> bool:
        if self.provider == "groq":
            return bool(settings.groq_api_key)
        if self.provider == "openai":
            return bool(settings.openai_api_key)
        if self.provider == "ollama":
            return bool(settings.ollama_base_url)
        return False

    def usage_summary(self) -> LLMUsageSummary:
        return LLMUsageSummary(calls=list(self.call_log))

    def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.1,
        caller: str = "unknown",
    ) -> Optional[str]:
        if not self.is_available():
            return None
        started = time.perf_counter()
        record = LLMCallRecord(
            caller=caller,
            provider=self.provider,
            model=self.model,
        )
        content: str | None = None
        try:
            if self.provider == "ollama":
                content, prompt_t, completion_t, total_t = self._ollama_chat(system, user, temperature)
            else:
                content, prompt_t, completion_t, total_t = self._openai_compatible_chat(
                    system, user, temperature
                )
            record.prompt_tokens = prompt_t
            record.completion_tokens = completion_t
            record.total_tokens = total_t
            record.success = True
            return content
        except Exception as exc:
            record.success = False
            record.error = str(exc)[:200]
            raise
        finally:
            record.latency_ms = int((time.perf_counter() - started) * 1000)
            self.call_log.append(record)
            self.last_call = record
            maybe_export_langsmith(
                record,
                run_id=self.run_id,
                system=system,
                user=user,
                assistant_content=content,
            )

    def chat_json(self, system: str, user: str, *, caller: str = "unknown") -> Optional[Any]:
        raw = self.chat(system, user, caller=caller)
        if not raw:
            return None
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
            start = text.find("[")
            end = text.rfind("]")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
            return None

    def _openai_compatible_chat(
        self, system: str, user: str, temperature: float
    ) -> tuple[str, int, int, int]:
        if self.provider == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
            api_key = settings.groq_api_key
        else:
            url = "https://api.openai.com/v1/chat/completions"
            api_key = settings.openai_api_key
        if not api_key:
            raise RuntimeError(f"No API key for provider {self.provider}")

        payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        resp = httpx.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=self.timeout_s,
        )
        resp.raise_for_status()
        body = resp.json()
        content = body["choices"][0]["message"]["content"]
        prompt_t, completion_t, total_t = parse_openai_usage(body)
        return content, prompt_t, completion_t, total_t

    def _ollama_chat(
        self, system: str, user: str, temperature: float
    ) -> tuple[str, int, int, int]:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": temperature},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        resp = httpx.post(url, json=payload, timeout=self.timeout_s)
        resp.raise_for_status()
        body = resp.json()
        content = body["message"]["content"]
        prompt_t, completion_t, total_t = parse_ollama_usage(body)
        return content, prompt_t, completion_t, total_t
