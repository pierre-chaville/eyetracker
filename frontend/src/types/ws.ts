export interface STTConnectedEvent {
  type: 'connected'
  data: { message: string }
  timestamp: string
}

export interface STTSpeechStartedEvent {
  type: 'speech_started'
  data: Record<string, never>
  timestamp: string
}

export interface STTTranscriptionEvent {
  type: 'transcription'
  data: { text: string }
  timestamp: string
}

export interface STTErrorEvent {
  type: 'error'
  data: { error: string }
  timestamp: string
}

export interface STTPongEvent {
  type: 'pong'
  data: string
}

export type STTEvent =
  | STTConnectedEvent
  | STTSpeechStartedEvent
  | STTTranscriptionEvent
  | STTErrorEvent
  | STTPongEvent
