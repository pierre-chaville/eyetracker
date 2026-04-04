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
        <div class="flex flex-wrap items-center gap-2">
          <button
            v-if="session"
            type="button"
            :disabled="analyzing"
            @click="runAiAnalysis"
            class="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-60 disabled:cursor-not-allowed text-white rounded-lg transition-colors touch-manipulation"
          >
            <span v-if="analyzing">{{ $t('sessionDetail.analyzing') }}</span>
            <span v-else-if="session.ai_analysis_markdown">{{ $t('sessionDetail.runAiAnalysisAgain') }}</span>
            <span v-else>{{ $t('sessionDetail.runAiAnalysis') }}</span>
          </button>
          <button
            v-if="session && !session.ended_at"
            @click="endSession"
            class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            {{ $t('sessionDetail.endSession') }}
          </button>
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

        <!-- Session Context (expandable) -->
        <div
          v-if="session.prompt || session.llm_model || session.temperature != null || session.user_notes || session.keyboard_layout_name"
          class="bg-white dark:bg-gray-800 rounded-lg shadow-md"
        >
          <button
            @click="showContext = !showContext"
            class="w-full flex items-center justify-between p-6 text-left focus:outline-none"
          >
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              {{ $t('sessionDetail.sessionContext') }}
            </h2>
            <ChevronDownIcon
              :class="['w-5 h-5 text-gray-500 transition-transform duration-200', showContext ? 'rotate-180' : '']"
            />
          </button>
          <div v-if="showContext" class="px-6 pb-6 space-y-4">
            <div v-if="session.llm_model || session.temperature != null" class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div v-if="session.llm_model">
                <span class="text-sm text-gray-500 dark:text-gray-400">{{ $t('sessionDetail.llmModel') }}</span>
                <p class="text-gray-900 dark:text-white font-medium">{{ session.llm_model }}</p>
              </div>
              <div v-if="session.temperature != null">
                <span class="text-sm text-gray-500 dark:text-gray-400">{{ $t('sessionDetail.temperature') }}</span>
                <p class="text-gray-900 dark:text-white font-medium">{{ session.temperature }}</p>
              </div>
            </div>
            <div v-if="session.keyboard_layout_name">
              <span class="text-sm text-gray-500 dark:text-gray-400">{{ $t('sessionDetail.keyboardLayout') }}</span>
              <p class="text-gray-900 dark:text-white font-medium">{{ session.keyboard_layout_name }}</p>
            </div>
            <div v-if="session.prompt">
              <span class="text-sm text-gray-500 dark:text-gray-400">{{ $t('sessionDetail.prompt') }}</span>
              <p class="mt-1 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 whitespace-pre-wrap">{{ session.prompt }}</p>
            </div>
            <div v-if="session.user_notes">
              <span class="text-sm text-gray-500 dark:text-gray-400">{{ $t('sessionDetail.userNotes') }}</span>
              <p class="mt-1 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 whitespace-pre-wrap">{{ session.user_notes }}</p>
            </div>
          </div>
        </div>

        <!-- Session Feedback (expandable) -->
        <div
          v-if="session.feedback && Object.keys(session.feedback).length > 0"
          class="bg-white dark:bg-gray-800 rounded-lg shadow-md"
        >
          <button
            @click="showFeedback = !showFeedback"
            class="w-full flex items-center justify-between p-6 text-left focus:outline-none"
          >
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              {{ $t('feedback.viewTitle') }}
            </h2>
            <ChevronDownIcon
              :class="['w-5 h-5 text-gray-500 transition-transform duration-200', showFeedback ? 'rotate-180' : '']"
            />
          </button>
          <div v-if="showFeedback" class="px-6 pb-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div v-for="(value, key) in session.feedback" :key="key" class="py-2">
                <template v-if="key !== 'quick_note'">
                  <span class="text-sm text-gray-500 dark:text-gray-400">{{ feedbackLabel(key as string) }}</span>
                  <p class="text-gray-900 dark:text-white font-medium mt-0.5">
                    <template v-if="Array.isArray(value)">
                      <span
                        v-for="(item, idx) in value"
                        :key="idx"
                        class="inline-block mr-1 mb-1 px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                      >
                        {{ feedbackValueLabel(key as string, item) }}
                      </span>
                    </template>
                    <template v-else>
                      {{ feedbackValueLabel(key as string, value as string) }}
                    </template>
                  </p>
                </template>
              </div>
            </div>
            <div v-if="session.feedback.quick_note" class="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
              <span class="text-sm text-gray-500 dark:text-gray-400">{{ $t('feedback.sections.note') }}</span>
              <p class="mt-1 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 whitespace-pre-wrap">{{ session.feedback.quick_note }}</p>
            </div>
          </div>
        </div>

        <!-- AI analysis (expandable, Markdown) -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md">
          <button
            type="button"
            @click="showAiAnalysis = !showAiAnalysis"
            class="w-full flex items-center justify-between p-6 text-left focus:outline-none"
          >
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              {{ $t('sessionDetail.aiAnalysis') }}
            </h2>
            <ChevronDownIcon
              :class="['w-5 h-5 text-gray-500 transition-transform duration-200 shrink-0', showAiAnalysis ? 'rotate-180' : '']"
            />
          </button>
          <div v-if="showAiAnalysis" class="px-6 pb-6">
            <div
              v-if="analysisError"
              class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-800 dark:text-red-200"
            >
              {{ analysisError }}
            </div>
            <SessionAnalysisMarkdown
              v-if="session.ai_analysis_markdown"
              :source="session.ai_analysis_markdown"
            />
            <p
              v-else
              class="text-sm text-gray-500 dark:text-gray-400"
            >
              {{ $t('sessionDetail.aiAnalysisEmpty') }}
            </p>
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
                <div class="flex flex-col items-end flex-shrink-0 space-y-1">
                  <span class="text-xs text-gray-500 dark:text-gray-400">
                    {{ formatDateTime(step.timestamp) }}
                  </span>
                  <div v-if="step.activation_mode" class="flex items-center space-x-1">
                    <span
                      :class="[
                        'px-1.5 py-0.5 rounded text-[10px] font-medium',
                        step.activation_mode === 'gaze_dwell'
                          ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                      ]"
                    >
                      {{ step.activation_mode === 'gaze_dwell' ? $t('sessionDetail.gazeDwell') : $t('sessionDetail.click') }}
                    </span>
                    <span v-if="step.dwell_time_ms" class="text-[10px] text-gray-400 dark:text-gray-500">
                      {{ (step.dwell_time_ms / 1000).toFixed(1) }}s
                    </span>
                  </div>
                </div>
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

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ArrowLeftIcon, ChevronDownIcon } from '@heroicons/vue/24/outline';
import SessionAnalysisMarkdown from '../components/SessionAnalysisMarkdown.vue';
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
const showContext = ref(false);
const showFeedback = ref(false);
const showAiAnalysis = ref(false);
const analyzing = ref(false);
const analysisError = ref<string | null>(null);

