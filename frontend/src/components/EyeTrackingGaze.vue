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
    >
      <!-- Circle -->
      <div class="w-8 h-8">
        <div
          class="w-full h-full rounded-full bg-primary-500 border-4 border-primary-300 shadow-lg shadow-primary-500/50"
        ></div>
        <div class="absolute inset-0 rounded-full bg-primary-400 opacity-50 animate-ping"></div>
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
    >
      <!-- Coordinate Label -->
      <div
        v-if="showCoordinates"
        class="absolute top-8 left-1/2 -translate-x-1/2 whitespace-nowrap bg-red-900/90 backdrop-blur-sm text-white text-xs font-mono px-2 py-1 rounded shadow-lg border border-red-700"
      >
        <div class="text-center">
          <div class="text-red-300">{{ $t('eyeTracking.invalid') }}</div>
          <div>X: {{ currentGazePoint.x.toFixed(1) }}px</div>
          <div>Y: {{ currentGazePoint.y.toFixed(1) }}px</div>
        </div>
      </div>
      <!-- Circle -->
      <div class="w-6 h-6">
        <div class="w-full h-full rounded-full bg-red-500 border-2 border-red-300 opacity-50"></div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { GazePoint, TrackingData } from '../types/tracking';

interface Props {
  gazePoint?: GazePoint | null
  trackingData?: TrackingData | null
  isConnected?: boolean
  showCoordinates?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  gazePoint: null,
  trackingData: null,
  isConnected: false,
  showCoordinates: true,
});

const { t } = useI18n();

const currentGazePoint = computed(() => props.gazePoint);
const currentTrackingData = computed(() => props.trackingData);
</script>

