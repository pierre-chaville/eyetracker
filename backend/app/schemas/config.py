from __future__ import annotations

from pydantic import BaseModel


class EyeTrackingConfig(BaseModel):
    """Eye tracking configuration model."""

    eye_used: str = "both"
    dwell_time: float = 2.0


class ConfigModel(BaseModel):
    """Application configuration model."""

    provider: str = "openai"
    model: str = ""
    temperature: float = 0.7
    communicate_prompt: str = ""
    keyboard_prompt: str = ""
    keyboard_multiple_letters_prompt: str = ""
    prompt_session_analysis: str = ""
    header_height_adjustment: int = 0
    menu_width_adjustment: int = 0
    tts_language: str = "fr"
    tts_voice_name: str = ""
    tts_pitch: float = 0.0
    tts_speaking_rate: float = 1.0
    eye_tracking: EyeTrackingConfig = EyeTrackingConfig()


class ConfigResponse(BaseModel):
    """Configuration response model."""

    provider: str
    model: str
    temperature: float
    communicate_prompt: str
    keyboard_prompt: str
    keyboard_multiple_letters_prompt: str
    prompt_session_analysis: str
    header_height_adjustment: int
    menu_width_adjustment: int
    tts_language: str
    tts_voice_name: str
    tts_pitch: float
    tts_speaking_rate: float
    eye_tracking: EyeTrackingConfig
