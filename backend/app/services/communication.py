from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CommunicationSession, SessionStep
from app.schemas import (
    Choice,
    ChoiceSelectionRequest,
    ChoiceSelectionResponse,
    ChoicesRequest,
    ChoicesResponse,
)
from app.schemas.session import (
    ChoiceData,
    CommunicationSessionCreate,
    CommunicationSessionRead,
    CommunicationSessionUpdate,
    SessionStepCreate,
    SessionStepRead,
)
from app.services.speak import speak_text
from app.services.suggestions import SuggestionsService
from app.utils.exceptions import EntityNotFoundError
from app.utils.logging import get_logger

logger = get_logger()


def step_to_response(step: SessionStep) -> SessionStepRead:
    choices = None
    if step.choices_json:
        choices = [
            ChoiceData(text=c.get("text", ""), probability=c.get("probability", 0.0))
            for c in step.choices_json
        ]
    return SessionStepRead(
        id=step.id,
        session_id=step.session_id,
        step_number=step.step_number,
        message_role=step.message_role,
        message_content=step.message_content,
        choices=choices,
        selected_choice_text=step.selected_choice_text,
        timestamp=step.timestamp,
    )


async def session_to_response(
    session: CommunicationSession,
    db_session: AsyncSession,
) -> CommunicationSessionRead:
    steps_statement = (
        select(SessionStep)
        .where(SessionStep.session_id == session.id)
        .order_by(SessionStep.step_number)
    )
    result = await db_session.execute(steps_statement)
    steps = list(result.scalars().all())
    return CommunicationSessionRead(
        id=session.id,
        user_id=session.user_id,
        caregiver_id=session.caregiver_id,
        session_type=getattr(session, "session_type", "communication"),
        started_at=session.started_at,
        ended_at=session.ended_at,
        created_at=session.created_at,
        updated_at=session.updated_at,
        steps=[step_to_response(step) for step in steps],
    )


