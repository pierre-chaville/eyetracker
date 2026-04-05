<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 relative overflow-hidden">
    <!-- Header (hidden during calibration) -->
    <header 
      v-if="!isCalibrating"
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
    <div :class="['relative w-full', isCalibrating ? 'h-screen' : 'h-[calc(100vh-80px)]']">
      <!-- Start Button (Initial State) -->
      <div
        v-if="!isCalibrating"
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

      <!-- Post-calibration review: targets, raw gaze dots, spread circles (geometric median ± median distance) -->
      <div
        v-if="calibrationReviewVisible"
        class="fixed inset-0 z-[60] bg-gray-950/92 pointer-events-none"
      >
        <div class="pointer-events-auto absolute top-4 left-0 right-0 text-center px-4 z-[70]">
          <p class="text-white text-lg font-semibold">{{ $t('calibration.reviewTitle') }}</p>
          <p class="text-gray-300 text-sm mt-2 max-w-xl mx-auto">{{ $t('calibration.reviewHint') }}</p>
          <button
            type="button"
            @click="dismissCalibrationReview"
            class="mt-5 px-8 py-3 rounded-xl bg-primary-600 hover:bg-primary-700 text-white font-semibold shadow-lg touch-manipulation"
          >
            {{ $t('calibration.reviewDone') }}
          </button>
        </div>
        <div class="absolute inset-0 pointer-events-none">
          <template v-for="(pair, idx) in calibrationReviewPairs" :key="idx">
            <!-- Raw gaze samples -->
            <div
              v-for="(s, si) in pair.raw.samplesData"
              :key="`s-${idx}-${si}`"
              class="absolute w-2 h-2 rounded-full bg-cyan-400/85 -translate-x-1/2 -translate-y-1/2 z-[10]"
              :style="{ left: `${s.x}px`, top: `${s.y}px` }"
            />
            <!-- Circle: center = geometric median gaze, diameter = 2 × median distance (precision) -->
            <div
              class="absolute rounded-full border-2 border-amber-400/95 bg-amber-400/[0.12] -translate-x-1/2 -translate-y-1/2 z-[20] box-border"
              :style="reviewCircleStyle(pair.processed)"
            />
            <!-- Calibration target: crosshair (circle = median gaze + spread) -->
            <div
              class="absolute z-[30] -translate-x-1/2 -translate-y-1/2 w-0 h-0"
              :style="{ left: `${pair.processed.targetX}px`, top: `${pair.processed.targetY}px` }"
            >
              <div
                class="absolute left-1/2 top-1/2 h-9 w-px -translate-x-1/2 -translate-y-1/2 rounded-full bg-white shadow-[0_0_3px_rgba(0,0,0,0.9)]"
              />
              <div
                class="absolute left-1/2 top-1/2 w-9 h-px -translate-x-1/2 -translate-y-1/2 rounded-full bg-white shadow-[0_0_3px_rgba(0,0,0,0.9)]"
              />
            </div>
          </template>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, inject, type Ref } from 'vue';
import { useEyeTracking } from '../composables/useEyeTracking';
import { usersAPI, calibrationAPI } from '../services/api';
import { useI18n } from 'vue-i18n';
import type { UserRead } from '../types/api';
import type { CalibrationCoefficients } from '../types/tracking';

const { t } = useI18n();

// Get calibration state from App.vue to hide sidebar
const isCalibratingApp = inject<Ref<boolean>>('isCalibrating', ref(false));

interface CalibrationPosition {
  x: number
  y: number
  label: string
}

interface GazeSample {
  x: number
  y: number
  screenX?: number
  screenY?: number
  timestamp: number
}

interface CalibrationPointData {
  position: CalibrationPosition
  targetX: number
  targetY: number
  samplesData: GazeSample[]
}

interface ProcessedCalibrationPoint {
  position: CalibrationPosition
  targetX: number
  targetY: number
  averageGazeX: number
  averageGazeY: number
  gaze_spread_diameter: number
  sampleCount?: number
}

