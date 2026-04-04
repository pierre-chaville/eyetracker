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
const API_V1_BASE = `${API_BASE_URL}/api/v1`

const apiClient = axios.create({
  baseURL: API_V1_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const eyeTrackingAPI = {
  async start(): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/eye-tracking/start')
    return response.data
  },

  async stop(): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/eye-tracking/stop')
    return response.data
  },

  async getStatus(): Promise<Record<string, unknown>> {
    const response = await apiClient.get<Record<string, unknown>>('/eye-tracking/status')
    return response.data
  },
}

export const communicationAPI = {
  async interpret(
    gazePoints: unknown[],
    context: string | null = null,
  ): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>('/communication/interpret', {
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
    aacMode?: boolean
    signal?: AbortSignal
  } = {}): Promise<ChoicesResponse> {
    const {
      conversationHistory = [],
      userId = null,
      caregiverId = null,
      currentText = null,
      sessionId = null,
      stepNumber = null,
      aacMode = false,
      signal,
    } = options
    const response = await apiClient.post<ChoicesResponse>('/communication/choices', {
      conversation_history: conversationHistory,
      user_id: userId,
      caregiver_id: caregiverId,
      current_text: currentText,
      session_id: sessionId,
      step_number: stepNumber,
      aac_mode: aacMode,
    }, { signal })
    return response.data
  },

  async selectChoice(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>('/communication/select', payload)
    return response.data
  },
}

export const calibrationAPI = {
  async start(): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/calibration/start')
    return response.data
  },

  async process(calibrationData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>(
      '/calibration/process',
      calibrationData,
    )
    return response.data
  },
}

export const usersAPI = {
  async list(skip = 0, limit = 100, activeOnly = false): Promise<UserRead[]> {
    const response = await apiClient.get<UserRead[]>('/users', {
      params: { skip, limit, active_only: activeOnly },
    })
    return response.data
  },

  async get(userId: number): Promise<UserRead> {
    const response = await apiClient.get<UserRead>(`/users/${userId}`)
    return response.data
  },

  async create(userData: Record<string, unknown>): Promise<UserRead> {
    const response = await apiClient.post<UserRead>('/users', userData)
    return response.data
  },

  async update(userId: number, userData: Record<string, unknown>): Promise<UserRead> {
    const response = await apiClient.put<UserRead>(`/users/${userId}`, userData)
    return response.data
  },

  async delete(userId: number): Promise<void> {
    await apiClient.delete(`/users/${userId}`)
  },
}

export const caregiversAPI = {
  async list(skip = 0, limit = 100): Promise<CaregiverRead[]> {
    const response = await apiClient.get<CaregiverRead[]>('/caregivers', {
      params: { skip, limit },
    })
    return response.data
  },

  async get(caregiverId: number): Promise<CaregiverRead> {
    const response = await apiClient.get<CaregiverRead>(`/caregivers/${caregiverId}`)
    return response.data
  },

  async create(caregiverData: Record<string, unknown>): Promise<CaregiverRead> {
    const response = await apiClient.post<CaregiverRead>('/caregivers', caregiverData)
    return response.data
  },

  async update(caregiverId: number, caregiverData: Record<string, unknown>): Promise<CaregiverRead> {
    const response = await apiClient.put<CaregiverRead>(
      `/caregivers/${caregiverId}`,
      caregiverData,
    )
    return response.data
  },

  async delete(caregiverId: number): Promise<void> {
    await apiClient.delete(`/caregivers/${caregiverId}`)
  },
}

export const configAPI = {
  async get(): Promise<Record<string, unknown>> {
    const response = await apiClient.get<Record<string, unknown>>('/config')
    return response.data
  },

  async update(configData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.put<Record<string, unknown>>('/config', configData)
    return response.data
  },
}

export const sessionsAPI = {
  async list(params: Record<string, unknown> = {}): Promise<Record<string, unknown>[]> {
    const response = await apiClient.get<Record<string, unknown>[]>('/communication/sessions', {
      params,
    })
    return response.data
  },

  async get(sessionId: number): Promise<Record<string, unknown>> {
    const response = await apiClient.get<Record<string, unknown>>(
      `/communication/sessions/${sessionId}`,
    )
    return response.data
  },

  async create(sessionData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>(
      '/communication/sessions',
      sessionData,
    )
    return response.data
  },

  async update(sessionId: number, sessionData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.put<Record<string, unknown>>(
      `/communication/sessions/${sessionId}`,
      sessionData,
    )
    return response.data
  },

  async analyze(sessionId: number): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>(
      `/communication/sessions/${sessionId}/analyze`,
    )
    return response.data
  },

  async delete(sessionId: number): Promise<void> {
    await apiClient.delete(`/communication/sessions/${sessionId}`)
  },
}

export const speechToTextAPI = {
  async start(): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/speech-to-text/start')
    return response.data
  },

  async stop(): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/speech-to-text/stop')
    return response.data
  },

  async status(): Promise<SpeechToTextStatusResponse> {
    const response = await apiClient.get<SpeechToTextStatusResponse>('/speech-to-text/status')
    return response.data
  },
}

export const keyboardAPI = {
  async predictions(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>('/keyboard/predictions', payload)
    return response.data
  },

  async tts(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>('/keyboard/tts', payload)
    return response.data
  },

  async createSession(sessionData: Record<string, unknown> = {}): Promise<{ id: number }> {
    const response = await apiClient.post<Record<string, unknown>>('/keyboard/sessions', sessionData)
    const id = response.data?.id
    return { id: typeof id === 'number' ? id : Number(id) }
  },

  async updateSession(sessionId: number, sessionData: Record<string, unknown>): Promise<void> {
    await apiClient.put(`/keyboard/sessions/${sessionId}`, sessionData)
  },

  async recordStepSelection(payload: {
    session_id: number
    step_number: number
    selected_text: string
  }): Promise<void> {
    await apiClient.post('/keyboard/session-selection', payload)
  },
}

export const keyboardLayoutsAPI = {
  async list(skip = 0, limit = 100): Promise<KeyboardLayoutRead[]> {
    const response = await apiClient.get<KeyboardLayoutRead[]>('/keyboards', {
      params: { skip, limit },
    })
    return response.data
  },

  async get(layoutId: number): Promise<KeyboardLayoutRead> {
    const response = await apiClient.get<KeyboardLayoutRead>(`/keyboards/${layoutId}`)
    return response.data
  },

  async create(payload: Record<string, unknown>): Promise<KeyboardLayoutRead> {
    const response = await apiClient.post<KeyboardLayoutRead>('/keyboards', payload)
    return response.data
  },

  async update(layoutId: number, payload: Record<string, unknown>): Promise<KeyboardLayoutRead> {
    const response = await apiClient.put<KeyboardLayoutRead>(`/keyboards/${layoutId}`, payload)
    return response.data
  },

  async delete(layoutId: number): Promise<void> {
    await apiClient.delete(`/keyboards/${layoutId}`)
  },
}

export default apiClient
