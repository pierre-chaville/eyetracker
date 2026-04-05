<template>
  <div :class="['min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900', isFullscreen ? 'p-0' : 'p-8']">
    <div :class="['mx-auto', isFullscreen ? 'w-full h-screen' : 'max-w-6xl']">
      <!-- Header (hidden in fullscreen) -->
      <h1 v-if="!isFullscreen" class="text-4xl font-bold text-gray-900 dark:text-white mb-8">{{ $t('sidebar.communicate') }}</h1>
      
      <!-- Speech-to-Text Control Panel (hidden in fullscreen) -->
      <div v-if="!isFullscreen" class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6">
        <div class="flex flex-col gap-5">
          <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div class="min-w-0 flex-1">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-1">
                {{ $t('communicate.speechToText') }}
              </h2>
              <p class="text-gray-600 dark:text-gray-400 text-sm">
                {{ $t('communicate.speechToTextDescription') }}
              </p>
            </div>
            <button
              @click="toggleSpeechToText"
              :disabled="isLoading"
              :class="[
                'shrink-0 px-8 py-4 rounded-xl text-lg font-semibold transition-all duration-200 touch-manipulation min-h-[3.25rem] sm:self-center',
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

          <!-- Choice display: text only vs AAC (touch-friendly) -->
          <div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('communicate.aacDisplayLabel') }}
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-3xl">
              <button
                type="button"
                @click="aacMode = false"
                class="rounded-xl border-2 px-5 py-4 text-left transition-all min-h-[4rem] touch-manipulation active:scale-[0.99]"
                :class="!aacMode
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/25 ring-2 ring-primary-400/40'
                  : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 hover:border-primary-300 dark:hover:border-primary-600'"
              >
                <span class="text-lg font-semibold text-gray-900 dark:text-white">{{ $t('communicate.aacTextOnly') }}</span>
              </button>
              <button
                type="button"
                @click="aacMode = true"
                class="rounded-xl border-2 px-5 py-4 text-left transition-all min-h-[4rem] touch-manipulation active:scale-[0.99]"
                :class="aacMode
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/25 ring-2 ring-primary-400/40'
                  : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 hover:border-primary-300 dark:hover:border-primary-600'"
              >
                <span class="text-lg font-semibold text-gray-900 dark:text-white">{{ $t('communicate.aacPictograms') }}</span>
              </button>
            </div>
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
        :class="['bg-white dark:bg-gray-800', isFullscreen ? 'h-screen w-screen rounded-none overflow-hidden flex flex-col' : 'rounded-xl shadow-lg p-6']"
        :style="gridContainerStyle"
      >
        <div 
          ref="gridInner"
          :class="['grid grid-cols-3', isFullscreen ? 'flex-1 w-full p-6' : 'max-w-4xl mx-auto']"
          :style="gridStyle"
        >
          <!-- Cell 1: Top Left -->
          <div
            v-if="shouldShowCell(1)"
            ref="cell1"
            data-cell="1"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200 relative overflow-hidden',
              getCellClasses(1)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(1))"
          >
            <!-- Progress bar at bottom -->
            <div
              v-if="dwellingCell === 1"
              class="absolute bottom-0 left-0 h-3 bg-blue-500 transition-all duration-75 ease-linear"
              :style="{ width: `${getDwellingProgress(1) * 100}%` }"
            ></div>
            <ChoiceCell :choice="getChoiceForCell(1)" :is-highlighted="isCellHighlighted(1)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 2: Top Center -->
          <div
            v-if="shouldShowCell(2)"
            ref="cell2"
            data-cell="2"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200 relative overflow-hidden',
              getCellClasses(2)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(2))"
          >
            <!-- Progress bar at bottom -->
            <div
              v-if="dwellingCell === 2"
              class="absolute bottom-0 left-0 h-3 bg-blue-500 transition-all duration-75 ease-linear"
              :style="{ width: `${getDwellingProgress(2) * 100}%` }"
            ></div>
            <ChoiceCell :choice="getChoiceForCell(2)" :is-highlighted="isCellHighlighted(2)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 3: Top Right -->
          <div
            v-if="shouldShowCell(3)"
            ref="cell3"
            data-cell="3"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200 relative overflow-hidden',
              getCellClasses(3)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(3))"
          >
            <!-- Progress bar at bottom -->
            <div
              v-if="dwellingCell === 3"
              class="absolute bottom-0 left-0 h-3 bg-blue-500 transition-all duration-75 ease-linear"
              :style="{ width: `${getDwellingProgress(3) * 100}%` }"
            ></div>
            <ChoiceCell :choice="getChoiceForCell(3)" :is-highlighted="isCellHighlighted(3)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 4: Middle Left -->
          <div
            v-if="shouldShowCell(4)"
            ref="cell4"
            data-cell="4"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200 relative overflow-hidden',
              getCellClasses(4)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(4))"
          >
            <!-- Progress bar at bottom -->
            <div
              v-if="dwellingCell === 4"
              class="absolute bottom-0 left-0 h-3 bg-blue-500 transition-all duration-75 ease-linear"
              :style="{ width: `${getDwellingProgress(4) * 100}%` }"
            ></div>
            <ChoiceCell :choice="getChoiceForCell(4)" :is-highlighted="isCellHighlighted(4)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 5: Center (Transcription Display) -->
          <div
            ref="cell5"
            class="border border-gray-300 dark:border-gray-600 rounded-lg flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-800/50 p-4"
            :class="{ 'cursor-pointer': isFullscreen }"
            :style="cellStyle"
            @click="isFullscreen && stopCommunication()"
          >
            <div class="w-full h-full flex flex-col">
              <!-- Searching indicator -->
              <div v-if="isSearching" class="mb-2 flex items-center justify-center space-x-2">
                <svg class="w-5 h-5 text-amber-500 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
                <span class="text-xs text-amber-500 font-medium">
                  {{ $t('communicate.searching') }}
                </span>
              </div>
              <!-- Speech Started Indicator -->
              <div v-else-if="isSpeaking" class="mb-2 flex items-center justify-center space-x-2">
                <MicrophoneIcon class="w-5 h-5 text-blue-600 dark:text-blue-400 animate-pulse" />
                <span class="text-xs text-blue-600 dark:text-blue-400 font-medium">
                  {{ $t('communicate.speaking') }}
                </span>
              </div>
              
              <!-- User's Text (from selected choices) - Last sentence large, previous 2 smaller -->
              <div class="flex-1 flex flex-col justify-center items-center text-center">
                <div v-if="textLines.length > 0" class="mb-2 space-y-1">
                  <!-- Previous sentences (last 2, excluding the last one) - smaller and lighter -->
                  <div v-if="textLines.length > 1" class="space-y-1 mb-2">
                    <div 
                      v-for="(line, index) in textLines.slice(0, -1).slice(-2)" 
                      :key="`prev-${index}`" 
                      class="break-words text-xl font-normal text-gray-400 dark:text-gray-500"
                    >
                      {{ line }}
                    </div>
                  </div>
                  <!-- Last sentence - large and bold -->
                  <div class="break-words text-4xl font-semibold text-gray-900 dark:text-white">
                    {{ textLines[textLines.length - 1] }}
                  </div>
                </div>
                <div v-else class="text-gray-400 dark:text-gray-500 text-xl italic">
                  {{ $t('communicate.noText') }}
                </div>
              </div>
              
              <!-- Caregiver Transcriptions - Small Font at Bottom -->
              <div v-if="transcriptions.length > 0" class="mt-auto pt-2 border-t border-gray-300 dark:border-gray-600">
                <div class="text-xs text-gray-500 dark:text-gray-400 max-h-16 overflow-y-auto">
                  <div v-for="(transcription, index) in transcriptions.slice(-3)" :key="index" class="mb-1">
                    {{ transcription.text }}
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Cell 6: Middle Right -->
          <div
            v-if="shouldShowCell(6)"
            ref="cell6"
            data-cell="6"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200 relative overflow-hidden',
              getCellClasses(6)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(6))"
          >
            <!-- Progress bar at bottom -->
            <div
              v-if="dwellingCell === 6"
              class="absolute bottom-0 left-0 h-3 bg-blue-500 transition-all duration-75 ease-linear"
              :style="{ width: `${getDwellingProgress(6) * 100}%` }"
            ></div>
            <ChoiceCell :choice="getChoiceForCell(6)" :is-highlighted="isCellHighlighted(6)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 7: Bottom Left -->
          <div
            v-if="shouldShowCell(7)"
            ref="cell7"
            data-cell="7"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200 relative overflow-hidden',
              getCellClasses(7)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(7))"
          >
            <!-- Progress bar at bottom -->
            <div
              v-if="dwellingCell === 7"
              class="absolute bottom-0 left-0 h-3 bg-blue-500 transition-all duration-75 ease-linear"
              :style="{ width: `${getDwellingProgress(7) * 100}%` }"
            ></div>
            <ChoiceCell :choice="getChoiceForCell(7)" :is-highlighted="isCellHighlighted(7)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 8: Bottom Center -->
          <div
            v-if="shouldShowCell(8)"
            ref="cell8"
            data-cell="8"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200 relative overflow-hidden',
              getCellClasses(8)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(8))"
          >
            <!-- Progress bar at bottom -->
            <div
              v-if="dwellingCell === 8"
              class="absolute bottom-0 left-0 h-3 bg-blue-500 transition-all duration-75 ease-linear"
              :style="{ width: `${getDwellingProgress(8) * 100}%` }"
            ></div>
            <ChoiceCell :choice="getChoiceForCell(8)" :is-highlighted="isCellHighlighted(8)" />
          </div>
          <div v-else :style="cellStyle"></div>
          
          <!-- Cell 9: Bottom Right -->
          <div
            v-if="shouldShowCell(9)"
            ref="cell9"
            data-cell="9"
            :class="[
              'border-2 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200 relative overflow-hidden',
              getCellClasses(9)
            ]"
            :style="cellStyle"
            @click="selectChoice(getChoiceForCell(9))"
          >
            <!-- Progress bar at bottom -->
            <div
              v-if="dwellingCell === 9"
              class="absolute bottom-0 left-0 h-3 bg-blue-500 transition-all duration-75 ease-linear"
              :style="{ width: `${getDwellingProgress(9) * 100}%` }"
            ></div>
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
        :is-searching="isSearching"
      />
    </div>

    <!-- Feedback Form Modal -->
    <SessionFeedbackForm
      v-if="showFeedbackForm"
      @submit="submitFeedback"
      @skip="skipFeedback"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, inject, nextTick, type Ref } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { MicrophoneIcon } from '@heroicons/vue/24/solid';
