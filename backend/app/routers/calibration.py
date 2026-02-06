from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.schemas import MessageResponse

from app.services.calibration import (
    CalibrationRequest,
    CalibrationResponse,
    process_calibration_data,
)

router = APIRouter(tags=["calibration"])


@router.post("/api/calibration/start", response_model=MessageResponse)
async def start_calibration() -> MessageResponse:
    """Start calibration process."""
    return MessageResponse(success=True, message="Calibration started")


@router.post("/api/calibration/process", response_model=CalibrationResponse)
async def process_calibration(
    request: CalibrationRequest,
    session: Session = Depends(get_session),
) -> CalibrationResponse:
    """Process calibration data and calculate averages for each position."""
    return process_calibration_data(request, session)
