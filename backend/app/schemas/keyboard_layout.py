from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field as PydanticField


class KeyboardLayoutBase(BaseModel):
    name: str = PydanticField(..., max_length=255)
    description: Optional[str] = PydanticField(None, max_length=1000)
    rows: int = PydanticField(3, ge=1)
    columns: int = PydanticField(3, ge=1)
    predictive_cells: int = PydanticField(0, ge=0)
    cells: Optional[List[List[str]]] = None


class KeyboardLayoutCreate(KeyboardLayoutBase):
    sort_order: Optional[int] = PydanticField(
        default=None,
        description="If omitted, appended after existing layouts.",
    )


class KeyboardLayoutRead(KeyboardLayoutBase):
    id: int
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KeyboardLayoutUpdate(BaseModel):
    name: Optional[str] = PydanticField(None, max_length=255)
    description: Optional[str] = PydanticField(None, max_length=1000)
    rows: Optional[int] = PydanticField(None, ge=1)
    columns: Optional[int] = PydanticField(None, ge=1)
    predictive_cells: Optional[int] = PydanticField(None, ge=0)
    cells: Optional[List[List[str]]] = None
    sort_order: Optional[int] = None
