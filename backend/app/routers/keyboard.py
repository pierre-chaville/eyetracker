from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import get_keyboard_service, get_session_service
from app.schemas import (
    ChoicesRequest,
    KeyboardPredictionsResponse,
    KeyboardStepSelectionRequest,
    KeyboardTTSRequest,
    KeyboardTTSResponse,
)
from app.schemas.session import (
    CommunicationSessionCreate,
    CommunicationSessionRead,
    CommunicationSessionUpdate,
    SessionStepCreate,
    SessionStepRead,
)
from app.services.communication import CommunicationSessionService
from app.services.keyboard import KeyboardService
from app.utils.exceptions import EntityNotFoundError

router = APIRouter(tags=["keyboard"])


@router.post("/keyboard/predictions", response_model=KeyboardPredictionsResponse)
async def get_keyboard_predictions(
    request: ChoicesRequest,
    service: KeyboardService = Depends(get_keyboard_service),
) -> KeyboardPredictionsResponse:
    """
    Get predictive words for the keyboard based on current text.
    Returns up to 5 words suggested by LLM.
    Pass session_id and step_number to persist this step in a keyboard session.
    """
    return await service.get_predictions(request)


@router.post("/keyboard/tts", response_model=KeyboardTTSResponse)
async def keyboard_tts(
    request: KeyboardTTSRequest,
    service: KeyboardService = Depends(get_keyboard_service),
) -> KeyboardTTSResponse:
    """Generate TTS for keyboard input (word or letter)."""
    return await service.generate_tts(request)


@router.post("/keyboard/session-selection", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def record_keyboard_step_selection(
    body: KeyboardStepSelectionRequest,
    service: CommunicationSessionService = Depends(get_session_service),
) -> Response:
    """Persist the user's selection for the current keyboard session step."""
    try:
        await service.update_step_selection(
            body.session_id,
            body.step_number,
            body.selected_text,
            activation_mode=body.activation_mode,
            dwell_time_ms=body.dwell_time_ms,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Keyboard sessions (same model as communication, filtered by session_type="keyboard")

@router.post(
    "/keyboard/sessions",
    response_model=CommunicationSessionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_keyboard_session(
    session_data: CommunicationSessionCreate,
    service: CommunicationSessionService = Depends(get_session_service),
) -> CommunicationSessionRead:
    """Create a new keyboard session (session_type=keyboard)."""
    data_with_type = CommunicationSessionCreate(
        user_id=session_data.user_id,
        caregiver_id=session_data.caregiver_id,
        session_type="keyboard",
    )
    return await service.create_session(data_with_type)


@router.get(
    "/keyboard/sessions",
    response_model=List[CommunicationSessionRead],
)
async def list_keyboard_sessions(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    caregiver_id: Optional[int] = None,
    service: CommunicationSessionService = Depends(get_session_service),
) -> List[CommunicationSessionRead]:
    """List keyboard sessions with optional filtering."""
    return await service.list_sessions(
        skip, limit, user_id, caregiver_id, session_type="keyboard"
    )


@router.get(
    "/keyboard/sessions/{session_id}",
    response_model=CommunicationSessionRead,
)
async def get_keyboard_session(
    session_id: int,
    service: CommunicationSessionService = Depends(get_session_service),
) -> CommunicationSessionRead:
    """Get a keyboard session by ID with all steps."""
    try:
        return await service.get_session(session_id)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc


@router.put(
    "/keyboard/sessions/{session_id}",
    response_model=CommunicationSessionRead,
)
async def update_keyboard_session(
    session_id: int,
    session_data: CommunicationSessionUpdate,
    service: CommunicationSessionService = Depends(get_session_service),
) -> CommunicationSessionRead:
    """Update a keyboard session (e.g. end it)."""
    try:
        return await service.update_session(session_id, session_data)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc


@router.delete(
    "/keyboard/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_keyboard_session(
    session_id: int,
    service: CommunicationSessionService = Depends(get_session_service),
) -> Response:
    """Delete a keyboard session and its steps."""
    try:
        await service.delete_session(session_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc


@router.post(
    "/keyboard/sessions/{session_id}/steps",
    response_model=SessionStepRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_keyboard_session_step(
    session_id: int,
    step_data: SessionStepCreate,
    service: CommunicationSessionService = Depends(get_session_service),
) -> SessionStepRead:
    """Create a step in a keyboard session."""
    try:
        return await service.create_session_step(session_id, step_data)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc
