from __future__ import annotations

import asyncio
import json
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
from app.config import load_config
from app.services import arasaac
from app.services.speak import speak_text
from app.services.suggestions import SuggestionsService
from app.utils.exceptions import EntityNotFoundError
from app.utils.logging import get_logger

logger = get_logger()

_DEFAULT_SESSION_ANALYSIS_PROMPT = (
    "You are an expert in augmentative and alternative communication (AAC) "
    "and assistive technology. Analyze the session data in the user message "
    "(JSON). Write your response in Markdown with clear sections such as "
    "summary, strengths, challenges, and recommendations. Be specific and "
    "professional."
)


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
        activation_mode=step.activation_mode,
        dwell_time_ms=step.dwell_time_ms,
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
        prompt=session.prompt,
        llm_model=session.llm_model,
        temperature=session.temperature,
        user_notes=session.user_notes,
        keyboard_layout_name=session.keyboard_layout_name,
        feedback=session.feedback_json,
        ai_analysis_markdown=getattr(session, "ai_analysis_markdown", None),
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
            prompt=session_data.prompt,
            llm_model=session_data.llm_model,
            temperature=session_data.temperature,
            user_notes=session_data.user_notes,
            keyboard_layout_name=session_data.keyboard_layout_name,
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
        if session_data.feedback is not None:
            session.feedback_json = session_data.feedback.model_dump(exclude_none=True)
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
        activation_mode: Optional[str] = None,
        dwell_time_ms: Optional[int] = None,
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
        step.activation_mode = activation_mode
        step.dwell_time_ms = dwell_time_ms
        step.timestamp = datetime.utcnow()
        self._session.add(step)
        session.updated_at = datetime.utcnow()
        self._session.add(session)
        await self._session.commit()

    async def run_ai_analysis(self, session_id: int) -> CommunicationSessionRead:
        """Build session payload, call LLM with setup prompt_session_analysis, store Markdown."""
        from app.services.llm import get_llm_service

        session = await self._session.get(CommunicationSession, session_id)
        if not session:
            raise EntityNotFoundError("Session", session_id)

        steps_statement = (
            select(SessionStep)
            .where(SessionStep.session_id == session_id)
            .order_by(SessionStep.step_number)
        )
        result = await self._session.execute(steps_statement)
        steps = list(result.scalars().all())

        config = load_config()
        system_prompt = (config.prompt_session_analysis or "").strip()
        if not system_prompt:
            system_prompt = _DEFAULT_SESSION_ANALYSIS_PROMPT

        if config.provider not in ("openai", "anthropic"):
            raise ValueError(
                "Session analysis requires AI provider 'openai' or 'anthropic' in Setup."
            )

        session_payload = {
            "session_context": {
                "id": session.id,
                "session_type": getattr(session, "session_type", "communication"),
                "llm_model": session.llm_model,
                "temperature": session.temperature,
                "prompt": session.prompt,
                "user_notes": session.user_notes,
                "keyboard_layout_name": session.keyboard_layout_name,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            },
            "caregiver_feedback": getattr(session, "feedback_json", None),
            "steps": [
                {
                    "step_number": s.step_number,
                    "message_role": s.message_role,
                    "message_content": s.message_content,
                    "choices": s.choices_json,
                    "selected_choice_text": s.selected_choice_text,
                    "activation_mode": s.activation_mode,
                    "dwell_time_ms": s.dwell_time_ms,
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                }
                for s in steps
            ],
        }
        user_message = (
            "Analyze the following session. Reply in Markdown only.\n\n"
            + json.dumps(session_payload, ensure_ascii=False, indent=2, default=str)
        )

        llm_service = get_llm_service(
            provider=config.provider,
            model=config.model,
            temperature=config.temperature,
        )
        markdown = await llm_service.generate_plain_text(system_prompt, user_message)
        if not markdown:
            raise RuntimeError("The language model returned an empty analysis.")

        session.ai_analysis_markdown = markdown
        session.updated_at = datetime.utcnow()
        self._session.add(session)
        await self._session.commit()
        await self._session.refresh(session)
        return await session_to_response(session, self._session)


class CommunicationService:
    """Service for communication-related features (choices and selection)."""

    def __init__(
        self,
        session: AsyncSession,
        suggestions_service: SuggestionsService,
    ) -> None:
        self._session = session
        self._suggestions_service = suggestions_service

    @property
    def _aac_locale(self) -> str:
        """ARASAAC locale derived from the TTS language config (e.g. 'fr', 'en')."""
        try:
            cfg = load_config()
            return (cfg.tts_language or "en")[:2].lower()
        except Exception:
            return "en"

    async def generate_choices(self, request: ChoicesRequest) -> ChoicesResponse:
        aac_mode = bool(request.aac_mode)
        items = await self._suggestions_service.generate(
            request, "communication", aac_mode=aac_mode,
        )

        if aac_mode:
            locale = self._aac_locale
            pictogram_tasks = [
                arasaac.resolve_pictogram_url(
                    item.get("arasaac_keywords") or [], locale=locale,
                )
                if item.get("arasaac_keywords")
                else asyncio.sleep(0, result=None)
                for item in items
            ]
            pictogram_urls = await asyncio.gather(*pictogram_tasks)
        else:
            pictogram_urls = [None] * len(items)

        choices: list[Choice] = [
            Choice(
                id=str(i + 1),
                text=item["text"],
                icon=None,
                probability=item["probability"],
                pictogram_url=purl,
            )
            for i, (item, purl) in enumerate(zip(items, pictogram_urls))
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
                        step.activation_mode = request.activation_mode
                        step.dwell_time_ms = request.dwell_time_ms
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


