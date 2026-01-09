<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 relative overflow-hidden">
    <!-- Header (hidden during calibration) -->
    <header 
      v-if="!isCalibrating && !calibrationComplete"
      class="bg-white dark:bg-gray-800 shadow-lg z-10 relative border-b border-gray-200 dark:border-gray-700"
    >
      <div class="px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ $t('calibration.title') }}</h1>
          <div v-if="selectedUser" class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('calibration.user') }}: {{ selectedUser.name }}
          </div>
        </div>
      </div>
    </header>

    <!-- Calibration Area -->
    <div :class="['relative w-full', isCalibrating || calibrationComplete ? 'h-screen' : 'h-[calc(100vh-80px)]']">
      <!-- Start Button (Initial State) -->
      <div
        v-if="!isCalibrating && !calibrationComplete"
        class="absolute inset-0 flex items-center justify-center"
      >
        <button
          @click="startCalibration"
          :disabled="!isConnected || !selectedUser"
          :class="[
            'px-12 py-6 rounded-xl font-semibold text-xl transition-all duration-200',
            !isConnected || !selectedUser
              ? 'bg-gray-400 dark:bg-gray-600 text-gray-200 cursor-not-allowed'
              : 'bg-primary-600 hover:bg-primary-700 text-white shadow-lg hover:shadow-xl'
          ]"
        >
          {{ $t('calibration.start') }}
        </button>
        <div v-if="!isConnected" class="absolute top-1/2 left-1/2 -translate-x-1/2 translate-y-20 text-red-600 dark:text-red-400 text-sm">
          {{ $t('calibration.notConnected') }}
        </div>
        <div v-if="!selectedUser" class="absolute top-1/2 left-1/2 -translate-x-1/2 translate-y-20 text-red-600 dark:text-red-400 text-sm">
          {{ $t('calibration.noUserSelected') }}
        </div>
      </div>

      <!-- Calibration Circle -->
      <div
        v-if="isCalibrating && currentPosition !== null"
        :style="{
          left: `${calibrationPositions[currentPosition].x}px`,
          top: `${calibrationPositions[currentPosition].y}px`,
        }"
        class="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none z-50"
      >
        <!-- Shrinking Circle -->
        <div
          :style="{
            width: `${circleSize}px`,
            height: `${circleSize}px`,
            borderRadius: '50%',
            border: '4px solid',
            borderColor: circleColor,
            backgroundColor: 'transparent',
            transition: 'width 0.1s linear, height 0.1s linear',
          }"
          class="absolute -translate-x-1/2 -translate-y-1/2"
        ></div>
        
        <!-- Center Dot -->
        <div
          class="absolute -translate-x-1/2 -translate-y-1/2 w-4 h-4 rounded-full"
          :style="{ backgroundColor: circleColor }"
        ></div>
      </div>


      <!-- Calibration Quality Check Visualization -->
      <div
        v-if="calibrationComplete && processedCalibrationData"
        class="absolute inset-0 bg-gray-50 dark:bg-gray-900 overflow-auto"
      >
        <!-- Quality Check Visualization -->
        <div class="relative w-full h-full">
          <!-- Draw crosses and samples for each calibration point -->
          <template v-for="(point, index) in processedCalibrationData.points" :key="index">
            <!-- Target Position Cross (100px lines) -->
            <div
              :style="{
                left: `${point.targetX}px`,
                top: `${point.targetY}px`,
              }"
              class="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none z-20"
            >
              <!-- Horizontal line (100px) -->
              <div
                class="absolute -translate-x-1/2 -translate-y-1/2 w-[100px] h-[2px] bg-blue-500 dark:bg-blue-400"
                style="left: 50%; top: 50%;"
              ></div>
              <!-- Vertical line (100px) -->
              <div
                class="absolute -translate-x-1/2 -translate-y-1/2 w-[2px] h-[100px] bg-blue-500 dark:bg-blue-400"
                style="left: 50%; top: 50%;"
              ></div>
              <!-- Center dot -->
              <div
                class="absolute -translate-x-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-blue-600 dark:bg-blue-500 border-2 border-white dark:border-gray-900"
                style="left: 50%; top: 50%;"
              ></div>
            </div>
            
            <!-- Gaze Samples (small circles) -->
            <template v-if="calibrationData[index] && calibrationData[index].samplesData">
              <div
                v-for="(sample, sampleIndex) in calibrationData[index].samplesData"
                :key="`sample-${index}-${sampleIndex}`"
                :style="{
                  left: `${sample.x}px`,
                  top: `${sample.y}px`,
                }"
                class="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none z-10"
              >
                <div
                  class="w-2 h-2 rounded-full bg-red-500 dark:bg-red-400 opacity-60"
                ></div>
              </div>
            </template>
            
            <!-- Average Gaze Position (larger circle) - calculated from samples using geometric median -->
            <div
              v-if="calibrationData[index] && calibrationData[index].samplesData && calibrationData[index].samplesData.length > 0"
              :style="{
                left: `${getRobustAverageGaze(calibrationData[index].samplesData).x}px`,
                top: `${getRobustAverageGaze(calibrationData[index].samplesData).y}px`,
              }"
              class="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none z-30"
            >
              <div
                class="w-4 h-4 rounded-full bg-green-500 dark:bg-green-400 border-2 border-white dark:border-gray-900 opacity-80"
              ></div>
            </div>
          </template>
        </div>
        
        <!-- Action Buttons -->
        <div class="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 flex gap-4">
          <button
            @click="validateCalibration"
            class="px-8 py-4 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold text-lg shadow-lg transition-colors"
          >
            {{ $t('calibration.validate') }}
          </button>
          <button
            @click="resetCalibration"
            class="px-8 py-4 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-semibold text-lg shadow-lg transition-colors"
          >
            {{ $t('calibration.restart') }}
          </button>
        </div>
        
        <!-- Info Panel -->
        <div class="absolute top-8 right-8 bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-xs border border-gray-200 dark:border-gray-700 z-20">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {{ $t('calibration.qualityCheck') }}
          </h3>
          <div class="space-y-2 text-sm">
            <div class="flex items-center space-x-2">
              <div class="w-4 h-4 border-2 border-blue-500 dark:border-blue-400"></div>
              <span class="text-gray-700 dark:text-gray-300">{{ $t('calibration.targetPosition') }}</span>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-2 h-2 rounded-full bg-red-500 dark:bg-red-400"></div>
              <span class="text-gray-700 dark:text-gray-300">{{ $t('calibration.gazeSamples') }}</span>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-4 h-4 rounded-full bg-green-500 dark:bg-green-400"></div>
              <span class="text-gray-700 dark:text-gray-300">{{ $t('calibration.averageGaze') }}</span>
            </div>
          </div>
          <div v-if="processedCalibrationData.affine_coefficients" class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <p class="text-xs text-gray-600 dark:text-gray-400 mb-2">{{ $t('calibration.calibrationApplied') }}</p>
            <p class="text-xs font-mono text-gray-700 dark:text-gray-300">
              {{ $t('calibration.coefficientsSaved') }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, inject } from 'vue';
