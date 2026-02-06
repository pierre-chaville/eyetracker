from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import get_caregiver_service
from app.models import CaregiverCreate, CaregiverResponse, CaregiverUpdate
from app.services.caregivers import CaregiverService
from app.utils.exceptions import EntityNotFoundError

router = APIRouter(tags=["caregivers"])


@router.get("/api/caregivers", response_model=List[CaregiverResponse])
async def list_caregivers(
    skip: int = 0,
    limit: int = 100,
    service: CaregiverService = Depends(get_caregiver_service),
) -> List[CaregiverResponse]:
    """List all caregivers."""
    return service.list_caregivers(skip=skip, limit=limit)


@router.get("/api/caregivers/{caregiver_id}", response_model=CaregiverResponse)
async def get_caregiver(
    caregiver_id: int,
    service: CaregiverService = Depends(get_caregiver_service),
) -> CaregiverResponse:
    """Get a specific caregiver by ID."""
    try:
        return service.get_caregiver(caregiver_id)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc


@router.post(
    "/api/caregivers",
    response_model=CaregiverResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_caregiver(
    caregiver_data: CaregiverCreate,
    service: CaregiverService = Depends(get_caregiver_service),
) -> CaregiverResponse:
    """Create a new caregiver."""
    return service.create_caregiver(caregiver_data)


@router.put("/api/caregivers/{caregiver_id}", response_model=CaregiverResponse)
async def update_caregiver(
    caregiver_id: int,
    caregiver_data: CaregiverUpdate,
    service: CaregiverService = Depends(get_caregiver_service),
) -> CaregiverResponse:
    """Update an existing caregiver."""
    try:
        return service.update_caregiver(caregiver_id, caregiver_data)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc


@router.delete(
    "/api/caregivers/{caregiver_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_caregiver(
    caregiver_id: int,
    service: CaregiverService = Depends(get_caregiver_service),
) -> Response:
    """Delete a caregiver."""
    try:
        service.delete_caregiver(caregiver_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc
