<template>
  <div
    class="fixed inset-0 z-50 flex items-stretch justify-stretch bg-black/60 backdrop-blur-sm p-2 sm:p-3"
  >
    <div
      class="flex flex-col flex-1 min-h-0 min-w-0 bg-white dark:bg-gray-800 rounded-2xl shadow-2xl overflow-hidden max-h-[100dvh]"
    >
      <!-- Header -->
      <div
        class="shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 sm:px-6 py-3 sm:py-4 z-10"
      >
        <h2 class="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">{{ $t('feedback.title') }}</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ $t('feedback.subtitle') }}</p>
      </div>

      <div class="flex-1 min-h-0 overflow-y-auto px-4 sm:px-6 py-4 space-y-6">

        <!-- Session Outcome (first — expected to always be filled) -->
        <SessionFeedbackSection :title="$t('feedback.sections.outcome')">
          <SessionFeedbackRadioGroup
            :label="$t('feedback.overallRating.label')"
            v-model="form.overall_rating"
            :options="overallRatingOptions"
          />
          <SessionFeedbackRadioGroup
            :label="$t('feedback.comparedPrevious.label')"
            v-model="form.compared_previous"
            :options="comparedPreviousOptions"
          />

          <!-- Key Achievements (multi-select) -->
          <div class="space-y-2">
            <p class="text-sm font-semibold text-gray-700 dark:text-gray-300">{{ $t('feedback.keyAchievements.label') }}</p>
            <div class="flex flex-nowrap gap-2 overflow-x-auto pb-1 -mx-1 px-1">
              <button
                v-for="opt in keyAchievementsOptions"
                :key="opt.value"
                type="button"
                @click="toggleAchievement(opt.value)"
                :class="[
                  'shrink-0 whitespace-nowrap px-4 py-2 rounded-lg text-sm font-medium border-2 transition-all duration-150',
                  form.key_achievements.includes(opt.value)
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                    : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:border-gray-300'
                ]"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>
        </SessionFeedbackSection>

        <!-- Engagement & Enjoyment (2nd) -->
        <SessionFeedbackSection :title="$t('feedback.sections.engagement')">
          <SessionFeedbackRadioGroup
            :label="$t('feedback.engagementLevel.label')"
            v-model="form.engagement_level"
            :options="engagementLevelOptions"
          />
          <SessionFeedbackRadioGroup
            :label="$t('feedback.enjoyment.label')"
            v-model="form.enjoyment"
            :options="enjoymentOptions"
          />
          <SessionFeedbackRadioGroup
            :label="$t('feedback.sessionEndReason.label')"
            v-model="form.session_end_reason"
            :options="sessionEndReasonOptions"
          />
        </SessionFeedbackSection>

        <!-- Communication & Interaction (3rd) -->
        <SessionFeedbackSection :title="$t('feedback.sections.communication')">
          <SessionFeedbackRadioGroup
            :label="$t('feedback.intentionalSelections.label')"
            v-model="form.intentional_selections"
            :options="intentionalSelectionsOptions"
          />
          <SessionFeedbackRadioGroup
            :label="$t('feedback.choicesRelevance.label')"
            v-model="form.choices_relevance"
            :options="choicesRelevanceOptions"
          />
          <SessionFeedbackRadioGroup
            :label="$t('feedback.communicationPace.label')"
            v-model="form.communication_pace"
            :options="communicationPaceOptions"
          />
        </SessionFeedbackSection>

        <!-- Session Context (before) -->
        <SessionFeedbackSection :title="$t('feedback.sections.context')">
          <SessionFeedbackRadioGroup
            :label="$t('feedback.stateBefore.label')"
            v-model="form.state_before"
            :options="stateBeforeOptions"
          />
          <SessionFeedbackRadioGroup
            :label="$t('feedback.moodBefore.label')"
            v-model="form.mood_before"
            :options="moodBeforeOptions"
          />
        </SessionFeedbackSection>

        <!-- Eye-Tracking Performance -->
        <SessionFeedbackSection :title="$t('feedback.sections.eyeTracking')">
          <SessionFeedbackRadioGroup
            :label="$t('feedback.gazeAccuracy.label')"
            v-model="form.gaze_accuracy"
            :options="gazeAccuracyOptions"
          />
          <SessionFeedbackRadioGroup
            :label="$t('feedback.calibrationQuality.label')"
            v-model="form.calibration_quality"
            :options="calibrationQualityOptions"
          />
          <SessionFeedbackRadioGroup
            :label="$t('feedback.headStability.label')"
            v-model="form.head_stability"
            :options="headStabilityOptions"
          />
        </SessionFeedbackSection>

        <!-- Quick Note -->
        <SessionFeedbackSection :title="$t('feedback.sections.note')">
          <textarea
            v-model="form.quick_note"
            :placeholder="$t('feedback.quickNote.placeholder')"
            rows="3"
            class="w-full rounded-lg border-2 border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-4 py-3 text-base focus:border-primary-500 focus:ring-0 resize-none"
          />
        </SessionFeedbackSection>
      </div>

      <!-- Footer -->
      <div
        class="shrink-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-4 sm:px-6 py-3 sm:py-4 flex justify-between gap-4"
      >
        <button
          @click="$emit('skip')"
          class="px-6 py-3 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 font-medium transition-colors"
        >
          {{ $t('feedback.skip') }}
        </button>
        <button
          @click="submit"
          class="px-8 py-3 rounded-lg bg-primary-600 hover:bg-primary-700 text-white font-semibold transition-colors"
        >
          {{ $t('feedback.submit') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import SessionFeedbackSection from './SessionFeedbackSection.vue';
import SessionFeedbackRadioGroup from './SessionFeedbackRadioGroup.vue';

const { t } = useI18n();

const emit = defineEmits<{
  (e: 'submit', feedback: Record<string, unknown>): void;
  (e: 'skip'): void;
}>();

const form = reactive({
  state_before: '',
  mood_before: '',
  gaze_accuracy: '',
  calibration_quality: '',
  head_stability: '',
  intentional_selections: '',
  choices_relevance: '',
  communication_pace: '',
  engagement_level: '',
  enjoyment: '',
  session_end_reason: '',
  overall_rating: '',
  compared_previous: '',
  key_achievements: [] as string[],
  quick_note: '',
});

const toggleAchievement = (value: string) => {
  const idx = form.key_achievements.indexOf(value);
  if (idx >= 0) {
    form.key_achievements.splice(idx, 1);
  } else {
    form.key_achievements.push(value);
  }
};

const submit = () => {
  const feedback: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(form)) {
    if (key === 'key_achievements') {
      if ((value as string[]).length > 0) feedback[key] = value;
    } else if (value) {
      feedback[key] = value;
    }
  }
  emit('submit', feedback);
};

// Option builders using i18n
const makeOptions = (prefix: string, keys: string[]) =>
  computed(() => keys.map(k => ({ value: k, label: t(`${prefix}.${k}`) })));

const stateBeforeOptions = makeOptions('feedback.stateBefore', [
  'alert_engaged', 'calm_passive', 'tired', 'agitated', 'unwell',
]);
const moodBeforeOptions = makeOptions('feedback.moodBefore', [
  'happy', 'neutral', 'upset', 'hard_to_tell',
]);
const gazeAccuracyOptions = makeOptions('feedback.gazeAccuracy', [
  'very_accurate', 'mostly_accurate', 'inconsistent', 'poor',
]);
const calibrationQualityOptions = makeOptions('feedback.calibrationQuality', [
  'good', 'acceptable', 'difficult', 'failed',
]);
const headStabilityOptions = makeOptions('feedback.headStability', [
  'stable', 'some_movement', 'frequent_repositioning', 'could_not_maintain',
]);
const intentionalSelectionsOptions = makeOptions('feedback.intentionalSelections', [
  'yes_clearly', 'mostly', 'unclear', 'mostly_accidental',
]);
const choicesRelevanceOptions = makeOptions('feedback.choicesRelevance', [
  'very_relevant', 'somewhat_relevant', 'not_relevant', 'hard_to_assess',
]);
const communicationPaceOptions = makeOptions('feedback.communicationPace', [
  'too_fast', 'good', 'too_slow',
]);
const engagementLevelOptions = makeOptions('feedback.engagementLevel', [
  'highly_engaged', 'moderately_engaged', 'low_engagement', 'refused',
]);
const enjoymentOptions = makeOptions('feedback.enjoyment', [
  'clearly_enjoyed', 'neutral', 'frustrated', 'hard_to_tell',
]);
const sessionEndReasonOptions = makeOptions('feedback.sessionEndReason', [
  'planned_duration', 'fatigue', 'agitated', 'technical_issue', 'disengaged', 'external_interruption',
]);
const overallRatingOptions = makeOptions('feedback.overallRating', [
  'excellent', 'good', 'fair', 'poor',
]);
const comparedPreviousOptions = makeOptions('feedback.comparedPrevious', [
  'better', 'same', 'worse', 'first_session',
]);
const keyAchievementsOptions = makeOptions('feedback.keyAchievements', [
  'made_request', 'expressed_emotion', 'responded_question', 'initiated_communication',
  'sustained_interaction', 'none_notable',
]);
</script>
