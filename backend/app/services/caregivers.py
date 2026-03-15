from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Caregiver
from app.schemas.caregiver import CaregiverCreate, CaregiverRead, CaregiverUpdate
from app.utils.exceptions import EntityNotFoundError


def caregiver_to_response(caregiver: Caregiver) -> CaregiverRead:
    """Convert Caregiver model to CaregiverResponse."""
    return CaregiverRead(
        id=caregiver.id,
        name=caregiver.name,
        gender=caregiver.gender,
        description=caregiver.description,
        created_at=caregiver.created_at,
        updated_at=caregiver.updated_at,
    )


class CaregiverService:
    """Service for caregiver operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_caregivers(self, skip: int, limit: int) -> List[CaregiverRead]:
        statement = select(Caregiver).offset(skip).limit(limit)
        result = await self._session.execute(statement)
        caregivers = list(result.scalars().all())
        return [caregiver_to_response(caregiver) for caregiver in caregivers]

    async def get_caregiver(self, caregiver_id: int) -> CaregiverRead:
        caregiver = await self._session.get(Caregiver, caregiver_id)
        if not caregiver:
            raise EntityNotFoundError("Caregiver", caregiver_id)
        return caregiver_to_response(caregiver)

    async def create_caregiver(self, caregiver_data: CaregiverCreate) -> CaregiverRead:
        caregiver = Caregiver(
            name=caregiver_data.name,
            gender=caregiver_data.gender,
            description=caregiver_data.description,
        )
        self._session.add(caregiver)
        await self._session.commit()
        await self._session.refresh(caregiver)
        return caregiver_to_response(caregiver)

    async def update_caregiver(
        self,
        caregiver_id: int,
        caregiver_data: CaregiverUpdate,
    ) -> CaregiverRead:
        caregiver = await self._session.get(Caregiver, caregiver_id)
        if not caregiver:
            raise EntityNotFoundError("Caregiver", caregiver_id)
        if caregiver_data.name is not None:
            caregiver.name = caregiver_data.name
        if caregiver_data.gender is not None:
            caregiver.gender = caregiver_data.gender
        if caregiver_data.description is not None:
            caregiver.description = caregiver_data.description
        caregiver.updated_at = datetime.utcnow()
        self._session.add(caregiver)
        await self._session.commit()
        await self._session.refresh(caregiver)
        return caregiver_to_response(caregiver)

    async def delete_caregiver(self, caregiver_id: int) -> None:
        caregiver = await self._session.get(Caregiver, caregiver_id)
        if not caregiver:
            raise EntityNotFoundError("Caregiver", caregiver_id)
        self._session.delete(caregiver)
        await self._session.commit()
