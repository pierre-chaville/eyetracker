"""
Calibration module for processing eye tracking calibration data.

This module handles:
- Processing raw calibration samples
- Calculating geometric median (L1 center) for robust averaging
- Computing affine transformation coefficients using weighted least squares
"""

from pydantic import BaseModel
from typing import Optional, List, Tuple
from sqlmodel import Session
from fastapi import HTTPException, status
import numpy as np
import json
from datetime import datetime

from models import User


# Calibration Models
class CalibrationPointData(BaseModel):
    """Data for a single calibration point"""
    position: dict  # {x, y, label}
    targetX: float
    targetY: float
    samples: List[dict]  # List of {x, y, screenX, screenY, timestamp}


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
    offsetX: float  # Difference between target and gaze
    offsetY: float


class AffineCoefficients(BaseModel):
    """Affine transformation coefficients"""
    a0: float  # X = a0 + a1*x + a2*y
    a1: float
    a2: float
    b0: float  # Y = b0 + b1*x + b2*y
    b1: float
    b2: float


class CalibrationResponse(BaseModel):
    """Response with processed calibration data"""
    user_id: int
    timestamp: int
    points: List[CalibrationPointResult]
    affine_coefficients: Optional[AffineCoefficients] = None
    calibration_data: str  # JSON string for storage


def calculate_geometric_median(samples: List[dict]) -> Tuple[float, float]:
    """
    Calculate geometric median (L1 center) for robustness to outliers.
    
    Args:
        samples: List of sample dictionaries with 'x' and 'y' keys
        
    Returns:
        Tuple of (average_x, average_y) coordinates
    """
    valid_samples = [s for s in samples if s.get('x') is not None and s.get('y') is not None]
    
    if len(valid_samples) == 0:
        return 0.0, 0.0
    
    try:
        # Try to use scipy's geometric median if available
        from scipy.optimize import minimize
        
        points = np.array([[s['x'], s['y']] for s in valid_samples])
        
        # Initial guess: coordinate-wise median
        initial_guess = np.array([
            np.median([s['x'] for s in valid_samples]),
            np.median([s['y'] for s in valid_samples])
        ])
        
        # Objective function: sum of distances (L1 norm)
        def objective(center):
            return np.sum(np.linalg.norm(points - center, axis=1))
        
        # Minimize sum of distances
        result = minimize(objective, initial_guess, method='BFGS')
        
        if result.success:
            return float(result.x[0]), float(result.x[1])
        else:
            # Fallback to coordinate-wise median
            return (
                float(np.median([s['x'] for s in valid_samples])),
                float(np.median([s['y'] for s in valid_samples]))
            )
    except ImportError:
        # Fallback to coordinate-wise median if scipy not available
        return (
            float(np.median([s['x'] for s in valid_samples])),
            float(np.median([s['y'] for s in valid_samples]))
        )
    except Exception as e:
        # Fallback to coordinate-wise median on any error
        print(f"Error calculating geometric median, using coordinate-wise median: {e}")
        return (
            float(np.median([s['x'] for s in valid_samples])),
            float(np.median([s['y'] for s in valid_samples]))
        )


