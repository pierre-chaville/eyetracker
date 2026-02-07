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

  console.log('window.innerWidth', window.innerWidth);
  console.log('window.innerHeight', window.innerHeight);
  const wsUrl = ref(defaultWsUrl)
  const isConnected = ref(false)
  const ws = ref<WebSocket | null>(null)
  const error = ref<string | null>(null)

  const gazePoint = ref<GazePoint | null>(null)
  const trackingData = ref<TrackingData | null>(null)
  const messageCount = ref(0)
  const fps = ref(0)


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

          trackingData.value = data
          if (onTrackingDataUpdate) {
            onTrackingDataUpdate(data)
          }

          // We will use the coordinates in percentages of the screen size, and then convert them to pixels based on the screen size.
          // NB: screen size is provided by browser and not the actual screen size: scale factor and also some space for the browser UI.

          let x = Math.max(0, Math.min((data.x ?? 0) * window.innerWidth, window.innerWidth))
          let y = Math.max(0, Math.min((data.y ?? 0) * window.innerHeight, window.innerHeight))

          // then apply calibration coefficients if they are available and calibration is not skipped
          if (calibrationCoefficients.value && !skipCalibration.value) {
            const calibrated = applyAffineTransformation({ x, y }, calibrationCoefficients.value)
            x = calibrated.x
            y = calibrated.y
          }

          gazePoint.value = { x, y }
          if (onGazeUpdate) {
            onGazeUpdate({ x, y })
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
    windowOffset.value = { x: 0, y: 0 }
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
    toggleConnection,
  }
}
