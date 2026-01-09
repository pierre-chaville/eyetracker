/**
 * Statistical utility functions for robust calculations
 */

/**
 * Calculate the median of an array of numbers
 * @param {number[]} values - Array of numbers
 * @returns {number} Median value
 */
export function median(values) {
  if (!values || values.length === 0) {
    return 0;
  }
  
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  
  if (sorted.length % 2 === 0) {
    return (sorted[mid - 1] + sorted[mid]) / 2;
  } else {
    return sorted[mid];
  }
}

/**
 * Calculate coordinate-wise median (median X and median Y separately)
 * This is a robust alternative to mean that is less sensitive to outliers
 * @param {Array<{x: number, y: number}>} points - Array of points with x and y
 * @returns {{x: number, y: number}} Median point
 */
export function coordinateWiseMedian(points) {
  if (!points || points.length === 0) {
    return { x: 0, y: 0 };
  }
  
  const xValues = points.map(p => p.x).filter(x => x !== null && x !== undefined);
  const yValues = points.map(p => p.y).filter(y => y !== null && y !== undefined);
  
  return {
    x: median(xValues),
    y: median(yValues),
  };
}

/**
 * Calculate geometric median using Weiszfeld's algorithm (iterative approximation)
 * This minimizes the sum of distances (L1 center), making it robust to outliers
 * @param {Array<{x: number, y: number}>} points - Array of points with x and y
 * @param {number} tolerance - Convergence tolerance (default: 0.001)
 * @param {number} maxIterations - Maximum iterations (default: 100)
 * @returns {{x: number, y: number}} Geometric median point
 */
export function geometricMedian(points, tolerance = 0.001, maxIterations = 100) {
  if (!points || points.length === 0) {
    return { x: 0, y: 0 };
  }
  
  // Filter out invalid points
  const validPoints = points.filter(p => 
    p.x !== null && p.x !== undefined && 
    p.y !== null && p.y !== undefined &&
    !isNaN(p.x) && !isNaN(p.y)
  );
  
  if (validPoints.length === 0) {
    return { x: 0, y: 0 };
  }
  
  if (validPoints.length === 1) {
    return { x: validPoints[0].x, y: validPoints[0].y };
  }
  
  // Start with coordinate-wise median as initial guess
  let current = coordinateWiseMedian(validPoints);
  
  for (let iter = 0; iter < maxIterations; iter++) {
    let numeratorX = 0;
    let numeratorY = 0;
    let denominator = 0;
    
    for (const point of validPoints) {
      const dx = point.x - current.x;
      const dy = point.y - current.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      // Avoid division by zero (if point is exactly at current position)
      if (distance > tolerance) {
        const weight = 1 / distance;
        numeratorX += point.x * weight;
        numeratorY += point.y * weight;
        denominator += weight;
      } else {
        // Point is at current position, add directly
        numeratorX += point.x;
        numeratorY += point.y;
        denominator += 1;
      }
    }
    
    if (denominator === 0) {
      break;
    }
    
    const next = {
      x: numeratorX / denominator,
      y: numeratorY / denominator,
    };
    
    // Check convergence
    const dx = next.x - current.x;
    const dy = next.y - current.y;
    const change = Math.sqrt(dx * dx + dy * dy);
    
    if (change < tolerance) {
      return next;
    }
    
    current = next;
  }
  
  // Return best estimate after max iterations
  return current;
}