const FEEDBACK_FIELD_MAP: Record<string, string> = {
  state_before: 'feedback.stateBefore',
  mood_before: 'feedback.moodBefore',
  gaze_accuracy: 'feedback.gazeAccuracy',
  calibration_quality: 'feedback.calibrationQuality',
  head_stability: 'feedback.headStability',
  intentional_selections: 'feedback.intentionalSelections',
  choices_relevance: 'feedback.choicesRelevance',
  communication_pace: 'feedback.communicationPace',
  engagement_level: 'feedback.engagementLevel',
  enjoyment: 'feedback.enjoyment',
  session_end_reason: 'feedback.sessionEndReason',
  overall_rating: 'feedback.overallRating',
  compared_previous: 'feedback.comparedPrevious',
  key_achievements: 'feedback.keyAchievements',
};

const feedbackLabel = (key: string): string => {
  const prefix = FEEDBACK_FIELD_MAP[key];
  return prefix ? t(`${prefix}.label`) : key;
};

const feedbackValueLabel = (key: string, value: string): string => {
  const prefix = FEEDBACK_FIELD_MAP[key];
  if (!prefix) return value;
  const path = `${prefix}.${value}`;
  const translated = t(path);
  return translated !== path ? translated : value;
};

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

const runAiAnalysis = async () => {
  analysisError.value = null;
  analyzing.value = true;
  try {
    const data = await sessionsAPI.analyze(sessionId.value);
    session.value = data;
    showAiAnalysis.value = true;
  } catch (err: unknown) {
    const ax = err as { response?: { data?: { detail?: string } }; message?: string };
    const detail = ax.response?.data?.detail;
    analysisError.value =
      typeof detail === 'string'
        ? detail
        : ax.message || t('sessionDetail.aiAnalysisError');
    showAiAnalysis.value = true;
    console.error('Error running session analysis:', err);
  } finally {
    analyzing.value = false;
  }
};

onMounted(async () => {
  await Promise.all([loadUsers(), loadCaregivers(), loadSession()]);
});
</script>

