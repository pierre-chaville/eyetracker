from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class KeyboardPredictionsResponse(BaseModel):
    words: List[str]


class KeyboardTTSRequest(BaseModel):
    text: Optional[str] = None


class KeyboardTTSResponse(BaseModel):
    audio_base64: Optional[str]
