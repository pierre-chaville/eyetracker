import { ref, type Ref } from 'vue'

import { applyAffineTransformation } from '../utils/calibration'
import type { CalibrationCoefficients, GazePoint, TrackingData } from '../types/tracking'

interface EyeTrackingOptions {
  wsUrl?: string
  autoConnect?: boolean
  onGazeUpdate?: (point: GazePoint) => void
  onTrackingDataUpdate?: (data: TrackingData) => void
  calibrationCoefficients?: CalibrationCoefficients | null
  isFullscreen?: boolean | Ref<boolean>
  initialIsFullscreen?: boolean
  skipCalibration?: boolean
}

interface EyeTrackingState {
  wsUrl: ReturnType<typeof ref<string>>
  isConnected: ReturnType<typeof ref<boolean>>
  gazePoint: ReturnType<typeof ref<GazePoint | null>>
  trackingData: ReturnType<typeof ref<TrackingData | null>>
  messageCount: ReturnType<typeof ref<number>>
  fps: ReturnType<typeof ref<number>>
  error: ReturnType<typeof ref<string | null>>
  isFrozen: ReturnType<typeof ref<boolean>>
  frozenGazePoint: ReturnType<typeof ref<GazePoint | null>>
  frozenTrackingData: ReturnType<typeof ref<TrackingData | null>>
  windowOffset: ReturnType<typeof ref<{ x: number; y: number }>>
  manualOffset: ReturnType<typeof ref<{ x: number; y: number }>>
  invertY: ReturnType<typeof ref<boolean>>
  scaleFactor: ReturnType<typeof ref<number>>
  manualScaleFactor: ReturnType<typeof ref<number | null>>
  applyScaling: ReturnType<typeof ref<boolean>>
  scaleMode: ReturnType<typeof ref<'divide' | 'multiply' | 'none'>>
  headerHeight: ReturnType<typeof ref<number>>
  manualHeaderHeight: ReturnType<typeof ref<number | null>>
  calibrationCoefficients: ReturnType<typeof ref<CalibrationCoefficients | null>>
  isFullscreen: ReturnType<typeof ref<boolean>>
  skipCalibration: ReturnType<typeof ref<boolean>>
  updateWindowPosition: () => void
  updateHeaderHeight: (headerElement?: HTMLElement | null) => void
  connectWebSocket: () => void
  disconnectWebSocket: () => void
  freezeTracking: () => void
  unfreezeTracking: () => void
  toggleConnection: () => void
}

let sharedState: EyeTrackingState | null = null

export function useEyeTracking(options: EyeTrackingOptions = {}) {
  if (!sharedState) {
    sharedState = createEyeTrackingState(options)
  }

  return sharedState
}

