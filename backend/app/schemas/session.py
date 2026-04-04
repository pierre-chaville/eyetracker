from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SessionFeedback(BaseModel):
    """Post-session caregiver feedback."""

    state_before: Optional[str] = None
    mood_before: Optional[str] = None
    gaze_accuracy: Optional[str] = None
    calibration_quality: Optional[str] = None
    head_stability: Optional[str] = None
    intentional_selections: Optional[str] = None
    choices_relevance: Optional[str] = None
    communication_pace: Optional[str] = None
    engagement_level: Optional[str] = None
    enjoyment: Optional[str] = None
    session_end_reason: Optional[str] = None
    overall_rating: Optional[str] = None
    compared_previous: Optional[str] = None
    key_achievements: Optional[List[str]] = None
    quick_note: Optional[str] = None


class CommunicationSessionCreate(BaseModel):
    user_id: Optional[int] = None
    caregiver_id: Optional[int] = None
    session_type: Optional[str] = "communication"
    prompt: Optional[str] = None
    llm_model: Optional[str] = None
    temperature: Optional[float] = None
    user_notes: Optional[str] = None
    keyboard_layout_name: Optional[str] = None


class CommunicationSessionUpdate(BaseModel):
    ended_at: Optional[datetime] = None
    feedback: Optional[SessionFeedback] = None


class CommunicationSessionRead(BaseModel):
    id: int
    user_id: Optional[int] = None
    caregiver_id: Optional[int] = None
    session_type: str = "communication"
    prompt: Optional[str] = None
    llm_model: Optional[str] = None
    temperature: Optional[float] = None
    user_notes: Optional[str] = None
    keyboard_layout_name: Optional[str] = None
    feedback: Optional[Dict[str, Any]] = None
    ai_analysis_markdown: Optional[str] = None
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
    activation_mode: Optional[str] = None
    dwell_time_ms: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True


CommunicationSessionRead.model_rebuild()
