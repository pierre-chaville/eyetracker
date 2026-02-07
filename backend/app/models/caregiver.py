from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, func
from sqlmodel import Column, Field, SQLModel


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
