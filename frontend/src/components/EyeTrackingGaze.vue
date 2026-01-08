<template>
  <div>
    <!-- Valid Gaze Point -->
    <div
      v-if="currentGazePoint && isConnected && currentTrackingData?.valid"
      :style="{
        left: `${currentGazePoint.x}px`,
        top: `${currentGazePoint.y}px`,
      }"
      class="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none transition-all duration-75 ease-linear z-50"
      :class="{ 'transition-none': isFrozen }"
    >
      <!-- Coordinate Label -->
      <div
        v-if="showCoordinates"
        class="absolute top-10 left-1/2 -translate-x-1/2 whitespace-nowrap bg-gray-900/90 backdrop-blur-sm text-white text-xs font-mono px-2 py-1 rounded shadow-lg border border-gray-700"
      >
        <div class="text-center">
          <div v-if="isFrozen" class="text-yellow-400 text-[10px] mb-1">
            {{ $t('eyeTracking.frozen') }}
          </div>
          <div>X: {{ currentGazePoint.x.toFixed(1) }}px</div>
          <div>Y: {{ currentGazePoint.y.toFixed(1) }}px</div>
          <div v-if="currentTrackingData" class="text-gray-400 text-[10px] mt-1 pt-1 border-t border-gray-700">
            <div>
              Screen: {{ (currentTrackingData.pixelX?.toFixed(0) || '--') }}, 
              {{ (currentTrackingData.pixelY?.toFixed(0) || '--') }}
            </div>
            <div>
              Norm: {{ ((currentTrackingData.x * 100).toFixed(1)) }}%, 
              {{ ((currentTrackingData.y * 100).toFixed(1)) }}%
            </div>
          </div>
        </div>
      </div>
      <!-- Circle -->
      <div class="w-8 h-8" :class="{ 'animate-pulse': !isFrozen }">
        <div
          class="w-full h-full rounded-full bg-primary-500 border-4 border-primary-300 shadow-lg shadow-primary-500/50"
          :class="{ 'animate-pulse': !isFrozen }"
        ></div>
        <div v-if="!isFrozen" class="absolute inset-0 rounded-full bg-primary-400 opacity-50 animate-ping"></div>
      </div>
    </div>

    <!-- Invalid Gaze Point -->
    <div
      v-if="currentGazePoint && isConnected && currentTrackingData && !currentTrackingData.valid"
      :style="{
        left: `${currentGazePoint.x}px`,
        top: `${currentGazePoint.y}px`,
      }"
      class="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none transition-all duration-75 ease-linear z-50"
      :class="{ 'transition-none': isFrozen }"
    >
      <!-- Coordinate Label -->
      <div
        v-if="showCoordinates"
        class="absolute top-8 left-1/2 -translate-x-1/2 whitespace-nowrap bg-red-900/90 backdrop-blur-sm text-white text-xs font-mono px-2 py-1 rounded shadow-lg border border-red-700"
      >
        <div class="text-center">
          <div class="text-red-300">{{ $t('eyeTracking.invalid') }}</div>
          <div v-if="isFrozen" class="text-yellow-400 text-[10px]">
            {{ $t('eyeTracking.frozen') }}
          </div>
          <div>X: {{ currentGazePoint.x.toFixed(1) }}px</div>
          <div>Y: {{ currentGazePoint.y.toFixed(1) }}px</div>
        </div>
      </div>
      <!-- Circle -->
      <div class="w-6 h-6">
        <div class="w-full h-full rounded-full bg-red-500 border-2 border-red-300 opacity-50"></div>
      </div>
    </div>

    <!-- Freeze Indicator -->
    <div
      v-if="isFrozen"
      class="absolute top-4 left-1/2 -translate-x-1/2 z-50 bg-yellow-500/90 backdrop-blur-sm text-black text-sm font-bold px-4 py-2 rounded-lg shadow-lg border-2 border-yellow-400"
    >
      ⏸ {{ $t('eyeTracking.frozenMessage') }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  gazePoint: {
    type: Object,
    default: null,
  },
  trackingData: {
    type: Object,
    default: null,
  },
  isConnected: {
    type: Boolean,
    default: false,
  },
  isFrozen: {
    type: Boolean,
    default: false,
  },
  frozenGazePoint: {
    type: Object,
    default: null,
  },
  frozenTrackingData: {
    type: Object,
    default: null,
  },
  showCoordinates: {
    type: Boolean,
    default: true,
  },
});

const { t } = useI18n();

const currentGazePoint = computed(() => {
  return props.isFrozen ? props.frozenGazePoint : props.gazePoint;
});

const currentTrackingData = computed(() => {
  return props.isFrozen ? props.frozenTrackingData : props.trackingData;
});
</script>

