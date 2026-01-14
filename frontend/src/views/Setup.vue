<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
          {{ $t('setup.title') }}
        </h1>
        <button
          v-if="!isEditMode"
          @click="enterEditMode"
          class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors flex items-center space-x-2"
        >
          <PencilIcon class="w-5 h-5" />
          <span>{{ $t('setup.edit') }}</span>
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

      <!-- Success Message -->
      <div
        v-if="successMessage"
        class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-6"
      >
        <p class="text-green-800 dark:text-green-200">{{ successMessage }}</p>
      </div>

      <!-- Configuration Form -->
      <form v-else @submit.prevent="saveConfig" class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 space-y-6">
        <!-- AI Provider -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ $t('setup.provider') }}
          </label>
          <select
            v-model="config.provider"
            :disabled="!isEditMode"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google</option>
            <option value="azure">Azure</option>
          </select>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ $t('setup.providerDescription') }}
          </p>
        </div>

        <!-- Model -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ $t('setup.model') }}
          </label>
          <input
            v-model="config.model"
            type="text"
            :disabled="!isEditMode"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
            :placeholder="$t('setup.modelPlaceholder')"
          />
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ $t('setup.modelDescription') }}
          </p>
        </div>

        <!-- Temperature -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ $t('setup.temperature') }}: {{ config.temperature.toFixed(1) }}
          </label>
          <input
            v-model.number="config.temperature"
            type="range"
            min="0"
            max="2"
            step="0.1"
            :disabled="!isEditMode"
            class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none disabled:cursor-not-allowed"
            :class="isEditMode ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'"
          />
          <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
            <span>0.0</span>
            <span>1.0</span>
            <span>2.0</span>
          </div>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ $t('setup.temperatureDescription') }}
          </p>
        </div>

        <!-- Prompt -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ $t('setup.prompt') }}
          </label>
          <textarea
            v-model="config.prompt"
            rows="6"
            :disabled="!isEditMode"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
            :placeholder="$t('setup.promptPlaceholder')"
          />
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ $t('setup.promptDescription') }}
          </p>
        </div>

        <!-- TTS Configuration Section -->
        <div class="pt-6 border-t border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {{ $t('setup.tts.title') }}
          </h2>

          <!-- TTS Language -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('setup.tts.language') }}
            </label>
            <select
              v-model="config.tts_language"
              :disabled="!isEditMode"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
            >
              <option value="fr">Français (fr-FR)</option>
              <option value="en">English (en-US)</option>
              <option value="es">Español (es-ES)</option>
              <option value="de">Deutsch (de-DE)</option>
              <option value="it">Italiano (it-IT)</option>
            </select>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ $t('setup.tts.languageDescription') }}
            </p>
          </div>

          <!-- TTS Voice Name -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('setup.tts.voiceName') }}
            </label>
            <input
              v-model="config.tts_voice_name"
              type="text"
              :disabled="!isEditMode"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
              :placeholder="$t('setup.tts.voiceNamePlaceholder')"
            />
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ $t('setup.tts.voiceNameDescription') }}
            </p>
          </div>

          <!-- TTS Pitch -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('setup.tts.pitch') }}: {{ config.tts_pitch.toFixed(1) }} {{ $t('setup.tts.semitones') }}
            </label>
            <input
              v-model.number="config.tts_pitch"
              type="range"
              min="-20"
              max="20"
              step="0.1"
              :disabled="!isEditMode"
              class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none disabled:cursor-not-allowed"
              :class="isEditMode ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'"
            />
            <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>-20.0</span>
              <span>0.0</span>
              <span>20.0</span>
            </div>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ $t('setup.tts.pitchDescription') }}
            </p>
          </div>

          <!-- TTS Speaking Rate -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('setup.tts.speakingRate') }}: {{ config.tts_speaking_rate.toFixed(2) }}x
            </label>
            <input
              v-model.number="config.tts_speaking_rate"
              type="range"
              min="0.25"
              max="4.0"
              step="0.05"
              :disabled="!isEditMode"
              class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none disabled:cursor-not-allowed"
              :class="isEditMode ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'"
            />
            <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>0.25x</span>
              <span>1.0x</span>
              <span>4.0x</span>
            </div>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ $t('setup.tts.speakingRateDescription') }}
            </p>
          </div>
        </div>

        <!-- Action Buttons (only shown in edit mode) -->
        <div v-if="isEditMode" class="flex space-x-3 pt-6 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            @click="cancelEdit"
            class="flex-1 px-6 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors font-medium"
          >
            {{ $t('setup.cancel') }}
          </button>
          <button
            type="submit"
            :disabled="saving"
            class="flex-1 px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50 font-medium"
          >
            {{ saving ? $t('setup.saving') : $t('setup.save') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { PencilIcon } from '@heroicons/vue/24/outline';
import { configAPI } from '../services/api';

const { t } = useI18n();

const config = ref({
  provider: 'openai',
  model: '',
  temperature: 0.7,
  prompt: '',
  tts_language: 'fr',
  tts_voice_name: '',
  tts_pitch: 0.0,
  tts_speaking_rate: 1.0,
});

const originalConfig = ref({});
const isEditMode = ref(false);
const loading = ref(true);
const saving = ref(false);
const error = ref(null);
const successMessage = ref(null);

const loadConfig = async () => {
  try {
    loading.value = true;
    error.value = null;
    successMessage.value = null;
    const data = await configAPI.get();
    const loadedConfig = {
      provider: data.provider || 'openai',
      model: data.model || '',
      temperature: data.temperature ?? 0.7,
      prompt: data.prompt || '',
      tts_language: data.tts_language || 'fr',
      tts_voice_name: data.tts_voice_name || '',
      tts_pitch: data.tts_pitch ?? 0.0,
      tts_speaking_rate: data.tts_speaking_rate ?? 1.0,
    };
    config.value = { ...loadedConfig };
    originalConfig.value = { ...loadedConfig };
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('setup.loadError');
    console.error('Error loading config:', err);
  } finally {
    loading.value = false;
  }
};

const enterEditMode = () => {
  // Store current config as original before editing
  originalConfig.value = { ...config.value };
  isEditMode.value = true;
};

const cancelEdit = () => {
  // Revert to original config
  config.value = { ...originalConfig.value };
  isEditMode.value = false;
  error.value = null;
  successMessage.value = null;
};

const saveConfig = async () => {
  try {
    saving.value = true;
    error.value = null;
    successMessage.value = null;
    
    // Validate temperature
    if (config.value.temperature < 0 || config.value.temperature > 2) {
      error.value = t('setup.temperatureRangeError');
      return;
    }
    
    // Validate TTS pitch
    if (config.value.tts_pitch < -20 || config.value.tts_pitch > 20) {
      error.value = t('setup.tts.pitchRangeError');
      return;
    }
    
    // Validate TTS speaking rate
    if (config.value.tts_speaking_rate < 0.25 || config.value.tts_speaking_rate > 4.0) {
      error.value = t('setup.tts.speakingRateRangeError');
      return;
    }
    
    await configAPI.update(config.value);
    // Update original config to match saved config
    originalConfig.value = { ...config.value };
    successMessage.value = t('setup.saveSuccess');
    
    // Exit edit mode after successful save
    isEditMode.value = false;
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      successMessage.value = null;
    }, 3000);
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('setup.saveError');
    console.error('Error saving config:', err);
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  loadConfig();
});
</script>
