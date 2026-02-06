from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import JSON as SQLJSON, DateTime, func
from sqlmodel import Field, SQLModel, Column


class EyeTrackingSetup(BaseModel):
    """Eye tracking configuration settings."""

    device_type: Optional[str] = None
    calibration_points: Optional[int] = 9
    sensitivity: Optional[float] = 1.0
    smoothing_factor: Optional[float] = 0.5
    gaze_threshold: Optional[float] = 0.1
    custom_settings: Optional[Dict[str, Any]] = None


class CommunicationSettings(BaseModel):
    """Communication preferences and settings."""

    language: Optional[str] = "en"
    prediction_enabled: Optional[bool] = True
    auto_complete: Optional[bool] = True
    word_suggestions_count: Optional[int] = 5
    gaze_dwell_time: Optional[float] = 0.5
    communication_method: Optional[str] = "gaze"
    custom_settings: Optional[Dict[str, Any]] = None


class User(SQLModel, table=True):
    """User model for storing user data."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    eye_tracking_setup: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(SQLJSON),
    )
    calibration: Optional[str] = Field(default=None)
    communication: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(SQLJSON),
    )
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False)),
    )
    is_active: bool = Field(default=True)
    notes: Optional[str] = Field(default=None, max_length=1000)
    gender: Optional[str] = Field(default=None, max_length=50)
    age: Optional[int] = Field(default=None)
    voice: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Voice identifier for TTS",
    )


class UserCreate(BaseModel):
    """Model for creating a new user."""

    name: str = PydanticField(..., max_length=255)
    eye_tracking_setup: Optional[EyeTrackingSetup] = None
    calibration: Optional[str] = None
    communication: Optional[CommunicationSettings] = None
    notes: Optional[str] = None
    gender: Optional[str] = PydanticField(None, max_length=50)
    age: Optional[int] = None
    voice: Optional[str] = PydanticField(None, max_length=100)


class UserUpdate(BaseModel):
    """Model for updating an existing user."""

    name: Optional[str] = PydanticField(None, max_length=255)
    eye_tracking_setup: Optional[EyeTrackingSetup] = None
    calibration: Optional[str] = None
    communication: Optional[CommunicationSettings] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    gender: Optional[str] = PydanticField(None, max_length=50)
    age: Optional[int] = None
    voice: Optional[str] = PydanticField(None, max_length=100)


class UserResponse(BaseModel):
    """Model for user API responses."""

    id: int
    name: str
    eye_tracking_setup: Optional[EyeTrackingSetup] = None
    calibration: Optional[str] = None
    communication: Optional[CommunicationSettings] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    notes: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    voice: Optional[str] = None

    class Config:
        from_attributes = True


class Caregiver(SQLModel, table=True):
    """Caregiver model for storing caregiver data."""

    __tablename__ = "caregivers"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    gender: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=2000)
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False)),
    )


class CaregiverCreate(BaseModel):
    """Model for creating a new caregiver."""

    name: str = PydanticField(..., max_length=255)
    gender: Optional[str] = PydanticField(None, max_length=50)
    description: Optional[str] = PydanticField(None, max_length=2000)


class CaregiverUpdate(BaseModel):
    """Model for updating an existing caregiver."""

    name: Optional[str] = PydanticField(None, max_length=255)
    gender: Optional[str] = PydanticField(None, max_length=50)
    description: Optional[str] = PydanticField(None, max_length=2000)


class CaregiverResponse(BaseModel):
    """Model for caregiver API responses."""

    id: int
    name: str
    gender: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommunicationSession(SQLModel, table=True):
    """Communication session model for storing conversation sessions."""

    __tablename__ = "communication_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    caregiver_id: Optional[int] = Field(default=None, foreign_key="caregivers.id")
    started_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
    )
    ended_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=False)))
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False)),
    )


class SessionStep(SQLModel, table=True):
    """Session step model for storing conversation steps with choices."""

    __tablename__ = "session_steps"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="communication_sessions.id")
    step_number: int = Field(description="Step number in the session (1, 2, 3, ...)")
    message_role: Optional[str] = Field(
        default=None,
        max_length=50,
        description="'caregiver' or 'user'",
    )
    message_content: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Message content",
    )
    choices_json: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(SQLJSON),
        description=(
            "JSON array of choices with text and probability: [{'text': '...', 'probability': 0.5}, ...]"
        ),
    )
    selected_choice_text: Optional[str] = Field(
        default=None,
        max_length=500,
        description="The choice that was selected",
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
    )


class CommunicationSessionCreate(BaseModel):
    """Model for creating a new communication session."""

    user_id: Optional[int] = None
    caregiver_id: Optional[int] = None


class CommunicationSessionUpdate(BaseModel):
    """Model for updating a communication session."""

    ended_at: Optional[datetime] = None


class SessionStepCreate(BaseModel):
    """Model for creating a session step."""

    session_id: int
    step_number: int
    message_role: Optional[str] = None
    message_content: Optional[str] = None
    choices: Optional[List[Dict[str, Any]]] = None
    selected_choice_text: Optional[str] = None


class ChoiceData(BaseModel):
    """Model for a choice with probability."""

    text: str
    probability: float


class SessionStepResponse(BaseModel):
    """Model for session step API responses."""

    id: int
    session_id: int
    step_number: int
    message_role: Optional[str] = None
    message_content: Optional[str] = None
    choices: Optional[List[ChoiceData]] = None
    selected_choice_text: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class CommunicationSessionResponse(BaseModel):
    """Model for communication session API responses."""

    id: int
    user_id: Optional[int] = None
    caregiver_id: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    steps: Optional[List[SessionStepResponse]] = None

    class Config:
        from_attributes = True
