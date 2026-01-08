import { ref, computed } from 'vue';

// Shared state instance - all components using this composable will share the same state
let sharedState = null;

/**
 * Composable for eye tracking functionality
 * Handles WebSocket connection, coordinate conversion, and tracking state
 * Uses a singleton pattern to share state across all components
 */
export function useEyeTracking(options = {}) {
  // Create shared state if it doesn't exist
  if (!sharedState) {
    sharedState = createEyeTrackingState(options);
  }
  
  return sharedState;
}

function createEyeTrackingState(options = {}) {
  const {
    wsUrl: defaultWsUrl = 'ws://127.0.0.1:8765',
    autoConnect = false,
    onGazeUpdate = null,
    onTrackingDataUpdate = null,
  } = options;

  // Connection state
  const wsUrl = ref(defaultWsUrl);
  const isConnected = ref(false);
  const ws = ref(null);
  const error = ref(null);

  // Tracking data
  const gazePoint = ref(null);
  const trackingData = ref(null);
  const messageCount = ref(0);
  const fps = ref(0);

  // Freeze functionality
  const isFrozen = ref(false);
  const frozenGazePoint = ref(null);
  const frozenTrackingData = ref(null);

  // Configuration
  const windowOffset = ref({ x: 0, y: 0 });
  const manualOffset = ref({ x: 0, y: 0 });
  const invertY = ref(false);
  const scaleFactor = ref(1.0);
  const manualScaleFactor = ref(null);
  const applyScaling = ref(true);
  const scaleMode = ref('divide'); // 'divide', 'multiply', or 'none'
  const headerHeight = ref(80);
  const manualHeaderHeight = ref(null);

  // FPS calculation
  const frameTimes = ref([]);

  const updateFPS = () => {
    const now = performance.now();
    frameTimes.value.push(now);
    if (frameTimes.value.length > 60) {
      frameTimes.value.shift();
    }
    if (frameTimes.value.length > 1) {
      const elapsed = frameTimes.value[frameTimes.value.length - 1] - frameTimes.value[0];
      fps.value = ((frameTimes.value.length - 1) / elapsed) * 1000;
    }
  };

  const connectWebSocket = () => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      error.value = null;
      ws.value = new WebSocket(wsUrl.value);

      ws.value.onopen = () => {
        isConnected.value = true;
        error.value = null;
        console.log('WebSocket connected');
      };

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Store the full tracking data (only update if not frozen)
          if (!isFrozen.value) {
            trackingData.value = data;
            if (onTrackingDataUpdate) {
              onTrackingDataUpdate(data);
            }
          }
          
          // Handle the coordinate data
          let screenX, screenY;
          
          if (data.pixelX !== undefined && data.pixelY !== undefined) {
            screenX = data.pixelX;
            screenY = data.pixelY;
          } else if (data.x !== undefined && data.y !== undefined && data.screenWidth && data.screenHeight) {
            screenX = data.x * data.screenWidth;
            screenY = data.y * data.screenHeight;
          } else {
            return;
          }
          
          // Convert screen coordinates to window coordinates
          let logicalX = screenX;
          let logicalY = screenY;
          
          // Apply scaling if enabled
          if (applyScaling.value) {
            const effectiveScaleFactor = manualScaleFactor.value !== null && manualScaleFactor.value > 0
              ? manualScaleFactor.value
              : scaleFactor.value;
            
            if (scaleMode.value === 'divide') {
              logicalX = screenX / effectiveScaleFactor;
              logicalY = screenY / effectiveScaleFactor;
            } else if (scaleMode.value === 'multiply') {
              logicalX = screenX * effectiveScaleFactor;
              logicalY = screenY * effectiveScaleFactor;
            }
          }
          
          // Apply offsets
          let totalOffsetX = windowOffset.value.x + manualOffset.value.x;
          let totalOffsetY = windowOffset.value.y + manualOffset.value.y;
          
          // Handle Y axis inversion
          let adjustedLogicalY = logicalY;
          if (invertY.value && data.screenHeight) {
            const screenHeightLogical = applyScaling.value && scaleFactor.value !== 1.0 
              ? data.screenHeight / scaleFactor.value 
              : data.screenHeight;
            adjustedLogicalY = screenHeightLogical - logicalY;
          }
          
          // Calculate effective header height
          let effectiveHeaderHeight = manualHeaderHeight.value !== null && manualHeaderHeight.value > 0
            ? manualHeaderHeight.value
            : headerHeight.value;
          
          if (applyScaling.value && scaleMode.value === 'divide') {
            const effectiveScaleFactor = manualScaleFactor.value !== null && manualScaleFactor.value > 0
              ? manualScaleFactor.value
              : scaleFactor.value;
            
            if (manualHeaderHeight.value === null || manualHeaderHeight.value === 0) {
              effectiveHeaderHeight = headerHeight.value * effectiveScaleFactor * effectiveScaleFactor;
            }
          }
          
          const windowX = logicalX - totalOffsetX;
          const windowY = adjustedLogicalY - totalOffsetY - effectiveHeaderHeight;
          
          // Ensure coordinates are within bounds
          const x = Math.max(0, Math.min(window.innerWidth, windowX));
          const y = Math.max(0, Math.min(window.innerHeight - effectiveHeaderHeight, windowY));
          
          // Only update gaze point if not frozen
          if (!isFrozen.value) {
            gazePoint.value = { x, y };
            if (onGazeUpdate) {
              onGazeUpdate({ x, y });
            }
          }
          
          messageCount.value++;
          updateFPS();
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
          error.value = 'Invalid message format';
        }
      };

      ws.value.onerror = (err) => {
        console.error('WebSocket error:', err);
        error.value = 'Connection error. Make sure the C# app is running.';
        isConnected.value = false;
      };

      ws.value.onclose = () => {
        isConnected.value = false;
        gazePoint.value = null;
        console.log('WebSocket disconnected');
      };
    } catch (err) {
      error.value = 'Failed to connect. Check the WebSocket URL.';
      console.error('WebSocket connection error:', err);
    }
  };

  const disconnectWebSocket = () => {
    if (ws.value) {
      ws.value.close();
      ws.value = null;
    }
    isConnected.value = false;
    gazePoint.value = null;
    trackingData.value = null;
  };

  const toggleConnection = () => {
    if (isConnected.value) {
      disconnectWebSocket();
    } else {
      connectWebSocket();
    }
  };

  const toggleFreeze = () => {
    if (isFrozen.value) {
      isFrozen.value = false;
      frozenGazePoint.value = null;
      frozenTrackingData.value = null;
    } else {
      if (gazePoint.value && trackingData.value) {
        frozenGazePoint.value = { ...gazePoint.value };
        frozenTrackingData.value = { ...trackingData.value };
        isFrozen.value = true;
      }
    }
  };

  const updateWindowPosition = async () => {
    if (window.electronAPI) {
      try {
        const position = await window.electronAPI.getWindowPosition();
        windowOffset.value = { x: position.x, y: position.y };
        
        try {
          const scale = await window.electronAPI.getDisplayScaleFactor();
          scaleFactor.value = scale;
          
          if (scaleFactor.value === 1.0 && window.devicePixelRatio && window.devicePixelRatio !== 1.0) {
            scaleFactor.value = window.devicePixelRatio;
          }
        } catch (err) {
          console.error('Error getting scale factor:', err);
          scaleFactor.value = window.devicePixelRatio || 1.0;
        }
      } catch (err) {
        console.error('Error getting window position:', err);
      }
    } else {
      if (window.screenX !== undefined && window.screenY !== undefined) {
        windowOffset.value = { x: window.screenX, y: window.screenY };
      } else {
        windowOffset.value = { x: 0, y: 0 };
      }
      scaleFactor.value = window.devicePixelRatio || 1.0;
    }
  };

  const updateHeaderHeight = (headerElement) => {
    if (headerElement) {
      const rect = headerElement.getBoundingClientRect();
      headerHeight.value = rect.height;
    }
  };

  // Computed values
  const currentGazePoint = computed(() => {
    return isFrozen.value ? frozenGazePoint.value : gazePoint.value;
  });

  const currentTrackingData = computed(() => {
    return isFrozen.value ? frozenTrackingData.value : trackingData.value;
  });

  return {
    // State
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
    
    // Computed
    currentGazePoint,
    currentTrackingData,
    
    // Configuration
    windowOffset,
    manualOffset,
    invertY,
    scaleFactor,
    manualScaleFactor,
    applyScaling,
    scaleMode,
    headerHeight,
    manualHeaderHeight,
    
    // Methods
    connectWebSocket,
    disconnectWebSocket,
    toggleConnection,
    toggleFreeze,
    updateWindowPosition,
    updateHeaderHeight,
  };
}