import { useEyeTracking } from '../composables/useEyeTracking';
import { useCalibration } from '../composables/useCalibration';
import { useSTTEvents } from '../composables/useSTTEvents';
import EyeTrackingGaze from '../components/EyeTrackingGaze.vue';
import ChoiceCell from '../components/ChoiceCell.vue';
import SessionFeedbackForm from '../components/SessionFeedbackForm.vue';
import { communicationAPI, configAPI, sessionsAPI, speechToTextAPI, usersAPI } from '../services/api';
import { safeExitFullscreen } from '../utils/fullscreen';
import type { Choice } from '../types/api';

const { t } = useI18n();

// Fullscreen state
const isFullscreen = ref(false);
// Get communication fullscreen state from App.vue to hide sidebar
const isCommunicationFullscreenApp = inject<Ref<boolean>>('isCommunicationFullscreen', ref(false));

// Speech-to-text state
const isActive = ref(false);
const isLoading = ref(false);
const error = ref<string | null>(null);
const successMessage = ref<string | null>(null);
const transcriptions = ref<{ text: string; timestamp: Date }[]>([]);
const currentText = ref('');
const textLines = ref<string[]>([]);
const conversationHistory = ref<{ role: 'user' | 'caregiver'; content: string }[]>([]);
let successTimeout: ReturnType<typeof setTimeout> | null = null;
let fullscreenChangeHandlers: Array<{ event: string; handler: (event: Event) => void }> = [];