interface ProcessedCalibrationData {
  points: ProcessedCalibrationPoint[]
  affine_coefficients?: CalibrationCoefficients
}

// Eye tracking - skip calibration transformation during calibration
// Also set isFullscreen to true so coordinate conversion matches fullscreen mode
const {
  isConnected,
  gazePoint,
  trackingData,
  skipCalibration,
  isFullscreen: trackingIsFullscreen,
} = useEyeTracking({ skipCalibration: true, initialIsFullscreen: true });

// Calibration state
const isCalibrating = ref(false);
const currentPosition = ref<number | null>(null);
const circleSize = ref(200); // Starting size in pixels
const circleColor = ref('#3b82f6'); // Primary blue
const calibrationData = ref<CalibrationPointData[]>([]);
const selectedUser = ref<UserRead | null>(null);
const processedCalibrationData = ref<ProcessedCalibrationData | null>(null); // Store processed calibration response

/** Fullscreen review after successful process: raw samples + API metrics */
const calibrationReviewVisible = ref(false);
const calibrationReviewRaw = ref<CalibrationPointData[]>([]);
const MIN_REVIEW_CIRCLE_PX = 14;

const calibrationReviewPairs = computed(() => {
  const raw = calibrationReviewRaw.value;
  const procList = processedCalibrationData.value?.points ?? [];
  if (!raw.length || !procList.length) return [];

  // Pair by target + position label — backend may drop points with no valid samples
  return raw
    .map((r) => {
      const processed = procList.find(
        (p) =>
          p.targetX === r.targetX &&
          p.targetY === r.targetY &&
          p.position?.label === r.position.label,
      );
      return processed ? { raw: r, processed } : null;
    })
    .filter(
      (pair): pair is { raw: CalibrationPointData; processed: ProcessedCalibrationPoint } =>
        pair !== null,
    );
});

const reviewCircleStyle = (p: ProcessedCalibrationPoint) => {
  const d = Math.max(p.gaze_spread_diameter ?? 0, MIN_REVIEW_CIRCLE_PX);
  return {
    left: `${p.averageGazeX}px`,
    top: `${p.averageGazeY}px`,
    width: `${d}px`,
    height: `${d}px`,
  };
};

// Calibration positions (5 points: center, top-left, top-right, bottom-right, bottom-left)
const calibrationPositions = ref<CalibrationPosition[]>([]);

// Gaze collection
const gazeSamples = ref<GazeSample[]>([]);
let gazeCollectionInterval: ReturnType<typeof setInterval> | null = null;
let circleAnimationInterval: ReturnType<typeof setInterval> | null = null;

const initializePositions = () => {
  // Use window dimensions (logical pixels) which match the coordinate system of gazePoint
  // The gaze coordinates are already converted to logical window coordinates
  // In fullscreen mode, window.innerWidth/Height should match the viewport
  const width = window.innerWidth;
  const height = window.innerHeight;

  console.log('Window width:', width);
  console.log('Window height:', height);
  console.log('Screen width:', screen.width);
  console.log('Screen height:', screen.height);
  console.log('Device pixel ratio:', window.devicePixelRatio);
  if (trackingData.value) {
    console.log('Tracking data screenWidth:', trackingData.value.screenWidth);
    console.log('Tracking data screenHeight:', trackingData.value.screenHeight);
    console.log('Tracking data pixelX/pixelY available:', trackingData.value.pixelX !== undefined);
  }

  // Increased margin from edges (20% of screen dimension) to bring corners more toward center
  const marginX = width * 0.1; // 20% from left/right edges
  const marginY = height * 0.1; // 20% from top/bottom edges
  
  calibrationPositions.value = [
    { x: width / 2, y: height / 2, label: 'center' }, // Center
    { x: marginX, y: marginY, label: 'top-left' }, // Top left
    { x: width - marginX, y: marginY, label: 'top-right' }, // Top right
    { x: width - marginX, y: height - marginY, label: 'bottom-right' }, // Bottom right
    { x: marginX, y: height - marginY, label: 'bottom-left' }, // Bottom left
  ];
  
  console.log('Calibration positions:', calibrationPositions.value);
  console.log('Expected coordinate system: logical window pixels (matching gazePoint.x/y)');
};

