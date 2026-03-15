import axios from 'axios'

import type {
  CaregiverRead,
  ChoicesResponse,
  KeyboardLayoutRead,
  MessageResponse,
  SpeechToTextStatusResponse,
  UserRead,
} from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const eyeTrackingAPI = {
  async start(): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/api/eye-tracking/start')
    return response.data
  },

  async stop(): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/api/eye-tracking/stop')
    return response.data
  },

  async getStatus(): Promise<Record<string, unknown>> {
    const response = await apiClient.get<Record<string, unknown>>('/api/eye-tracking/status')
    return response.data
  },
}

export const communicationAPI = {
  async interpret(
    gazePoints: unknown[],
    context: string | null = null,
  ): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>('/api/communication/interpret', {
      gaze_points: gazePoints,
      context,
    })
    return response.data
  },

  async getChoices(options: {
    conversationHistory?: unknown[]
    userId?: number | null
    caregiverId?: number | null
    currentText?: string | null
    sessionId?: number | null
    stepNumber?: number | null
  } = {}): Promise<ChoicesResponse> {
    const {
      conversationHistory = [],
      userId = null,
      caregiverId = null,
      currentText = null,
      sessionId = null,
      stepNumber = null,
    } = options
    const response = await apiClient.post<ChoicesResponse>('/api/communication/choices', {
      conversation_history: conversationHistory,
      user_id: userId,
      caregiver_id: caregiverId,
      current_text: currentText,
      session_id: sessionId,
      step_number: stepNumber,
    })
    return response.data
  },

  async selectChoice(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>('/api/communication/select', payload)
    return response.data
  },
}

export const calibrationAPI = {
  async start(): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/api/calibration/start')
    return response.data
  },

  async process(calibrationData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/calibration/process',
      calibrationData,
    )
    return response.data
  },
}

export const usersAPI = {
  async list(skip = 0, limit = 100, activeOnly = false): Promise<UserRead[]> {
    const response = await apiClient.get<UserRead[]>('/api/users', {
      params: { skip, limit, active_only: activeOnly },
    })
    return response.data
  },

  async get(userId: number): Promise<UserRead> {
    const response = await apiClient.get<UserRead>(`/api/users/${userId}`)
    return response.data
  },

  async create(userData: Record<string, unknown>): Promise<UserRead> {
    const response = await apiClient.post<UserRead>('/api/users', userData)
    return response.data
  },

  async update(userId: number, userData: Record<string, unknown>): Promise<UserRead> {
    const response = await apiClient.put<UserRead>(`/api/users/${userId}`, userData)
    return response.data
  },

  async delete(userId: number): Promise<void> {
    await apiClient.delete(`/api/users/${userId}`)
  },
}

export const caregiversAPI = {
  async list(skip = 0, limit = 100): Promise<CaregiverRead[]> {
    const response = await apiClient.get<CaregiverRead[]>('/api/caregivers', {
      params: { skip, limit },
    })
    return response.data
  },

  async get(caregiverId: number): Promise<CaregiverRead> {
    const response = await apiClient.get<CaregiverRead>(`/api/caregivers/${caregiverId}`)
    return response.data
  },

  async create(caregiverData: Record<string, unknown>): Promise<CaregiverRead> {
    const response = await apiClient.post<CaregiverRead>('/api/caregivers', caregiverData)
    return response.data
  },

  async update(caregiverId: number, caregiverData: Record<string, unknown>): Promise<CaregiverRead> {
    const response = await apiClient.put<CaregiverRead>(
      `/api/caregivers/${caregiverId}`,
      caregiverData,
    )
    return response.data
  },

  async delete(caregiverId: number): Promise<void> {
    await apiClient.delete(`/api/caregivers/${caregiverId}`)
  },
}

export const configAPI = {
  async get(): Promise<Record<string, unknown>> {
    const response = await apiClient.get<Record<string, unknown>>('/api/config')
    return response.data
  },

  async update(configData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.put<Record<string, unknown>>('/api/config', configData)
    return response.data
  },
}

export const sessionsAPI = {
  async list(params: Record<string, unknown> = {}): Promise<Record<string, unknown>[]> {
    const response = await apiClient.get<Record<string, unknown>[]>('/api/communication/sessions', {
      params,
    })
    return response.data
  },

  async get(sessionId: number): Promise<Record<string, unknown>> {
    const response = await apiClient.get<Record<string, unknown>>(
      `/api/communication/sessions/${sessionId}`,
    )
    return response.data
  },

  async create(sessionData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/communication/sessions',
      sessionData,
    )
    return response.data
  },

  async update(sessionId: number, sessionData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.put<Record<string, unknown>>(
      `/api/communication/sessions/${sessionId}`,
      sessionData,
    )
    return response.data
  },

  async delete(sessionId: number): Promise<void> {
    await apiClient.delete(`/api/communication/sessions/${sessionId}`)
  },
}

export const speechToTextAPI = {
  async start(): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/api/speech-to-text/start')
    return response.data
  },

  async stop(): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/api/speech-to-text/stop')
    return response.data
  },

  async status(): Promise<SpeechToTextStatusResponse> {
    const response = await apiClient.get<SpeechToTextStatusResponse>('/api/speech-to-text/status')
    return response.data
  },
}

export const keyboardAPI = {
  async predictions(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>('/api/keyboard/predictions', payload)
    return response.data
  },

  async tts(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>('/api/keyboard/tts', payload)
    return response.data
  },
}

export const keyboardLayoutsAPI = {
  async list(skip = 0, limit = 100): Promise<KeyboardLayoutRead[]> {
    const response = await apiClient.get<KeyboardLayoutRead[]>('/api/keyboards', {
      params: { skip, limit },
    })
    return response.data
  },

  async get(layoutId: number): Promise<KeyboardLayoutRead> {
    const response = await apiClient.get<KeyboardLayoutRead>(`/api/keyboards/${layoutId}`)
    return response.data
  },

  async create(payload: Record<string, unknown>): Promise<KeyboardLayoutRead> {
    const response = await apiClient.post<KeyboardLayoutRead>('/api/keyboards', payload)
    return response.data
  },

  async update(layoutId: number, payload: Record<string, unknown>): Promise<KeyboardLayoutRead> {
    const response = await apiClient.put<KeyboardLayoutRead>(`/api/keyboards/${layoutId}`, payload)
    return response.data
  },

  async delete(layoutId: number): Promise<void> {
    await apiClient.delete(`/api/keyboards/${layoutId}`)
  },
}

export default apiClient
