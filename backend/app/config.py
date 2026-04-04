from __future__ import annotations

import json
from pathlib import Path

from app.schemas.config import ConfigModel, ConfigResponse
from app.settings import get_settings
from app.utils.exceptions import ConfigSaveError, ConfigValidationError
from app.utils.logging import get_logger

logger = get_logger()
BASE_DIR = Path(__file__).resolve().parents[1]


def _config_file_path() -> Path:
    """Config file path from settings or default."""
    settings = get_settings()
    if settings.config_file is not None:
        return settings.config_file
    return BASE_DIR / "config.json"


def load_config() -> ConfigModel:
    """Load configuration from config.json file."""
    config_file = _config_file_path()
    if config_file.exists():
        try:
            with config_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
                if "prompt" in data and "communicate_prompt" not in data:
                    data["communicate_prompt"] = data["prompt"]
                    del data["prompt"]
                if "keyboard_prompt" not in data:
                    data["keyboard_prompt"] = (
                        "You are a helpful assistant that suggests words for text input "
                        "using eye tracking. Based on the conversation history and current "
                        "text, suggest 5 words that the user might want to type next."
                    )
                if "keyboard_multiple_letters_prompt" not in data:
                    data["keyboard_multiple_letters_prompt"] = (
                        "You are a helpful assistant that suggests words for text input "
                        "using eye tracking. The user has selected multiple letters. Based "
                        "on the conversation history, current text, and the selected letters, "
                        "suggest 5 words that match or could be formed from these letters."
                    )
                if "eye_tracking" not in data:
                    data["eye_tracking"] = {"eye_used": "both", "dwell_time": 2.0}
                if "prompt_session_analysis" not in data:
                    data["prompt_session_analysis"] = ""
                return ConfigModel(**data)
        except (json.JSONDecodeError, ValueError, KeyError):
            logger.exception("Error loading config")
            return ConfigModel()
    return ConfigModel()


def save_config(config: ConfigModel) -> None:
    """Save configuration to config.json file."""
    config_file = _config_file_path()
    try:
        with config_file.open("w", encoding="utf-8") as file:
            json.dump(config.model_dump(), file, indent=2, ensure_ascii=False)
    except Exception as exc:
        logger.exception("Failed to persist configuration")
        raise ConfigSaveError(f"Failed to save configuration: {exc}") from exc


class ConfigService:
    """Service for managing application configuration."""

    def get_config(self) -> ConfigResponse:
        config = load_config()
        return ConfigResponse(**config.model_dump())

    def update_config(self, config: ConfigModel) -> ConfigResponse:
        valid_providers = ["openai", "anthropic", "google", "azure"]
        if config.provider not in valid_providers:
            raise ConfigValidationError(
                f"Invalid provider. Must be one of: {', '.join(valid_providers)}"
            )
        if not 0 <= config.temperature <= 2:
            raise ConfigValidationError("Temperature must be between 0 and 2")
        if config.eye_tracking:
            if config.eye_tracking.eye_used not in ["left", "right", "both"]:
                raise ConfigValidationError("eye_used must be one of: left, right, both")
            if config.eye_tracking.dwell_time < 0:
                raise ConfigValidationError("dwell_time must be a positive number")
        save_config(config)
        return ConfigResponse(**config.model_dump())
