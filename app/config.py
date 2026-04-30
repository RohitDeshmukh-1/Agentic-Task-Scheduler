"""
Centralized configuration management using Pydantic Settings.

All environment variables are validated and typed at startup, ensuring
fast-fail on misconfiguration.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import List, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────────────────────
    llm_api_key: str
    llm_model: str = "llama-3.3-70b-versatile"
    llm_provider: Literal["groq", "openai", "together"] = "groq"

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./taskbot.db"

    # ── Telegram ─────────────────────────────────────────────────────────
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = "taskpilot_telegram_2026"
    telegram_mode: Literal["polling", "webhook"] = "webhook"
    telegram_webhook_url: str = ""
    public_base_url: str = ""

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = "TaskPilot"
    app_env: Literal["development", "staging", "production"] = "development"
    app_secret_key: str = "change-me"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # ── Scheduler ────────────────────────────────────────────────────────
    morning_reminder_hour: int = 8
    morning_reminder_minute: int = 0
    night_check_hour: int = 21
    night_check_minute: int = 0
    weekly_report_day: str = "sun"
    weekly_report_hour: int = 10
    recurrence_lookahead_days: int = 30

    # ── Dashboard ────────────────────────────────────────────────────────
    dashboard_enabled: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """
        Normalize database URLs.
        - Replaces 'postgres://' with 'postgresql+asyncpg://'
        - Ensures 'postgresql+asyncpg://' is used for postgres connections
        - Strips any whitespace
        """
        if not v:
            return v
        
        v = v.strip()
        
        # Handle standard Railway/Heroku URLs
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.database_url


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — avoids re-reading .env on every import."""
    return Settings()
