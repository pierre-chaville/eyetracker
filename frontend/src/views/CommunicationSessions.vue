<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
          {{ $t('sessions.title') }}
        </h1>
      </div>

      <!-- Filters -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('sessions.filterByUser') }}
            </label>
            <select
              v-model="selectedUserId"
              @change="loadSessions"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option :value="null">{{ $t('sessions.allUsers') }}</option>
              <option v-for="user in users" :key="user.id" :value="user.id">
                {{ user.name }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('sessions.filterByCaregiver') }}
            </label>
            <select
              v-model="selectedCaregiverId"
              @change="loadSessions"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option :value="null">{{ $t('sessions.allCaregivers') }}</option>
              <option v-for="caregiver in caregivers" :key="caregiver.id" :value="caregiver.id">
                {{ caregiver.name }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
        <p class="text-red-800 dark:text-red-200">{{ error }}</p>
      </div>

      <!-- Sessions List -->
      <div v-else-if="sessions.length > 0" class="space-y-4">
        <div
          v-for="session in sessions"
          :key="session.id"
          @click="goToSessionDetail(session.id)"
          class="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow p-6 cursor-pointer"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-4 mb-2">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                  {{ $t('sessions.session') }} #{{ session.id }}
                </h3>
                <span
                  :class="[
                    'px-2 py-1 rounded-full text-xs font-medium',
                    session.ended_at
                      ? 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                      : 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                  ]"
                >
                  {{ session.ended_at ? $t('sessions.ended') : $t('sessions.active') }}
                </span>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 text-sm">
                <div>
                  <span class="text-gray-500 dark:text-gray-400">{{ $t('sessions.user') }}:</span>
                  <span class="ml-2 text-gray-900 dark:text-white">
                    {{ getUserName(session.user_id) || $t('sessions.unknown') }}
                  </span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">{{ $t('sessions.caregiver') }}:</span>
                  <span class="ml-2 text-gray-900 dark:text-white">
                    {{ getCaregiverName(session.caregiver_id) || $t('sessions.unknown') }}
                  </span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">{{ $t('sessions.startedAt') }}:</span>
                  <span class="ml-2 text-gray-900 dark:text-white">
                    {{ formatDateTime(session.started_at) }}
                  </span>
                </div>
                <div v-if="session.ended_at" class="md:col-span-3">
                  <span class="text-gray-500 dark:text-gray-400">{{ $t('sessions.endedAt') }}:</span>
                  <span class="ml-2 text-gray-900 dark:text-white">
                    {{ formatDateTime(session.ended_at) }}
                  </span>
                </div>
                <div class="md:col-span-3">
                  <span class="text-gray-500 dark:text-gray-400">{{ $t('sessions.steps') }}:</span>
                  <span class="ml-2 text-gray-900 dark:text-white">
                    {{ session.steps ? session.steps.length : 0 }}
                  </span>
                </div>
              </div>
            </div>
            <ChevronRightIcon class="w-6 h-6 text-gray-400 flex-shrink-0 ml-4" />
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-12 text-center">
        <p class="text-gray-500 dark:text-gray-400 text-lg">
          {{ $t('sessions.noSessions') }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ChevronRightIcon } from '@heroicons/vue/24/outline';
import { sessionsAPI, usersAPI, caregiversAPI } from '../services/api';

const router = useRouter();
const { t } = useI18n();

const sessions = ref([]);
const users = ref([]);
const caregivers = ref([]);
const loading = ref(false);
const error = ref(null);
const selectedUserId = ref(null);
const selectedCaregiverId = ref(null);

const loadUsers = async () => {
  try {
    const data = await usersAPI.list();
    users.value = data;
  } catch (err) {
    console.error('Error loading users:', err);
  }
};

const loadCaregivers = async () => {
  try {
    const data = await caregiversAPI.list();
    caregivers.value = data;
  } catch (err) {
    console.error('Error loading caregivers:', err);
  }
};

const loadSessions = async () => {
  loading.value = true;
  error.value = null;
  try {
    const params = {};
    if (selectedUserId.value) {
      params.user_id = selectedUserId.value;
    }
    if (selectedCaregiverId.value) {
      params.caregiver_id = selectedCaregiverId.value;
    }
    const data = await sessionsAPI.list(params);
    sessions.value = data;
  } catch (err) {
    console.error('Error loading sessions:', err);
    error.value = t('sessions.errorLoading');
  } finally {
    loading.value = false;
  }
};

const getUserName = (userId) => {
  const user = users.value.find(u => u.id === userId);
  return user ? user.name : null;
};

const getCaregiverName = (caregiverId) => {
  const caregiver = caregivers.value.find(c => c.id === caregiverId);
  return caregiver ? caregiver.name : null;
};

const formatDateTime = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString();
};

const goToSessionDetail = (sessionId) => {
  router.push(`/communication-sessions/${sessionId}`);
};

onMounted(async () => {
  await Promise.all([loadUsers(), loadCaregivers(), loadSessions()]);
});
</script>