import { useEyeTracking } from '../composables/useEyeTracking';
import { usersAPI, calibrationAPI } from '../services/api';
import { CheckIcon } from '@heroicons/vue/24/outline';
import { useI18n } from 'vue-i18n';
import { geometricMedian, coordinateWiseMedian } from '../utils/statistics';

const { t } = useI18n();

// Get calibration state from App.vue to hide sidebar
const isCalibratingApp = inject('isCalibrating', ref(false));

// Eye tracking - skip calibration transformation during calibration
const {
  isConnected,
  gazePoint,
  trackingData,
  skipCalibration,
} = useEyeTracking({ skipCalibration: true });

// Calibration state
const isCalibrating = ref(false);
const calibrationComplete = ref(false);
const currentPosition = ref(null);
const circleSize = ref(200); // Starting size in pixels
const circleColor = ref('#3b82f6'); // Primary blue
const calibrationData = ref([]);
const selectedUser = ref(null);
const processedCalibrationData = ref(null); // Store processed calibration response

// Calibration positions (5 points: center, top-left, top-right, bottom-right, bottom-left)
const calibrationPositions = ref([]);

// Gaze collection
const gazeSamples = ref([]);
let gazeCollectionInterval = null;
let circleAnimationInterval = null;

const initializePositions = () => {
  const width = window.innerWidth;
  const height = window.innerHeight;
  // Increased margin from edges (20% of screen dimension) to bring corners more toward center
  const marginX = width * 0.2; // 20% from left/right edges
  const marginY = height * 0.2; // 20% from top/bottom edges
  
  calibrationPositions.value = [
    { x: width / 2, y: height / 2, label: 'center' }, // Center
    { x: marginX, y: marginY, label: 'top-left' }, // Top left
    { x: width - marginX, y: marginY, label: 'top-right' }, // Top right
    { x: width - marginX, y: height - marginY, label: 'bottom-right' }, // Bottom right
    { x: marginX, y: height - marginY, label: 'bottom-left' }, // Bottom left
  ];
};

