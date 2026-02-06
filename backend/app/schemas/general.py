from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class RootResponse(BaseModel):
    message: str
    status: str


class HealthResponse(BaseModel):
    status: str


class MessageResponse(BaseModel):
    success: bool
    message: str


class EyeTrackingStatus(BaseModel):
    is_active: bool
    calibration_status: Optional[str] = None


class SpeechToTextStatusResponse(BaseModel):
    is_active: bool
    websocket_connections: int
