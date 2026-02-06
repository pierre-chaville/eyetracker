from __future__ import annotations

from datetime import datetime
from typing import List

from sqlmodel import Session, select

from app.models import Caregiver, CaregiverCreate, CaregiverResponse, CaregiverUpdate
from app.utils.exceptions import EntityNotFoundError


def caregiver_to_response(caregiver: Caregiver) -> CaregiverResponse:
    """Convert Caregiver model to CaregiverResponse."""
    return CaregiverResponse(
        id=caregiver.id,
        name=caregiver.name,
        gender=caregiver.gender,
        description=caregiver.description,
        created_at=caregiver.created_at,
        updated_at=caregiver.updated_at,
    )


class CaregiverService:
    """Service for caregiver operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_caregivers(self, skip: int, limit: int) -> List[CaregiverResponse]:
        statement = select(Caregiver).offset(skip).limit(limit)
        caregivers = self._session.exec(statement).all()
        return [caregiver_to_response(caregiver) for caregiver in caregivers]

    def get_caregiver(self, caregiver_id: int) -> CaregiverResponse:
        caregiver = self._session.get(Caregiver, caregiver_id)
        if not caregiver:
            raise EntityNotFoundError("Caregiver", caregiver_id)
        return caregiver_to_response(caregiver)

    def create_caregiver(self, caregiver_data: CaregiverCreate) -> CaregiverResponse:
        caregiver = Caregiver(
            name=caregiver_data.name,
            gender=caregiver_data.gender,
            description=caregiver_data.description,
        )
        self._session.add(caregiver)
        self._session.commit()
        self._session.refresh(caregiver)
        return caregiver_to_response(caregiver)

    def update_caregiver(
        self,
        caregiver_id: int,
        caregiver_data: CaregiverUpdate,
    ) -> CaregiverResponse:
        caregiver = self._session.get(Caregiver, caregiver_id)
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
        self._session.commit()
        self._session.refresh(caregiver)
        return caregiver_to_response(caregiver)

    def delete_caregiver(self, caregiver_id: int) -> None:
        caregiver = self._session.get(Caregiver, caregiver_id)
        if not caregiver:
            raise EntityNotFoundError("Caregiver", caregiver_id)
        self._session.delete(caregiver)
        self._session.commit()
