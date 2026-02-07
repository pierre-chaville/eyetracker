import { onMounted, onUnmounted, ref } from 'vue'

import type { STTEvent } from '../types/ws'
import type { WSConnectionStatus } from '../services/ws'
import { createWSClient } from '../services/ws'

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

interface STTEventOptions {
  autoConnect?: boolean
}

export function useSTTEvents(options: STTEventOptions = {}) {
  const autoConnect = options.autoConnect ?? true
  const connectionStatus = ref<WSConnectionStatus>('disconnected')
  const isSpeaking = ref(false)
  const lastTranscription = ref<string | null>(null)
  const error = ref<string | null>(null)

  const handlers = new Map<string, Set<(event: STTEvent) => void>>()

  function on<T extends STTEvent['type']>(
    type: T,
    handler: (event: Extract<STTEvent, { type: T }>) => void,
  ) {
    if (!handlers.has(type)) {
      handlers.set(type, new Set())
    }
    handlers.get(type)!.add(handler as (event: STTEvent) => void)
    return () => handlers.get(type)?.delete(handler as (event: STTEvent) => void)
  }

  const wsClient = createWSClient({
    url: WS_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws/speech-to-text',
    onMessage: (data) => {
      const event = data as STTEvent
      if (event.type === 'speech_started') {
        isSpeaking.value = true
      }
      if (event.type === 'transcription') {
        isSpeaking.value = false
        lastTranscription.value = event.data.text
      }
      if (event.type === 'error') {
        isSpeaking.value = false
        error.value = event.data.error
      }
      handlers.get(event.type)?.forEach((fn) => fn(event))
    },
    onStatusChange: (status) => {
      connectionStatus.value = status
    },
  })

  function connect() {
    wsClient.enableReconnect(true)
    wsClient.connect()
  }

  function disconnect() {
    wsClient.enableReconnect(false)
    wsClient.disconnect()
  }

  onMounted(() => {
    if (autoConnect) {
      connect()
    }
  })
  onUnmounted(() => disconnect())

  return {
    connectionStatus,
    isSpeaking,
    lastTranscription,
    error,
    on,
    connect,
    disconnect,
  }
}
