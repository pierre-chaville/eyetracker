from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_keyboard_service
from app.schemas import ChoicesRequest, KeyboardPredictionsResponse, KeyboardTTSRequest, KeyboardTTSResponse
from app.services.keyboard import KeyboardService

router = APIRouter(tags=["keyboard"])


@router.post("/keyboard/predictions", response_model=KeyboardPredictionsResponse)
async def get_keyboard_predictions(
    request: ChoicesRequest,
    service: KeyboardService = Depends(get_keyboard_service),
) -> KeyboardPredictionsResponse:
    """
    Get predictive words for the keyboard based on current text.
    Returns up to 5 words suggested by LLM.
    """
    return await service.get_predictions(request)


@router.post("/keyboard/tts", response_model=KeyboardTTSResponse)
async def keyboard_tts(
    request: KeyboardTTSRequest,
    service: KeyboardService = Depends(get_keyboard_service),
) -> KeyboardTTSResponse:
    """Generate TTS for keyboard input (word or letter)."""
    return await service.generate_tts(request)
