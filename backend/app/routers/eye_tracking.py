from __future__ import annotations

from fastapi import APIRouter

from app.schemas import EyeTrackingStatus, MessageResponse

router = APIRouter(tags=["eye-tracking"])


@router.post("/eye-tracking/start", response_model=MessageResponse)
async def start_eye_tracking() -> MessageResponse:
    """Start eye tracking session."""
    return MessageResponse(success=True, message="Eye tracking started")


@router.post("/eye-tracking/stop", response_model=MessageResponse)
async def stop_eye_tracking() -> MessageResponse:
    """Stop eye tracking session."""
    return MessageResponse(success=True, message="Eye tracking stopped")


@router.get("/eye-tracking/status", response_model=EyeTrackingStatus)
async def get_eye_tracking_status() -> EyeTrackingStatus:
    """Get current eye tracking status."""
    return EyeTrackingStatus(is_active=False, calibration_status="not_calibrated")
