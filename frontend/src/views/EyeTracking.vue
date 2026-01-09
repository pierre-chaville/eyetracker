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
      @click="stopEyeTracking"
    >
      <!-- Gaze Visualization Component -->
      <EyeTrackingGaze
        :gaze-point="gazePoint"
        :tracking-data="trackingData"
        :is-connected="isConnected"
        :is-frozen="isFrozen"
        :frozen-gaze-point="frozenGazePoint"
        :frozen-tracking-data="frozenTrackingData"
        :show-coordinates="true"
      />

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

    <!-- Info Panel (hidden in fullscreen) -->
    <div v-if="!isFullscreen" class="absolute bottom-4 left-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg p-4 shadow-xl max-w-xs border border-gray-200 dark:border-gray-700">
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
            ({{ (trackingData.x * 100).toFixed(1) }}%)
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
            ({{ (trackingData.y * 100).toFixed(1) }}%)
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
          <span class="text-gray-900 dark:text-white ml-2">{{ fps.toFixed(1) }}</span>
        </div>
        <div class="text-gray-600 dark:text-gray-400">
          <span class="text-gray-700 dark:text-gray-500">{{ $t('eyeTracking.messages') }}:</span>
          <span class="text-gray-900 dark:text-white ml-2">{{ messageCount }}</span>
        </div>
        <div class="text-gray-600 dark:text-gray-400 pt-2 border-t border-gray-300 dark:border-gray-700 mt-2">
          <span class="text-gray-700 dark:text-gray-500">{{ $t('eyeTracking.windowOffset') }}:</span>
          <span class="text-gray-900 dark:text-white ml-2">{{ windowOffset.x }}, {{ windowOffset.y }}</span>
        </div>
        <div v-if="manualOffset.x !== 0 || manualOffset.y !== 0" class="text-gray-600 dark:text-gray-400">
          <span class="text-gray-700 dark:text-gray-500">{{ $t('eyeTracking.manualOffset') }}:</span>
          <span class="text-yellow-600 dark:text-yellow-400 ml-2">{{ manualOffset.x }}, {{ manualOffset.y }}</span>
        </div>
        <div class="text-gray-600 dark:text-gray-400">
          <span class="text-gray-700 dark:text-gray-500">{{ $t('eyeTracking.scaleFactor') }}:</span>
          <span class="text-gray-900 dark:text-white ml-2">{{ scaleFactor.toFixed(2) }}x</span>
        </div>
        <div class="text-gray-600 dark:text-gray-400">
          <span class="text-gray-700 dark:text-gray-500">{{ $t('eyeTracking.scaleApplied') }}:</span>
          <span :class="[
            'ml-2 font-semibold',
            applyScaling ? 'text-green-600 dark:text-green-400' : 'text-gray-700 dark:text-gray-500'
          ]">
            {{ applyScaling ? scaleMode : $t('eyeTracking.scaleModeNone') }}
          </span>
        </div>
        <div class="text-gray-600 dark:text-gray-400">
          <span class="text-gray-700 dark:text-gray-500">{{ $t('eyeTracking.headerHeight') }}:</span>
          <span class="text-gray-900 dark:text-white ml-2">
            {{ (manualHeaderHeight !== null && manualHeaderHeight > 0 ? manualHeaderHeight : headerHeight).toFixed(0) }}px
          </span>
          <span v-if="manualHeaderHeight !== null && manualHeaderHeight > 0" class="text-yellow-600 dark:text-yellow-400 text-[10px] ml-1">({{ $t('eyeTracking.manual') }})</span>
        </div>
      </div>
    </div>

      <!-- Connection Settings (hidden in fullscreen) -->
      <div v-if="!isFullscreen" class="absolute bottom-4 right-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg p-4 shadow-xl max-w-xs border border-gray-200 dark:border-gray-700">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-300 mb-2">{{ $t('eyeTracking.connectionSettings') }}</h3>
      <div class="space-y-2">
        <div>
          <label class="block text-xs text-gray-700 dark:text-gray-400 mb-1">{{ $t('eyeTracking.websocketUrl') }}</label>
          <input
            v-model="wsUrl"
            type="text"
            :disabled="isConnected"
            class="w-full px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
            placeholder="ws://127.0.0.1:8765"
          />
        </div>
        <div class="pt-2 border-t border-gray-300 dark:border-gray-700">
          <label class="block text-xs text-gray-700 dark:text-gray-400 mb-1">{{ $t('eyeTracking.manualOffset') }}</label>
          <div class="flex gap-2">
            <input
              v-model.number="manualOffset.x"
              type="number"
              step="1"
              class="w-full px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="X"
            />
            <input
              v-model.number="manualOffset.y"
              type="number"
              step="1"
              class="w-full px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Y"
            />
          </div>
          <button
            @click="updateWindowPosition"
            class="mt-2 w-full px-2 py-1 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded text-xs transition-colors"
          >
            {{ $t('eyeTracking.refreshPosition') }}
          </button>
          <label class="flex items-center mt-2 cursor-pointer">
            <input
              v-model="invertY"
              type="checkbox"
              class="mr-2"
            />
            <span class="text-xs text-gray-700 dark:text-gray-400">{{ $t('eyeTracking.invertYAxis') }}</span>
          </label>
          <label class="flex items-center mt-2 cursor-pointer">
            <input
              v-model="applyScaling"
              type="checkbox"
              class="mr-2"
            />
            <span class="text-xs text-gray-700 dark:text-gray-400">{{ $t('eyeTracking.applyScaleCorrection') }}</span>
          </label>
          <div v-if="applyScaling" class="mt-2 space-y-2">
            <div>
              <label class="block text-xs text-gray-700 dark:text-gray-400 mb-1">{{ $t('eyeTracking.scaleMode') }}</label>
              <select
                v-model="scaleMode"
                class="w-full px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="none">{{ $t('eyeTracking.scaleModeNone') }}</option>
                <option value="divide">{{ $t('eyeTracking.scaleModeDivide') }}</option>
                <option value="multiply">{{ $t('eyeTracking.scaleModeMultiply') }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-gray-700 dark:text-gray-400 mb-1">{{ $t('eyeTracking.scaleFactorOverride', { value: scaleFactor.toFixed(2) }) }}</label>
              <input
                v-model.number="manualScaleFactor"
                type="number"
                step="0.1"
                min="0.5"
                max="3.0"
                class="w-full px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Auto"
              />
            </div>
            <div>
              <label class="block text-xs text-gray-700 dark:text-gray-400 mb-1">{{ $t('eyeTracking.headerHeightOverride', { value: headerHeight.toFixed(0) }) }}</label>
              <input
                v-model.number="manualHeaderHeight"
                type="number"
                step="1"
                min="0"
                max="200"
                class="w-full px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Auto"
              />
            </div>
          </div>
        </div>
        <div v-if="error" class="mt-2 p-2 bg-red-900/50 border border-red-700 rounded text-xs text-red-300">
          {{ error }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, inject } from 'vue';
import { EyeIcon } from '@heroicons/vue/24/outline';
import { useEyeTracking } from '../composables/useEyeTracking';
import { useCalibration } from '../composables/useCalibration';
import EyeTrackingGaze from '../components/EyeTrackingGaze.vue';

const trackingArea = ref(null);
const headerElement = ref(null);
let positionInterval = null;
let resizeObserver = null;
let resizeHandler = null;

// Fullscreen state
const isFullscreen = ref(false);
// Get eye tracking fullscreen state from App.vue to hide sidebar
const isEyeTrackingFullscreenApp = inject('isEyeTrackingFullscreen', ref(false));

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
  calibrationCoefficients: trackingCalibrationCoefficients,
  isFullscreen: trackingIsFullscreen,
  toggleConnection,
  toggleFreeze,
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
  
  // Set fullscreen state in App.vue to hide sidebar
  isEyeTrackingFullscreenApp.value = true;
  
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
  
  isFullscreen.value = true;
  // Update fullscreen state in composable
  if (trackingIsFullscreen) {
    trackingIsFullscreen.value = true;
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
  } catch (error) {
    console.warn('Could not exit fullscreen mode:', error);
  }
};