const {
  connectionStatus: sttConnectionStatus,
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

// AAC pictogram mode
const aacMode = ref(false);

// Searching state (backend generating choices)
const isSearching = ref(false);

// AbortController for in-flight choices requests
let choicesAbortController: AbortController | null = null;

// Session tracking
const sessionId = ref<number | null>(null);
const stepNumber = ref(0);

// Feedback form
const showFeedbackForm = ref(false);
const pendingFeedbackSessionId = ref<number | null>(null);

// Eye tracking
const { calibrationCoefficients } = useCalibration();
const {
  isConnected: isEyeTrackingConnected,
  gazePoint,
  trackingData,
  calibrationCoefficients: trackingCalibrationCoefficients,
  isFullscreen: trackingIsFullscreen,
  toggleConnection: toggleEyeTrackingConnection,
  updateWindowPosition,
  updateHeaderHeight,
} = useEyeTracking({ 
  skipCalibration: false,
  calibrationCoefficients: calibrationCoefficients.value,
  isFullscreen: isFullscreen
});

// Choices from backend
const choices = ref<Choice[]>([]);
const highlightedCell = ref<number | null>(null);
const cellRefs: Record<string, Ref<HTMLElement | null>> = {
  cell1: ref<HTMLElement | null>(null),
  cell2: ref<HTMLElement | null>(null),
  cell3: ref<HTMLElement | null>(null),
  cell4: ref<HTMLElement | null>(null),
  cell5: ref<HTMLElement | null>(null),
  cell6: ref<HTMLElement | null>(null),
  cell7: ref<HTMLElement | null>(null),
  cell8: ref<HTMLElement | null>(null),
  cell9: ref<HTMLElement | null>(null),
};

// Dwelling state
const dwellTime = ref(2.0); // Default dwell time in seconds
const dwellingCell = ref<number | null>(null); // Currently dwelling cell number
const dwellingStartTime = ref<number | null>(null); // When dwelling started
const dwellingProgress = ref(0); // Progress from 0 to 1
let dwellingInterval: ReturnType<typeof setInterval> | null = null;

// Grid layout and scaling
const gridContainer = ref<HTMLElement | null>(null);
const gridInner = ref<HTMLElement | null>(null);
const displayScaleFactor = ref(1.0);
const gridGap = ref(24); // Gap between cells in pixels (increased from 16)

// Computed styles for grid and cells
const gridContainerStyle = computed(() => {
  // No special styling needed for container
  return {};
});

const gridStyle = computed(() => {
  const gap = gridGap.value;
  if (isFullscreen.value) {
    return {
      gap: `${gap}px`,
      gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
      gridTemplateRows: 'repeat(3, minmax(0, 1fr))',
      width: '100%',
      height: '100%',
    };
  }
  return {
    gap: `${gap}px`,
    aspectRatio: '4 / 3',
  };
});

const cellStyle = computed(() => ({
  minWidth: 0,
  minHeight: 0,
}));

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
  const baseClasses = 'border-4 border-primary-400 dark:border-primary-500 bg-white dark:bg-gray-700 hover:bg-primary-50 dark:hover:bg-primary-900/20 hover:border-primary-500 dark:hover:border-primary-400';
  const highlightedClasses = 'border-4 border-primary-600 dark:border-primary-400 bg-primary-100 dark:bg-primary-900/40 ring-4 ring-primary-300 dark:ring-primary-700';
  
  if (isCellHighlighted(cellNumber)) {
    return highlightedClasses;
  }
  return baseClasses;
};

