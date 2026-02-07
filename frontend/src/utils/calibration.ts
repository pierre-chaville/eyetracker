import type { CalibrationCoefficients, GazePoint } from '../types/tracking'

export function applyAffineTransformation(
  rawPoint: GazePoint,
  coefficients: CalibrationCoefficients | null,
): GazePoint {
  if (!coefficients || !rawPoint) {
    return rawPoint
  }

  const { a0, a1, a2, b0, b1, b2 } = coefficients
  const { x, y } = rawPoint

  return {
    x: a0 + a1 * x + a2 * y,
    y: b0 + b1 * x + b2 * y,
  }
}

export function parseCalibrationData(
  user: { calibration?: string | { affine_coefficients?: CalibrationCoefficients } } | null,
): CalibrationCoefficients | null {
  if (!user || !user.calibration) {
    return null
  }

  try {
    const calibrationData =
      typeof user.calibration === 'string'
        ? (JSON.parse(user.calibration) as { affine_coefficients?: CalibrationCoefficients })
        : user.calibration

    return calibrationData.affine_coefficients || null
  } catch (error) {
    console.error('Error parsing calibration data:', error)
    return null
  }
}
