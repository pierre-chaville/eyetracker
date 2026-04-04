from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON as SQLJSON, DateTime, func
from sqlmodel import Column, Field, SQLModel


class KeyboardLayout(SQLModel, table=True):
    """Keyboard layout definition for communication grids."""

    __tablename__ = "keyboard_layouts"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    rows: int = Field(default=3, ge=1)
    columns: int = Field(default=3, ge=1)
    predictive_cells: int = Field(default=0, ge=0)
    sort_order: int = Field(
        default=0,
        description="Display order (lower first); used on keyboard screen and setup list.",
    )
    cells: Optional[List[List[str]]] = Field(default=None, sa_column=Column(SQLJSON))
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False)),
    )
