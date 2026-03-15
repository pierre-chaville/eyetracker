from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import get_user_service
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.users import UserService
from app.utils.exceptions import EntityNotFoundError

router = APIRouter(tags=["users"])


@router.get("/api/users", response_model=List[UserRead])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    service: UserService = Depends(get_user_service),
) -> List[UserRead]:
    """List all users with optional filtering (UserRead)."""
    return await service.list_users(skip=skip, limit=limit, active_only=active_only)


@router.get("/api/users/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Get a specific user by ID (UserRead)."""
    try:
        return await service.get_user(user_id)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc


@router.post(
    "/api/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Create a new user (UserRead)."""
    return await service.create_user(user_data)


@router.put("/api/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Update an existing user (UserRead)."""
    try:
        return await service.update_user(user_id, user_data)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc


@router.delete(
    "/api/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> Response:
    """Delete a user."""
    try:
        await service.delete_user(user_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.entity} with id {exc.entity_id} not found",
        ) from exc
