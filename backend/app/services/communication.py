from __future__ import annotations

import base64
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import load_config
from app.models import Caregiver, CommunicationSession, SessionStep, User
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
from app.utils.logging import get_logger
from app.utils.tts import resolve_audio_format, resolve_tts_provider
from app.utils.exceptions import EntityNotFoundError
from app.services.speech_to_text import get_current_speech_to_text_service

from app.services.llm import get_llm_service
from app.services.tts import get_tts_service

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
        session = CommunicationSession(
            user_id=session_data.user_id,
            caregiver_id=session_data.caregiver_id,
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
    ) -> List[CommunicationSessionRead]:
        statement = select(CommunicationSession)
        if user_id is not None:
            statement = statement.where(CommunicationSession.user_id == user_id)
        if caregiver_id is not None:
            statement = statement.where(CommunicationSession.caregiver_id == caregiver_id)
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


class CommunicationService:
    """Service for communication-related features (choices and selection)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def generate_choices(self, request: ChoicesRequest) -> ChoicesResponse:
        try:
            config = load_config()
            user_notes = None
            caregiver_description = None
            if request.user_id:
                user = await self._session.get(User, request.user_id)
                if user:
                    user_notes = user.notes
            if request.caregiver_id:
                caregiver = await self._session.get(Caregiver, request.caregiver_id)
                if caregiver:
                    caregiver_description = caregiver.description
            llm_service = get_llm_service(
                provider=config.provider,
                model=config.model,
                temperature=config.temperature,
            )
            llm_choices = await llm_service.generate_choices(
                system_prompt=config.communicate_prompt,
                conversation_history=request.conversation_history or [],
                user_notes=user_notes,
                caregiver_description=caregiver_description,
                current_text=request.current_text,
            )
            choices = [
                Choice(
                    id=str(i + 1),
                    text=choice["text"],
                    probability=choice["probability"],
                )
                for i, choice in enumerate(llm_choices)
            ]
            if request.session_id and request.step_number is not None:
                try:
                    message_role = None
                    message_content = None
                    if request.conversation_history:
                        last_message = request.conversation_history[-1]
                        message_role = last_message.get("role", "").lower()
                        message_content = last_message.get("content", "")
                        if message_role == "assistant":
                            message_role = "user"
                        elif message_role == "human":
                            message_role = "user"
                        elif message_role not in ("user", "caregiver"):
                            message_role = None
                    choices_data = [
                        {"text": c.text, "probability": c.probability} for c in choices
                    ]
                    step = SessionStep(
                        session_id=request.session_id,
                        step_number=request.step_number,
                        message_role=message_role,
                        message_content=message_content,
                        choices_json=choices_data,
                        selected_choice_text=None,
                    )
                    self._session.add(step)
                    comm_session = await self._session.get(
                        CommunicationSession, request.session_id
                    )
                    if comm_session:
                        comm_session.updated_at = datetime.utcnow()
                        self._session.add(comm_session)
                    await self._session.commit()
                except Exception:
                    logger.exception("Error saving session step")
            return ChoicesResponse(choices=choices)
        except Exception:
            logger.exception("Error generating choices")
            choices = [
                Choice(id="1", text="Yes", icon="✓", probability=0.5),
                Choice(id="2", text="No", icon="✗", probability=0.5),
                Choice(id="3", text="More", icon="+", probability=0.3),
                Choice(id="4", text="Done", icon="✓", probability=0.2),
            ]
            return ChoicesResponse(choices=choices)

    async def select_choice(self, request: ChoiceSelectionRequest) -> ChoiceSelectionResponse:
        try:
            config = load_config()
            tts_provider = resolve_tts_provider(config)
            tts_service = get_tts_service(provider=tts_provider)
            audio_base64 = None
            audio_data = None
            audio_format = resolve_audio_format(tts_provider)
            if request.choice_text:
                tts_config = load_config()
                logger.info(
                    "Generating TTS for selected choice",
                    extra={"provider": tts_provider},
                )
                audio_data = tts_service.generate_speech(
                    text=request.choice_text,
                    language=tts_config.tts_language or "en",
                    voice_name=tts_config.tts_voice_name if tts_config.tts_voice_name else None,
                    pitch=tts_config.tts_pitch if tts_config.tts_pitch is not None else None,
                    speaking_rate=(
                        tts_config.tts_speaking_rate
                        if tts_config.tts_speaking_rate is not None
                        else None
                    ),
                )
                if audio_data:
                    audio_format = resolve_audio_format(tts_provider)
                    audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                    logger.info(
                        "Playing selected choice audio in backend",
                        extra={"audio_format": audio_format},
                    )
                    tts_service.play_audio_async(
                        audio_data,
                        audio_format,
                        stt_service=get_current_speech_to_text_service(),
                    )
                    logger.info(
                        "TTS generated for selected choice",
                        extra={"audio_bytes": len(audio_data)},
                    )
                else:
                    logger.warning("TTS generation returned no audio data")
            if request.session_id and request.step_number is not None and request.choice_text:
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
            audio_base64 = None
            try:
                if request.choice_text:
                    config = load_config()
                    tts_provider = resolve_tts_provider(config)
                    tts_service = get_tts_service(provider=tts_provider)
                    tts_config = load_config()
                    audio_data = tts_service.generate_speech(
                        text=request.choice_text,
                        language=tts_config.tts_language or "en",
                        voice_name=tts_config.tts_voice_name if tts_config.tts_voice_name else None,
                        pitch=tts_config.tts_pitch if tts_config.tts_pitch is not None else None,
                        speaking_rate=(
                            tts_config.tts_speaking_rate
                            if tts_config.tts_speaking_rate is not None
                            else None
                        ),
                    )
                    if audio_data:
                        audio_format = resolve_audio_format(tts_provider)
                        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                        tts_service.play_audio_async(
                            audio_data,
                            audio_format,
                            stt_service=get_current_speech_to_text_service(),
                        )
            except Exception:
                logger.exception("Error generating TTS in exception handler")
            return ChoiceSelectionResponse(
                success=True,
                message=f"Choice '{request.choice_id}' selected",
                updated_text=request.current_text,
                audio_base64=audio_base64,
                error=str(exc),
            )


