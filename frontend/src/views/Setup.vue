<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-6">
        {{ $t('setup.title') }}
      </h1>

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
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
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
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
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
            class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
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
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm"
            :placeholder="$t('setup.promptPlaceholder')"
          />
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ $t('setup.promptDescription') }}
          </p>
        </div>

        <!-- UI Adjustments Section -->
        <div class="border-t border-gray-200 dark:border-gray-700 pt-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {{ $t('setup.uiAdjustments') }}
          </h2>

          <!-- Header Height Adjustment -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('setup.headerHeightAdjustment') }} (px)
            </label>
            <input
              v-model.number="config.header_height_adjustment"
              type="number"
              step="1"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              :placeholder="$t('setup.headerHeightPlaceholder')"
            />
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ $t('setup.headerHeightDescription') }}
            </p>
          </div>

          <!-- Menu Width Adjustment -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('setup.menuWidthAdjustment') }} (px)
            </label>
            <input
              v-model.number="config.menu_width_adjustment"
              type="number"
              step="1"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              :placeholder="$t('setup.menuWidthPlaceholder')"
            />
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ $t('setup.menuWidthDescription') }}
            </p>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex space-x-3 pt-6 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            @click="loadConfig"
            class="px-6 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
          >
            {{ $t('setup.reset') }}
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
import { configAPI } from '../services/api';

const { t } = useI18n();

const config = ref({
  provider: 'openai',
  model: '',
  temperature: 0.7,
  prompt: '',
  header_height_adjustment: 0,
  menu_width_adjustment: 0,
});

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
    config.value = {
      provider: data.provider || 'openai',
      model: data.model || '',
      temperature: data.temperature ?? 0.7,
      prompt: data.prompt || '',
      header_height_adjustment: data.header_height_adjustment ?? 0,
      menu_width_adjustment: data.menu_width_adjustment ?? 0,
    };
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('setup.loadError');
    console.error('Error loading config:', err);
  } finally {
    loading.value = false;
  }
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
    
    await configAPI.update(config.value);
    successMessage.value = t('setup.saveSuccess');
    
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