function createEyeTrackingState(options: EyeTrackingOptions): EyeTrackingState {
  const {
    wsUrl: defaultWsUrl = 'ws://127.0.0.1:8765',
    autoConnect = false,
    onGazeUpdate = null,
    onTrackingDataUpdate = null,
    calibrationCoefficients: initialCalibrationCoefficients = null,
    isFullscreen: fullscreenOption = false,
    initialIsFullscreen = false,
    skipCalibration: initialSkipCalibration = false,
  } = options

  const wsUrl = ref(defaultWsUrl)
  const isConnected = ref(false)
  const ws = ref<WebSocket | null>(null)
  const error = ref<string | null>(null)

  const gazePoint = ref<GazePoint | null>(null)
  const trackingData = ref<TrackingData | null>(null)
  const messageCount = ref(0)
  const fps = ref(0)

  const isFrozen = ref(false)
  const frozenGazePoint = ref<GazePoint | null>(null)
  const frozenTrackingData = ref<TrackingData | null>(null)

  const windowOffset = ref({ x: 0, y: 0 })
  const manualOffset = ref({ x: 0, y: 0 })
  const invertY = ref(false)
  const scaleFactor = ref(1.0)
  const manualScaleFactor = ref<number | null>(null)
  const applyScaling = ref(true)
  const scaleMode = ref<'divide' | 'multiply' | 'none'>('divide')
  const headerHeight = ref(80)
  const manualHeaderHeight = ref<number | null>(null)
  const calibrationCoefficients = ref<CalibrationCoefficients | null>(initialCalibrationCoefficients)
  const resolvedFullscreen =
    typeof fullscreenOption === 'object' ? fullscreenOption.value : fullscreenOption
  const isFullscreen = ref(resolvedFullscreen || initialIsFullscreen || false)
  const skipCalibration = ref(initialSkipCalibration)

  const frameTimes = ref<number[]>([])

  const updateFPS = () => {
    const now = performance.now()
    frameTimes.value.push(now)
    if (frameTimes.value.length > 60) {
      frameTimes.value.shift()
    }
    if (frameTimes.value.length > 1) {
      const elapsed = frameTimes.value[frameTimes.value.length - 1] - frameTimes.value[0]
      fps.value = ((frameTimes.value.length - 1) / elapsed) * 1000
    }
  }

  const connectWebSocket = () => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      return
    }

    try {
      error.value = null
      ws.value = new WebSocket(wsUrl.value)

      ws.value.onopen = () => {
        isConnected.value = true
        error.value = null
        console.log('WebSocket connected')
      }

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as TrackingData

          if (!isFrozen.value) {
            trackingData.value = data
            if (onTrackingDataUpdate) {
              onTrackingDataUpdate(data)
            }
          }

          let screenX: number
          let screenY: number

          if (data.pixelX !== undefined && data.pixelY !== undefined) {
            screenX = data.pixelX
            screenY = data.pixelY
          } else if (data.x !== undefined && data.y !== undefined && data.screenWidth && data.screenHeight) {
            screenX = data.x * data.screenWidth
            screenY = data.y * data.screenHeight
          } else {
            return
          }

          let logicalX = screenX
          let logicalY = screenY

          if (applyScaling.value) {
            const effectiveScaleFactor =
              manualScaleFactor.value !== null && manualScaleFactor.value > 0
                ? manualScaleFactor.value
                : scaleFactor.value

            if (scaleMode.value === 'divide') {
              logicalX = screenX / effectiveScaleFactor
              logicalY = screenY / effectiveScaleFactor
            } else if (scaleMode.value === 'multiply') {
              logicalX = screenX * effectiveScaleFactor
              logicalY = screenY * effectiveScaleFactor
            }
          }

          let windowX: number
          let windowY: number

          if (isFullscreen.value) {
            windowX = logicalX
            windowY = logicalY

            if (invertY.value && data.screenHeight) {
              const screenHeightLogical =
                applyScaling.value && scaleFactor.value !== 1.0
                  ? data.screenHeight / scaleFactor.value
                  : data.screenHeight
              windowY = screenHeightLogical - logicalY
            }
          } else {
            const totalOffsetX = windowOffset.value.x + manualOffset.value.x
            const totalOffsetY = windowOffset.value.y + manualOffset.value.y

            let adjustedLogicalY = logicalY
            if (invertY.value && data.screenHeight) {
              const screenHeightLogical =
                applyScaling.value && scaleFactor.value !== 1.0
                  ? data.screenHeight / scaleFactor.value
                  : data.screenHeight
              adjustedLogicalY = screenHeightLogical - logicalY
            }

            let effectiveHeaderHeight =
              manualHeaderHeight.value !== null && manualHeaderHeight.value > 0
                ? manualHeaderHeight.value
                : headerHeight.value

            if (applyScaling.value && scaleMode.value === 'divide') {
              const effectiveScaleFactor =
                manualScaleFactor.value !== null && manualScaleFactor.value > 0
                  ? manualScaleFactor.value
                  : scaleFactor.value

              if (manualHeaderHeight.value === null || manualHeaderHeight.value === 0) {
                effectiveHeaderHeight = headerHeight.value * effectiveScaleFactor * effectiveScaleFactor
              }
            }

            windowX = logicalX - totalOffsetX
            windowY = adjustedLogicalY - totalOffsetY - effectiveHeaderHeight
          }

          let x: number
          let y: number
          if (isFullscreen.value) {
            x = Math.max(0, Math.min(window.innerWidth, windowX))
            y = Math.max(0, Math.min(window.innerHeight, windowY))
          } else {
            const effectiveHeaderHeight =
              manualHeaderHeight.value !== null && manualHeaderHeight.value > 0
                ? manualHeaderHeight.value
                : headerHeight.value
            x = Math.max(0, Math.min(window.innerWidth, windowX))
            y = Math.max(0, Math.min(window.innerHeight - effectiveHeaderHeight, windowY))
          }

          if (calibrationCoefficients.value && !skipCalibration.value) {
            const calibrated = applyAffineTransformation({ x, y }, calibrationCoefficients.value)
            x = calibrated.x
            y = calibrated.y
          }

          if (!isFrozen.value) {
            gazePoint.value = { x, y }
            if (onGazeUpdate) {
              onGazeUpdate({ x, y })
            }
          }

          messageCount.value += 1
          updateFPS()
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
          error.value = 'Invalid message format'
        }
      }

      ws.value.onerror = (err) => {
        console.error('WebSocket error:', err)
        error.value = 'Connection error. Make sure the C# app is running.'
        isConnected.value = false
      }

      ws.value.onclose = () => {
        isConnected.value = false
        gazePoint.value = null
        console.log('WebSocket disconnected')
      }
    } catch (err) {
      error.value = 'Failed to connect. Check the WebSocket URL.'
      console.error('WebSocket connection error:', err)
    }
  }

  const disconnectWebSocket = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  const updateWindowPosition = () => {
    const x = typeof window.screenX === 'number' ? window.screenX : window.screenLeft || 0
    const y = typeof window.screenY === 'number' ? window.screenY : window.screenTop || 0
    windowOffset.value = { x, y }
  }

  const updateHeaderHeight = (headerElement?: HTMLElement | null) => {
    if (!headerElement) {
      return
    }
    const rect = headerElement.getBoundingClientRect()
    headerHeight.value = rect.height
  }

  const toggleConnection = () => {
    if (isConnected.value) {
      disconnectWebSocket()
    } else {
      connectWebSocket()
    }
  }

  const freezeTracking = () => {
    isFrozen.value = true
    frozenGazePoint.value = gazePoint.value
    frozenTrackingData.value = trackingData.value
  }

  const unfreezeTracking = () => {
    isFrozen.value = false
    frozenGazePoint.value = null
    frozenTrackingData.value = null
  }

  if (autoConnect) {
    connectWebSocket()
  }

  return {
    wsUrl,
    isConnected,
    gazePoint,
    trackingData,
    messageCount,
    fps,
    error,
    isFrozen,
    frozenGazePoint,
    frozenTrackingData,
    windowOffset,
    manualOffset,
    invertY,
    scaleFactor,
    manualScaleFactor,
    applyScaling,
    scaleMode,
    headerHeight,
    manualHeaderHeight,
    calibrationCoefficients,
    isFullscreen,
    skipCalibration,
    updateWindowPosition,
    updateHeaderHeight,
    connectWebSocket,
    disconnectWebSocket,
    freezeTracking,
    unfreezeTracking,
    toggleConnection,
  }
}
