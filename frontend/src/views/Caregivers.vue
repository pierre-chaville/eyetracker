<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
          {{ $t('caregivers.title') }}
        </h1>
        <button
          @click="showCreateModal = true"
          class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors flex items-center space-x-2"
        >
          <PlusIcon class="w-5 h-5" />
          <span>{{ $t('caregivers.createCaregiver') }}</span>
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

      <!-- Caregivers Grid -->
      <div v-else-if="caregivers.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="caregiver in caregivers"
          :key="caregiver.id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow p-6"
        >
          <div class="flex items-start justify-between mb-4">
            <div>
              <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-1">
                {{ caregiver.name }}
              </h3>
              <p v-if="caregiver.gender" class="text-sm text-gray-500 dark:text-gray-400">
                {{ $t('caregivers.gender') }}: {{ caregiver.gender }}
              </p>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ $t('caregivers.createdAt') }}: {{ formatDate(caregiver.created_at) }}
              </p>
            </div>
          </div>

          <div class="mb-4">
            <p v-if="caregiver.description" class="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
              {{ caregiver.description }}
            </p>
            <p v-else class="text-sm text-gray-400 dark:text-gray-500 italic">
              {{ $t('caregivers.noDescription') }}
            </p>
          </div>

          <div class="flex space-x-2">
            <button
              @click="$router.push(`/caregivers/${caregiver.id}`)"
              class="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors text-sm font-medium"
            >
              {{ $t('caregivers.view') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-12 text-center">
        <UserGroupIcon class="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4" />
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          {{ $t('caregivers.noCaregivers') }}
        </h3>
        <p class="text-gray-600 dark:text-gray-400 mb-6">
          {{ $t('caregivers.noCaregiversDescription') }}
        </p>
        <button
          @click="showCreateModal = true"
          class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
        >
          {{ $t('caregivers.createCaregiver') }}
        </button>
      </div>

      <!-- Create Caregiver Modal -->
      <div
        v-if="showCreateModal"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        @click.self="showCreateModal = false"
      >
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            {{ $t('caregivers.createCaregiver') }}
          </h2>
          <form @submit.prevent="createCaregiver">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ $t('caregivers.name') }}
              </label>
              <input
                v-model="newCaregiver.name"
                type="text"
                required
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                :placeholder="$t('caregivers.namePlaceholder')"
              />
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ $t('caregivers.gender') }}
              </label>
              <select
                v-model="newCaregiver.gender"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">{{ $t('caregivers.genderNotSpecified') }}</option>
                <option value="Male">{{ $t('caregivers.genderMale') }}</option>
                <option value="Female">{{ $t('caregivers.genderFemale') }}</option>
                <option value="Other">{{ $t('caregivers.genderOther') }}</option>
              </select>
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ $t('caregivers.description') }}
              </label>
              <textarea
                v-model="newCaregiver.description"
                rows="4"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                :placeholder="$t('caregivers.descriptionPlaceholder')"
              />
            </div>
            <div class="flex space-x-3">
              <button
                type="button"
                @click="showCreateModal = false"
                class="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
              >
                {{ $t('caregivers.cancel') }}
              </button>
              <button
                type="submit"
                :disabled="creating"
                class="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {{ creating ? $t('caregivers.creating') : $t('caregivers.create') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { caregiversAPI } from '../services/api';
import { PlusIcon, UserGroupIcon } from '@heroicons/vue/24/outline';

const router = useRouter();
const { t } = useI18n();

const caregivers = ref([]);
const loading = ref(true);
const error = ref(null);
const showCreateModal = ref(false);
const creating = ref(false);
const newCaregiver = ref({
  name: '',
  gender: '',
  description: '',
});

const loadCaregivers = async () => {
  try {
    loading.value = true;
    error.value = null;
    caregivers.value = await caregiversAPI.list();
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('caregivers.loadError');
    console.error('Error loading caregivers:', err);
  } finally {
    loading.value = false;
  }
};

const createCaregiver = async () => {
  try {
    creating.value = true;
    await caregiversAPI.create(newCaregiver.value);
    showCreateModal.value = false;
    newCaregiver.value = { name: '', gender: '', description: '' };
    await loadCaregivers();
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('caregivers.createError');
    console.error('Error creating caregiver:', err);
  } finally {
    creating.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

onMounted(() => {
  loadCaregivers();
});
</script>

