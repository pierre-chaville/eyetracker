from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON as SQLJSON, DateTime, func
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field as PydanticField
import json


# Pydantic models for JSON storage
class EyeTrackingSetup(BaseModel):
    """Eye tracking configuration settings"""
    device_type: Optional[str] = None
    calibration_points: Optional[int] = 9  # Default 9-point calibration
    sensitivity: Optional[float] = 1.0
    smoothing_factor: Optional[float] = 0.5
    gaze_threshold: Optional[float] = 0.1
    custom_settings: Optional[Dict[str, Any]] = None


class CommunicationSettings(BaseModel):
    """Communication preferences and settings"""
    language: Optional[str] = "en"
    prediction_enabled: Optional[bool] = True
    auto_complete: Optional[bool] = True
    word_suggestions_count: Optional[int] = 5
    gaze_dwell_time: Optional[float] = 0.5  # seconds
    communication_method: Optional[str] = "gaze"  # gaze, blink, etc.
    custom_settings: Optional[Dict[str, Any]] = None


# SQLModel User model
class User(SQLModel, table=True):
    """User model for storing user data"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    eye_tracking_setup: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(SQLJSON))  # Stored as JSON
    calibration: Optional[str] = Field(default=None)  # Can store calibration data as JSON string
    communication: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(SQLJSON))  # Stored as JSON
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False))
    )
    is_active: bool = Field(default=True)
    notes: Optional[str] = Field(default=None, max_length=1000)


# Pydantic models for API requests/responses
class UserCreate(BaseModel):
    """Model for creating a new user"""
    name: str = PydanticField(..., max_length=255)
    eye_tracking_setup: Optional[EyeTrackingSetup] = None
    calibration: Optional[str] = None
    communication: Optional[CommunicationSettings] = None
    notes: Optional[str] = None


class UserUpdate(BaseModel):
    """Model for updating an existing user"""
    name: Optional[str] = PydanticField(None, max_length=255)
    eye_tracking_setup: Optional[EyeTrackingSetup] = None
    calibration: Optional[str] = None
    communication: Optional[CommunicationSettings] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class UserResponse(BaseModel):
    """Model for user API responses"""
    id: int
    name: str
    eye_tracking_setup: Optional[EyeTrackingSetup] = None
    calibration: Optional[str] = None
    communication: Optional[CommunicationSettings] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True

