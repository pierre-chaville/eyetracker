<template>
  <div class="min-h-screen bg-white dark:bg-gray-900 relative overflow-hidden">
    <!-- Header (hidden in fullscreen mode) -->
    <header 
      v-if="!isFullscreen"
      ref="headerElement" 
      class="bg-white dark:bg-gray-800 shadow-lg z-10 relative border-b border-gray-200 dark:border-gray-700"
    >
      <div class="px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ $t('eyeTracking.title') }}</h1>
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <div :class="[
                'w-3 h-3 rounded-full',
                isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
              ]"></div>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                {{ isConnected ? $t('common.connected') : $t('common.disconnected') }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
    
    <!-- Start Button (shown before fullscreen) -->
    <div
      v-if="!isFullscreen"
      class="absolute inset-0 flex items-center justify-center bg-gray-50 dark:bg-gray-900"
    >
      <button
        @click="startEyeTracking"
        :disabled="!isConnected"
        :class="[
          'px-12 py-6 rounded-xl font-semibold text-xl transition-all duration-200',
          !isConnected
            ? 'bg-gray-400 dark:bg-gray-600 text-gray-200 cursor-not-allowed'
            : 'bg-primary-600 hover:bg-primary-700 text-white shadow-lg hover:shadow-xl'
        ]"
      >
        {{ $t('eyeTracking.start') }}
      </button>
      <div v-if="!isConnected" class="absolute top-1/2 left-1/2 -translate-x-1/2 translate-y-20 text-red-600 dark:text-red-400 text-sm">
        {{ $t('eyeTracking.notConnected') }}
      </div>
    </div>

    <!-- Eye Tracking Canvas Area (fullscreen when active) -->
    <div 
      v-if="isFullscreen"
      class="relative w-screen h-screen cursor-pointer bg-white dark:bg-gray-900" 
      ref="trackingArea"
      @click="showAnimalIcon"
    >
      <!-- Gaze Visualization Component -->
      <EyeTrackingGaze
        :gaze-point="gazePoint"
        :tracking-data="trackingData"
        :is-connected="isConnected"
        :show-coordinates="false"
      />

      <!-- Animal Icon (10% of screen size) -->
      <div
        v-if="showAnimal"
        :style="{
          left: `${animalPosition.x}px`,
          top: `${animalPosition.y}px`,
          fontSize: `${animalSize}px`,
        }"
        class="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none z-40 flex items-center justify-center select-none"
      >
        🦁
      </div>

      <!-- Crosshair at center (for reference) -->
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none opacity-20">
        <div class="w-px h-20 bg-white"></div>
        <div class="w-20 h-px bg-white -mt-px -ml-10"></div>
      </div>

      <!-- Status Overlay -->
      <div v-if="!isConnected" class="absolute inset-0 flex items-center justify-center">
        <div class="text-center">
          <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-800 flex items-center justify-center">
            <EyeIcon class="w-8 h-8 text-gray-500" />
          </div>
          <h2 class="text-2xl font-semibold text-gray-300 mb-2">{{ $t('eyeTracking.notConnected') }}</h2>
          <p class="text-gray-400 mb-6">{{ $t('eyeTracking.connectMessage') }}</p>
          <button
            @click="toggleConnection"
            class="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
          >
            {{ $t('eyeTracking.connectWebSocket') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Info Panel (toggleable in fullscreen) -->
    <div
      v-if="isFullscreen && showDebugPanel"
      class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg p-4 shadow-xl max-w-xs border border-gray-200 dark:border-gray-700"
    >
      <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-300 mb-2">{{ $t('eyeTracking.eyeTrackingData') }}</h3>
      <div class="space-y-1 text-xs font-mono">
        <div class="text-gray-600 dark:text-gray-400">
          <span class="text-gray-700 dark:text-gray-500">{{ $t('eyeTracking.status') }}:</span>
          <span :class="[
            'ml-2 font-semibold',
            trackingData?.valid ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
          ]">
            {{ trackingData?.valid ? $t('eyeTracking.valid') : $t('eyeTracking.invalid') }}
          </span>
        </div>
        <div class="text-gray-600 dark:text-gray-400">
          <span class="text-gray-700 dark:text-gray-500">X:</span>
          <span class="text-gray-900 dark:text-white ml-2">{{ gazePoint ? gazePoint.x.toFixed(1) : '--' }}px</span>
          <span v-if="trackingData" class="text-gray-700 dark:text-gray-500 ml-1">
            ({{ (((trackingData?.x ?? 0) * 100).toFixed(1)) }}%)
          </span>
        </div>
        <div v-if="trackingData?.pixelX !== undefined" class="text-gray-600 dark:text-gray-400 text-[10px]">
          <span class="text-gray-700 dark:text-gray-500">{{ $t('eyeTracking.screenX') }}:</span>
          <span class="text-gray-900 dark:text-white ml-2">{{ trackingData.pixelX.toFixed(1) }}px</span>
        </div>
        <div class="text-gray-600 dark:text-gray-400">
          <span class="text-gray-700 dark:text-gray-500">Y:</span>
          <span class="text-gray-900 dark:text-white ml-2">{{ gazePoint ? gazePoint.y.toFixed(1) : '--' }}px</span>
          <span v-if="trackingData" class="text-gray-700 dark:text-gray-500 ml-1">
            ({{ (((trackingData?.y ?? 0) * 100).toFixed(1)) }}%)
          </span>
        </div>
        <div v-if="trackingData?.pixelY !== undefined" class="text-gray-600 dark:text-gray-400 text-[10px]">
          <span class="text-gray-700 dark:text-gray-500">{{ $t('eyeTracking.screenY') }}:</span>
          <span class="text-gray-900 dark:text-white ml-2">{{ trackingData.pixelY.toFixed(1) }}px</span>
        </div>
        <div v-if="trackingData" class="text-gray-600 dark:text-gray-400">
          <span class="text-gray-700 dark:text-gray-500">{{ $t('eyeTracking.screen') }}:</span>
          <span class="text-gray-900 dark:text-white ml-2">{{ trackingData.screenWidth }}×{{ trackingData.screenHeight }}</span>
        </div>
        <div class="text-gray-600 dark:text-gray-400">
          <span class="text-gray-700 dark:text-gray-500">{{ $t('eyeTracking.fps') }}:</span>
          <span class="text-gray-900 dark:text-white ml-2">{{ fps?.toFixed(1) ?? '--' }}</span>
        </div>
        <div class="text-gray-600 dark:text-gray-400">
          <span class="text-gray-700 dark:text-gray-500">{{ $t('eyeTracking.messages') }}:</span>
          <span class="text-gray-900 dark:text-white ml-2">{{ messageCount }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, inject, type Ref } from 'vue';
import { EyeIcon } from '@heroicons/vue/24/outline';
import { useEyeTracking } from '../composables/useEyeTracking';
import { useCalibration } from '../composables/useCalibration';
import EyeTrackingGaze from '../components/EyeTrackingGaze.vue';
import { isDocumentElementFullscreen, safeExitFullscreen } from '../utils/fullscreen';

const trackingArea = ref<HTMLElement | null>(null);
const headerElement = ref<HTMLElement | null>(null);
let positionInterval: ReturnType<typeof setInterval> | null = null;
let resizeObserver: ResizeObserver | null = null;
let resizeHandler: (() => void) | null = null;

// Fullscreen state
const isFullscreen = ref(false);
// Get eye tracking fullscreen state from App.vue to hide sidebar
const isEyeTrackingFullscreenApp = inject<Ref<boolean>>('isEyeTrackingFullscreen', ref(false));

// Animal icon state
const showAnimal = ref(false);
const animalPosition = ref({ x: 0, y: 0 });
const animalSize = ref(0);
const showDebugPanel = ref(false);

// Use calibration composable to get coefficients for selected user
const { calibrationCoefficients } = useCalibration();

// Use the eye tracking composable
const {
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
  calibrationCoefficients: trackingCalibrationCoefficients,
  isFullscreen: trackingIsFullscreen,
  toggleConnection,
  updateWindowPosition,
  updateHeaderHeight: updateHeaderHeightFromComposable,
} = useEyeTracking({ isFullscreen });

// Update calibration coefficients in eye tracking when they change
watch(calibrationCoefficients, (newCoefficients) => {
  if (trackingCalibrationCoefficients) {
    trackingCalibrationCoefficients.value = newCoefficients;
  }
}, { immediate: true });

const updateHeaderHeight = () => {
  if (headerElement.value) {
    updateHeaderHeightFromComposable(headerElement.value);
  }
};

const startEyeTracking = async () => {
  if (!isConnected.value) {
    return;
  }
  
  // Reset animal icon state
  showAnimal.value = false;
  
  // Set fullscreen state in App.vue to hide sidebar
  isEyeTrackingFullscreenApp.value = true;
  
  // Enter fullscreen mode
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
  } catch (error) {
    console.warn('Could not enter fullscreen mode:', error);
  }
  
  isFullscreen.value = true;
  // Update fullscreen state in composable
  if (trackingIsFullscreen) {
    trackingIsFullscreen.value = true;
  }
};

