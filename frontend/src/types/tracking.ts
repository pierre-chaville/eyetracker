export interface GazePoint {
  x: number
  y: number
}

export interface TrackingData {
  x?: number
  y?: number
  pixelX?: number
  pixelY?: number
  screenWidth?: number
  screenHeight?: number
  valid?: boolean
  [key: string]: unknown
}

export interface CalibrationCoefficients {
  a0: number
  a1: number
  a2: number
  b0: number
  b1: number
  b2: number
}
