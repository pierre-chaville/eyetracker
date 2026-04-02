"""
Unified suggestions/choices service for communication grid and keyboard.

One LLM-backed flow: same context (user, caregiver, conversation, current text),
different prompts and response shape by mode ("communication" | "keyboard").
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Literal, Optional, TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import load_config
from app.models import CommunicationSession, SessionStep, User, Caregiver
from app.schemas import ChoicesRequest
from app.services.llm import get_llm_service
from app.utils.logging import get_logger

logger = get_logger(__name__)

SuggestionsMode = Literal["communication", "keyboard"]


class SuggestionItem(TypedDict, total=False):
    text: str
    probability: float
    arasaac_keywords: Optional[List[str]]


# Fallback when LLM fails (communication-style).
_FALLBACK_CHOICES: List[SuggestionItem] = [
    {"text": "Yes", "probability": 0.5},
    {"text": "No", "probability": 0.5},
    {"text": "More", "probability": 0.3},
    {"text": "Done", "probability": 0.2},
]


def _normalize_keyboard_current_text(current_text: str | None) -> str:
    """Normalize current_text for keyboard: '<A> <B>' -> 'AB' for multi-letter prompts."""
    if not current_text or not current_text.strip():
        return ""
    words = current_text.split()
    normalized = []
    for word in words:
        match = re.match(r"^<([A-Za-z])>$", word)
        normalized.append(match.group(1) if match else word)
    return " ".join(normalized)


class SuggestionsService:
    """Unified service for generating LLM suggestions (communication grid or keyboard)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def generate(
        self,
        request: ChoicesRequest,
        mode: SuggestionsMode,
        aac_mode: bool = False,
    ) -> List[SuggestionItem]:
        """
        Generate suggestions using the LLM.

        Args:
            request: Context (user_id, caregiver_id, conversation_history, current_text,
                and optionally session_id, step_number for communication).
            mode: "communication" uses communicate_prompt and can persist a step;
                "keyboard" uses keyboard_prompt or keyboard_multiple_letters_prompt.

        Returns:
            List of {text, probability}, ordered by probability descending.
        """
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

            conversation_history = request.conversation_history or []
            current_text = request.current_text or ""

            if mode == "keyboard":
                normalized = _normalize_keyboard_current_text(current_text)
                system_prompt = config.keyboard_prompt or (
                    "You are a helpful assistant that suggests words for text input."
                )
            else:
                system_prompt = config.communicate_prompt or (
                    "You are a helpful assistant for communication. "
                    "Suggest 2-8 short phrases the user might want to say."
                )

            if aac_mode:
                system_prompt += (
                    "\n\nIMPORTANT: For each choice, also provide 1-3 simple "
                    "ARASAAC pictogram search keywords in the `arasaac_keywords` field. "
                    "Use simple, concrete nouns or verbs that are likely to match "
                    "pictograms in the ARASAAC database (e.g., 'eat', 'happy', 'water', "
                    "'play'). Keep keywords in the same language as the choices."
                )

            llm_service = get_llm_service(
                provider=config.provider,
                model=config.model,
                temperature=config.temperature,
            )
            llm_choices = await llm_service.generate_choices(
                system_prompt=system_prompt,
                conversation_history=conversation_history,
                user_notes=user_notes,
                caregiver_description=caregiver_description,
                current_text=current_text,
            )
            items: List[SuggestionItem] = [
                {
                    "text": c["text"],
                    "probability": c["probability"],
                    "arasaac_keywords": c.get("arasaac_keywords"),
                }
                for c in llm_choices
            ]

            if request.session_id is not None and request.step_number is not None:
                await self._persist_session_step(request, items)

            return items
        except Exception:
            logger.exception("Error generating suggestions (mode=%s)", mode)
            return _FALLBACK_CHOICES.copy()

    async def _persist_session_step(
        self,
        request: ChoicesRequest,
        items: List[SuggestionItem],
    ) -> None:
        """Persist choices as a session step (communication or keyboard)."""
        try:
            message_role = None
            message_content = None
            if request.conversation_history:
                last = request.conversation_history[-1]
                message_role = (last.get("role") or "").lower()
                message_content = last.get("content") or ""
                if message_role == "assistant":
                    message_role = "user"
                elif message_role == "human":
                    message_role = "user"
                elif message_role not in ("user", "caregiver"):
                    message_role = None
            choices_data = [{"text": c["text"], "probability": c["probability"]} for c in items]
            step = SessionStep(
                session_id=request.session_id,
                step_number=request.step_number,
                message_role=message_role,
                message_content=message_content,
                choices_json=choices_data,
                selected_choice_text=None,
            )
            self._session.add(step)
            comm_session = await self._session.get(CommunicationSession, request.session_id)
            if comm_session:
                comm_session.updated_at = datetime.utcnow()
                self._session.add(comm_session)
            await self._session.commit()
        except Exception:
            logger.exception("Error saving session step")
