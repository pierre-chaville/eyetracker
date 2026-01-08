<template>
  <div class="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <!-- Hero Section -->
      <div class="text-center mb-16">
        <h2 class="text-5xl font-bold text-gray-900 dark:text-white mb-4">
          {{ $t('home.title') }}
        </h2>
        <p class="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
          {{ $t('home.subtitle') }}
        </p>
      </div>

      <!-- Status Card -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 mb-8 max-w-2xl mx-auto">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-2xl font-semibold text-gray-900 dark:text-white">{{ $t('home.eyeTrackingStatus') }}</h3>
          <div class="flex items-center space-x-2">
            <div :class="[
              'w-3 h-3 rounded-full',
              isTracking ? 'bg-green-500 animate-pulse' : 'bg-gray-300'
            ]"></div>
            <span class="text-sm font-medium text-gray-600 dark:text-gray-300">
              {{ isTracking ? $t('home.active') : $t('home.inactive') }}
            </span>
          </div>
        </div>
        
        <div class="space-y-4">
          <button
            @click="toggleTracking"
            :class="[
              'w-full py-4 rounded-xl font-semibold text-lg transition-all duration-200',
              isTracking
                ? 'bg-red-500 hover:bg-red-600 text-white'
                : 'bg-primary-600 hover:bg-primary-700 text-white'
            ]"
          >
            <span v-if="!isTracking">{{ $t('home.startEyeTracking') }}</span>
            <span v-else>{{ $t('home.stopEyeTracking') }}</span>
          </button>
        </div>
      </div>

      <!-- Features Grid -->
        <div class="grid md:grid-cols-3 gap-6 mb-12">
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
          <div class="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center mb-4">
            <EyeIcon class="w-6 h-6 text-primary-600 dark:text-primary-400" />
          </div>
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">{{ $t('home.features.eyeTracking.title') }}</h3>
          <p class="text-gray-600 dark:text-gray-300">
            {{ $t('home.features.eyeTracking.description') }}
          </p>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
          <div class="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center mb-4">
            <SparklesIcon class="w-6 h-6 text-primary-600 dark:text-primary-400" />
          </div>
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">{{ $t('home.features.aiAssistance.title') }}</h3>
          <p class="text-gray-600 dark:text-gray-300">
            {{ $t('home.features.aiAssistance.description') }}
          </p>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
          <div class="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center mb-4">
            <HeartIcon class="w-6 h-6 text-primary-600 dark:text-primary-400" />
          </div>
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">{{ $t('home.features.accessibleDesign.title') }}</h3>
          <p class="text-gray-600 dark:text-gray-300">
            {{ $t('home.features.accessibleDesign.description') }}
          </p>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 max-w-2xl mx-auto">
        <h3 class="text-2xl font-semibold text-gray-900 dark:text-white mb-6">{{ $t('home.quickActions.title') }}</h3>
        <div class="grid grid-cols-2 gap-4">
          <router-link to="/eye-tracking" class="btn-secondary py-6 text-lg font-medium flex flex-col items-center">
            <EyeIcon class="w-8 h-8 mb-2" />
            {{ $t('home.quickActions.viewEyeTracking') }}
          </router-link>
          <button class="btn-secondary py-6 text-lg font-medium">
            <ChatBubbleLeftRightIcon class="w-8 h-8 mx-auto mb-2" />
            {{ $t('home.quickActions.startCommunication') }}
          </button>
          <button class="btn-secondary py-6 text-lg font-medium">
            <Cog6ToothIcon class="w-8 h-8 mx-auto mb-2" />
            {{ $t('home.quickActions.calibrate') }}
          </button>
          <button class="btn-secondary py-6 text-lg font-medium">
            <BookOpenIcon class="w-8 h-8 mx-auto mb-2" />
            {{ $t('home.quickActions.practiceMode') }}
          </button>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p class="text-center text-gray-600 dark:text-gray-300">
          {{ $t('home.footer') }}
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import {
  EyeIcon,
  SparklesIcon,
  HeartIcon,
  ChatBubbleLeftRightIcon,
  Cog6ToothIcon,
  BookOpenIcon,
  ChartBarIcon,
} from '@heroicons/vue/24/outline';
import { eyeTrackingAPI } from '@/services/api';

const isTracking = ref(false);

const toggleTracking = async () => {
  try {
    if (isTracking.value) {
      // Try Electron API first, fallback to HTTP API
      if (window.electronAPI) {
        await window.electronAPI.stopEyeTracking();
      } else {
        await eyeTrackingAPI.stop();
      }
    } else {
      if (window.electronAPI) {
        await window.electronAPI.startEyeTracking();
      } else {
        await eyeTrackingAPI.start();
      }
    }
    isTracking.value = !isTracking.value;
  } catch (error) {
    console.error('Error toggling eye tracking:', error);
  }
};

onMounted(async () => {
  // Check initial status
  try {
    const status = await eyeTrackingAPI.getStatus();
    isTracking.value = status.is_active;
  } catch (error) {
    console.error('Error fetching eye tracking status:', error);
  }
});
</script>

