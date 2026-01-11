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
              isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-300'
            ]"></div>
            <span class="text-sm font-medium text-gray-600 dark:text-gray-300">
              {{ isConnected ? $t('home.active') : $t('home.inactive') }}
            </span>
          </div>
        </div>
        
        <div class="space-y-4">
          <!-- Connection Status -->
          <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div class="flex items-center space-x-3">
              <div :class="[
                'w-3 h-3 rounded-full',
                isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
              ]"></div>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                {{ isConnected ? $t('common.connected') : $t('common.disconnected') }}
              </span>
            </div>
            <button
              @click="toggleConnection"
              :class="[
                'px-4 py-2 rounded-lg font-medium transition-colors text-sm',
                isConnected
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              ]"
            >
              {{ isConnected ? $t('common.disconnect') : $t('common.connect') }}
            </button>
          </div>
          
          <!-- Start/Stop Eye Tracking Button -->
          <button
            @click="toggleTracking"
            :class="[
              'w-full py-4 rounded-xl font-semibold text-lg transition-all duration-200',
              isTracking
                ? 'bg-red-500 hover:bg-red-600 text-white'
                : 'bg-primary-600 hover:bg-primary-700 text-white'
            ]"
            :disabled="!isConnected"
          >
            <span v-if="!isTracking">{{ $t('home.startEyeTracking') }}</span>
            <span v-else>{{ $t('home.stopEyeTracking') }}</span>
          </button>
          
          <!-- Connection Error -->
          <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p class="text-sm text-red-800 dark:text-red-200">{{ error }}</p>
          </div>
        </div>
      </div>

      <!-- Select User and Caregiver Card -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 mb-8 max-w-2xl mx-auto">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-2xl font-semibold text-gray-900 dark:text-white">{{ $t('home.selectUser') }}</h3>
          <div v-if="selectedUser" class="flex items-center space-x-2">
            <div class="w-3 h-3 rounded-full bg-green-500"></div>
            <span class="text-sm font-medium text-gray-600 dark:text-gray-300">
              {{ selectedUser.name }}
            </span>
          </div>
        </div>
        
        <div class="space-y-4">
          <!-- User and Caregiver Selection Row -->
          <div class="grid grid-cols-2 gap-4">
            <!-- User Selection -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ $t('home.selectUserLabel') }}
              </label>
              <select
                v-model="selectedUserId"
                @change="onUserSelected"
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">{{ $t('home.noUserSelected') }}</option>
                <option
                  v-for="user in users"
                  :key="user.id"
                  :value="user.id"
                >
                  {{ user.name }} {{ user.is_active ? '' : `(${$t('users.inactive')})` }}
                </option>
              </select>
            </div>
            
            <!-- Caregiver Selection -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ $t('home.selectCaregiverLabel') }}
              </label>
              <select
                v-model="selectedCaregiverId"
                @change="onCaregiverSelected"
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">{{ $t('home.noCaregiverSelected') }}</option>
                <option
                  v-for="caregiver in caregivers"
                  :key="caregiver.id"
                  :value="caregiver.id"
                >
                  {{ caregiver.name }}
                </option>
              </select>
            </div>
          </div>
          
          <!-- Selected User Info -->
          <div v-if="selectedUser" class="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div class="flex items-center justify-between">
              <div>
                <p class="font-semibold text-gray-900 dark:text-white">{{ selectedUser.name }}</p>
                <p v-if="selectedUser.notes" class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {{ selectedUser.notes }}
                </p>
                <span
                  :class="[
                    'inline-block mt-2 px-2 py-1 rounded-full text-xs font-medium',
                    selectedUser.is_active
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                  ]"
                >
                  {{ selectedUser.is_active ? $t('users.active') : $t('users.inactive') }}
                </span>
              </div>
              <button
                @click="showUserList = true"
                class="px-3 py-1 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
              >
                {{ $t('home.changeUser') }}
              </button>
            </div>
          </div>
          
          <!-- Selected Caregiver Info -->
          <div v-if="selectedCaregiver" class="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div class="flex items-center justify-between">
              <div>
                <p class="font-semibold text-gray-900 dark:text-white">{{ selectedCaregiver.name }}</p>
                <p v-if="selectedCaregiver.gender" class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {{ $t('caregivers.gender') }}: {{ selectedCaregiver.gender }}
                </p>
                <p v-if="selectedCaregiver.description" class="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                  {{ selectedCaregiver.description }}
                </p>
              </div>
              <button
                @click="selectedCaregiverId = null; selectedCaregiver = null; localStorage.removeItem('selectedCaregiverId')"
                class="px-3 py-1 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
              >
                {{ $t('home.changeCaregiver') }}
              </button>
            </div>
          </div>
          
          <!-- Loading State -->
          <div v-if="loadingUsers || loadingCaregivers" class="text-center py-4">
            <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-2">
              {{ loadingUsers ? $t('home.loadingUsers') : $t('home.loadingCaregivers') }}
            </p>
          </div>
          
          <!-- Error State -->
          <div v-if="userError || caregiverError" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p class="text-sm text-red-800 dark:text-red-200">{{ userError || caregiverError }}</p>
          </div>
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
  ChatBubbleLeftRightIcon,
  Cog6ToothIcon,
  BookOpenIcon,
} from '@heroicons/vue/24/outline';
import { useEyeTracking } from '../composables/useEyeTracking';
import { eyeTrackingAPI, usersAPI, caregiversAPI } from '@/services/api';

