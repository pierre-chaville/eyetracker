<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
    <div class="max-w-4xl mx-auto">
      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
        <p class="text-red-800 dark:text-red-200">{{ error }}</p>
        <button
          @click="$router.push('/caregivers')"
          class="mt-4 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
        >
          {{ $t('caregiverDetail.backToCaregivers') }}
        </button>
      </div>

      <!-- Caregiver Detail -->
      <div v-else-if="caregiver" class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <!-- Header -->
        <div class="flex items-start justify-between mb-6">
          <div>
            <button
              @click="$router.push('/caregivers')"
              class="mb-4 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white flex items-center space-x-2"
            >
              <ArrowLeftIcon class="w-5 h-5" />
              <span>{{ $t('caregiverDetail.back') }}</span>
            </button>
            <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
              {{ caregiver.name }}
            </h1>
            <p v-if="caregiver.gender" class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ $t('caregivers.gender') }}: {{ caregiver.gender }}
            </p>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ $t('caregiverDetail.createdAt') }}: {{ formatDate(caregiver.created_at) }}
            </p>
          </div>
          <div class="flex space-x-2">
            <button
              @click="showEditModal = true"
              class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors flex items-center space-x-2"
            >
              <PencilIcon class="w-5 h-5" />
              <span>{{ $t('caregiverDetail.edit') }}</span>
            </button>
            <button
              @click="showDeleteModal = true"
              class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center space-x-2"
            >
              <TrashIcon class="w-5 h-5" />
              <span>{{ $t('caregiverDetail.delete') }}</span>
            </button>
          </div>
        </div>

        <!-- Description Section -->
        <div class="mb-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {{ $t('caregiverDetail.description') }}
          </h2>
          <p v-if="caregiver.description" class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
            {{ caregiver.description }}
          </p>
          <p v-else class="text-gray-400 dark:text-gray-500 italic">
            {{ $t('caregivers.noDescription') }}
          </p>
        </div>
      </div>

      <!-- Edit Modal -->
      <div
        v-if="showEditModal"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        @click.self="showEditModal = false"
      >
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            {{ $t('caregiverDetail.editCaregiver') }}
          </h2>
          <form @submit.prevent="updateCaregiver">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ $t('caregivers.name') }}
              </label>
              <input
                v-model="editForm.name"
                type="text"
                required
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ $t('caregivers.gender') }}
              </label>
              <select
                v-model="editForm.gender"
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
                v-model="editForm.description"
                rows="4"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div class="flex space-x-3">
              <button
                type="button"
                @click="showEditModal = false"
                class="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
              >
                {{ $t('caregivers.cancel') }}
              </button>
              <button
                type="submit"
                :disabled="updating"
                class="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {{ updating ? $t('caregiverDetail.updating') : $t('caregiverDetail.save') }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Delete Confirmation Modal -->
      <div
        v-if="showDeleteModal"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        @click.self="showDeleteModal = false"
      >
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            {{ $t('caregiverDetail.deleteCaregiver') }}
          </h2>
          <p class="text-gray-700 dark:text-gray-300 mb-6">
            {{ $t('caregiverDetail.deleteConfirmation', { name: caregiver?.name }) }}
          </p>
          <div class="flex space-x-3">
            <button
              @click="showDeleteModal = false"
              class="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
            >
              {{ $t('caregivers.cancel') }}
            </button>
            <button
              @click="deleteCaregiver"
              :disabled="deleting"
              class="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {{ deleting ? $t('caregiverDetail.deleting') : $t('caregiverDetail.delete') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { caregiversAPI } from '../services/api';
import {
  ArrowLeftIcon,
  PencilIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline';

const route = useRoute();
const router = useRouter();
const { t } = useI18n();

const caregiver = ref(null);
const loading = ref(true);
const error = ref(null);
const showEditModal = ref(false);
const showDeleteModal = ref(false);
const updating = ref(false);
const deleting = ref(false);
const editForm = ref({
  name: '',
  gender: '',
  description: '',
});

const loadCaregiver = async () => {
  try {
    loading.value = true;
    error.value = null;
    const caregiverId = parseInt(route.params.id);
    caregiver.value = await caregiversAPI.get(caregiverId);
    editForm.value = {
      name: caregiver.value.name,
      gender: caregiver.value.gender || '',
      description: caregiver.value.description || '',
    };
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('caregiverDetail.loadError');
    console.error('Error loading caregiver:', err);
  } finally {
    loading.value = false;
  }
};

const updateCaregiver = async () => {
  try {
    updating.value = true;
    const caregiverId = parseInt(route.params.id);
    caregiver.value = await caregiversAPI.update(caregiverId, editForm.value);
    showEditModal.value = false;
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('caregiverDetail.updateError');
    console.error('Error updating caregiver:', err);
  } finally {
    updating.value = false;
  }
};

const deleteCaregiver = async () => {
  try {
    deleting.value = true;
    const caregiverId = parseInt(route.params.id);
    await caregiversAPI.delete(caregiverId);
    router.push('/caregivers');
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('caregiverDetail.deleteError');
    console.error('Error deleting caregiver:', err);
    showDeleteModal.value = false;
  } finally {
    deleting.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

onMounted(() => {
  loadCaregiver();
});
</script>

