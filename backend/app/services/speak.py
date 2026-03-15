"""
Shared TTS: generate speech for given text, play it, and return base64 audio.

Used by both communication (select choice) and keyboard (speak word/letter).
"""
from __future__ import annotations

import base64
from typing import Optional

from app.config import load_config
from app.services.speech_to_text import get_current_speech_to_text_service
from app.services.tts import get_tts_service
from app.utils.logging import get_logger
from app.utils.tts import resolve_audio_format, resolve_tts_provider

logger = get_logger(__name__)


async def speak_text(
    text: str,
    language: Optional[str] = None,
    voice_name: Optional[str] = None,
    pitch: Optional[float] = None,
    speaking_rate: Optional[float] = None,
) -> Optional[str]:
    """
    Generate TTS for text, play it (with STT pause), and return base64 audio.

    Args:
        text: Text to speak.
        language: Language code (default from config).
        voice_name: Voice identifier (default from config).
        pitch: TTS pitch (default from config).
        speaking_rate: TTS speaking rate (default from config).

    Returns:
        Base64-encoded audio string, or None if generation failed.
    """
    if not text or not text.strip():
        return None
    config = load_config()
    tts_provider = resolve_tts_provider(config)
    tts_service = get_tts_service(provider=tts_provider)
    lang = language or config.tts_language or "en"
    voice = voice_name if voice_name is not None else config.tts_voice_name
    p = pitch if pitch is not None else config.tts_pitch
    sr = speaking_rate if speaking_rate is not None else config.tts_speaking_rate

    audio_data = await tts_service.generate_speech(
        text=text.strip(),
        language=lang,
        voice_name=voice,
        pitch=p,
        speaking_rate=sr,
    )
    if not audio_data:
        logger.warning("TTS returned no audio for text length=%s", len(text))
        return None
    audio_format = resolve_audio_format(tts_provider)
    logger.info(
        "TTS generated and playing",
        extra={"provider": tts_provider, "format": audio_format, "bytes": len(audio_data)},
    )
    tts_service.play_audio_async(
        audio_data,
        audio_format,
        stt_service=get_current_speech_to_text_service(),
    )
    return base64.b64encode(audio_data).decode("utf-8")
