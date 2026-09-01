"""Thin LLM client for Groq, OpenAI, and Ollama (optional — rule fallback when unavailable)."""

from __future__ import annotations

import json
from typing import Any, Optional

import httpx

from src.common.settings import settings


class LLMClient:
    """Chat completion wrapper. Returns None when no provider is configured."""

    def __init__(
        self,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        timeout_s: float = 60.0,
    ) -> None:
        self.provider = (provider or settings.llm_provider).lower()
        self.model = model or settings.llm_model
        self.timeout_s = timeout_s

    def is_available(self) -> bool:
        if self.provider == "groq":
            return bool(settings.groq_api_key)
        if self.provider == "openai":
            return bool(settings.openai_api_key)
        if self.provider == "ollama":
            return bool(settings.ollama_base_url)
        return False

    def chat(self, system: str, user: str, *, temperature: float = 0.1) -> Optional[str]:
        if not self.is_available():
            return None
        if self.provider == "ollama":
            return self._ollama_chat(system, user, temperature)
        return self._openai_compatible_chat(system, user, temperature)

    def chat_json(self, system: str, user: str) -> Optional[Any]:
        raw = self.chat(system, user)
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

    def _openai_compatible_chat(self, system: str, user: str, temperature: float) -> str:
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
        return resp.json()["choices"][0]["message"]["content"]

    def _ollama_chat(self, system: str, user: str, temperature: float) -> str:
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
        return resp.json()["message"]["content"]
