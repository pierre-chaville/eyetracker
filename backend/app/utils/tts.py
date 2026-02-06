from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from app.schemas.config import ConfigModel


def resolve_google_credentials() -> Optional[str]:
    """Resolve Google Cloud credentials path if available."""
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not google_creds:
        backend_dir = Path(__file__).resolve().parents[2]
        google_json_path = backend_dir / "google.json"
        if google_json_path.exists():
            google_creds = str(google_json_path)
    return google_creds


def resolve_tts_provider(config: ConfigModel) -> str:
    """Select the best available TTS provider."""
    if resolve_google_credentials():
        return "google"
    if os.getenv("ELEVEN_LABS_API_KEY") and os.getenv("ELEVEN_LABS_VOICE_ID"):
        return "elevenlabs"
    if config.provider == "openai" and os.getenv("OPENAI_API_KEY"):
        return "openai"
    return "pyttsx3"


def resolve_audio_format(provider: str) -> str:
    """Resolve audio format based on TTS provider."""
    if provider in ("google", "elevenlabs"):
        return "mp3"
    return "wav"