// Use the shared eye tracking composable
const {
  isConnected,
  error,
  toggleConnection,
} = useEyeTracking();

// Local state for backend API tracking (separate from WebSocket connection)
const isTracking = ref(false);

// User selection state
const users = ref([]);
const selectedUserId = ref(null);
const selectedUser = ref(null);
const loadingUsers = ref(false);
const userError = ref(null);
const showUserList = ref(false);

// Caregiver selection state
const caregivers = ref([]);
const selectedCaregiverId = ref(null);
const selectedCaregiver = ref(null);
const loadingCaregivers = ref(false);
const caregiverError = ref(null);

const loadUsers = async () => {
  try {
    loadingUsers.value = true;
    userError.value = null;
    users.value = await usersAPI.list();
  } catch (err) {
    userError.value = err.response?.data?.detail || err.message || 'Failed to load users';
    console.error('Error loading users:', err);
  } finally {
    loadingUsers.value = false;
  }
};

const loadCaregivers = async () => {
  try {
    loadingCaregivers.value = true;
    caregiverError.value = null;
    caregivers.value = await caregiversAPI.list();
  } catch (err) {
    caregiverError.value = err.response?.data?.detail || err.message || 'Failed to load caregivers';
    console.error('Error loading caregivers:', err);
  } finally {
    loadingCaregivers.value = false;
  }
};

const onUserSelected = async () => {
  if (!selectedUserId.value) {
    selectedUser.value = null;
    showUserList.value = false;
    localStorage.removeItem('selectedUserId');
    return;
  }
  
  try {
    const user = await usersAPI.get(selectedUserId.value);
    selectedUser.value = user;
    showUserList.value = false;
    // Store selected user in localStorage for persistence
    localStorage.setItem('selectedUserId', selectedUserId.value.toString());
  } catch (err) {
    userError.value = err.response?.data?.detail || err.message || 'Failed to load user';
    console.error('Error loading user:', err);
  }
};

const onCaregiverSelected = async () => {
  if (!selectedCaregiverId.value) {
    selectedCaregiver.value = null;
    localStorage.removeItem('selectedCaregiverId');
    return;
  }
  
  try {
    const caregiver = await caregiversAPI.get(selectedCaregiverId.value);
    selectedCaregiver.value = caregiver;
    // Store selected caregiver in localStorage for persistence
    localStorage.setItem('selectedCaregiverId', selectedCaregiverId.value.toString());
  } catch (err) {
    caregiverError.value = err.response?.data?.detail || err.message || 'Failed to load caregiver';
    console.error('Error loading caregiver:', err);
  }
};

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
  // Load users and caregivers
  await Promise.all([loadUsers(), loadCaregivers()]);
  
  // Restore previously selected user
  const savedUserId = localStorage.getItem('selectedUserId');
  if (savedUserId) {
    const userId = parseInt(savedUserId);
    const user = users.value.find(u => u.id === userId);
    if (user) {
      selectedUserId.value = userId;
      await onUserSelected();
    }
  }
  
  // Restore previously selected caregiver
  const savedCaregiverId = localStorage.getItem('selectedCaregiverId');
  if (savedCaregiverId) {
    const caregiverId = parseInt(savedCaregiverId);
    const caregiver = caregivers.value.find(c => c.id === caregiverId);
    if (caregiver) {
      selectedCaregiverId.value = caregiverId;
      await onCaregiverSelected();
    }
  }
});
</script>

