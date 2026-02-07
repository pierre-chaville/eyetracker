export interface Point {
  x: number
  y: number
}

export function median(values: number[]): number {
  if (!values || values.length === 0) {
    return 0
  }

  const sorted = [...values].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)

  if (sorted.length % 2 === 0) {
    return (sorted[mid - 1] + sorted[mid]) / 2
  }

  return sorted[mid]
}

export function coordinateWiseMedian(points: Point[]): Point {
  if (!points || points.length === 0) {
    return { x: 0, y: 0 }
  }

  const xValues = points.map((p) => p.x).filter((x) => x !== null && x !== undefined)
  const yValues = points.map((p) => p.y).filter((y) => y !== null && y !== undefined)

  return {
    x: median(xValues),
    y: median(yValues),
  }
}

export function geometricMedian(
  points: Point[],
  tolerance = 0.001,
  maxIterations = 100,
): Point {
  if (!points || points.length === 0) {
    return { x: 0, y: 0 }
  }

  const validPoints = points.filter(
    (p) =>
      p.x !== null &&
      p.x !== undefined &&
      p.y !== null &&
      p.y !== undefined &&
      !Number.isNaN(p.x) &&
      !Number.isNaN(p.y),
  )

  if (validPoints.length === 0) {
    return { x: 0, y: 0 }
  }

  if (validPoints.length === 1) {
    return { x: validPoints[0].x, y: validPoints[0].y }
  }

  let current = coordinateWiseMedian(validPoints)

  for (let iter = 0; iter < maxIterations; iter += 1) {
    let numeratorX = 0
    let numeratorY = 0
    let denominator = 0

    for (const point of validPoints) {
      const dx = point.x - current.x
      const dy = point.y - current.y
      const distance = Math.sqrt(dx * dx + dy * dy)

      if (distance > tolerance) {
        const weight = 1 / distance
        numeratorX += point.x * weight
        numeratorY += point.y * weight
        denominator += weight
      } else {
        numeratorX += point.x
        numeratorY += point.y
        denominator += 1
      }
    }

    if (denominator === 0) {
      break
    }

    const next = {
      x: numeratorX / denominator,
      y: numeratorY / denominator,
    }

    const dx = next.x - current.x
    const dy = next.y - current.y
    const change = Math.sqrt(dx * dx + dy * dy)

    if (change < tolerance) {
      return next
    }

    current = next
  }

  return current
}