def calculate_affine_coefficients(processed_points: List[CalibrationPointResult]) -> Optional[AffineCoefficients]:
    """
    Calculate affine transformation coefficients using weighted least squares.
    
    Transformation equations:
    X = a0 + a1*x + a2*y
    Y = b0 + b1*x + b2*y
    
    Args:
        processed_points: List of processed calibration points
        
    Returns:
        AffineCoefficients if calculation succeeds, None otherwise
    """
    if len(processed_points) < 3:  # Need at least 3 points for affine transformation
        return None
    
    try:
        # Prepare data for weighted least squares
        n_points = len(processed_points)
        A_x = np.zeros((n_points, 3))  # Design matrix for X: [1, x, y]
        b_x = np.zeros(n_points)  # Target X values
        A_y = np.zeros((n_points, 3))  # Design matrix for Y: [1, x, y]
        b_y = np.zeros(n_points)  # Target Y values
        weights = np.zeros(n_points)  # Weights based on sample count
        
        for i, point in enumerate(processed_points):
            # Use average gaze coordinates as input (x, y)
            gaze_x = point.averageGazeX
            gaze_y = point.averageGazeY
            
            # Design matrix: [1, x, y]
            A_x[i] = [1.0, gaze_x, gaze_y]
            A_y[i] = [1.0, gaze_x, gaze_y]
            
            # Target values (where the circle was displayed)
            b_x[i] = point.targetX
            b_y[i] = point.targetY
            
            # Weight based on sample count (more samples = more reliable)
            weights[i] = point.sampleCount
        
        # Normalize weights to sum to n_points (for numerical stability)
        if weights.sum() > 0:
            weights = weights / weights.sum() * n_points
        
        # Create weighted design matrices: W * A and W * b
        W = np.diag(np.sqrt(weights))
        A_x_weighted = W @ A_x
        b_x_weighted = W @ b_x
        A_y_weighted = W @ A_y
        b_y_weighted = W @ b_y
        
        # Solve weighted least squares: (A^T W A) coeffs = A^T W b
        # Using numpy's lstsq for numerical stability
        coeffs_x, residuals_x, rank_x, s_x = np.linalg.lstsq(A_x_weighted, b_x_weighted, rcond=None)
        coeffs_y, residuals_y, rank_y, s_y = np.linalg.lstsq(A_y_weighted, b_y_weighted, rcond=None)
        
        # Extract coefficients
        a0, a1, a2 = float(coeffs_x[0]), float(coeffs_x[1]), float(coeffs_x[2])
        b0, b1, b2 = float(coeffs_y[0]), float(coeffs_y[1]), float(coeffs_y[2])
        
        affine_coefficients = AffineCoefficients(
            a0=a0,
            a1=a1,
            a2=a2,
            b0=b0,
            b1=b1,
            b2=b2,
        )
        
        print(f"Affine coefficients calculated:")
        print(f"  X = {a0:.2f} + {a1:.4f}*x + {a2:.4f}*y")
        print(f"  Y = {b0:.2f} + {b1:.4f}*x + {b2:.4f}*y")
        
        return affine_coefficients
        
    except Exception as e:
        print(f"Error calculating affine coefficients: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_calibration_data(request: CalibrationRequest, session: Session) -> CalibrationResponse:
    """
    Process calibration data and calculate averages and affine coefficients.
    
    Args:
        request: CalibrationRequest with raw calibration samples
        session: Database session
        
    Returns:
        CalibrationResponse with processed data
        
    Raises:
        HTTPException: If user not found
    """
    # Verify user exists
    user = session.get(User, request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {request.user_id} not found"
        )
    
    # Process each calibration point
    processed_points = []
    for point_data in request.points:
        if not point_data.samples or len(point_data.samples) == 0:
            continue
        
        # Calculate averages using geometric median
        valid_samples = [s for s in point_data.samples if s.get('x') is not None and s.get('y') is not None]
        
        if len(valid_samples) == 0:
            continue
        
        # Calculate geometric median (robust to outliers)
        avg_gaze_x, avg_gaze_y = calculate_geometric_median(valid_samples)
        
        # Calculate screen averages if available
        screen_samples = [s for s in valid_samples if s.get('screenX') is not None and s.get('screenY') is not None]
        avg_screen_x = sum(s['screenX'] for s in screen_samples) / len(screen_samples) if screen_samples else None
        avg_screen_y = sum(s['screenY'] for s in screen_samples) / len(screen_samples) if screen_samples else None
        
        # Calculate offset (difference between target and actual gaze)
        offset_x = point_data.targetX - avg_gaze_x
        offset_y = point_data.targetY - avg_gaze_y
        
        processed_points.append(CalibrationPointResult(
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
        ))
    
    # Calculate affine transformation coefficients using weighted least squares
    affine_coefficients = calculate_affine_coefficients(processed_points)
    
    # Create calibration data JSON
    timestamp = request.timestamp or int(datetime.utcnow().timestamp() * 1000)
    
    calibration_dict = {
        "timestamp": timestamp,
        "points": [p.model_dump() for p in processed_points],
        "version": "1.0",
    }
    
    # Add affine coefficients if available
    if affine_coefficients:
        calibration_dict["affine_coefficients"] = affine_coefficients.model_dump()
    
    calibration_json = json.dumps(calibration_dict, indent=2)
    
    # Update user's calibration field
    user.calibration = calibration_json
    user.updated_at = datetime.utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return CalibrationResponse(
        user_id=request.user_id,
        timestamp=timestamp,
        points=processed_points,
        affine_coefficients=affine_coefficients,
        calibration_data=calibration_json,
    )

