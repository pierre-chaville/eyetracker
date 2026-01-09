<template>
  <div id="app" class="min-h-screen">
    <Sidebar 
      v-if="!isCalibrating && !isEyeTrackingFullscreen"
      :is-open="sidebarOpen" 
      :is-expanded="sidebarExpanded"
      @close="sidebarOpen = false" 
      @toggle="toggleSidebarExpanded"
    />
    <!-- Main content area with sidebar offset -->
    <div :class="['transition-all duration-300 min-h-screen', (isCalibrating || isEyeTrackingFullscreen) ? '' : (sidebarExpanded ? 'md:ml-64' : 'md:ml-20')]">
      <!-- Mobile menu button -->
      <button
        v-if="!isCalibrating && !isEyeTrackingFullscreen"
        @click="sidebarOpen = !sidebarOpen"
        class="fixed top-4 left-4 z-50 md:hidden p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700"
      >
        <Bars3Icon class="w-6 h-6 text-gray-600 dark:text-gray-300" />
      </button>
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, provide } from 'vue';
import Sidebar from './components/Sidebar.vue';
import { Bars3Icon } from '@heroicons/vue/24/outline';
import { useRouter } from 'vue-router';

const sidebarOpen = ref(false);
// Load expanded state from localStorage, default to true
const sidebarExpanded = ref(localStorage.getItem('sidebarExpanded') !== 'false');
const router = useRouter();

// Calibration state - shared with Calibration component
const isCalibrating = ref(false);
// Eye tracking fullscreen state - shared with EyeTracking component
const isEyeTrackingFullscreen = ref(false);

// Provide states for child components
provide('isCalibrating', isCalibrating);
provide('isEyeTrackingFullscreen', isEyeTrackingFullscreen);

// Save expanded state to localStorage when it changes
const toggleSidebarExpanded = () => {
  sidebarExpanded.value = !sidebarExpanded.value;
  localStorage.setItem('sidebarExpanded', sidebarExpanded.value.toString());
};

// Close sidebar on route change (mobile)
const handleRouteChange = () => {
  if (window.innerWidth < 768) {
    sidebarOpen.value = false;
  }
};

onMounted(() => {
  router.afterEach(handleRouteChange);
});

onBeforeUnmount(() => {
  // Router cleanup is handled automatically, but we can remove listener if needed
});
</script>