// Get dwelling progress for a cell (0 to 1)
const getDwellingProgress = (cellNumber) => {
  if (dwellingCell.value === cellNumber) {
    return dwellingProgress.value;
  }
  return 0;
};


// Track if we've found cells at least once
let cellsFoundOnce = false;
let cellCheckCounter = 0;

// Check which cell the gaze is pointing at and handle dwelling
const checkGazePosition = () => {
  if (isSearching.value) {
    highlightedCell.value = null;
    stopDwelling();
    return;
  }

  if (!gazePoint.value || !isEyeTrackingConnected.value) {
    if (highlightedCell.value !== null || dwellingCell.value !== null) {
      highlightedCell.value = null;
      stopDwelling();
    }
    return;
  }
  
  // Verify grid is rendered
  if (!gridInner.value) {
    return;
  }
  
  const gazeX = gazePoint.value.x;
  const gazeY = gazePoint.value.y;
  
  // Try to get cell element - first try ref, then fallback to DOM query
  const getCellElement = (cellNum) => {
    // Try ref first
    const cellRef = cellRefs[`cell${cellNum}`];
    if (cellRef?.value) {
      return cellRef.value;
    }
    
    // Fallback: query DOM directly using data attribute or class
    // We'll add a data-cell attribute to make this easier
    const grid = gridInner.value;
    if (grid) {
      const cellElement = grid.querySelector<HTMLElement>(`[data-cell="${cellNum}"]`);
      if (cellElement) {
        return cellElement;
      }
    }
    
    return null;
  };
  
  // Check if we have any cells available
  let hasAnyCells = false;
  let cellsFound = 0;
  
  for (let cellNum = 1; cellNum <= 9; cellNum++) {
    if (cellNum === 5) continue;
    if (shouldShowCell(cellNum)) {
      const cellElement = getCellElement(cellNum);
      if (cellElement) {
        const rect = cellElement.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          hasAnyCells = true;
          cellsFound++;
        }
      }
    }
  }
  
  // Log when cells are first found
  if (hasAnyCells && !cellsFoundOnce) {
    console.log(`[Dwelling Debug] Cells are now available! Found ${cellsFound} cells`);
    cellsFoundOnce = true;
  }
  
  // If no cells available, can't check gaze
  if (!hasAnyCells) {
    return;
  }
  
  // Check each cell
  for (let cellNum = 1; cellNum <= 9; cellNum++) {
    if (cellNum === 5) continue; // Skip center cell
    
    // Skip if cell shouldn't be shown
    if (!shouldShowCell(cellNum)) {
      continue;
    }
    
    const cellElement = getCellElement(cellNum);
    if (!cellElement) {
      continue;
    }
    
    const rect = cellElement.getBoundingClientRect();
    
    // Skip if rect has zero dimensions (cell not visible)
    if (rect.width === 0 || rect.height === 0) {
      continue;
    }
    
    // gazePoint is in window coordinates, rect is also in window coordinates
    const isInside = (
      gazeX >= rect.left &&
      gazeX <= rect.right &&
      gazeY >= rect.top &&
      gazeY <= rect.bottom
    );
    
    if (isInside) {
      // Update highlighted cell
      if (highlightedCell.value !== cellNum) {
        console.log(`[Dwelling Debug] Gaze entered cell ${cellNum} at (${gazeX.toFixed(1)}, ${gazeY.toFixed(1)}), rect: (${rect.left.toFixed(1)}, ${rect.top.toFixed(1)}) to (${rect.right.toFixed(1)}, ${rect.bottom.toFixed(1)})`);
        highlightedCell.value = cellNum;
      }
      
      // Start or continue dwelling
      if (dwellingCell.value !== cellNum) {
        console.log(`[Dwelling Debug] Starting dwelling on cell ${cellNum}`);
        startDwelling(cellNum);
      }
      
      return;
    }
  }
  
  // Gaze is not inside any cell
  if (highlightedCell.value !== null) {
    highlightedCell.value = null;
  }
  stopDwelling();
};

