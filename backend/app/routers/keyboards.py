from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_keyboard_layout_service
from app.schemas.keyboard_layout import (
    KeyboardLayoutCreate,
    KeyboardLayoutRead,
    KeyboardLayoutUpdate,
)
from app.services.keyboard_layouts import KeyboardLayoutService

router = APIRouter(tags=["keyboards"])


@router.get("/api/keyboards", response_model=List[KeyboardLayoutRead])
async def list_keyboards(
    skip: int = 0,
    limit: int = 100,
    service: KeyboardLayoutService = Depends(get_keyboard_layout_service),
) -> List[KeyboardLayoutRead]:
    """List keyboard layouts (KeyboardLayoutRead)."""
    return await service.list_layouts(skip=skip, limit=limit)


@router.get("/api/keyboards/{keyboard_id}", response_model=KeyboardLayoutRead)
async def get_keyboard(
    keyboard_id: int,
    service: KeyboardLayoutService = Depends(get_keyboard_layout_service),
) -> KeyboardLayoutRead:
    """Get a keyboard layout (KeyboardLayoutRead)."""
    return await service.get_layout(keyboard_id)


@router.post("/api/keyboards", response_model=KeyboardLayoutRead)
async def create_keyboard(
    payload: KeyboardLayoutCreate,
    service: KeyboardLayoutService = Depends(get_keyboard_layout_service),
) -> KeyboardLayoutRead:
    """Create a keyboard layout (KeyboardLayoutRead)."""
    return await service.create_layout(payload)


@router.put("/api/keyboards/{keyboard_id}", response_model=KeyboardLayoutRead)
async def update_keyboard(
    keyboard_id: int,
    payload: KeyboardLayoutUpdate,
    service: KeyboardLayoutService = Depends(get_keyboard_layout_service),
) -> KeyboardLayoutRead:
    """Update a keyboard layout (KeyboardLayoutRead)."""
    return await service.update_layout(keyboard_id, payload)


@router.delete(
    "/api/keyboards/{keyboard_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_keyboard(
    keyboard_id: int,
    service: KeyboardLayoutService = Depends(get_keyboard_layout_service),
) -> Response:
    """Delete a keyboard layout."""
    await service.delete_layout(keyboard_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
