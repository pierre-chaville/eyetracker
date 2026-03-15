"""
Application settings from environment variables (pydantic-settings).
Use for API keys, feature flags, and paths — not for user-editable config (see config.py / config.json).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Env-derived settings. Load from .env and environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API keys (optional at load; services validate when used)
    deepgram_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    eleven_labs_api_key: Optional[str] = None
    eleven_labs_voice_id: Optional[str] = None

    # Paths
    google_application_credentials: Optional[str] = None
    config_file: Optional[Path] = None  # overrides default config.json path if set

    # Timeouts and retry for external APIs
    http_timeout_seconds: float = 30.0
    llm_request_timeout_seconds: float = 60.0
    retry_max_attempts: int = 3
    retry_wait_min_seconds: float = 1.0
    retry_wait_max_seconds: float = 10.0


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return application settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
