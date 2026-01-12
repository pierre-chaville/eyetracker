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
        <!-- 4x5 Grid -->
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
              'border-4 rounded-lg flex items-center justify-center cursor-pointer transition-all duration-200 font-semibold',
              isCellHighlighted(index) 
                ? 'border-primary-500 bg-primary-100 dark:bg-primary-900/30 ring-4 ring-primary-300 dark:ring-primary-700' 
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600',
              'text-gray-900 dark:text-white text-2xl'
            ]"
            :style="cellStyle"
            @click="selectWord(word)"
          >
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
              'border-4 rounded-lg flex items-center justify-center cursor-pointer transition-all duration-200 font-bold',
              isCellHighlighted(5 + index) 
                ? 'border-primary-500 bg-primary-100 dark:bg-primary-900/30 ring-4 ring-primary-300 dark:ring-primary-700' 
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600',
              'text-gray-900 dark:text-white text-4xl'
            ]"
            :style="cellStyle"
            @click="selectLetter(vowel)"
          >
            {{ vowel.toUpperCase() }}
          </div>
          
          <!-- Row 3: Consonants (b, d, f, l, m) -->
          <div
            v-for="(consonant, index) in consonants1"
            :key="`consonant1-${index}`"
            :ref="`consonant1-${index}`"
            :class="[
              'border-4 rounded-lg flex items-center justify-center cursor-pointer transition-all duration-200 font-bold',
              isCellHighlighted(10 + index) 
                ? 'border-primary-500 bg-primary-100 dark:bg-primary-900/30 ring-4 ring-primary-300 dark:ring-primary-700' 
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600',
              'text-gray-900 dark:text-white text-4xl'
            ]"
            :style="cellStyle"
            @click="selectLetter(consonant)"
          >
            {{ consonant.toUpperCase() }}
          </div>
          
          <!-- Row 4: Consonants (n, p, r, s, t) -->
          <div
            v-for="(consonant, index) in consonants2"
            :key="`consonant2-${index}`"
            :ref="`consonant2-${index}`"
            :class="[
              'border-4 rounded-lg flex items-center justify-center cursor-pointer transition-all duration-200 font-bold',
              isCellHighlighted(15 + index) 
                ? 'border-primary-500 bg-primary-100 dark:bg-primary-900/30 ring-4 ring-primary-300 dark:ring-primary-700' 
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600',
              'text-gray-900 dark:text-white text-4xl'
            ]"
            :style="cellStyle"
            @click="selectLetter(consonant)"
          >
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

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, inject } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { useEyeTracking } from '../composables/useEyeTracking';
import { MicrophoneIcon } from '@heroicons/vue/24/solid';

const { t } = useI18n();

// Inject fullscreen state from App.vue
const isCommunicationFullscreenApp = inject('isCommunicationFullscreenApp', ref(false));

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || API_BASE_URL;

// State
const isFullscreen = ref(false);
const isActive = ref(false);
const isLoading = ref(false);
const isSpeaking = ref(false);
const error = ref(null);
const currentText = ref('');
const predictiveWords = ref([]);
const highlightedCellIndex = ref(null);
const lastTranscription = ref('');
let ws = null;

// Keyboard layout
const vowels = ['a', 'e', 'i', 'o', 'u'];
const consonants1 = ['b', 'd', 'f', 'l', 'm'];
const consonants2 = ['n', 'p', 'r', 's', 't'];

// Eye tracking
const { gazePoint, isConnected, connect, disconnect } = useEyeTracking({ skipCalibration: false });

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
    const gapTotal = 48; // Gap between 4 rows (1rem * 3 gaps = 16px * 3)
    const availableHeight = window.innerHeight - bottomBarHeight - gridPadding - gapTotal;
    const cellHeight = Math.max(availableHeight / 4, 60); // Minimum 60px per cell
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

