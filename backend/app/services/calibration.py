"""
Calibration module for processing eye tracking calibration data.

This module handles:
- Processing raw calibration samples
- Calculating geometric median (L1 center) for robust averaging
- Computing affine transformation coefficients using weighted least squares
"""
from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Optional, List, Tuple

import numpy as np
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CalibrationPointData(BaseModel):
    """Data for a single calibration point"""

    position: dict
    targetX: float
    targetY: float
    samples: List[dict]


class CalibrationRequest(BaseModel):
    """Request to process calibration data"""

    user_id: int
    points: List[CalibrationPointData]
    timestamp: Optional[int] = None


class CalibrationPointResult(BaseModel):
    """Result for a processed calibration point"""

    position: dict
    targetX: float
    targetY: float
    averageGazeX: float
    averageGazeY: float
    averageScreenX: float
    averageScreenY: float
    sampleCount: int
    offsetX: float
    offsetY: float
    gaze_spread_diameter: float


class AffineCoefficients(BaseModel):
    """Affine transformation coefficients"""

    a0: float
    a1: float
    a2: float
    b0: float
    b1: float
    b2: float


class CalibrationResponse(BaseModel):
    """Response with processed calibration data"""

    user_id: int
    timestamp: int
    points: List[CalibrationPointResult]
    affine_coefficients: Optional[AffineCoefficients] = None
    calibration_data: str


def calculate_geometric_median(samples: List[dict]) -> Tuple[float, float]:
    """Calculate geometric median (L1 center) for robustness to outliers."""
    valid_samples = [s for s in samples if s.get("x") is not None and s.get("y") is not None]

    if len(valid_samples) == 0:
        return 0.0, 0.0

    try:
        from scipy.optimize import minimize

        points = np.array([[s["x"], s["y"]] for s in valid_samples])

        initial_guess = np.array(
            [
                np.median([s["x"] for s in valid_samples]),
                np.median([s["y"] for s in valid_samples]),
            ]
        )

        def objective(center):
            return np.sum(np.linalg.norm(points - center, axis=1))

        result = minimize(objective, initial_guess, method="BFGS")

        if result.success:
            return float(result.x[0]), float(result.x[1])

        return (
            float(np.median([s["x"] for s in valid_samples])),
            float(np.median([s["y"] for s in valid_samples])),
        )
    except ImportError:
        return (
            float(np.median([s["x"] for s in valid_samples])),
            float(np.median([s["y"] for s in valid_samples])),
        )
    except Exception as e:
        logger.warning(
            "Error calculating geometric median, using coordinate-wise median: %s",
            e,
            exc_info=True,
        )
        return (
            float(np.median([s["x"] for s in valid_samples])),
            float(np.median([s["y"] for s in valid_samples])),
        )


def calculate_affine_coefficients(
    processed_points: List[CalibrationPointResult],
) -> Optional[AffineCoefficients]:
    """Calculate affine transformation coefficients using weighted least squares."""
    if len(processed_points) < 3:
        return None

    try:
        n_points = len(processed_points)
        A_x = np.zeros((n_points, 3))
        b_x = np.zeros(n_points)
        A_y = np.zeros((n_points, 3))
        b_y = np.zeros(n_points)
        weights = np.zeros(n_points)

        for i, point in enumerate(processed_points):
            gaze_x = point.averageGazeX
            gaze_y = point.averageGazeY

            A_x[i] = [1.0, gaze_x, gaze_y]
            A_y[i] = [1.0, gaze_x, gaze_y]

            b_x[i] = point.targetX
            b_y[i] = point.targetY

            weights[i] = point.sampleCount

        if weights.sum() > 0:
            weights = weights / weights.sum() * n_points

        W = np.diag(np.sqrt(weights))
        A_x_weighted = W @ A_x
        b_x_weighted = W @ b_x
        A_y_weighted = W @ A_y
        b_y_weighted = W @ b_y

        coeffs_x, _, _, _ = np.linalg.lstsq(A_x_weighted, b_x_weighted, rcond=None)
        coeffs_y, _, _, _ = np.linalg.lstsq(A_y_weighted, b_y_weighted, rcond=None)

        a0, a1, a2 = float(coeffs_x[0]), float(coeffs_x[1]), float(coeffs_x[2])
        b0, b1, b2 = float(coeffs_y[0]), float(coeffs_y[1]), float(coeffs_y[2])

        affine_coefficients = AffineCoefficients(a0=a0, a1=a1, a2=a2, b0=b0, b1=b1, b2=b2)

        logger.debug(
            "Affine coefficients: X = %.2f + %.4f*x + %.4f*y, Y = %.2f + %.4f*x + %.4f*y",
            a0, a1, a2, b0, b1, b2,
        )
        return affine_coefficients

    except Exception as e:
        logger.exception("Error calculating affine coefficients: %s", e)
        return None


async def process_calibration_data(
    request: CalibrationRequest, session: AsyncSession
) -> CalibrationResponse:
    """Process calibration data and calculate averages and affine coefficients."""
    user = await session.get(User, request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {request.user_id} not found",
        )

    processed_points = []
    for point_data in request.points:
        if not point_data.samples or len(point_data.samples) == 0:
            continue

        valid_samples = [s for s in point_data.samples if s.get("x") is not None and s.get("y") is not None]

        if len(valid_samples) == 0:
            continue

        avg_gaze_x, avg_gaze_y = calculate_geometric_median(valid_samples)

        distances = [
            math.hypot(float(s["x"]) - avg_gaze_x, float(s["y"]) - avg_gaze_y)
            for s in valid_samples
        ]
        median_dist = float(np.median(distances)) if distances else 0.0
        # Diameter = 2 × median distance to geometric median (robust precision indicator)
        gaze_spread_diameter = float(2.0 * median_dist)

        screen_samples = [
            s for s in valid_samples if s.get("screenX") is not None and s.get("screenY") is not None
        ]
        avg_screen_x = sum(s["screenX"] for s in screen_samples) / len(screen_samples) if screen_samples else None
        avg_screen_y = sum(s["screenY"] for s in screen_samples) / len(screen_samples) if screen_samples else None

        offset_x = point_data.targetX - avg_gaze_x
        offset_y = point_data.targetY - avg_gaze_y

        processed_points.append(
            CalibrationPointResult(
                position=point_data.position,
                targetX=point_data.targetX,
                targetY=point_data.targetY,
                averageGazeX=avg_gaze_x,
                averageGazeY=avg_gaze_y,
                averageScreenX=avg_screen_x if avg_screen_x is not None else 0.0,
                averageScreenY=avg_screen_y if avg_screen_y is not None else 0.0,
                sampleCount=len(valid_samples),
                offsetX=offset_x,
                offsetY=offset_y,
                gaze_spread_diameter=gaze_spread_diameter,
            )
        )

    affine_coefficients = calculate_affine_coefficients(processed_points)

    timestamp = request.timestamp or int(datetime.utcnow().timestamp() * 1000)
    calibration_dict = {
        "timestamp": timestamp,
        "points": [p.model_dump() for p in processed_points],
        "version": "1.0",
    }

    if affine_coefficients:
        calibration_dict["affine_coefficients"] = affine_coefficients.model_dump()

    calibration_json = json.dumps(calibration_dict, indent=2)

    user.calibration = calibration_json
    user.updated_at = datetime.utcnow()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return CalibrationResponse(
        user_id=request.user_id,
        timestamp=timestamp,
        points=processed_points,
        affine_coefficients=affine_coefficients,
        calibration_data=calibration_json,
    )


__all__ = ["CalibrationRequest", "CalibrationResponse", "process_calibration_data"]