class CommunicationSessionService:
    """Service for communication session operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(
        self,
        session_data: CommunicationSessionCreate,
    ) -> CommunicationSessionRead:
        session_type = session_data.session_type or "communication"
        session = CommunicationSession(
            user_id=session_data.user_id,
            caregiver_id=session_data.caregiver_id,
            session_type=session_type,
        )
        self._session.add(session)
        await self._session.commit()
        await self._session.refresh(session)
        return await session_to_response(session, self._session)

    async def list_sessions(
        self,
        skip: int,
        limit: int,
        user_id: Optional[int],
        caregiver_id: Optional[int],
        session_type: Optional[str] = None,
    ) -> List[CommunicationSessionRead]:
        statement = select(CommunicationSession)
        if user_id is not None:
            statement = statement.where(CommunicationSession.user_id == user_id)
        if caregiver_id is not None:
            statement = statement.where(CommunicationSession.caregiver_id == caregiver_id)
        if session_type is not None:
            statement = statement.where(CommunicationSession.session_type == session_type)
        statement = (
            statement.order_by(CommunicationSession.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(statement)
        sessions = list(result.scalars().all())
        return [await session_to_response(session, self._session) for session in sessions]

    async def get_session(self, session_id: int) -> CommunicationSessionRead:
        session = await self._session.get(CommunicationSession, session_id)
        if not session:
            raise EntityNotFoundError("Session", session_id)
        return await session_to_response(session, self._session)

    async def update_session(
        self,
        session_id: int,
        session_data: CommunicationSessionUpdate,
    ) -> CommunicationSessionRead:
        session = await self._session.get(CommunicationSession, session_id)
        if not session:
            raise EntityNotFoundError("Session", session_id)
        if session_data.ended_at is not None:
            session.ended_at = session_data.ended_at
        session.updated_at = datetime.utcnow()
        self._session.add(session)
        await self._session.commit()
        await self._session.refresh(session)
        return await session_to_response(session, self._session)

    async def delete_session(self, session_id: int) -> None:
        session = await self._session.get(CommunicationSession, session_id)
        if not session:
            raise EntityNotFoundError("Session", session_id)
        steps_statement = select(SessionStep).where(SessionStep.session_id == session_id)
        result = await self._session.execute(steps_statement)
        steps = list(result.scalars().all())
        for step in steps:
            self._session.delete(step)
        self._session.delete(session)
        await self._session.commit()

    async def create_session_step(
        self,
        session_id: int,
        step_data: SessionStepCreate,
    ) -> SessionStepRead:
        session = await self._session.get(CommunicationSession, session_id)
        if not session:
            raise EntityNotFoundError("Session", session_id)
        choices_json = None
        if step_data.choices:
            choices_json = [
                {"text": c.get("text", ""), "probability": c.get("probability", 0.0)}
                for c in step_data.choices
            ]
        step = SessionStep(
            session_id=session_id,
            step_number=step_data.step_number,
            message_role=step_data.message_role,
            message_content=step_data.message_content,
            choices_json=choices_json,
            selected_choice_text=step_data.selected_choice_text,
        )
        self._session.add(step)
        await self._session.commit()
        await self._session.refresh(step)
        session.updated_at = datetime.utcnow()
        self._session.add(session)
        await self._session.commit()
        return step_to_response(step)

    async def update_step_selection(
        self,
        session_id: int,
        step_number: int,
        selected_text: str,
    ) -> None:
        """Set selected_choice_text on an existing step (keyboard or communication)."""
        session = await self._session.get(CommunicationSession, session_id)
        if not session:
            raise EntityNotFoundError("Session", session_id)
        step_statement = select(SessionStep).where(
            SessionStep.session_id == session_id,
            SessionStep.step_number == step_number,
        )
        result = await self._session.execute(step_statement)
        step = result.scalars().first()
        if not step:
            raise EntityNotFoundError("SessionStep", step_number)
        step.selected_choice_text = selected_text
        step.timestamp = datetime.utcnow()
        self._session.add(step)
        session.updated_at = datetime.utcnow()
        self._session.add(session)
        await self._session.commit()


class CommunicationService:
    """Service for communication-related features (choices and selection)."""

    def __init__(
        self,
        session: AsyncSession,
        suggestions_service: SuggestionsService,
    ) -> None:
        self._session = session
        self._suggestions_service = suggestions_service

    async def generate_choices(self, request: ChoicesRequest) -> ChoicesResponse:
        items = await self._suggestions_service.generate(request, "communication")
        choices = [
            Choice(
                id=str(i + 1),
                text=item["text"],
                icon=None,
                probability=item["probability"],
            )
            for i, item in enumerate(items)
        ]
        return ChoicesResponse(choices=choices)

    async def select_choice(self, request: ChoiceSelectionRequest) -> ChoiceSelectionResponse:
        try:
            audio_base64 = None
            if request.choice_text:
                audio_base64 = await speak_text(text=request.choice_text)
            if (
                request.session_id is not None
                and request.step_number is not None
                and request.choice_text
            ):
                try:
                    step_statement = select(SessionStep).where(
                        SessionStep.session_id == request.session_id,
                        SessionStep.step_number == request.step_number,
                    )
                    result = await self._session.execute(step_statement)
                    step = result.scalars().first()
                    if step:
                        step.selected_choice_text = request.choice_text
                        step.timestamp = datetime.utcnow()
                        self._session.add(step)
                        comm_session = await self._session.get(
                            CommunicationSession, request.session_id
                        )
                        if comm_session:
                            comm_session.updated_at = datetime.utcnow()
                            self._session.add(comm_session)
                        await self._session.commit()
                except Exception:
                    logger.exception("Error updating session step with selected choice")
            return ChoiceSelectionResponse(
                success=True,
                message=f"Choice '{request.choice_id}' selected",
                updated_text=request.current_text,
                audio_base64=audio_base64,
            )
        except Exception as exc:
            logger.exception("Error in select_choice")
            audio_base64 = await speak_text(text=request.choice_text or "") if request.choice_text else None
            return ChoiceSelectionResponse(
                success=True,
                message=f"Choice '{request.choice_id}' selected",
                updated_text=request.current_text,
                audio_base64=audio_base64,
                error=str(exc),
            )


