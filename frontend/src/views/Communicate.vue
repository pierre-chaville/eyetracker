<template>
  <div :class="['min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900', isFullscreen ? 'p-0' : 'p-8']">
    <div :class="['mx-auto', isFullscreen ? 'w-full h-screen' : 'max-w-6xl']">
      <!-- Header (hidden in fullscreen) -->
      <h1 v-if="!isFullscreen" class="text-4xl font-bold text-gray-900 dark:text-white mb-8">{{ $t('sidebar.communicate') }}</h1>
      
      <!-- Speech-to-Text Control Panel (hidden in fullscreen) -->
      <div v-if="!isFullscreen" class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-1">
              {{ $t('communicate.speechToText') }}
            </h2>
            <p class="text-gray-600 dark:text-gray-400 text-sm">
              {{ $t('communicate.speechToTextDescription') }}
            </p>
          </div>
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <div :class="[
                'w-3 h-3 rounded-full',
                isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
              ]"></div>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                {{ isActive ? $t('communicate.active') : $t('communicate.inactive') }}
              </span>
            </div>
            <button
              @click="toggleSpeechToText"
              :disabled="isLoading"
              :class="[
                'px-6 py-3 rounded-lg font-semibold transition-all duration-200',
                isActive
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-primary-600 hover:bg-primary-700 text-white',
                isLoading ? 'opacity-50 cursor-not-allowed' : ''
              ]"
            >
              <span v-if="isLoading">{{ $t('communicate.loading') }}</span>
              <span v-else-if="isActive">{{ $t('communicate.stop') }}</span>
              <span v-else>{{ $t('communicate.start') }}</span>
            </button>
          </div>
        </div>
        
        <!-- Status Messages -->
        <div v-if="error" class="mt-4 p-4 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg">
          <p class="text-red-800 dark:text-red-200 text-sm">{{ error }}</p>
        </div>
        
        <div v-if="successMessage" class="mt-4 p-4 bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 rounded-lg">
          <p class="text-green-800 dark:text-green-200 text-sm">{{ successMessage }}</p>
        </div>
      </div>
      
      <!-- 3x3 Grid Layout -->
      <div 
        ref="gridContainer"
        :class="['bg-white dark:bg-gray-800', isFullscreen ? 'h-screen w-screen rounded-none overflow-hidden' : 'rounded-xl shadow-lg p-6']"
        :style="gridContainerStyle"
      >
        <div 
          ref="gridInner"
          :class="['grid grid-cols-3 mx-auto', isFullscreen ? 'h-full w-full p-6' : 'max-w-4xl']"
          :style="gridStyle"
        >
          <!-- Cell 1: Top Left -->
          <div
            v-if="shouldShowCell(1)"
            ref="cell1"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200',
              getCellClasses(1)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(1))"
          >
            <ChoiceCell :choice="getChoiceForCell(1)" :is-highlighted="isCellHighlighted(1)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 2: Top Center -->
          <div
            v-if="shouldShowCell(2)"
            ref="cell2"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200',
              getCellClasses(2)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(2))"
          >
            <ChoiceCell :choice="getChoiceForCell(2)" :is-highlighted="isCellHighlighted(2)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 3: Top Right -->
          <div
            v-if="shouldShowCell(3)"
            ref="cell3"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200',
              getCellClasses(3)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(3))"
          >
            <ChoiceCell :choice="getChoiceForCell(3)" :is-highlighted="isCellHighlighted(3)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 4: Middle Left -->
          <div
            v-if="shouldShowCell(4)"
            ref="cell4"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200',
              getCellClasses(4)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(4))"
          >
            <ChoiceCell :choice="getChoiceForCell(4)" :is-highlighted="isCellHighlighted(4)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 5: Center (Transcription Display) -->
          <div
            ref="cell5"
            class="border-2 border-primary-500 dark:border-primary-400 rounded-lg flex flex-col items-center justify-center bg-primary-50 dark:bg-primary-900/20 p-4"
            :style="cellStyle"
          >
            <div class="w-full h-full flex flex-col">
              <!-- Speech Started Indicator -->
              <div v-if="isSpeaking" class="mb-2 flex items-center justify-center space-x-2">
                <div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <span class="text-xs text-blue-600 dark:text-blue-400 font-medium">
                  {{ $t('communicate.speaking') }}
                </span>
              </div>
              
              <!-- Current Text -->
              <div class="flex-1 flex flex-col justify-center items-center text-center">
                <div v-if="currentText" class="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                  {{ currentText }}
                </div>
                <div v-else class="text-gray-400 dark:text-gray-500 text-sm">
                  {{ $t('communicate.noText') }}
                </div>
              </div>
              
              <!-- Recent Transcriptions -->
              <div v-if="transcriptions.length > 0" class="mt-2 text-xs text-gray-500 dark:text-gray-400 max-h-20 overflow-y-auto">
                <div v-for="(transcription, index) in transcriptions.slice(-3)" :key="index" class="mb-1">
                  {{ transcription.text }}
                </div>
              </div>
            </div>
          </div>
          
          <!-- Cell 6: Middle Right -->
          <div
            v-if="shouldShowCell(6)"
            ref="cell6"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200',
              getCellClasses(6)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(6))"
          >
            <ChoiceCell :choice="getChoiceForCell(6)" :is-highlighted="isCellHighlighted(6)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 7: Bottom Left -->
          <div
            v-if="shouldShowCell(7)"
            ref="cell7"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200',
              getCellClasses(7)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(7))"
          >
            <ChoiceCell :choice="getChoiceForCell(7)" :is-highlighted="isCellHighlighted(7)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 8: Bottom Center -->
          <div
            v-if="shouldShowCell(8)"
            ref="cell8"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200',
              getCellClasses(8)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(8))"
          >
            <ChoiceCell :choice="getChoiceForCell(8)" :is-highlighted="isCellHighlighted(8)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 9: Bottom Right -->
          <div
            v-if="shouldShowCell(9)"
            ref="cell9"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200',
              getCellClasses(9)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(9))"
          >
            <ChoiceCell :choice="getChoiceForCell(9)" :is-highlighted="isCellHighlighted(9)" />
          </div>
          <div v-else :style="cellStyle"></div>
        </div>
      </div>
      
      <!-- Gaze Visualization (for debugging) -->
      <EyeTrackingGaze
        v-if="gazePoint && isEyeTrackingConnected"
        :gaze-point="gazePoint"
        :tracking-data="trackingData"
        :is-connected="isEyeTrackingConnected"
        :is-frozen="false"
        :show-coordinates="false"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, inject } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { useEyeTracking } from '../composables/useEyeTracking';
import { useCalibration } from '../composables/useCalibration';
import EyeTrackingGaze from '../components/EyeTrackingGaze.vue';
import ChoiceCell from '../components/ChoiceCell.vue';

const { t } = useI18n();

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

// Fullscreen state
const isFullscreen = ref(false);
// Get communication fullscreen state from App.vue to hide sidebar
const isCommunicationFullscreenApp = inject('isCommunicationFullscreen', ref(false));

// Speech-to-text state
const isActive = ref(false);
const isLoading = ref(false);
const isSpeaking = ref(false);
const error = ref(null);
const successMessage = ref(null);
const transcriptions = ref([]);
const currentText = ref('');
let ws = null;
let successTimeout = null;
let fullscreenChangeHandlers = [];

// Eye tracking
const { calibrationCoefficients } = useCalibration();
const {
  isConnected: isEyeTrackingConnected,
  gazePoint,
  trackingData,
} = useEyeTracking({ 
  skipCalibration: false,
  calibrationCoefficients: calibrationCoefficients.value 
});

// Choices from backend
const choices = ref([]);
const highlightedCell = ref(null);
const cellRefs = {
  cell1: ref(null),
  cell2: ref(null),
  cell3: ref(null),
  cell4: ref(null),
  cell5: ref(null),
  cell6: ref(null),
  cell7: ref(null),
  cell8: ref(null),
  cell9: ref(null),
};

// Grid layout and scaling
const gridContainer = ref(null);
const gridInner = ref(null);
const displayScaleFactor = ref(1.0);
const gridGap = ref(24); // Gap between cells in pixels (increased from 16)

// Computed styles for grid and cells
const gridContainerStyle = computed(() => {
  // No special styling needed for container
  return {};
});

const gridStyle = computed(() => {
  // Calculate cell size based on available space
  // 3 columns, 3 rows, with gaps
  const gap = gridGap.value;
  const gapsTotal = gap * 2; // 2 gaps (between 3 cells)
  
  if (isFullscreen.value) {
    // In fullscreen, use viewport dimensions
    const containerWidth = window.innerWidth;
    const containerHeight = window.innerHeight;
    const padding = 48; // p-6 = 24px * 2
    
    const availableWidth = containerWidth - padding;
    const availableHeight = containerHeight - padding;
    
    // Calculate cell dimensions - make them rectangular (wider than tall)
    const cellWidth = (availableWidth - gapsTotal) / 3;
    const cellHeight = (availableHeight - gapsTotal) / 3;
    
    // Ensure cells fit without scrolling
    const maxCellWidth = cellWidth;
    const maxCellHeight = cellHeight;
    
    return {
      gap: `${gap}px`,
      gridTemplateColumns: `repeat(3, ${maxCellWidth}px)`,
      gridTemplateRows: `repeat(3, ${maxCellHeight}px)`,
      width: '100%',
      height: '100%',
      maxWidth: '100%',
      maxHeight: '100%',
    };
  } else {
    // In normal mode, use aspect ratio with rectangular cells
    return {
      gap: `${gap}px`,
      aspectRatio: '4 / 3', // Rectangular instead of square
    };
  }
});

const cellStyle = computed(() => {
  // Cells will be sized by grid-template-columns/rows
  return {
    minWidth: 0,
    minHeight: 0,
  };
});

// Cell position mapping based on number of choices
const getCellPositions = (count) => {
  const mappings = {
    2: [4, 6],
    3: [2, 4, 6],
    4: [1, 3, 7, 9],
    5: [1, 2, 3, 7, 9],
    6: [1, 2, 3, 7, 8, 9],
    7: [1, 2, 3, 4, 7, 8, 9],
    8: [1, 2, 3, 4, 6, 7, 8, 9],
  };
  return mappings[count] || [];
};

const shouldShowCell = (cellNumber) => {
  if (cellNumber === 5) return false; // Center cell is always shown separately
  const positions = getCellPositions(choices.value.length);
  return positions.includes(cellNumber);
};

const getChoiceForCell = (cellNumber) => {
  const positions = getCellPositions(choices.value.length);
  const index = positions.indexOf(cellNumber);
  return index >= 0 ? choices.value[index] : null;
};

const isCellHighlighted = (cellNumber) => {
  return highlightedCell.value === cellNumber;
};

const getCellClasses = (cellNumber) => {
  const baseClasses = 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600';
  const highlightedClasses = 'border-primary-500 dark:border-primary-400 bg-primary-100 dark:bg-primary-900/30 ring-2 ring-primary-500 dark:ring-primary-400';
  
  if (isCellHighlighted(cellNumber)) {
    return highlightedClasses;
  }
  return baseClasses;
};

// Check which cell the gaze is pointing at
const checkGazePosition = () => {
  if (!gazePoint.value || !isEyeTrackingConnected.value || !trackingData.value?.valid) {
    highlightedCell.value = null;
    return;
  }
  
  const gazeX = gazePoint.value.x;
  const gazeY = gazePoint.value.y;
  
  // Check each cell
  for (let cellNum = 1; cellNum <= 9; cellNum++) {
    if (cellNum === 5) continue; // Skip center cell
    
    const cellRef = cellRefs[`cell${cellNum}`];
    if (!cellRef?.value || !shouldShowCell(cellNum)) continue;
    
    const rect = cellRef.value.getBoundingClientRect();
    // gazePoint is in window coordinates, rect is also in window coordinates
    const isInside = (
      gazeX >= rect.left &&
      gazeX <= rect.right &&
      gazeY >= rect.top &&
      gazeY <= rect.bottom
    );
    
    if (isInside) {
      highlightedCell.value = cellNum;
      return;
    }
  }
  
  highlightedCell.value = null;
};

// Watch gaze point to update highlighted cell
watch(gazePoint, () => {
  checkGazePosition();
}, { immediate: true });

// Load choices from backend
const loadChoices = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/communication/choices`);
    choices.value = response.data.choices || [];
  } catch (err) {
    console.error('Error loading choices:', err);
    // Use empty choices on error
    choices.value = [];
  }
};

// Select a choice
const selectChoice = async (choice) => {
  if (!choice) return;
  
  try {
    // Append choice text to current text
    if (choice.text) {
      currentText.value = (currentText.value + ' ' + choice.text).trim();
    }
    
    // Send selection to backend
    await axios.post(`${API_BASE_URL}/api/communication/select`, {
      choice_id: choice.id,
      choice_text: choice.text,
      current_text: currentText.value,
    });
    
    // Reload choices for next context
    await loadChoices();
  } catch (err) {
    console.error('Error selecting choice:', err);
  }
};

// WebSocket connection for speech-to-text
const connectWebSocket = () => {
  try {
    const wsUrl = WS_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws/speech-to-text';
    console.log('Connecting to WebSocket:', wsUrl);
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('Speech-to-text WebSocket connected');
      error.value = null;
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        
        switch (data.type) {
          case 'connected':
            console.log('WebSocket connection confirmed');
            break;
          case 'speech_started':
            console.log('Speech started event received');
            isSpeaking.value = true;
            break;
          case 'transcription':
            console.log('Transcription received:', data.data.text);
            isSpeaking.value = false;
            const transcribedText = data.data.text;
            
            // Append to current text
            currentText.value = (currentText.value + ' ' + transcribedText).trim();
            
            // Add to transcriptions list
            transcriptions.value.push({
              text: transcribedText,
              timestamp: new Date(data.timestamp)
            });
            
            // Reload choices based on new context
            loadChoices();
            break;
          case 'error':
            console.error('Error event received:', data.data.error);
            error.value = data.data.error;
            isSpeaking.value = false;
            break;
          case 'pong':
            // Keep-alive response
            break;
          default:
            console.log('Unknown WebSocket message type:', data.type);
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err, event.data);
      }
    };
    
    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      error.value = 'WebSocket connection error';
    };
    
    ws.onclose = (event) => {
      console.log('Speech-to-text WebSocket disconnected', event.code, event.reason);
      if (isActive.value) {
        setTimeout(connectWebSocket, 3000);
      }
    };
  } catch (err) {
    console.error('Failed to connect WebSocket:', err);
    error.value = 'Failed to connect to WebSocket';
  }
};

const disconnectWebSocket = () => {
  if (ws) {
    ws.close();
    ws = null;
  }
};

const loadStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/speech-to-text/status`);
    isActive.value = response.data.is_active;
    if (isActive.value) {
      connectWebSocket();
    }
  } catch (err) {
    console.error('Error loading status:', err);
  }
};

const enterFullscreen = async () => {
  try {
    const element = document.documentElement;
    if (element.requestFullscreen) {
      await element.requestFullscreen();
    } else if (element.webkitRequestFullscreen) {
      await element.webkitRequestFullscreen();
    } else if (element.msRequestFullscreen) {
      await element.msRequestFullscreen();
    }
    isFullscreen.value = true;
  } catch (error) {
    console.warn('Could not enter fullscreen mode:', error);
    isFullscreen.value = false;
  }
};

const exitFullscreen = () => {
  try {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen();
    }
    isFullscreen.value = false;
  } catch (error) {
    console.warn('Could not exit fullscreen mode:', error);
    isFullscreen.value = false;
  }
};

const handleFullscreenChange = () => {
  if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
    // Exited fullscreen, reset state
    if (isFullscreen.value) {
      stopCommunication();
    }
  }
};

const startCommunication = async () => {
  isLoading.value = true;
  error.value = null;
  successMessage.value = null;
  
  try {
    // Start speech-to-text
    await axios.post(`${API_BASE_URL}/api/speech-to-text/start`);
    isActive.value = true;
    connectWebSocket();
    
    // Set fullscreen state in App.vue to hide sidebar
    isCommunicationFullscreenApp.value = true;
    
    // Enter fullscreen mode
    await enterFullscreen();
    
    successMessage.value = t('communicate.started');
  } catch (err) {
    console.error('Error starting communication:', err);
    error.value = err.response?.data?.detail || t('communicate.error');
    isActive.value = false;
    disconnectWebSocket();
    isCommunicationFullscreenApp.value = false;
  } finally {
    isLoading.value = false;
  }
};

const stopCommunication = async () => {
  isLoading.value = true;
  error.value = null;
  successMessage.value = null;
  
  try {
    // Stop speech-to-text
    await axios.post(`${API_BASE_URL}/api/speech-to-text/stop`);
    isActive.value = false;
    disconnectWebSocket();
    
    // Reset fullscreen state in App.vue to show sidebar
    isCommunicationFullscreenApp.value = false;
    
    // Exit fullscreen mode
    exitFullscreen();
    
    successMessage.value = t('communicate.stopped');
  } catch (err) {
    console.error('Error stopping communication:', err);
    error.value = err.response?.data?.detail || t('communicate.error');
    isCommunicationFullscreenApp.value = false;
    exitFullscreen();
  } finally {
    isLoading.value = false;
  }
};

const toggleSpeechToText = async () => {
  if (isActive.value) {
    await stopCommunication();
  } else {
    await startCommunication();
  }
  
  if (successTimeout) {
    clearTimeout(successTimeout);
  }
  successTimeout = setTimeout(() => {
    successMessage.value = null;
  }, 3000);
};

// Update calibration coefficients when they change
watch(calibrationCoefficients, (newCoefficients) => {
  // The useEyeTracking composable should handle this, but we can update if needed
}, { immediate: true });

let gazeCheckInterval = null;

// Load display scale factor
const loadDisplayScaleFactor = async () => {
  try {
    // Try to get scale factor from Electron API
    if (window.electronAPI && window.electronAPI.getDisplayScaleFactor) {
      const scale = await window.electronAPI.getDisplayScaleFactor();
      displayScaleFactor.value = scale || 1.0;
    } else {
      // Fallback to devicePixelRatio
      displayScaleFactor.value = window.devicePixelRatio || 1.0;
    }
    
    // If scale is 1.0, try devicePixelRatio as fallback
    if (displayScaleFactor.value === 1.0 && window.devicePixelRatio && window.devicePixelRatio !== 1.0) {
      displayScaleFactor.value = window.devicePixelRatio;
    }
    
    console.log('Display scale factor:', displayScaleFactor.value);
  } catch (err) {
    console.error('Error getting display scale factor:', err);
    displayScaleFactor.value = window.devicePixelRatio || 1.0;
  }
};

// Update grid size on window resize
const updateGridSize = () => {
  // Force reactivity update
  if (gridStyle.value) {
    // Trigger computed property recalculation
  }
};

onMounted(() => {
  loadStatus();
  loadChoices();
  loadDisplayScaleFactor();
  
  // Check gaze position periodically
  gazeCheckInterval = setInterval(() => {
    checkGazePosition();
  }, 100); // Check every 100ms
  
  // Listen for window resize to update grid
  window.addEventListener('resize', updateGridSize);
  
  // Listen for fullscreen changes
  const handleFullscreenChange = () => {
    if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
      if (isFullscreen.value) {
        stopCommunication();
      }
    } else {
      // Fullscreen entered, update grid size
      setTimeout(() => {
        updateGridSize();
      }, 100);
    }
  };
  
  document.addEventListener('fullscreenchange', handleFullscreenChange);
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
  document.addEventListener('msfullscreenchange', handleFullscreenChange);
  
  fullscreenChangeHandlers = [
    { event: 'fullscreenchange', handler: handleFullscreenChange },
    { event: 'webkitfullscreenchange', handler: handleFullscreenChange },
    { event: 'msfullscreenchange', handler: handleFullscreenChange },
  ];
});

onBeforeUnmount(() => {
  // Remove window resize listener
  window.removeEventListener('resize', updateGridSize);
  
  // Remove fullscreen event listeners
  if (fullscreenChangeHandlers && fullscreenChangeHandlers.length > 0) {
    fullscreenChangeHandlers.forEach(({ event, handler }) => {
      document.removeEventListener(event, handler);
    });
  }
  
  // Exit fullscreen if still active when component unmounts
  if (isFullscreen.value) {
    exitFullscreen();
    isCommunicationFullscreenApp.value = false;
  }
  
  disconnectWebSocket();
  if (successTimeout) {
    clearTimeout(successTimeout);
  }
  if (gazeCheckInterval) {
    clearInterval(gazeCheckInterval);
  }
});
</script>