const startCalibration = async () => {
  if (!isConnected.value || !selectedUser.value) {
    return;
  }
  
  // Set calibration state in App.vue to hide sidebar
  isCalibratingApp.value = true;
  
  // Set fullscreen state in eye tracking composable BEFORE entering fullscreen
  // This ensures coordinate conversion uses fullscreen mode
  if (trackingIsFullscreen) {
    trackingIsFullscreen.value = true;
  }
  
  // Enter fullscreen mode and wait for it to complete
  try {
    const element = document.documentElement as HTMLElement & {
      webkitRequestFullscreen?: () => Promise<void>
      msRequestFullscreen?: () => Promise<void>
    };
    let fullscreenPromise: Promise<void> | undefined;
    
    if (element.requestFullscreen) {
      fullscreenPromise = element.requestFullscreen();
    } else if (element.webkitRequestFullscreen) {
      fullscreenPromise = element.webkitRequestFullscreen();
    } else if (element.msRequestFullscreen) {
      fullscreenPromise = element.msRequestFullscreen();
    }
    
    if (fullscreenPromise) {
      await fullscreenPromise;
      
      // Wait for fullscreen change event and then wait for dimensions to update
      await new Promise<void>((resolve) => {
        const checkFullscreen = () => {
          const doc = document as Document & {
            webkitFullscreenElement?: Element | null
            msFullscreenElement?: Element | null
          };
          const isFullscreen = !!(
            doc.fullscreenElement ||
            doc.webkitFullscreenElement ||
            doc.msFullscreenElement
          );
          if (isFullscreen) {
            // Wait for next frame to ensure dimensions are updated
            requestAnimationFrame(() => {
              requestAnimationFrame(() => {
                resolve();
              });
            });
          } else {
            // Retry after a short delay
            setTimeout(checkFullscreen, 50);
          }
        };
        checkFullscreen();
      });
    }
  } catch (error) {
    console.warn('Could not enter fullscreen mode:', error);
  }
  
  // Now initialize positions with correct fullscreen dimensions
  // Wait a bit more to ensure all coordinate systems are aligned
  await new Promise<void>((resolve) => setTimeout(resolve, 100));
  initializePositions();
  isCalibrating.value = true;
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
      if (circleAnimationInterval) {
        if (circleAnimationInterval) {
          clearInterval(circleAnimationInterval);
        }
      }
      if (gazeCollectionInterval) {
        if (gazeCollectionInterval) {
          clearInterval(gazeCollectionInterval);
        }
      }
      
      // Calculate mean of all collected gaze samples for debugging
      if (gazeSamples.value.length > 0) {
        const meanX = gazeSamples.value.reduce((sum, s) => sum + s.x, 0) / gazeSamples.value.length;
        const meanY = gazeSamples.value.reduce((sum, s) => sum + s.y, 0) / gazeSamples.value.length;
        const meanScreenX = gazeSamples.value.reduce((sum, s) => sum + (s.screenX || 0), 0) / gazeSamples.value.length;
        const meanScreenY = gazeSamples.value.reduce((sum, s) => sum + (s.screenY || 0), 0) / gazeSamples.value.length;
        
        const targetX = calibrationPositions.value[positionIndex].x;
        const targetY = calibrationPositions.value[positionIndex].y;
        const offsetX = targetX - meanX;
        const offsetY = targetY - meanY;
        const offsetPercentX = (offsetX / targetX) * 100;
        const offsetPercentY = (offsetY / targetY) * 100;
        
        console.log(`Calibration point ${positionIndex} (${calibrationPositions.value[positionIndex].label}):`, {
          targetPosition: { x: targetX, y: targetY },
          meanGazePoint: { x: meanX.toFixed(2), y: meanY.toFixed(2) },
          meanScreenCoords: { 
            pixelX: meanScreenX.toFixed(2), 
            pixelY: meanScreenY.toFixed(2) 
          },
          offset: { 
            x: offsetX.toFixed(2), 
            y: offsetY.toFixed(2),
            xPercent: offsetPercentX.toFixed(2) + '%',
            yPercent: offsetPercentY.toFixed(2) + '%'
          },
          sampleCount: gazeSamples.value.length,
          trackingData: trackingData.value ? {
            screenWidth: trackingData.value.screenWidth,
            screenHeight: trackingData.value.screenHeight
          } : null
        });
        
        // Store raw calibration data (backend will calculate averages)
        calibrationData.value.push({
          position: calibrationPositions.value[positionIndex],
          targetX: targetX,
          targetY: targetY,
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
  currentPosition.value = null;

  if (selectedUser.value && calibrationData.value.length > 0) {
    try {
      const calibrationRequest = {
        user_id: selectedUser.value.id,
        timestamp: Date.now(),
        points: calibrationData.value.map(point => ({
          position: point.position,
          targetX: point.targetX,
          targetY: point.targetY,
          samples: point.samplesData,
        })),
      };

      const response = await calibrationAPI.process(calibrationRequest);
      console.log('Calibration processed and saved:', response);
      const data = response as unknown as ProcessedCalibrationData;
      processedCalibrationData.value = data;

      if (data.points?.length) {
        calibrationReviewRaw.value = calibrationData.value.map(p => ({
          ...p,
          samplesData: [...p.samplesData],
        }));
        calibrationData.value = [];
        calibrationReviewVisible.value = true;
        return;
      }
    } catch (error) {
      console.error('Error processing calibration data:', error);
      alert('Error saving calibration data. Please try again.');
    }
  }

  validateCalibration();
};

const dismissCalibrationReview = () => {
  calibrationReviewVisible.value = false;
  calibrationReviewRaw.value = [];
  validateCalibration();
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
  currentPosition.value = null;
  calibrationData.value = [];
  calibrationReviewVisible.value = false;
  calibrationReviewRaw.value = [];
  processedCalibrationData.value = null;
  circleSize.value = 200;
  
  if (gazeCollectionInterval) {
    if (gazeCollectionInterval) {
      clearInterval(gazeCollectionInterval);
    }
  }
  if (circleAnimationInterval) {
    if (circleAnimationInterval) {
      clearInterval(circleAnimationInterval);
    }
  }
  
  // Optionally navigate to home or show success message
  // router.push('/');
};

const exitFullscreen = () => {
  try {
    const doc = document as Document & {
      webkitExitFullscreen?: () => Promise<void>
      msExitFullscreen?: () => Promise<void>
    };
    if (doc.exitFullscreen) {
      doc.exitFullscreen();
    } else if (doc.webkitExitFullscreen) {
      doc.webkitExitFullscreen();
    } else if (doc.msExitFullscreen) {
      doc.msExitFullscreen();
    }
  } catch (error) {
    console.warn('Could not exit fullscreen mode:', error);
  }
};

const resetCalibration = () => {
  isCalibrating.value = false;
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
    if (gazeCollectionInterval) {
      clearInterval(gazeCollectionInterval);
    }
  }
  if (circleAnimationInterval) {
    if (circleAnimationInterval) {
      clearInterval(circleAnimationInterval);
    }
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
// Fullscreen change handlers
let fullscreenChangeHandlers: Array<{ event: string; handler: () => void }> = [];

onMounted(() => {
  initializePositions();
  loadSelectedUser();
  
  const handleFullscreenChange = () => {
    // If user exits fullscreen manually (ESC key), reset calibration state
    const doc = document as Document & {
      webkitFullscreenElement?: Element | null
      msFullscreenElement?: Element | null
    };
    if (!doc.fullscreenElement && !doc.webkitFullscreenElement && !doc.msFullscreenElement) {
      if (isCalibrating.value || calibrationReviewVisible.value) {
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
