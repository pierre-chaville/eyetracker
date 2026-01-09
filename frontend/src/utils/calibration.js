/**
 * Utility functions for applying calibration transformations
 */

/**
 * Apply affine transformation to raw gaze coordinates
 * X = a0 + a1*x + a2*y
 * Y = b0 + b1*x + b2*y
 * 
 * @param {Object} rawPoint - Raw gaze point {x, y}
 * @param {Object} coefficients - Affine coefficients {a0, a1, a2, b0, b1, b2}
 * @returns {Object} Calibrated point {x, y}
 */
export function applyAffineTransformation(rawPoint, coefficients) {
  if (!coefficients || !rawPoint) {
    return rawPoint; // Return original if no calibration available
  }
  
  const { a0, a1, a2, b0, b1, b2 } = coefficients;
  const { x, y } = rawPoint;
  
  const calibratedX = a0 + a1 * x + a2 * y;
  const calibratedY = b0 + b1 * x + b2 * y;
  
  return {
    x: calibratedX,
    y: calibratedY,
  };
}

/**
 * Parse calibration data from user object
 * @param {Object} user - User object with calibration field
 * @returns {Object|null} Parsed calibration data with affine coefficients
 */
export function parseCalibrationData(user) {
  if (!user || !user.calibration) {
    return null;
  }
  
  try {
    const calibrationData = typeof user.calibration === 'string' 
      ? JSON.parse(user.calibration)
      : user.calibration;
    
    return calibrationData.affine_coefficients || null;
  } catch (error) {
    console.error('Error parsing calibration data:', error);
    return null;
  }
}

