from __future__ import annotations

from fastapi import APIRouter

from app.schemas import HealthResponse, RootResponse

router = APIRouter(tags=["general"])


@router.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    return RootResponse(message="Eye Tracker API", status="running")


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")