// Start dwelling on a cell
const startDwelling = (cellNum) => {
  // Stop any existing dwelling
  stopDwelling();
  
  dwellingCell.value = cellNum;
  dwellingStartTime.value = Date.now();
  dwellingProgress.value = 0;
  
  console.log(`Starting dwelling on cell ${cellNum}, dwell_time: ${dwellTime.value}s`);
  
  // Update progress every frame (60fps)
  dwellingInterval = setInterval(() => {
    if (!dwellingStartTime.value || dwellingCell.value !== cellNum) {
      stopDwelling();
      return;
    }
    
    const elapsed = (Date.now() - dwellingStartTime.value) / 1000; // seconds
    const progress = Math.min(elapsed / dwellTime.value, 1.0);
    dwellingProgress.value = progress;
    
    // If dwelling is complete, trigger click
    if (progress >= 1.0) {
      console.log(`Dwelling complete on cell ${cellNum}, selecting choice`);
      const choice = getChoiceForCell(cellNum);
      if (choice) {
        const actualDwellMs = Math.round(dwellTime.value * 1000);
        selectChoice(choice, 'gaze_dwell', actualDwellMs);
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
  dwellingCell.value = null;
  dwellingStartTime.value = null;
  dwellingProgress.value = 0;
};

// Watch gaze point to update highlighted cell
watch(gazePoint, (newGazePoint) => {
  if (newGazePoint && isEyeTrackingConnected.value) {
    checkGazePosition();
  }
}, { immediate: true });

// Also watch connection state
watch(isEyeTrackingConnected, (connected) => {
  console.log('Eye tracking connection changed:', connected);
  if (connected && gazePoint.value) {
    checkGazePosition();
  } else {
    highlightedCell.value = null;
    stopDwelling();
  }
}, { immediate: true });

// Track if we've logged cell availability
let cellsAvailabilityLogged = false;

// Watch for choices to be loaded
watch(choices, async (newChoices) => {
  console.log(`[Dwelling Debug] Choices loaded: ${newChoices.length} choices`);
  cellsFoundOnce = false; // Reset when choices change
  cellCheckCounter = 0; // Reset counter
  
  // Wait for DOM to update, then verify cells
  await nextTick();
  setTimeout(() => {
    // Force a gaze check to see if cells are available now
    if (isEyeTrackingConnected.value && gazePoint.value) {
      checkGazePosition();
    }
  }, 200);
}, { immediate: true });

// Load choices from backend
const loadChoices = async () => {
  if (!isActive.value) return;

  // Cancel any previous in-flight request
  if (choicesAbortController) {
    choicesAbortController.abort();
  }
  choicesAbortController = new AbortController();
  const { signal } = choicesAbortController;

  isSearching.value = true;
  stopDwelling();
  try {
    const userIdValue = localStorage.getItem('selectedUserId');
    const caregiverIdValue = localStorage.getItem('selectedCaregiverId');
    const userId = userIdValue ? Number.parseInt(userIdValue, 10) : null;
    const caregiverId = caregiverIdValue ? Number.parseInt(caregiverIdValue, 10) : null;
    
    if (sessionId.value) {
      stepNumber.value += 1;
    }
    
    const response = await communicationAPI.getChoices({
      conversationHistory: conversationHistory.value,
      userId,
      caregiverId,
      currentText: currentText.value || null,
      sessionId: sessionId.value,
      stepNumber: sessionId.value ? stepNumber.value : null,
      aacMode: aacMode.value,
      signal,
    });

    if (signal.aborted) return;
    choices.value = response.choices || [];
  } catch (err) {
    if (axios.isCancel(err) || (err instanceof DOMException && err.name === 'AbortError')) return;
    console.error('Error loading choices:', err);
    choices.value = [];
  } finally {
    if (!signal.aborted) {
      isSearching.value = false;
    }
  }
};

// Play audio from base64 data
const playAudio = async (audioBase64) => {
  if (!audioBase64) {
    console.warn('playAudio called with empty audioBase64');
    return;
  }
  
  console.log('playAudio called, base64 length:', audioBase64.length);
  
  // Store original STT state
  const wasSTTActive = isActive.value;
  
  // Pause STT if it's active to prevent feedback loop
  if (wasSTTActive) {
    console.log('Pausing STT during TTS playback');
    try {
      await speechToTextAPI.stop();
      // Don't update isActive.value here - we'll restore it after playback
    } catch (err) {
      console.error('Error stopping STT for TTS playback:', err);
    }
  }
  
  try {
    // Convert base64 to blob
    const audioData = atob(audioBase64);
    const arrayBuffer = new ArrayBuffer(audioData.length);
    const uint8Array = new Uint8Array(arrayBuffer);
    for (let i = 0; i < audioData.length; i++) {
      uint8Array[i] = audioData.charCodeAt(i);
    }
    
    console.log('Audio data converted, first bytes:', Array.from(uint8Array.slice(0, 10)));
    
    // Detect audio format - ElevenLabs returns MP3, pyttsx3 returns WAV
    // Check first few bytes to determine format
    let mimeType = 'audio/mpeg'; // Default to MP3 (ElevenLabs)
    if (uint8Array[0] === 0x52 && uint8Array[1] === 0x49 && uint8Array[2] === 0x46 && uint8Array[3] === 0x46) {
      // RIFF header indicates WAV format
      mimeType = 'audio/wav';
      console.log('Detected WAV format');
    } else if (uint8Array[0] === 0xFF && (uint8Array[1] === 0xFB || uint8Array[1] === 0xF3)) {
      // MP3 header
      mimeType = 'audio/mpeg';
      console.log('Detected MP3 format');
    } else {
      console.log('Unknown format, defaulting to MP3. First bytes:', Array.from(uint8Array.slice(0, 4)).map(b => '0x' + b.toString(16)));
    }
    
    // Create audio blob and play
    const blob = new Blob([arrayBuffer], { type: mimeType });
    const audioUrl = URL.createObjectURL(blob);
    console.log('Created blob URL:', audioUrl, 'size:', blob.size, 'type:', mimeType);
    
    const audio = new Audio(audioUrl);
    
    // Set volume to ensure it's audible
    audio.volume = 1.0;
    
    audio.addEventListener('canplaythrough', () => {
      console.log('Audio can play through');
    });
    
    audio.addEventListener('loadeddata', () => {
      console.log('Audio data loaded');
    });
    
    audio.addEventListener('loadstart', () => {
      console.log('Audio loading started');
    });
    
    audio.addEventListener('error', (e) => {
      console.error('Audio playback error:', e);
      console.error('Audio error details:', {
        code: audio.error?.code,
        message: audio.error?.message,
        MEDIA_ERR_ABORTED: 1,
        MEDIA_ERR_NETWORK: 2,
        MEDIA_ERR_DECODE: 3,
        MEDIA_ERR_SRC_NOT_SUPPORTED: 4
      });
      // Resume STT even if audio fails
      if (wasSTTActive) {
        resumeSTT();
      }
    });
    
    // Resume STT after audio finishes playing
    audio.addEventListener('ended', async () => {
      console.log('Audio playback ended');
      URL.revokeObjectURL(audioUrl);
      
      // Resume STT if it was active before
      if (wasSTTActive) {
        await resumeSTT();
      }
    });
    
    // Try to play audio
    const playPromise = audio.play();
    if (playPromise !== undefined) {
      playPromise.then(() => {
        console.log('Audio playback started successfully');
      }).catch(err => {
        console.error('Error playing audio (playPromise rejected):', err);
        // Resume STT if playback fails
        if (wasSTTActive) {
          resumeSTT();
        }
        // Try to play again after user interaction
        console.log('Attempting to play audio after user interaction...');
        document.addEventListener('click', () => {
          audio.play().catch(e => console.error('Still cannot play audio:', e));
        }, { once: true });
      });
    }
  } catch (err) {
    console.error('Error processing audio:', err);
    // Resume STT if there's an error
    if (wasSTTActive) {
      resumeSTT();
    }
  }
};

// Resume STT after TTS playback
const resumeSTT = async () => {
  console.log('Resuming STT after TTS playback');
  try {
    await speechToTextAPI.start();
    isActive.value = true;
    connectSTT();
  } catch (err) {
    console.error('Error resuming STT:', err);
    error.value = 'Failed to resume speech-to-text';
  }
};

// Select a choice
const selectChoice = async (choice, activationMode: 'click' | 'gaze_dwell' = 'click', dwellTimeMs: number | null = null) => {
  if (!choice || !isActive.value) return;
  
  try {
    // Add choice text to current text
    if (choice.text) {
      const choiceText = choice.text.trim();
      const isSingleWord = choiceText.split(/\s+/).length === 1;
      
      if (isSingleWord) {
        if (textLines.value.length > 0) {
          const lastLine = textLines.value[textLines.value.length - 1];
          textLines.value[textLines.value.length - 1] = (lastLine + ' ' + choiceText).trim();
        } else {
          textLines.value.push(choiceText);
        }
      } else {
        textLines.value.push(choiceText);
        if (textLines.value.length > 4) {
          textLines.value = textLines.value.slice(-4);
        }
      }
      
      currentText.value = textLines.value.join(' ');
      
      conversationHistory.value.push({
        role: 'user',
        content: choice.text
      });
    }
    
    const response = await communicationAPI.selectChoice({
      choice_id: choice.id,
      choice_text: choice.text,
      current_text: currentText.value,
      session_id: sessionId.value,
      step_number: sessionId.value ? stepNumber.value : null,
      activation_mode: activationMode,
      dwell_time_ms: dwellTimeMs,
    });
    
    // Audio is played in the backend, so we don't need to play it here
    console.log('Response from select_choice:', response);
    
    if (!isActive.value) return;
    await loadChoices();
  } catch (err) {
    console.error('Error selecting choice:', err);
  }
};

onSTTEvent('transcription', (event) => {
  if (!isActive.value) return;
  const transcribedText = event.data.text.trim();
  conversationHistory.value.push({
    role: 'caregiver',
    content: transcribedText,
  });
  transcriptions.value.push({
    text: transcribedText,
    timestamp: new Date(event.timestamp),
  });
  loadChoices();
});

onSTTEvent('error', (event) => {
  error.value = event.data.error;
});

const loadStatus = async () => {
  try {
    const response = await speechToTextAPI.status();
    isActive.value = response.is_active;
    if (isActive.value) {
      connectSTT();
    }
  } catch (err) {
    console.error('Error loading status:', err);
  }
};

const enterFullscreen = async () => {
  try {
    const element = document.documentElement as HTMLElement & {
      webkitRequestFullscreen?: () => Promise<void>
      msRequestFullscreen?: () => Promise<void>
    };
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
  void safeExitFullscreen();
  isFullscreen.value = false;
};

const handleFullscreenChange = () => {
  const doc = document as Document & {
    webkitFullscreenElement?: Element | null
    msFullscreenElement?: Element | null
  };
  if (!doc.fullscreenElement && !doc.webkitFullscreenElement && !doc.msFullscreenElement) {
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
    // Get user and caregiver IDs from localStorage
    const userIdValue = localStorage.getItem('selectedUserId');
    const caregiverIdValue = localStorage.getItem('selectedCaregiverId');
    const userId = userIdValue ? Number.parseInt(userIdValue, 10) : null;
    const caregiverId = caregiverIdValue ? Number.parseInt(caregiverIdValue, 10) : null;
    
    // Create a new communication session with context
    try {
      let prompt: string | null = null;
      let llmModel: string | null = null;
      let temperature: number | null = null;
      let userNotes: string | null = null;
      try {
        const cfg = await configAPI.get() as Record<string, unknown>;
        prompt = (cfg.communicate_prompt as string) || null;
        llmModel = (cfg.model as string) || null;
        temperature = (cfg.temperature as number) ?? null;
      } catch { /* config fetch optional */ }
      if (userId) {
        try {
          const user = await usersAPI.get(userId) as Record<string, unknown>;
          userNotes = (user.notes as string) || null;
        } catch { /* user fetch optional */ }
      }
      const sessionResponse = await sessionsAPI.create({
        user_id: userId,
        caregiver_id: caregiverId,
        prompt,
        llm_model: llmModel,
        temperature,
        user_notes: userNotes,
      });
      sessionId.value = (sessionResponse as { id?: number }).id ?? null;
      stepNumber.value = 0;
      console.log('Created session:', sessionId.value);
    } catch (sessionErr) {
      console.error('Error creating session:', sessionErr);
    }
    
    // Start speech-to-text
    await speechToTextAPI.start();
    isActive.value = true;
    connectSTT();
    
    // Set fullscreen state in App.vue to hide sidebar
    isCommunicationFullscreenApp.value = true;
    
    // Enter fullscreen mode
    await enterFullscreen();
    
    // If conversation is empty, initialize with LLM choices
    if (conversationHistory.value.length === 0) {
      console.log('Conversation is empty, initializing with LLM choices');
      await loadChoices();
    }
    
    successMessage.value = t('communicate.started');
  } catch (err) {
    console.error('Error starting communication:', err);
    error.value = t('communicate.error');
    isActive.value = false;
    disconnectSTT();
    isCommunicationFullscreenApp.value = false;
  } finally {
    isLoading.value = false;
  }
};

const stopCommunication = async () => {
  isLoading.value = true;
  error.value = null;
  successMessage.value = null;
  
  // Cancel any in-flight choices request first
  if (choicesAbortController) {
    choicesAbortController.abort();
    choicesAbortController = null;
  }
  isSearching.value = false;

  try {
    // Stop dwelling if active
    stopDwelling();
    highlightedCell.value = null;
    
    // Stop speech-to-text
    await speechToTextAPI.stop();
    isActive.value = false;
    disconnectSTT();
    
    // End the session if it exists
    if (sessionId.value) {
      const endedSessionId = sessionId.value;
      try {
        await sessionsAPI.update(endedSessionId, {
          ended_at: new Date().toISOString(),
        });
        console.log('Ended session:', endedSessionId);
      } catch (sessionErr) {
        console.error('Error ending session:', sessionErr);
      }
      sessionId.value = null;
      stepNumber.value = 0;

      // Reset fullscreen/sidebar before showing feedback
      isCommunicationFullscreenApp.value = false;
      exitFullscreen();

      // Reset display
      textLines.value = [];
      currentText.value = '';
      transcriptions.value = [];
      conversationHistory.value = [];
      choices.value = [];

      // Show feedback form
      pendingFeedbackSessionId.value = endedSessionId;
      showFeedbackForm.value = true;
      successMessage.value = t('communicate.stopped');
    } else {
      // No session, just reset
      textLines.value = [];
      currentText.value = '';
      transcriptions.value = [];
      conversationHistory.value = [];
      choices.value = [];
      isCommunicationFullscreenApp.value = false;
      exitFullscreen();
      successMessage.value = t('communicate.stopped');
    }
  } catch (err) {
    console.error('Error stopping communication:', err);
    error.value = t('communicate.error');
    isCommunicationFullscreenApp.value = false;
    exitFullscreen();
  } finally {
    isLoading.value = false;
  }
};

const submitFeedback = async (feedback: Record<string, unknown>) => {
  if (pendingFeedbackSessionId.value) {
    try {
      await sessionsAPI.update(pendingFeedbackSessionId.value, { feedback });
    } catch (err) {
      console.error('Error saving feedback:', err);
    }
  }
  showFeedbackForm.value = false;
  pendingFeedbackSessionId.value = null;
};

const skipFeedback = () => {
  showFeedbackForm.value = false;
  pendingFeedbackSessionId.value = null;
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
// Update calibration coefficients in eye tracking when they change
watch(calibrationCoefficients, (newCoefficients) => {
  if (trackingCalibrationCoefficients) {
    trackingCalibrationCoefficients.value = newCoefficients;
  }
}, { immediate: true });

// Update fullscreen state in eye tracking when it changes
watch(isFullscreen, (newIsFullscreen) => {
  if (trackingIsFullscreen) {
    trackingIsFullscreen.value = newIsFullscreen;
  }
}, { immediate: true });

let gazeCheckInterval: ReturnType<typeof setInterval> | null = null;
let positionInterval: ReturnType<typeof setInterval> | null = null;
let resizeHandler: (() => void) | null = null;

// Load display scale factor
const loadDisplayScaleFactor = async () => {
  try {
    displayScaleFactor.value = window.devicePixelRatio || 1.0;
    console.log('Display scale factor:', displayScaleFactor.value);
  } catch (err) {
    console.error('Error getting display scale factor:', err);
    displayScaleFactor.value = window.devicePixelRatio || 1.0;
  }
};

// Load configuration to get dwell_time
const loadConfig = async () => {
  try {
    const data = (await configAPI.get()) as {
      eye_tracking?: { dwell_time?: number }
    };
    if (data.eye_tracking?.dwell_time) {
      dwellTime.value = data.eye_tracking.dwell_time;
      console.log('Loaded dwell_time:', dwellTime.value);
    }
  } catch (err) {
    console.error('Error loading config:', err);
    // Use default dwell_time
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
  // Don't load choices on mount - wait for first transcription
  loadDisplayScaleFactor();
  loadConfig();
  
  // Initialize eye tracking offsets (important for correct gaze coordinates)
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
  if (resizeHandler) {
    window.addEventListener('resize', resizeHandler);
  }
  
  // Start gaze check immediately - it will handle missing refs gracefully
  // Check gaze position periodically
  gazeCheckInterval = setInterval(() => {
    if (isEyeTrackingConnected.value && gazePoint.value) {
      checkGazePosition();
    }
  }, 50); // Check every 50ms for smoother dwelling
  
  console.log('[Dwelling Debug] Gaze check interval started');
  
  // Also verify cells after a delay (for debugging)
  setTimeout(() => {
    let cellsAvailable = 0;
    for (let cellNum = 1; cellNum <= 9; cellNum++) {
      if (cellNum === 5) continue;
      if (shouldShowCell(cellNum)) {
        const cellRef = cellRefs[`cell${cellNum}`];
        if (cellRef?.value) {
          const rect = cellRef.value.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) {
            cellsAvailable++;
          }
        }
      }
    }
    console.log(`[Dwelling Debug] Cells available: ${cellsAvailable} (choices: ${choices.value.length})`);
  }, 1000);
  
  // Listen for window resize to update grid
  window.addEventListener('resize', updateGridSize);
  
  // Listen for fullscreen changes
  const handleFullscreenChange = () => {
    const doc = document as Document & {
      webkitFullscreenElement?: Element | null
      msFullscreenElement?: Element | null
    };
    if (!doc.fullscreenElement && !doc.webkitFullscreenElement && !doc.msFullscreenElement) {
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
  // Cancel any in-flight choices request
  if (choicesAbortController) {
    choicesAbortController.abort();
    choicesAbortController = null;
  }

  // Stop dwelling
  stopDwelling();
  
  // Clean up position tracking
  if (positionInterval) {
    clearInterval(positionInterval);
  }
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler);
  }
  
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
  
  disconnectSTT();
  if (successTimeout) {
    clearTimeout(successTimeout);
  }
  if (gazeCheckInterval) {
    clearInterval(gazeCheckInterval);
  }
});
</script>

