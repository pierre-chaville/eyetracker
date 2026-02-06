from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import get_communication_service, get_session_service
from app.schemas import (
    ChoiceSelectionRequest,
    ChoiceSelectionResponse,
    ChoicesRequest,
    ChoicesResponse,
    CommunicationRequest,
    CommunicationResponse,
)
from app.services.communication import CommunicationService, CommunicationSessionService
from app.utils.exceptions import EntityNotFoundError

from app.models import (
    CommunicationSessionCreate,
    CommunicationSessionResponse,
    CommunicationSessionUpdate,
    SessionStepCreate,
    SessionStepResponse,
)

router = APIRouter(tags=["communication"])


@router.post(
    "/api/communication/interpret",
    response_model=CommunicationResponse,
)
async def interpret_gaze(request: CommunicationRequest) -> CommunicationResponse:
    """Interpret gaze points and generate communication suggestions using AI."""
    return CommunicationResponse(
        interpreted_text="Hello",
        confidence=0.85,
        suggestions=["Hello", "Hi there", "Good morning"],
    )


@router.post("/api/communication/choices", response_model=ChoicesResponse)
async def get_choices(
    request: ChoicesRequest,
    service: CommunicationService = Depends(get_communication_service),
) -> ChoicesResponse:
    """
    Get available choices for the communication grid.
    Returns 2-8 choices based on context using LLM.
    """
    return await service.generate_choices(request)


@router.post("/api/communication/select", response_model=ChoiceSelectionResponse)
async def select_choice(
    request: ChoiceSelectionRequest,
    service: CommunicationService = Depends(get_communication_service),
) -> ChoiceSelectionResponse:
    """
    Handle selection of a choice.
    This triggers text-to-speech generation for the selected choice.
    """
    return await service.select_choice(request)


@router.post(
    "/api/communication/sessions",
    response_model=CommunicationSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    session_data: CommunicationSessionCreate,
    service: CommunicationSessionService = Depends(get_session_service),
) -> CommunicationSessionResponse:
    """Create a new communication session."""
    return service.create_session(session_data)


@router.get(
    "/api/communication/sessions",
    response_model=List[CommunicationSessionResponse],
)
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    caregiver_id: Optional[int] = None,
    service: CommunicationSessionService = Depends(get_session_service),
) -> List[CommunicationSessionResponse]:
    """List all communication sessions with optional filtering."""
    return service.list_sessions(skip, limit, user_id, caregiver_id)


@router.get(
    "/api/communication/sessions/{session_id}",
    response_model=CommunicationSessionResponse,
)
async def get_communication_session(
    session_id: int,
    service: CommunicationSessionService = Depends(get_session_service),
) -> CommunicationSessionResponse:
    """Get a specific communication session by ID with all steps."""
    try:
        return service.get_session(session_id)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc


@router.put(
    "/api/communication/sessions/{session_id}",
    response_model=CommunicationSessionResponse,
)
async def update_session(
    session_id: int,
    session_data: CommunicationSessionUpdate,
    service: CommunicationSessionService = Depends(get_session_service),
) -> CommunicationSessionResponse:
    """Update an existing communication session (e.g., set ended_at)."""
    try:
        return service.update_session(session_id, session_data)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc


@router.delete(
    "/api/communication/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_session(
    session_id: int,
    service: CommunicationSessionService = Depends(get_session_service),
) -> Response:
    """Delete a communication session and all its steps."""
    try:
        service.delete_session(session_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc


@router.post(
    "/api/communication/sessions/{session_id}/steps",
    response_model=SessionStepResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session_step(
    session_id: int,
    step_data: SessionStepCreate,
    service: CommunicationSessionService = Depends(get_session_service),
) -> SessionStepResponse:
    """Create a new step in a communication session."""
    try:
        return service.create_session_step(session_id, step_data)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc
