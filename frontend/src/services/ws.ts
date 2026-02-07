export type WSConnectionStatus =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'reconnecting'

export interface WSClientOptions {
  url: string
  reconnectIntervalMs?: number
  maxReconnectAttempts?: number
  onMessage: (data: unknown) => void
  onStatusChange?: (status: WSConnectionStatus) => void
}

export function createWSClient(options: WSClientOptions) {
  const reconnectIntervalMs = options.reconnectIntervalMs ?? 3000
  const maxReconnectAttempts = options.maxReconnectAttempts ?? 10
  let ws: WebSocket | null = null
  let reconnectAttempts = 0
  let shouldReconnect = true

  function setStatus(status: WSConnectionStatus) {
    options.onStatusChange?.(status)
  }

  function connect() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      return
    }
    setStatus(reconnectAttempts > 0 ? 'reconnecting' : 'connecting')
    ws = new WebSocket(options.url)

    ws.onopen = () => {
      reconnectAttempts = 0
      setStatus('connected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        options.onMessage(data)
      } catch {
        options.onMessage(event.data)
      }
    }

    ws.onerror = () => {
      setStatus('disconnected')
    }

    ws.onclose = () => {
      setStatus('disconnected')
      if (shouldReconnect && reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts += 1
        setTimeout(connect, reconnectIntervalMs)
      }
    }
  }

  function disconnect() {
    shouldReconnect = false
    if (ws) {
      ws.close()
      ws = null
    }
    setStatus('disconnected')
  }

  function send(message: object) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
    }
  }

  function enableReconnect(enabled: boolean) {
    shouldReconnect = enabled
  }

  return {
    connect,
    disconnect,
    send,
    enableReconnect,
  }
}
