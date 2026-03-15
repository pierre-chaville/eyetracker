from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import ConfigService
from app.database import get_session
from app.services.caregivers import CaregiverService
from app.services.communication import CommunicationService, CommunicationSessionService
from app.services.keyboard import KeyboardService
from app.services.keyboard_layouts import KeyboardLayoutService
from app.services.suggestions import SuggestionsService
from app.services.users import UserService


def get_config_service() -> ConfigService:
    return ConfigService()


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)


def get_caregiver_service(session: AsyncSession = Depends(get_session)) -> CaregiverService:
    return CaregiverService(session)


def get_session_service(
    session: AsyncSession = Depends(get_session),
) -> CommunicationSessionService:
    return CommunicationSessionService(session)


def get_suggestions_service(
    session: AsyncSession = Depends(get_session),
) -> SuggestionsService:
    return SuggestionsService(session)


def get_communication_service(
    session: AsyncSession = Depends(get_session),
    suggestions_service: SuggestionsService = Depends(get_suggestions_service),
) -> CommunicationService:
    return CommunicationService(session, suggestions_service)


def get_keyboard_service(
    session: AsyncSession = Depends(get_session),
    suggestions_service: SuggestionsService = Depends(get_suggestions_service),
) -> KeyboardService:
    return KeyboardService(session, suggestions_service)


def get_keyboard_layout_service(
    session: AsyncSession = Depends(get_session),
) -> KeyboardLayoutService:
    return KeyboardLayoutService(session)