const exitFullscreen = () => {
  void safeExitFullscreen();
};

const stopEyeTracking = () => {
  showAnimal.value = false;
  isEyeTrackingFullscreenApp.value = false;
  // Avoid exitFullscreen() when user already left via ESC (prevents "Document not active")
  if (isDocumentElementFullscreen()) {
    void safeExitFullscreen();
  }
  isFullscreen.value = false;
  if (trackingIsFullscreen) {
    trackingIsFullscreen.value = false;
  }
};

const showAnimalIcon = (event) => {
  // Calculate 10% of screen size
  const screenWidth = window.innerWidth;
  const screenHeight = window.innerHeight;
  const size = Math.min(screenWidth, screenHeight) * 0.1;
  animalSize.value = size;
  
  // Position animal at click location
  animalPosition.value = {
    x: event.clientX,
    y: event.clientY
  };
  
  // Show the animal icon
  showAnimal.value = true;
};

// Fullscreen change handlers
let fullscreenChangeHandlers: Array<{ event: string; handler: (event: Event) => void }> = [];

onMounted(() => {
  // Wait for next tick to ensure header element is rendered
  setTimeout(() => {
    // Measure header height
    updateHeaderHeight();
    
    // Use ResizeObserver to watch for header size changes
    if (headerElement.value && window.ResizeObserver) {
      const observer = new ResizeObserver(() => {
        updateHeaderHeight();
      });
      observer.observe(headerElement.value);
      resizeObserver = observer;
    }
  }, 0);
  
  // Get initial window position
  updateWindowPosition();
  
  // Update window position periodically (in case window is moved)
  positionInterval = setInterval(() => {
    updateWindowPosition();
    updateHeaderHeight(); // Also update header height in case it changes
  }, 1000);
  
  // Also update on window resize/move events
  resizeHandler = () => {
    updateWindowPosition();
    updateHeaderHeight();
  };
  if (resizeHandler) {
    window.addEventListener('resize', resizeHandler);
  }

  const handleKeyToggle = (event: Event) => {
    if (!isFullscreen.value) {
      return;
    }
    const target = event.target as HTMLElement | null;
    if (target && ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) {
      return;
    }
    const keyEvent = event as KeyboardEvent;
    if (keyEvent.key.toLowerCase() === 'd') {
      showDebugPanel.value = !showDebugPanel.value;
    }
  };
  window.addEventListener('keydown', handleKeyToggle);
  
  // Listen for fullscreen changes to handle ESC key
  const handleFullscreenChange = () => {
    // If user exits fullscreen manually (ESC key), reset state
    const doc = document as Document & {
      webkitFullscreenElement?: Element | null
      msFullscreenElement?: Element | null
    };
    if (!doc.fullscreenElement && !doc.webkitFullscreenElement && !doc.msFullscreenElement) {
      if (isFullscreen.value) {
        stopEyeTracking();
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
    { event: 'keydown', handler: handleKeyToggle },
  ];
});

onBeforeUnmount(() => {
  // Remove fullscreen event listeners
  if (fullscreenChangeHandlers && fullscreenChangeHandlers.length > 0) {
    fullscreenChangeHandlers.forEach(({ event, handler }) => {
      if (event === 'keydown') {
        window.removeEventListener(event, handler);
      } else {
        document.removeEventListener(event, handler);
      }
    });
  }
  
  // Exit fullscreen if still active when component unmounts
  if (isFullscreen.value) {
    exitFullscreen();
    isEyeTrackingFullscreenApp.value = false;
  }
  
  if (positionInterval) {
    clearInterval(positionInterval);
  }
  if (resizeObserver && headerElement.value) {
    resizeObserver.unobserve(headerElement.value);
    resizeObserver.disconnect();
  }
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler);
  }
});
</script>

