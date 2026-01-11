<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <button
            @click="goBack"
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <ArrowLeftIcon class="w-6 h-6 text-gray-600 dark:text-gray-300" />
          </button>
          <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
            {{ $t('sessionDetail.title') }} #{{ sessionId }}
          </h1>
        </div>
        <button
          v-if="session && !session.ended_at"
          @click="endSession"
          class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
        >
          {{ $t('sessionDetail.endSession') }}
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
        <p class="text-red-800 dark:text-red-200">{{ error }}</p>
      </div>

      <!-- Session Details -->
      <div v-else-if="session" class="space-y-6">
        <!-- Session Info Card -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {{ $t('sessionDetail.sessionInfo') }}
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <span class="text-gray-500 dark:text-gray-400">{{ $t('sessionDetail.user') }}:</span>
              <span class="ml-2 text-gray-900 dark:text-white">
                {{ getUserName(session.user_id) || $t('sessionDetail.unknown') }}
              </span>
            </div>
            <div>
              <span class="text-gray-500 dark:text-gray-400">{{ $t('sessionDetail.caregiver') }}:</span>
              <span class="ml-2 text-gray-900 dark:text-white">
                {{ getCaregiverName(session.caregiver_id) || $t('sessionDetail.unknown') }}
              </span>
            </div>
            <div>
              <span class="text-gray-500 dark:text-gray-400">{{ $t('sessionDetail.startedAt') }}:</span>
              <span class="ml-2 text-gray-900 dark:text-white">
                {{ formatDateTime(session.started_at) }}
              </span>
            </div>
            <div v-if="session.ended_at">
              <span class="text-gray-500 dark:text-gray-400">{{ $t('sessionDetail.endedAt') }}:</span>
              <span class="ml-2 text-gray-900 dark:text-white">
                {{ formatDateTime(session.ended_at) }}
              </span>
            </div>
            <div>
              <span class="text-gray-500 dark:text-gray-400">{{ $t('sessionDetail.status') }}:</span>
              <span
                :class="[
                  'ml-2 px-2 py-1 rounded-full text-xs font-medium',
                  session.ended_at
                    ? 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                    : 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                ]"
              >
                {{ session.ended_at ? $t('sessionDetail.ended') : $t('sessionDetail.active') }}
              </span>
            </div>
            <div>
              <span class="text-gray-500 dark:text-gray-400">{{ $t('sessionDetail.totalSteps') }}:</span>
              <span class="ml-2 text-gray-900 dark:text-white">
                {{ session.steps ? session.steps.length : 0 }}
              </span>
            </div>
          </div>
        </div>

        <!-- Conversation History -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              {{ $t('sessionDetail.conversationHistory') }}
            </h2>
            <label class="flex items-center space-x-2 cursor-pointer">
              <span class="text-sm text-gray-700 dark:text-gray-300">
                {{ $t('sessionDetail.showChoices') }}
              </span>
              <input
                type="checkbox"
                v-model="showChoices"
                class="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
              />
            </label>
          </div>
          <div v-if="session.steps && session.steps.length > 0" class="space-y-6">
            <div
              v-for="(step, index) in session.steps"
              :key="step.id"
              class="border-l-4 pl-4 pb-4"
              :class="[
                step.message_role === 'caregiver' ? 'border-blue-500' : 'border-green-500'
              ]"
            >
              <!-- Message Content with Badge -->
              <div v-if="step.message_content" class="mb-3 flex items-start space-x-3">
                <span
                  :class="[
                    'px-2 py-1 rounded-full text-xs font-medium flex-shrink-0',
                    step.message_role === 'caregiver'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200'
                      : 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                  ]"
                >
                  {{ step.message_role === 'caregiver' 
                    ? (getCaregiverName(session.caregiver_id) || $t('sessionDetail.caregiver'))
                    : (getUserName(session.user_id) || $t('sessionDetail.user')) }}
                </span>
                <div class="flex-1">
                  <p class="text-gray-900 dark:text-white font-medium">
                    {{ step.message_content }}
                  </p>
                </div>
                <span class="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                  {{ formatDateTime(step.timestamp) }}
                </span>
              </div>

              <!-- Choices from Previous Step (shown below message to understand context) -->
              <div v-if="showChoices && index > 0 && session.steps[index - 1].choices && session.steps[index - 1].choices.length > 0" class="mb-3">
                <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {{ $t('sessionDetail.availableChoices') }}:
                </p>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <div
                    v-for="choice in session.steps[index - 1].choices"
                    :key="choice.text"
                    :class="[
                      'p-3 rounded-lg border-2 transition-colors',
                      choice.text === session.steps[index - 1].selected_choice_text
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50'
                    ]"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-gray-900 dark:text-white font-medium">
                        {{ choice.text }}
                      </span>
                      <span class="text-xs text-gray-500 dark:text-gray-400">
                        {{ (choice.probability * 100).toFixed(1) }}%
                      </span>
                    </div>
                    <div v-if="choice.text === session.steps[index - 1].selected_choice_text" class="mt-2">
                      <span class="text-xs font-medium text-primary-600 dark:text-primary-400">
                        ✓ {{ $t('sessionDetail.selected') }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Selected Choice from Previous Step (if different from choices) -->
              <div v-if="showChoices && index > 0 && session.steps[index - 1].selected_choice_text && (!session.steps[index - 1].choices || !session.steps[index - 1].choices.find(c => c.text === session.steps[index - 1].selected_choice_text))" class="mb-3">
                <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {{ $t('sessionDetail.selectedChoice') }}:
                </p>
                <p class="text-gray-900 dark:text-white font-medium">
                  {{ session.steps[index - 1].selected_choice_text }}
                </p>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
            {{ $t('sessionDetail.noSteps') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ArrowLeftIcon } from '@heroicons/vue/24/outline';
import { sessionsAPI, usersAPI, caregiversAPI } from '../services/api';

const router = useRouter();
const route = useRoute();
const { t } = useI18n();

const sessionId = ref(parseInt(route.params.id));
const session = ref(null);
const users = ref([]);
const caregivers = ref([]);
const loading = ref(false);
const error = ref(null);
const showChoices = ref(false);

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

const loadSession = async () => {
  loading.value = true;
  error.value = null;
  try {
    const data = await sessionsAPI.get(sessionId.value);
    session.value = data;
  } catch (err) {
    console.error('Error loading session:', err);
    error.value = t('sessionDetail.errorLoading');
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

const goBack = () => {
  router.push('/communication-sessions');
};

const endSession = async () => {
  try {
    await sessionsAPI.update(sessionId.value, {
      ended_at: new Date().toISOString()
    });
    await loadSession();
  } catch (err) {
    console.error('Error ending session:', err);
    error.value = t('sessionDetail.errorEnding');
  }
};

onMounted(async () => {
  await Promise.all([loadUsers(), loadCaregivers(), loadSession()]);
});
</script>