const stopEyeTracking = () => {
  // Reset fullscreen state in App.vue to show sidebar
  isEyeTrackingFullscreenApp.value = false;
  
  // Exit fullscreen mode
  exitFullscreen();
  
  isFullscreen.value = false;
  // Update fullscreen state in composable
  if (trackingIsFullscreen) {
    trackingIsFullscreen.value = false;
  }
};

// Fullscreen change handlers
let fullscreenChangeHandlers = [];

onMounted(() => {
  // Wait for next tick to ensure header element is rendered
  setTimeout(() => {
    // Measure header height
    updateHeaderHeight();
    
    // Use ResizeObserver to watch for header size changes
    if (headerElement.value && window.ResizeObserver) {
      resizeObserver = new ResizeObserver(() => {
        updateHeaderHeight();
      });
      resizeObserver.observe(headerElement.value);
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
  window.addEventListener('resize', resizeHandler);
  
  // Listen for fullscreen changes to handle ESC key
  const handleFullscreenChange = () => {
    // If user exits fullscreen manually (ESC key), reset state
    if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
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
  ];
});

onBeforeUnmount(() => {
  // Remove fullscreen event listeners
  if (fullscreenChangeHandlers && fullscreenChangeHandlers.length > 0) {
    fullscreenChangeHandlers.forEach(({ event, handler }) => {
      document.removeEventListener(event, handler);
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

<style scoped>
/* Smooth transitions for the gaze point */
</style>

