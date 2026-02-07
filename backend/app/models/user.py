from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON as SQLJSON, DateTime, func
from sqlmodel import Column, Field, SQLModel


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
