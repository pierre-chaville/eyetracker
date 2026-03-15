from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import (
    ChoicesRequest,
    KeyboardPredictionsResponse,
    KeyboardTTSRequest,
    KeyboardTTSResponse,
)
from app.services.speak import speak_text
from app.services.suggestions import SuggestionsService
from app.utils.logging import get_logger

logger = get_logger(__name__)


class KeyboardService:
    """Service for keyboard predictions and TTS."""

    def __init__(
        self,
        session: AsyncSession,
        suggestions_service: SuggestionsService,
    ) -> None:
        self._session = session
        self._suggestions_service = suggestions_service

    async def get_predictions(self, request: ChoicesRequest) -> KeyboardPredictionsResponse:
        items = await self._suggestions_service.generate(request, "keyboard")
        words = [item["text"] for item in items[:5] if item.get("text")]
        return KeyboardPredictionsResponse(words=words)

    async def generate_tts(self, request: KeyboardTTSRequest) -> KeyboardTTSResponse:
        text = request.text or ""
        if not text.strip():
            return KeyboardTTSResponse(audio_base64=None)
        try:
            audio_base64 = await speak_text(text=text)
            return KeyboardTTSResponse(audio_base64=audio_base64)
        except Exception:
            logger.exception("Error generating TTS for keyboard")
            return KeyboardTTSResponse(audio_base64=None)


