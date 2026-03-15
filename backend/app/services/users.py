"""
User service: CRUD and serialization for users.

Converts between DB models and API schemas (UserRead, UserCreate, UserUpdate).
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas.user import (
    CommunicationSettings,
    EyeTrackingSetup,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.utils.exceptions import EntityNotFoundError


def serialize_eye_tracking_setup(
    setup: Optional[EyeTrackingSetup],
) -> Optional[dict]:
    """
    Serialize EyeTrackingSetup to a dict for JSON storage.

    Args:
        setup: Pydantic model or None.

    Returns:
        Dict suitable for JSON, or None.
    """
    if setup is None:
        return None
    return setup.model_dump()


def serialize_communication(
    comm: Optional[CommunicationSettings],
) -> Optional[dict]:
    """
    Serialize CommunicationSettings to a dict for JSON storage.

    Args:
        comm: Pydantic model or None.

    Returns:
        Dict suitable for JSON, or None.
    """
    if comm is None:
        return None
    return comm.model_dump()


def deserialize_eye_tracking_setup(
    data: Optional[dict],
) -> Optional[EyeTrackingSetup]:
    """
    Deserialize a dict from JSON to EyeTrackingSetup.

    Args:
        data: Dict (e.g. from DB) or None.

    Returns:
        EyeTrackingSetup instance or None if invalid/missing.
    """
    if data is None:
        return None
    try:
        return EyeTrackingSetup(**data)
    except (TypeError, ValueError):
        return None


def deserialize_communication(
    data: Optional[dict],
) -> Optional[CommunicationSettings]:
    """
    Deserialize a dict from JSON to CommunicationSettings.

    Args:
        data: Dict (e.g. from DB) or None.

    Returns:
        CommunicationSettings instance or None if invalid/missing.
    """
    if data is None:
        return None
    try:
        return CommunicationSettings(**data)
    except (TypeError, ValueError):
        return None


def user_to_response(user: User) -> UserRead:
    """
    Convert a User model to the API response schema.

    Args:
        user: DB User instance.

    Returns:
        UserRead with serialized eye_tracking_setup and communication.
    """
    return UserRead(
        id=user.id,
        name=user.name,
        eye_tracking_setup=deserialize_eye_tracking_setup(user.eye_tracking_setup),
        calibration=user.calibration,
        communication=deserialize_communication(user.communication),
        created_at=user.created_at,
        updated_at=user.updated_at,
        is_active=user.is_active,
        notes=user.notes,
        gender=user.gender,
        age=user.age,
        voice=user.voice,
    )


class UserService:
    """
    Service for user CRUD using an async DB session.

    All methods are async and raise EntityNotFoundError when a requested
    user does not exist.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Args:
            session: AsyncSession for DB access.
        """
        self._session = session

    async def list_users(
        self, skip: int, limit: int, active_only: bool
    ) -> List[UserRead]:
        """List users with optional pagination and active filter."""
        statement = select(User)
        if active_only:
            statement = statement.where(User.is_active == True)
        statement = statement.offset(skip).limit(limit)
        result = await self._session.execute(statement)
        users = list(result.scalars().all())
        return [user_to_response(user) for user in users]

    async def get_user(self, user_id: int) -> UserRead:
        user = await self._session.get(User, user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)
        return user_to_response(user)

    async def create_user(self, user_data: UserCreate) -> UserRead:
        eye_tracking_json = serialize_eye_tracking_setup(user_data.eye_tracking_setup)
        communication_json = serialize_communication(user_data.communication)
        user = User(
            name=user_data.name,
            eye_tracking_setup=eye_tracking_json,
            calibration=user_data.calibration,
            communication=communication_json,
            notes=user_data.notes,
            gender=user_data.gender,
            age=user_data.age,
            voice=user_data.voice,
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user_to_response(user)

    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserRead:
        user = await self._session.get(User, user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)
        if user_data.name is not None:
            user.name = user_data.name
        if user_data.eye_tracking_setup is not None:
            user.eye_tracking_setup = serialize_eye_tracking_setup(user_data.eye_tracking_setup)
        if user_data.calibration is not None:
            user.calibration = user_data.calibration
        if user_data.communication is not None:
            user.communication = serialize_communication(user_data.communication)
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        if user_data.notes is not None:
            user.notes = user_data.notes
        if user_data.gender is not None:
            user.gender = user_data.gender
        if user_data.age is not None:
            user.age = user_data.age
        if user_data.voice is not None:
            user.voice = user_data.voice
        user.updated_at = datetime.utcnow()
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user_to_response(user)

    async def delete_user(self, user_id: int) -> None:
        user = await self._session.get(User, user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)
        self._session.delete(user)
        await self._session.commit()
