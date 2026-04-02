import type { CalibrationCoefficients } from './tracking'

export interface MessageResponse {
  success: boolean
  message: string
}

export interface SpeechToTextStatusResponse {
  is_active: boolean
  websocket_connections: number
}

export interface UserRead {
  id: number
  name: string
  calibration?: string | { affine_coefficients?: CalibrationCoefficients }
  [key: string]: unknown
}

export interface CaregiverRead {
  id: number
  name: string
  [key: string]: unknown
}

export interface Choice {
  id: string
  text?: string
  icon?: string
  probability?: number
  pictogram_url?: string
}

export interface ChoicesResponse {
  choices: Choice[]
}

export interface KeyboardLayoutRead {
  id: number
  name: string
  description?: string | null
  rows: number
  columns: number
  predictive_cells: number
  cells?: string[][] | null
  created_at: string
  updated_at: string
}
