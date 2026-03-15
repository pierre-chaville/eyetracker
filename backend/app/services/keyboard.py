from __future__ import annotations

import base64
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import load_config
from app.models import Caregiver, User
from app.schemas import (
    ChoicesRequest,
    KeyboardPredictionsResponse,
    KeyboardTTSRequest,
    KeyboardTTSResponse,
)
from app.utils.logging import get_logger
from app.utils.tts import resolve_audio_format, resolve_tts_provider
from app.services.speech_to_text import get_current_speech_to_text_service

from app.services.llm import get_llm_service
from app.services.tts import get_tts_service

logger = get_logger()


class KeyboardService:
    """Service for keyboard predictions and TTS."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_predictions(self, request: ChoicesRequest) -> KeyboardPredictionsResponse:
        try:
            config = load_config()
            user_notes = None
            caregiver_description = None
            if request.user_id:
                user = await self._session.get(User, request.user_id)
                if user:
                    user_notes = user.notes
            if request.caregiver_id:
                caregiver = await self._session.get(Caregiver, request.caregiver_id)
                if caregiver:
                    caregiver_description = caregiver.description
            llm_service = get_llm_service()
            conversation_history = request.conversation_history or []
            current_text = request.current_text or ""
            text_words = current_text.split() if current_text else []
            normalized_words = []
            for word in text_words:
                match = re.match(r"^<([A-Za-z])>$", word)
                normalized_words.append(match.group(1) if match else word)
            is_multiple_letters = len(normalized_words) > 1 and all(
                len(word) == 1 for word in normalized_words
            )
            system_prompt = (
                config.keyboard_multiple_letters_prompt
                if is_multiple_letters
                else config.keyboard_prompt
            ) or "You are a helpful assistant that suggests words for text input."
            choices = await llm_service.generate_choices(
                system_prompt=system_prompt,
                conversation_history=conversation_history,
                user_notes=user_notes,
                caregiver_description=caregiver_description,
                current_text=current_text,
            )
            words = [choice["text"] for choice in choices[:5] if choice.get("text")]
            return KeyboardPredictionsResponse(words=words)
        except Exception:
            logger.exception("Error generating keyboard predictions")
            return KeyboardPredictionsResponse(words=[])

    async def generate_tts(self, request: KeyboardTTSRequest) -> KeyboardTTSResponse:
        try:
            text = request.text or ""
            if not text:
                return KeyboardTTSResponse(audio_base64=None)
            tts_config = load_config()
            tts_provider = resolve_tts_provider(tts_config)
            tts_service = get_tts_service(provider=tts_provider)
            audio_data = tts_service.generate_speech(
                text=text,
                language=tts_config.tts_language or "fr",
                voice_name=tts_config.tts_voice_name if tts_config.tts_voice_name else None,
                pitch=tts_config.tts_pitch if tts_config.tts_pitch is not None else None,
                speaking_rate=(
                    tts_config.tts_speaking_rate
                    if tts_config.tts_speaking_rate is not None
                    else None
                ),
            )
            if audio_data:
                audio_format = resolve_audio_format(tts_provider)
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                logger.info(
                    "Playing keyboard TTS audio in backend",
                    extra={"audio_format": audio_format},
                )
                tts_service.play_audio_async(
                    audio_data,
                    audio_format,
                    stt_service=get_current_speech_to_text_service(),
                )
                return KeyboardTTSResponse(audio_base64=audio_base64)
            return KeyboardTTSResponse(audio_base64=None)
        except Exception:
            logger.exception("Error generating TTS for keyboard")
            return KeyboardTTSResponse(audio_base64=None)


