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
from app.schemas.session import (
    CommunicationSessionCreate,
    CommunicationSessionRead,
    CommunicationSessionUpdate,
    SessionStepCreate,
    SessionStepRead,
)

router = APIRouter(tags=["communication"])


@router.post(
    "/communication/interpret",
    response_model=CommunicationResponse,
)
async def interpret_gaze(request: CommunicationRequest) -> CommunicationResponse:
    """Interpret gaze points and generate communication suggestions using AI."""
    return CommunicationResponse(
        interpreted_text="Hello",
        confidence=0.85,
        suggestions=["Hello", "Hi there", "Good morning"],
    )


@router.post("/communication/choices", response_model=ChoicesResponse)
async def get_choices(
    request: ChoicesRequest,
    service: CommunicationService = Depends(get_communication_service),
) -> ChoicesResponse:
    """
    Get available choices for the communication grid.
    Returns 2-8 choices based on context using LLM.
    """
    return await service.generate_choices(request)


@router.post("/communication/select", response_model=ChoiceSelectionResponse)
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
    "/communication/sessions",
    response_model=CommunicationSessionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    session_data: CommunicationSessionCreate,
    service: CommunicationSessionService = Depends(get_session_service),
) -> CommunicationSessionRead:
    """Create a new communication session (CommunicationSessionRead)."""
    return await service.create_session(session_data)


@router.get(
    "/communication/sessions",
    response_model=List[CommunicationSessionRead],
)
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    caregiver_id: Optional[int] = None,
    service: CommunicationSessionService = Depends(get_session_service),
) -> List[CommunicationSessionRead]:
    """List all communication sessions with optional filtering (CommunicationSessionRead)."""
    return await service.list_sessions(
        skip, limit, user_id, caregiver_id, session_type="communication"
    )


@router.get(
    "/communication/sessions/{session_id}",
    response_model=CommunicationSessionRead,
)
async def get_communication_session(
    session_id: int,
    service: CommunicationSessionService = Depends(get_session_service),
) -> CommunicationSessionRead:
    """Get a specific communication session by ID with all steps (CommunicationSessionRead)."""
    try:
        return await service.get_session(session_id)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc


@router.put(
    "/communication/sessions/{session_id}",
    response_model=CommunicationSessionRead,
)
async def update_session(
    session_id: int,
    session_data: CommunicationSessionUpdate,
    service: CommunicationSessionService = Depends(get_session_service),
) -> CommunicationSessionRead:
    """Update an existing communication session (CommunicationSessionRead)."""
    try:
        return await service.update_session(session_id, session_data)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc


@router.delete(
    "/communication/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_session(
    session_id: int,
    service: CommunicationSessionService = Depends(get_session_service),
) -> Response:
    """Delete a communication session and all its steps."""
    try:
        await service.delete_session(session_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc


@router.post(
    "/communication/sessions/{session_id}/steps",
    response_model=SessionStepRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_session_step(
    session_id: int,
    step_data: SessionStepCreate,
    service: CommunicationSessionService = Depends(get_session_service),
) -> SessionStepRead:
    """Create a new step in a communication session (SessionStepRead)."""
    try:
        return await service.create_session_step(session_id, step_data)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc
