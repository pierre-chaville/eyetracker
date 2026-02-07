<template>
  <div :class="['min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900', isFullscreen ? 'p-0' : 'p-8']">
    <div :class="['mx-auto', isFullscreen ? 'w-full h-screen' : 'max-w-6xl']">
      <!-- Header (hidden in fullscreen) -->
      <h1 v-if="!isFullscreen" class="text-4xl font-bold text-gray-900 dark:text-white mb-8">{{ $t('sidebar.keyboard') }}</h1>
      
      <!-- Control Panel (hidden in fullscreen) -->
      <div v-if="!isFullscreen" class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-1">
              {{ $t('keyboard.title') }}
            </h2>
            <p class="text-gray-600 dark:text-gray-400 text-sm">
              {{ $t('keyboard.description') }}
            </p>
          </div>
          <div class="flex items-center space-x-4">
            <button
              @click="toggleCommunication"
              :disabled="isLoading"
              :class="[
                'px-6 py-3 rounded-lg font-semibold transition-all duration-200',
                isActive
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-primary-600 hover:bg-primary-700 text-white',
                isLoading ? 'opacity-50 cursor-not-allowed' : ''
              ]"
            >
              <span v-if="isLoading">{{ $t('keyboard.loading') }}</span>
              <span v-else-if="isActive">{{ $t('keyboard.stop') }}</span>
              <span v-else>{{ $t('keyboard.start') }}</span>
            </button>
          </div>
        </div>
        
        <!-- Status Messages -->
        <div v-if="error" class="mt-4 p-4 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg">
          <p class="text-red-800 dark:text-red-200 text-sm">{{ error }}</p>
        </div>
      </div>
      
      <!-- Keyboard Grid Layout -->
      <div 
        ref="gridContainer"
        :class="['bg-white dark:bg-gray-800', isFullscreen ? 'h-screen w-screen rounded-none overflow-hidden flex flex-col' : 'rounded-xl shadow-lg p-6']"
        :style="gridContainerStyle"
      >
        <!-- 5x5 Grid -->
        <div 
          ref="gridInner"
          :class="['grid grid-cols-5 mx-auto', isFullscreen ? 'w-full p-6 flex-1 min-h-0' : 'max-w-5xl']"
          :style="gridStyle"
        >
          <!-- Row 1: Predictive Words (LLM suggestions) -->
          <div
            v-for="(word, index) in predictiveWords"
            :key="`word-${index}`"
            :ref="`cell-${index}`"
            :class="[
              'border-4 rounded-lg flex items-center justify-center cursor-pointer transition-all duration-200 font-semibold relative overflow-hidden',
              isCellHighlighted(index) 
                ? 'border-primary-500 bg-primary-100 dark:bg-primary-900/30 ring-4 ring-primary-300 dark:ring-primary-700' 
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600',
              'text-gray-900 dark:text-white text-2xl'
            ]"
            :style="cellStyle"
            @click="selectWord(word)"
          >
            <!-- Progress bar at bottom -->
            <div
              v-if="dwellingCellIndex === index"
              class="absolute bottom-0 left-0 h-3 bg-blue-500 transition-all duration-75 ease-linear"
              :style="{ width: `${getDwellingProgress(index) * 100}%` }"
            ></div>
            {{ word }}
          </div>
          
          <!-- Fill empty cells in row 1 if less than 5 words -->
          <div
            v-for="n in (5 - predictiveWords.length)"
            :key="`empty-${n}`"
            :style="cellStyle"
            class="border-2 border-transparent"
          ></div>
          
          <!-- Row 2: Vowels (a, e, i, o, u) -->
          <div
            v-for="(vowel, index) in vowels"
            :key="`vowel-${index}`"
            :ref="`vowel-${index}`"
            :class="[
              'border-4 rounded-lg flex items-center justify-center cursor-pointer transition-all duration-200 font-bold relative overflow-hidden',
              isCellHighlighted(5 + index) 
                ? 'border-primary-500 bg-primary-100 dark:bg-primary-900/30 ring-4 ring-primary-300 dark:ring-primary-700' 
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600',
              'text-gray-900 dark:text-white text-4xl'
            ]"
            :style="cellStyle"
            @click="selectLetter(vowel)"
          >
            <!-- Progress bar at bottom -->
            <div
              v-if="dwellingCellIndex === (5 + index)"
              class="absolute bottom-0 left-0 h-3 bg-blue-500 transition-all duration-75 ease-linear"
              :style="{ width: `${getDwellingProgress(5 + index) * 100}%` }"
            ></div>
            {{ vowel.toUpperCase() }}
          </div>
          
          <!-- Row 3: Consonants (B, C, D, F, G) -->
          <div
            v-for="(consonant, index) in consonants1"
            :key="`consonant1-${index}`"
            :ref="`consonant1-${index}`"
            :class="[
              'border-4 rounded-lg flex items-center justify-center cursor-pointer transition-all duration-200 font-bold relative overflow-hidden',
              isCellHighlighted(10 + index) 
                ? 'border-primary-500 bg-primary-100 dark:bg-primary-900/30 ring-4 ring-primary-300 dark:ring-primary-700' 
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600',
              'text-gray-900 dark:text-white text-4xl'
            ]"
            :style="cellStyle"
            @click="selectLetter(consonant)"
          >
            <!-- Progress bar at bottom -->
            <div
              v-if="dwellingCellIndex === (10 + index)"
              class="absolute bottom-0 left-0 h-3 bg-blue-500 transition-all duration-75 ease-linear"
              :style="{ width: `${getDwellingProgress(10 + index) * 100}%` }"
            ></div>
            {{ consonant.toUpperCase() }}
          </div>
          
          <!-- Row 4: Consonants (J, L, M, N, P) -->
          <div
            v-for="(consonant, index) in consonants2"
            :key="`consonant2-${index}`"
            :ref="`consonant2-${index}`"
            :class="[
              'border-4 rounded-lg flex items-center justify-center cursor-pointer transition-all duration-200 font-bold relative overflow-hidden',
              isCellHighlighted(15 + index) 
                ? 'border-primary-500 bg-primary-100 dark:bg-primary-900/30 ring-4 ring-primary-300 dark:ring-primary-700' 
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600',
              'text-gray-900 dark:text-white text-4xl'
            ]"
            :style="cellStyle"
            @click="selectLetter(consonant)"
          >
            <!-- Progress bar at bottom -->
            <div
              v-if="dwellingCellIndex === (15 + index)"
              class="absolute bottom-0 left-0 h-3 bg-blue-500 transition-all duration-75 ease-linear"
              :style="{ width: `${getDwellingProgress(15 + index) * 100}%` }"
            ></div>
            {{ consonant.toUpperCase() }}
          </div>
          
          <!-- Row 5: Consonants (Q, R, S, T, V) -->
          <div
            v-for="(consonant, index) in consonants3"
            :key="`consonant3-${index}`"
            :ref="`consonant3-${index}`"
            :class="[
              'border-4 rounded-lg flex items-center justify-center cursor-pointer transition-all duration-200 font-bold relative overflow-hidden',
              isCellHighlighted(20 + index) 
                ? 'border-primary-500 bg-primary-100 dark:bg-primary-900/30 ring-4 ring-primary-300 dark:ring-primary-700' 
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600',
              'text-gray-900 dark:text-white text-4xl'
            ]"
            :style="cellStyle"
            @click="selectLetter(consonant)"
          >
            <!-- Progress bar at bottom -->
            <div
              v-if="dwellingCellIndex === (20 + index)"
              class="absolute bottom-0 left-0 h-3 bg-blue-500 transition-all duration-75 ease-linear"
              :style="{ width: `${getDwellingProgress(20 + index) * 100}%` }"
            ></div>
            {{ consonant.toUpperCase() }}
          </div>
        </div>
        
        <!-- Bottom Bar: Microphone and Transcription (only in fullscreen) -->
        <div 
          v-if="isFullscreen"
          class="w-full p-4 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-300 dark:border-gray-600 flex items-center justify-center space-x-3 flex-shrink-0"
        >
          <MicrophoneIcon 
            v-if="isSpeaking" 
            class="w-5 h-5 text-blue-500 dark:text-blue-400 animate-pulse flex-shrink-0" 
          />
          <div class="flex-1 text-center">
            <p v-if="lastTranscription" class="text-sm text-gray-700 dark:text-gray-300">
              {{ lastTranscription }}
            </p>
            <p v-else class="text-xs text-gray-400 dark:text-gray-500 italic">
              {{ $t('keyboard.noTranscription') }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, inject, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useEyeTracking } from '../composables/useEyeTracking';
import { useCalibration } from '../composables/useCalibration';
import { useSTTEvents } from '../composables/useSTTEvents';
import { MicrophoneIcon } from '@heroicons/vue/24/solid';
import { configAPI, keyboardAPI, speechToTextAPI } from '../services/api';

const { t } = useI18n();

// Inject fullscreen state from App.vue
const isCommunicationFullscreenApp = inject('isCommunicationFullscreenApp', ref(false));

// State
const isFullscreen = ref(false);
const isActive = ref(false);
const isLoading = ref(false);
const error = ref<string | null>(null);
const currentText = ref('');
const predictiveWords = ref<string[]>([]);
const highlightedCellIndex = ref<number | null>(null);
const lastTranscription = ref('');

// Dwelling state
const dwellTime = ref(2.0); // Default dwell time in seconds
const dwellingCellIndex = ref<number | null>(null); // Currently dwelling cell index
const dwellingStartTime = ref(null); // When dwelling started
const dwellingProgress = ref(0); // Progress from 0 to 1
let dwellingInterval = null;

// Keyboard layout
const vowels = ['a', 'e', 'i', 'o', 'u'];
const consonants1 = ['b', 'c', 'd', 'f', 'g'];
const consonants2 = ['j', 'l', 'm', 'n', 'p'];
const consonants3 = ['q', 'r', 's', 't', 'v'];

// Eye tracking
const { calibrationCoefficients } = useCalibration();
const {
  gazePoint,
  isConnected,
  connect,
  disconnect,
  calibrationCoefficients: trackingCalibrationCoefficients,
  isFullscreen: trackingIsFullscreen,
  updateWindowPosition,
  updateHeaderHeight,
} = useEyeTracking({ 
  skipCalibration: false,
  calibrationCoefficients: calibrationCoefficients.value,
  isFullscreen: isFullscreen
});

const {
  isSpeaking,
  error: sttError,
  on: onSTTEvent,
  connect: connectSTT,
  disconnect: disconnectSTT,
} = useSTTEvents({ autoConnect: false });

watch(sttError, (value) => {
  if (value) {
    error.value = value;
  }
});

// Update calibration coefficients in eye tracking when they change
watch(calibrationCoefficients, (newCoefficients) => {
  if (trackingCalibrationCoefficients) {
    trackingCalibrationCoefficients.value = newCoefficients;
  }
}, { immediate: true });

// Watch isFullscreen to update trackingIsFullscreen
watch(isFullscreen, (newValue) => {
  if (trackingIsFullscreen) {
    trackingIsFullscreen.value = newValue;
  }
});

// Grid refs
const gridContainer = ref(null);
const gridInner = ref(null);

// Cell positions for eye tracking
const cellPositions = ref([]);

// Computed styles
const gridContainerStyle = computed(() => {
  if (isFullscreen.value) {
    return {
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      zIndex: 1000,
    };
  }
  return {};
});

const gridStyle = computed(() => {
  if (isFullscreen.value) {
    const scale = window.devicePixelRatio || 1;
    return {
      gap: '1rem',
    };
  }
  return {
    gap: '1rem',
  };
});

const cellStyle = computed(() => {
  if (isFullscreen.value) {
    // Account for bottom bar (microphone/transcription) and padding
    const bottomBarHeight = 72; // Height of bottom bar (p-4 = 16px top + 16px bottom + ~40px content)
    const gridPadding = 48; // Top and bottom padding (24px * 2)
    const gapTotal = 64; // Gap between 5 rows (1rem * 4 gaps = 16px * 4)
    const availableHeight = window.innerHeight - bottomBarHeight - gridPadding - gapTotal;
    const cellHeight = Math.max(availableHeight / 5, 60); // Minimum 60px per cell, divide by 5 rows
    return {
      minHeight: `${cellHeight}px`,
      height: `${cellHeight}px`,
    };
  }
  return {
    minHeight: '80px',
    height: '80px',
  };
});

// Check if cell is highlighted
const isCellHighlighted = (index) => {
  return highlightedCellIndex.value === index;
};

// Get dwelling progress for a cell (0 to 1)
const getDwellingProgress = (cellIndex) => {
  if (dwellingCellIndex.value === cellIndex) {
    return dwellingProgress.value;
  }
  return 0;
};

// Start dwelling on a cell
const startDwelling = (cellIndex) => {
  // Stop any existing dwelling
  stopDwelling();
  
  dwellingCellIndex.value = cellIndex;
  dwellingStartTime.value = Date.now();
  dwellingProgress.value = 0;
  
  // Update progress every frame (60fps)
  dwellingInterval = setInterval(() => {
    if (!dwellingStartTime.value || dwellingCellIndex.value !== cellIndex) {
      stopDwelling();
      return;
    }
    
    const elapsed = (Date.now() - dwellingStartTime.value) / 1000; // seconds
    const progress = Math.min(elapsed / dwellTime.value, 1.0);
    dwellingProgress.value = progress;
    
    // If dwelling is complete, trigger selection
    if (progress >= 1.0) {
      // Determine what to select based on cell index
      if (cellIndex < 5) {
        // Row 1: Predictive words
        if (cellIndex < predictiveWords.value.length) {
          selectWord(predictiveWords.value[cellIndex]);
        }
      } else if (cellIndex < 10) {
        // Row 2: Vowels
        const vowelIndex = cellIndex - 5;
        if (vowelIndex < vowels.length) {
          selectLetter(vowels[vowelIndex]);
        }
      } else if (cellIndex < 15) {
        // Row 3: Consonants1
        const consonantIndex = cellIndex - 10;
        if (consonantIndex < consonants1.length) {
          selectLetter(consonants1[consonantIndex]);
        }
      } else if (cellIndex < 20) {
        // Row 4: Consonants2
        const consonantIndex = cellIndex - 15;
        if (consonantIndex < consonants2.length) {
          selectLetter(consonants2[consonantIndex]);
        }
      } else if (cellIndex < 25) {
        // Row 5: Consonants3
        const consonantIndex = cellIndex - 20;
        if (consonantIndex < consonants3.length) {
          selectLetter(consonants3[consonantIndex]);
        }
      }
      stopDwelling();
    }
  }, 16); // ~60fps
};

// Stop dwelling
const stopDwelling = () => {
  if (dwellingInterval) {
    clearInterval(dwellingInterval);
    dwellingInterval = null;
  }
  dwellingCellIndex.value = null;
  dwellingStartTime.value = null;
  dwellingProgress.value = 0;
};

// Load predictive words from backend
const loadPredictiveWords = async () => {
  try {
    const userId = localStorage.getItem('selectedUserId') ? parseInt(localStorage.getItem('selectedUserId')) : null;
    const caregiverId = localStorage.getItem('selectedCaregiverId') ? parseInt(localStorage.getItem('selectedCaregiverId')) : null;
    
    const response = await keyboardAPI.predictions({
      current_text: currentText.value,
      user_id: userId,
      caregiver_id: caregiverId,
    });
    
    predictiveWords.value = (response as { words?: string[] }).words || [];
  } catch (err) {
    console.error('Error loading predictive words:', err);
    // Fallback to empty array
    predictiveWords.value = [];
  }
};

// Select a word
const selectWord = async (word) => {
  currentText.value = (currentText.value + ' ' + word).trim();
  await loadPredictiveWords();
  
  // Generate TTS for the word
  await playTTS(word);
};

// Select a letter
const selectLetter = async (letter) => {
  const keyToken = `<${letter.toUpperCase()}>`;
  currentText.value = currentText.value + keyToken;
  await loadPredictiveWords();
};

// Play TTS
const playTTS = async (text) => {
  try {
    await keyboardAPI.tts({
      text,
    });
    
    // Audio is played in the backend, so we don't need to play it here
    // This prevents double playback/echo
    console.log('Audio is being played in the backend');
  } catch (err) {
    console.error('Error generating TTS:', err);
  }
};

// Play audio (similar to Communicate page)
const playAudio = async (audioBase64) => {
  if (!audioBase64) return;
  
  const wasSTTActive = isActive.value;
  
  if (wasSTTActive) {
    try {
      await speechToTextAPI.stop();
    } catch (err) {
      console.error('Error stopping STT for TTS playback:', err);
    }
  }
  
  try {
    const audioData = atob(audioBase64);
    const arrayBuffer = new ArrayBuffer(audioData.length);
    const uint8Array = new Uint8Array(arrayBuffer);
    for (let i = 0; i < audioData.length; i++) {
      uint8Array[i] = audioData.charCodeAt(i);
    }
    
    let mimeType = 'audio/mpeg';
    if (uint8Array[0] === 0x52 && uint8Array[1] === 0x49 && uint8Array[2] === 0x46 && uint8Array[3] === 0x46) {
      mimeType = 'audio/wav';
    } else if (uint8Array[0] === 0xFF && (uint8Array[1] === 0xFB || uint8Array[1] === 0xF3)) {
      mimeType = 'audio/mpeg';
    }
    
    const blob = new Blob([arrayBuffer], { type: mimeType });
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);
    audio.volume = 1.0;
    
    audio.addEventListener('ended', async () => {
      URL.revokeObjectURL(audioUrl);
      if (wasSTTActive) {
        await resumeSTT();
      }
    });
    
    audio.addEventListener('error', async () => {
      if (wasSTTActive) {
        await resumeSTT();
      }
    });
    
    await audio.play();
  } catch (err) {
    console.error('Error playing audio:', err);
    if (wasSTTActive) {
      await resumeSTT();
    }
  }
};

// Resume STT
const resumeSTT = async () => {
  try {
    await speechToTextAPI.start();
    isActive.value = true;
    connectSTT();
  } catch (err) {
    console.error('Error resuming STT:', err);
  }
};

// Toggle communication
const toggleCommunication = async () => {
  if (isActive.value) {
    await stopCommunication();
  } else {
    await startCommunication();
  }
};

onSTTEvent('transcription', (event) => {
  const transcribedText = event.data.text;
  lastTranscription.value = transcribedText;
  currentText.value = transcribedText;
  loadPredictiveWords();
});

onSTTEvent('error', (event) => {
  error.value = event.data.error;
});

// Start communication
const startCommunication = async () => {
  isLoading.value = true;
  error.value = null;
  
  try {
    await speechToTextAPI.start();
    isActive.value = true;
    
    // Set fullscreen state in App.vue to hide sidebar
    isCommunicationFullscreenApp.value = true;
    
    // Enter fullscreen mode
    await enterFullscreen();
    
    // Connect WebSocket for speech-to-text events
    connectSTT();
    
    // Load initial predictive words
    await loadPredictiveWords();
  } catch (err) {
    console.error('Error starting communication:', err);
    error.value = t('keyboard.error');
    isActive.value = false;
    isCommunicationFullscreenApp.value = false;
  } finally {
    isLoading.value = false;
  }
};

// Stop communication
const stopCommunication = async () => {
  stopDwelling();
  highlightedCellIndex.value = null;
  isLoading.value = true;
  error.value = null;
  
  try {
    await speechToTextAPI.stop();
    isActive.value = false;
    disconnectSTT();
    
    // Reset fullscreen state in App.vue to show sidebar
    isCommunicationFullscreenApp.value = false;
    
    // Exit fullscreen mode
    exitFullscreen();
  } catch (err) {
    console.error('Error stopping communication:', err);
    error.value = t('keyboard.error');
  } finally {
    isLoading.value = false;
  }
};

// Fullscreen functions
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

// Eye tracking detection
const detectCellFromGaze = () => {
  if (!gazePoint.value || !isConnected.value || !isFullscreen.value) {
    highlightedCellIndex.value = null;
    stopDwelling();
    return;
  }
  
  // Calculate which cell the gaze is on
  // Total cells: 5 (words) + 5 (vowels) + 5 (consonants1) + 5 (consonants2) + 5 (consonants3) = 25 cells
  const totalCells = 25;
  const cols = 5;
  const rows = 5;
  
  if (!gridInner.value) return;
  
  const rect = gridInner.value.getBoundingClientRect();
  const cellWidth = rect.width / cols;
  const cellHeight = rect.height / rows;
  
  const relativeX = gazePoint.value.x - rect.left;
  const relativeY = gazePoint.value.y - rect.top;
  
  const col = Math.floor(relativeX / cellWidth);
  const row = Math.floor(relativeY / cellHeight);
  
  if (col >= 0 && col < cols && row >= 0 && row < rows) {
    const cellIndex = row * cols + col;
    
    // Check if cell has content
    let hasContent = false;
    if (row === 0 && col < predictiveWords.value.length) {
      hasContent = true;
    } else if (row === 1 && col < vowels.length) {
      hasContent = true;
    } else if (row === 2 && col < consonants1.length) {
      hasContent = true;
    } else if (row === 3 && col < consonants2.length) {
      hasContent = true;
    } else if (row === 4 && col < consonants3.length) {
      hasContent = true;
    }
    
    if (hasContent) {
      // Update highlighted cell
      if (highlightedCellIndex.value !== cellIndex) {
        highlightedCellIndex.value = cellIndex;
      }
      
      // Start or continue dwelling
      if (dwellingCellIndex.value !== cellIndex) {
        startDwelling(cellIndex);
      }
    } else {
      highlightedCellIndex.value = null;
      stopDwelling();
    }
  } else {
    highlightedCellIndex.value = null;
    stopDwelling();
  }
};

// Watch gaze point for cell detection
watch(gazePoint, () => {
  detectCellFromGaze();
});

// Handle fullscreen changes
const handleFullscreenChange = () => {
  if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
    if (isFullscreen.value) {
      stopCommunication();
    }
  }
};

// Load configuration to get dwell_time
const loadConfig = async () => {
  try {
    const data = await configAPI.get();
    if (data.eye_tracking?.dwell_time) {
      dwellTime.value = data.eye_tracking.dwell_time;
    }
  } catch (err) {
    console.error('Error loading config:', err);
    // Use default dwell_time
  }
};

let gazeCheckInterval = null;
let positionInterval = null;
let resizeHandler = null;

// Connect eye tracking on mount
onMounted(() => {
  connectSTT();
  loadConfig();
  
  // Initialize window position and header height
  updateWindowPosition();
  updateHeaderHeight();
  
  // Update window position periodically (in case window is moved)
  positionInterval = setInterval(() => {
    updateWindowPosition();
    updateHeaderHeight();
  }, 1000);
  
  // Also update on window resize/move events
  resizeHandler = () => {
    updateWindowPosition();
    updateHeaderHeight();
  };
  window.addEventListener('resize', resizeHandler);
  
  // Check gaze position periodically
  gazeCheckInterval = setInterval(() => {
    if (isConnected.value && gazePoint.value && isFullscreen.value) {
      detectCellFromGaze();
    }
  }, 50); // Check every 50ms for smoother dwelling
  
  // Handle fullscreen changes
  document.addEventListener('fullscreenchange', handleFullscreenChange);
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
  document.addEventListener('msfullscreenchange', handleFullscreenChange);
});

onBeforeUnmount(() => {
  stopDwelling();
  if (gazeCheckInterval) {
    clearInterval(gazeCheckInterval);
    gazeCheckInterval = null;
  }
  if (positionInterval) {
    clearInterval(positionInterval);
    positionInterval = null;
  }
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler);
    resizeHandler = null;
  }
  disconnectSTT();
  if (isFullscreen.value) {
    exitFullscreen();
    isCommunicationFullscreenApp.value = false;
  }
  
  // Remove fullscreen event listeners
  document.removeEventListener('fullscreenchange', handleFullscreenChange);
  document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
  document.removeEventListener('msfullscreenchange', handleFullscreenChange);
});
</script>

