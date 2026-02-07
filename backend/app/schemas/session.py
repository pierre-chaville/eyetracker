from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class CommunicationSessionCreate(BaseModel):
    user_id: Optional[int] = None
    caregiver_id: Optional[int] = None


class CommunicationSessionUpdate(BaseModel):
    ended_at: Optional[datetime] = None


class CommunicationSessionRead(BaseModel):
    id: int
    user_id: Optional[int] = None
    caregiver_id: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    steps: Optional[List["SessionStepRead"]] = None

    class Config:
        from_attributes = True


class SessionStepCreate(BaseModel):
    session_id: int
    step_number: int
    message_role: Optional[str] = None
    message_content: Optional[str] = None
    choices: Optional[List[Dict[str, float]]] = None
    selected_choice_text: Optional[str] = None


class ChoiceData(BaseModel):
    text: str
    probability: float


class SessionStepRead(BaseModel):
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


CommunicationSessionRead.model_rebuild()
