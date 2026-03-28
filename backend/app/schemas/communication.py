from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class GazePoint(BaseModel):
    x: float
    y: float
    timestamp: float


class CommunicationRequest(BaseModel):
    gaze_points: List[GazePoint]
    context: Optional[str] = None


class CommunicationResponse(BaseModel):
    interpreted_text: str
    confidence: float
    suggestions: List[str]


class Choice(BaseModel):
    """A choice option for the communication grid."""

    id: str
    text: Optional[str] = None
    icon: Optional[str] = None
    probability: Optional[float] = None


class ChoicesResponse(BaseModel):
    """Response with available choices."""

    choices: List[Choice]


class ChoiceSelectionRequest(BaseModel):
    """Request to select a choice."""

    choice_id: str
    choice_text: Optional[str] = None
    current_text: Optional[str] = None
    session_id: Optional[int] = None
    step_number: Optional[int] = None
    activation_mode: Optional[str] = None
    dwell_time_ms: Optional[int] = None


class ChoiceSelectionResponse(BaseModel):
    success: bool
    message: str
    updated_text: Optional[str] = None
    audio_base64: Optional[str] = None
    error: Optional[str] = None


class ChoicesRequest(BaseModel):
    """Request for generating choices."""

    conversation_history: Optional[List[Dict[str, str]]] = None
    user_id: Optional[int] = None
    caregiver_id: Optional[int] = None
    current_text: Optional[str] = None
    session_id: Optional[int] = None
    step_number: Optional[int] = None
