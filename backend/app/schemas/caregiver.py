from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field as PydanticField


class CaregiverBase(BaseModel):
    name: str = PydanticField(..., max_length=255)
    gender: Optional[str] = PydanticField(None, max_length=50)
    description: Optional[str] = PydanticField(None, max_length=2000)


class CaregiverCreate(CaregiverBase):
    pass


class CaregiverRead(CaregiverBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaregiverUpdate(BaseModel):
    name: Optional[str] = PydanticField(None, max_length=255)
    gender: Optional[str] = PydanticField(None, max_length=50)
    description: Optional[str] = PydanticField(None, max_length=2000)
