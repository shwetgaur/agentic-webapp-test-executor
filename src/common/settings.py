"""Application settings loaded from environment / .env."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Agentic Web-App Test Executor"
    app_env: str = "dev"
    database_url: str = "sqlite:///./data/executor.db"

    llm_provider: str = "groq"
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    ollama_base_url: str = "http://127.0.0.1:11434"
    llm_model: str = "openai/gpt-oss-20b"

    notify_enabled: bool = True
    notify_channel: str = "console"
    slack_webhook_url: str | None = None

    headless: bool = True
    default_timeout_ms: int = 30000
    navigation_timeout_ms: int = 45000
    goto_wait_until: str = "domcontentloaded"


settings = Settings()
