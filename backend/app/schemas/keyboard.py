from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class KeyboardPredictionsResponse(BaseModel):
    words: List[str]


class KeyboardTTSRequest(BaseModel):
    text: Optional[str] = None


class KeyboardTTSResponse(BaseModel):
    audio_base64: Optional[str]


class KeyboardStepSelectionRequest(BaseModel):
    """Record which option the user chose for a keyboard session step (matches communication select)."""

    session_id: int
    step_number: int
    selected_text: str