const startCalibration = async () => {
  if (!isConnected.value || !selectedUser.value) {
    return;
  }
  
  // Set calibration state in App.vue to hide sidebar
  isCalibratingApp.value = true;
  
  // Enter fullscreen mode
  try {
    const element = document.documentElement;
    if (element.requestFullscreen) {
      await element.requestFullscreen();
    } else if (element.webkitRequestFullscreen) {
      await element.webkitRequestFullscreen();
    } else if (element.msRequestFullscreen) {
      await element.msRequestFullscreen();
    }
  } catch (error) {
    console.warn('Could not enter fullscreen mode:', error);
  }
  
  initializePositions();
  isCalibrating.value = true;
  calibrationComplete.value = false;
  currentPosition.value = null;
  calibrationData.value = [];
  circleSize.value = 200;
  
  startCalibrationPoint(0);
};

const startCalibrationPoint = (positionIndex) => {
  if (positionIndex >= calibrationPositions.value.length) {
    finishCalibration();
    return;
  }
  
  currentPosition.value = positionIndex;
  circleSize.value = 200; // Reset circle size
  gazeSamples.value = []; // Clear previous samples
  
  // Start collecting gaze data
  gazeCollectionInterval = setInterval(() => {
    if (gazePoint.value && trackingData.value?.valid) {
      gazeSamples.value.push({
        x: gazePoint.value.x,
        y: gazePoint.value.y,
        screenX: trackingData.value.pixelX,
        screenY: trackingData.value.pixelY,
        timestamp: Date.now(),
      });
    }
  }, 50); // Collect every 50ms (20 samples per second)
  
  // Animate circle shrinking
  const duration = 3000; // 3 seconds per point
  const steps = 30; // 30 steps for smooth animation
  const stepSize = 200 / steps; // Size reduction per step
  const stepDuration = duration / steps;
  
  let step = 0;
  circleAnimationInterval = setInterval(() => {
    step++;
    circleSize.value = 200 - (step * stepSize);
    
    if (step >= steps) {
      // Circle has finished shrinking, save calibration data
      clearInterval(circleAnimationInterval);
      clearInterval(gazeCollectionInterval);
      
      // Store raw calibration data (backend will calculate averages)
      if (gazeSamples.value.length > 0) {
        calibrationData.value.push({
          position: calibrationPositions.value[positionIndex],
          targetX: calibrationPositions.value[positionIndex].x,
          targetY: calibrationPositions.value[positionIndex].y,
          samplesData: gazeSamples.value, // Store all raw samples for backend processing
        });
      }
      
      // Move to next position after a short delay
      setTimeout(() => {
        startCalibrationPoint(positionIndex + 1);
      }, 500);
    }
  }, stepDuration);
};

