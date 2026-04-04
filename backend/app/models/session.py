from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON as SQLJSON, DateTime, func
from sqlmodel import Column, Field, SQLModel


class CommunicationSession(SQLModel, table=True):
    """Session model for communication grid or keyboard (session_type distinguishes)."""

    __tablename__ = "communication_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    caregiver_id: Optional[int] = Field(default=None, foreign_key="caregivers.id")
    session_type: str = Field(
        default="communication",
        max_length=50,
        description="'communication' or 'keyboard'",
    )
    prompt: Optional[str] = Field(default=None, description="System prompt used for this session")
    llm_model: Optional[str] = Field(default=None, max_length=100, description="LLM model name")
    temperature: Optional[float] = Field(default=None, description="LLM temperature")
    user_notes: Optional[str] = Field(default=None, description="User notes/context at session start")
    keyboard_layout_name: Optional[str] = Field(
        default=None, max_length=200, description="Keyboard layout name (keyboard sessions only)"
    )
    feedback_json: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(SQLJSON),
        description="Post-session caregiver feedback (JSON)",
    )
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
            "JSON array of choices with text and probability: "
            "[{'text': '...', 'probability': 0.5}, ...]"
        ),
    )
    selected_choice_text: Optional[str] = Field(
        default=None,
        max_length=500,
        description="The choice that was selected",
    )
    activation_mode: Optional[str] = Field(
        default=None,
        max_length=50,
        description="'click' or 'gaze_dwell'",
    )
    dwell_time_ms: Optional[int] = Field(
        default=None,
        description="Dwell duration in milliseconds (when activation_mode is gaze_dwell)",
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
    )