// Load predictive words from backend
const loadPredictiveWords = async () => {
  try {
    const userId = localStorage.getItem('selectedUserId') ? parseInt(localStorage.getItem('selectedUserId')) : null;
    const caregiverId = localStorage.getItem('selectedCaregiverId') ? parseInt(localStorage.getItem('selectedCaregiverId')) : null;
    
    const response = await axios.post(`${API_BASE_URL}/api/keyboard/predictions`, {
      current_text: currentText.value,
      user_id: userId,
      caregiver_id: caregiverId,
    });
    
    predictiveWords.value = response.data.words || [];
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
  currentText.value = currentText.value + letter;
  await loadPredictiveWords();
  
  // Generate TTS for the letter
  await playTTS(letter);
};

// Play TTS
const playTTS = async (text) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/keyboard/tts`, {
      text: text,
    });
    
    if (response.data.audio_base64) {
      await playAudio(response.data.audio_base64);
    }
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
      await axios.post(`${API_BASE_URL}/api/speech-to-text/stop`);
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
    await axios.post(`${API_BASE_URL}/api/speech-to-text/start`);
    isActive.value = true;
    // WebSocket should still be connected, but reconnect if needed
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      connectWebSocket();
    }
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
            lastTranscription.value = transcribedText;
            // Update current text with transcription
            currentText.value = transcribedText;
            // Reload predictive words based on new text
            loadPredictiveWords();
            break;
          case 'error':
            console.error('Error event received:', data.data.error);
            error.value = data.data.error;
            isSpeaking.value = false;
            break;
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };
    
    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      error.value = 'WebSocket connection error';
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      isSpeaking.value = false;
    };
  } catch (err) {
    console.error('Error connecting WebSocket:', err);
    error.value = 'Failed to connect to speech-to-text service';
  }
};

const disconnectWebSocket = () => {
  if (ws) {
    ws.close();
    ws = null;
  }
  isSpeaking.value = false;
};

// Start communication
const startCommunication = async () => {
  isLoading.value = true;
  error.value = null;
  
  try {
    await axios.post(`${API_BASE_URL}/api/speech-to-text/start`);
    isActive.value = true;
    
    // Set fullscreen state in App.vue to hide sidebar
    isCommunicationFullscreenApp.value = true;
    
    // Enter fullscreen mode
    await enterFullscreen();
    
    // Connect WebSocket for speech-to-text events
    connectWebSocket();
    
    // Load initial predictive words
    await loadPredictiveWords();
  } catch (err) {
    console.error('Error starting communication:', err);
    error.value = err.response?.data?.detail || t('keyboard.error');
    isActive.value = false;
    isCommunicationFullscreenApp.value = false;
  } finally {
    isLoading.value = false;
  }
};

// Stop communication
const stopCommunication = async () => {
  isLoading.value = true;
  error.value = null;
  
  try {
    await axios.post(`${API_BASE_URL}/api/speech-to-text/stop`);
    isActive.value = false;
    disconnectWebSocket();
    
    // Reset fullscreen state in App.vue to show sidebar
    isCommunicationFullscreenApp.value = false;
    
    // Exit fullscreen mode
    exitFullscreen();
  } catch (err) {
    console.error('Error stopping communication:', err);
    error.value = err.response?.data?.detail || t('keyboard.error');
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
    return;
  }
  
  // Calculate which cell the gaze is on
  // Total cells: 5 (words) + 5 (vowels) + 5 (consonants1) + 5 (consonants2) = 20 cells
  const totalCells = 20;
  const cols = 5;
  const rows = 4;
  
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
    if (row === 0 && col < predictiveWords.value.length) {
      highlightedCellIndex.value = cellIndex;
    } else if (row === 1 && col < vowels.length) {
      highlightedCellIndex.value = cellIndex;
    } else if (row === 2 && col < consonants1.length) {
      highlightedCellIndex.value = cellIndex;
    } else if (row === 3 && col < consonants2.length) {
      highlightedCellIndex.value = cellIndex;
    } else {
      highlightedCellIndex.value = null;
    }
  } else {
    highlightedCellIndex.value = null;
  }
};

// Watch gaze point for cell detection
import { watch } from 'vue';
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

// Connect eye tracking on mount
onMounted(() => {
  connectWebSocket();
  
  // Handle fullscreen changes
  document.addEventListener('fullscreenchange', handleFullscreenChange);
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
  document.addEventListener('msfullscreenchange', handleFullscreenChange);
});

onBeforeUnmount(() => {
  disconnectWebSocket();
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