const finishCalibration = async () => {
  isCalibrating.value = false;
  calibrationComplete.value = true;
  
  // Send calibration data to backend for processing
  if (selectedUser.value && calibrationData.value.length > 0) {
    try {
      // Prepare data with raw samples for backend processing
      const calibrationRequest = {
        user_id: selectedUser.value.id,
        timestamp: Date.now(),
        points: calibrationData.value.map(point => ({
          position: point.position,
          targetX: point.targetX,
          targetY: point.targetY,
          samples: point.samplesData, // Send all raw samples
        })),
      };
      
      // Send to backend for processing
      const response = await calibrationAPI.process(calibrationRequest);
      
      console.log('Calibration processed and saved:', response);
      
      // Store processed data for quality check visualization
      processedCalibrationData.value = response;
    } catch (error) {
      console.error('Error processing calibration data:', error);
      // Show error to user
      alert('Error saving calibration data. Please try again.');
    }
  }
};

const validateCalibration = () => {
  // Calibration is already saved, just navigate away or show success
  // Re-enable calibration transformation after calibration
  if (skipCalibration) {
    skipCalibration.value = false;
  }
  
  // Reset calibration state in App.vue to show sidebar
  isCalibratingApp.value = false;
  
  // Exit fullscreen mode
  exitFullscreen();
  
  isCalibrating.value = false;
  calibrationComplete.value = false;
  currentPosition.value = null;
  calibrationData.value = [];
  processedCalibrationData.value = null;
  circleSize.value = 200;
  
  if (gazeCollectionInterval) {
    clearInterval(gazeCollectionInterval);
  }
  if (circleAnimationInterval) {
    clearInterval(circleAnimationInterval);
  }
  
  // Optionally navigate to home or show success message
  // router.push('/');
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
  } catch (error) {
    console.warn('Could not exit fullscreen mode:', error);
  }
};

const resetCalibration = () => {
  isCalibrating.value = false;
  calibrationComplete.value = false;
  currentPosition.value = null;
  calibrationData.value = [];
  processedCalibrationData.value = null;
  circleSize.value = 200;
  
  // Re-enable calibration transformation after calibration
  if (skipCalibration) {
    skipCalibration.value = false;
  }
  
  // Reset calibration state in App.vue to show sidebar
  isCalibratingApp.value = false;
  
  // Exit fullscreen mode
  exitFullscreen();
  
  if (gazeCollectionInterval) {
    clearInterval(gazeCollectionInterval);
  }
  if (circleAnimationInterval) {
    clearInterval(circleAnimationInterval);
  }
};

const loadSelectedUser = async () => {
  const savedUserId = localStorage.getItem('selectedUserId');
  if (savedUserId) {
    try {
      const userId = parseInt(savedUserId);
      selectedUser.value = await usersAPI.get(userId);
    } catch (error) {
      console.error('Error loading selected user:', error);
    }
  }
};

/**
 * Calculate robust average gaze position using geometric median
 * Falls back to coordinate-wise median if geometric median fails
 */
const getRobustAverageGaze = (samples) => {
  if (!samples || samples.length === 0) {
    return { x: 0, y: 0 };
  }
  
  try {
    // Try geometric median first (most robust to outliers)
    return geometricMedian(samples.map(s => ({ x: s.x, y: s.y })));
  } catch (error) {
    console.warn('Error calculating geometric median, using coordinate-wise median:', error);
    // Fallback to coordinate-wise median
    return coordinateWiseMedian(samples.map(s => ({ x: s.x, y: s.y })));
  }
};

// Fullscreen change handlers
let fullscreenChangeHandlers = [];

onMounted(() => {
  initializePositions();
  loadSelectedUser();
  
  const handleFullscreenChange = () => {
    // If user exits fullscreen manually (ESC key), reset calibration state
    if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
      if (isCalibrating.value) {
        resetCalibration();
      }
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
  // Remove fullscreen event listeners
  fullscreenChangeHandlers.forEach(({ event, handler }) => {
    document.removeEventListener(event, handler);
  });
  
  // Exit fullscreen if still in calibration when component unmounts
  exitFullscreen();
  
  // Reset calibration state in App.vue
  isCalibratingApp.value = false;
  
  resetCalibration();
});
</script>
