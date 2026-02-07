from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field as PydanticField


class EyeTrackingSetup(BaseModel):
    device_type: Optional[str] = None
    calibration_points: Optional[int] = 9
    sensitivity: Optional[float] = 1.0
    smoothing_factor: Optional[float] = 0.5
    gaze_threshold: Optional[float] = 0.1
    custom_settings: Optional[Dict[str, Any]] = None


class CommunicationSettings(BaseModel):
    language: Optional[str] = "en"
    prediction_enabled: Optional[bool] = True
    auto_complete: Optional[bool] = True
    word_suggestions_count: Optional[int] = 5
    gaze_dwell_time: Optional[float] = 0.5
    communication_method: Optional[str] = "gaze"
    custom_settings: Optional[Dict[str, Any]] = None


class UserBase(BaseModel):
    name: str = PydanticField(..., max_length=255)
    eye_tracking_setup: Optional[EyeTrackingSetup] = None
    calibration: Optional[str] = None
    communication: Optional[CommunicationSettings] = None
    notes: Optional[str] = None
    gender: Optional[str] = PydanticField(None, max_length=50)
    age: Optional[int] = None
    voice: Optional[str] = PydanticField(None, max_length=100)


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = PydanticField(None, max_length=255)
    eye_tracking_setup: Optional[EyeTrackingSetup] = None
    calibration: Optional[str] = None
    communication: Optional[CommunicationSettings] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    gender: Optional[str] = PydanticField(None, max_length=50)
    age: Optional[int] = None
    voice: Optional[str] = PydanticField(None, max_length=100)
