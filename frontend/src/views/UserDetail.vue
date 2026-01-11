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
          @click="$router.push('/users')"
          class="mt-4 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
        >
          {{ $t('userDetail.backToUsers') }}
        </button>
      </div>

      <!-- User Detail -->
      <div v-else-if="user" class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <!-- Header -->
        <div class="flex items-start justify-between mb-6">
          <div>
            <button
              @click="$router.push('/users')"
              class="mb-4 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white flex items-center space-x-2"
            >
              <ArrowLeftIcon class="w-5 h-5" />
              <span>{{ $t('userDetail.back') }}</span>
            </button>
            <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
              {{ user.name }}
            </h1>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ $t('userDetail.createdAt') }}: {{ formatDate(user.created_at) }}
            </p>
          </div>
          <div class="flex space-x-2">
            <button
              @click="showEditModal = true"
              class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors flex items-center space-x-2"
            >
              <PencilIcon class="w-5 h-5" />
              <span>{{ $t('userDetail.edit') }}</span>
            </button>
            <button
              @click="showDeleteModal = true"
              class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center space-x-2"
            >
              <TrashIcon class="w-5 h-5" />
              <span>{{ $t('userDetail.delete') }}</span>
            </button>
          </div>
        </div>

        <!-- Status Badge -->
        <div class="mb-6">
          <span
            :class="[
              'inline-block px-3 py-1 rounded-full text-sm font-medium',
              user.is_active
                ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
            ]"
          >
            {{ user.is_active ? $t('users.active') : $t('users.inactive') }}
          </span>
        </div>

        <!-- User Info Section -->
        <div class="mb-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {{ $t('userDetail.userInfo') }}
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-if="user.gender">
              <span class="text-gray-500 dark:text-gray-400">{{ $t('users.gender') }}:</span>
              <span class="ml-2 text-gray-900 dark:text-white">{{ user.gender }}</span>
            </div>
            <div v-if="user.age">
              <span class="text-gray-500 dark:text-gray-400">{{ $t('users.age') }}:</span>
              <span class="ml-2 text-gray-900 dark:text-white">{{ user.age }}</span>
            </div>
            <div v-if="user.voice" class="md:col-span-2">
              <span class="text-gray-500 dark:text-gray-400">{{ $t('users.voice') }}:</span>
              <span class="ml-2 text-gray-900 dark:text-white">{{ user.voice }}</span>
            </div>
          </div>
        </div>

        <!-- Notes Section -->
        <div class="mb-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {{ $t('userDetail.notes') }}
          </h2>
          <p v-if="user.notes" class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
            {{ user.notes }}
          </p>
          <p v-else class="text-gray-400 dark:text-gray-500 italic">
            {{ $t('users.noNotes') }}
          </p>
        </div>

        <!-- Eye Tracking Setup -->
        <div class="mb-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {{ $t('userDetail.eyeTrackingSetup') }}
          </h2>
          <div v-if="user.eye_tracking_setup" class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
            <pre class="text-sm text-gray-700 dark:text-gray-300 overflow-x-auto">{{ JSON.stringify(user.eye_tracking_setup, null, 2) }}</pre>
          </div>
          <p v-else class="text-gray-400 dark:text-gray-500 italic">
            {{ $t('userDetail.notConfigured') }}
          </p>
        </div>

        <!-- Communication Settings -->
        <div class="mb-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {{ $t('userDetail.communicationSettings') }}
          </h2>
          <div v-if="user.communication" class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
            <pre class="text-sm text-gray-700 dark:text-gray-300 overflow-x-auto">{{ JSON.stringify(user.communication, null, 2) }}</pre>
          </div>
          <p v-else class="text-gray-400 dark:text-gray-500 italic">
            {{ $t('userDetail.notConfigured') }}
          </p>
        </div>

        <!-- Calibration -->
        <div class="mb-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {{ $t('userDetail.calibration') }}
          </h2>
          <p v-if="user.calibration" class="text-gray-700 dark:text-gray-300">
            {{ user.calibration }}
          </p>
          <p v-else class="text-gray-400 dark:text-gray-500 italic">
            {{ $t('userDetail.notConfigured') }}
          </p>
        </div>

        <!-- Action Buttons -->
        <div class="flex space-x-3 pt-6 border-t border-gray-200 dark:border-gray-700">
          <button
            @click="startSession"
            class="flex-1 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors font-medium"
          >
            {{ $t('users.start') }}
          </button>
          <button
            @click="$router.push('/calibration')"
            class="px-6 py-3 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors font-medium"
          >
            {{ $t('userDetail.calibrate') }}
          </button>
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
            {{ $t('userDetail.editUser') }}
          </h2>
          <form @submit.prevent="updateUser">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ $t('users.name') }}
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
                {{ $t('users.gender') }}
              </label>
              <select
                v-model="editForm.gender"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">{{ $t('users.genderNotSpecified') }}</option>
                <option value="Male">{{ $t('users.genderMale') }}</option>
                <option value="Female">{{ $t('users.genderFemale') }}</option>
                <option value="Other">{{ $t('users.genderOther') }}</option>
              </select>
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ $t('users.age') }}
              </label>
              <input
                v-model.number="editForm.age"
                type="number"
                min="0"
                max="150"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                :placeholder="$t('users.agePlaceholder')"
              />
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ $t('users.voice') }}
              </label>
              <input
                v-model="editForm.voice"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                :placeholder="$t('users.voicePlaceholder')"
              />
              <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {{ $t('users.voiceDescription') }}
              </p>
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ $t('users.notes') }}
              </label>
              <textarea
                v-model="editForm.notes"
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div class="mb-4">
              <label class="flex items-center space-x-2">
                <input
                  v-model="editForm.is_active"
                  type="checkbox"
                  class="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {{ $t('users.active') }}
                </span>
              </label>
            </div>
            <div class="flex space-x-3">
              <button
                type="button"
                @click="showEditModal = false"
                class="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
              >
                {{ $t('users.cancel') }}
              </button>
              <button
                type="submit"
                :disabled="updating"
                class="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {{ updating ? $t('userDetail.updating') : $t('userDetail.save') }}
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
            {{ $t('userDetail.deleteUser') }}
          </h2>
          <p class="text-gray-700 dark:text-gray-300 mb-6">
            {{ $t('userDetail.deleteConfirmation', { name: user?.name }) }}
          </p>
          <div class="flex space-x-3">
            <button
              @click="showDeleteModal = false"
              class="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
            >
              {{ $t('users.cancel') }}
            </button>
            <button
              @click="deleteUser"
              :disabled="deleting"
              class="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {{ deleting ? $t('userDetail.deleting') : $t('userDetail.delete') }}
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
import { usersAPI } from '../services/api';
import {
  ArrowLeftIcon,
  PencilIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline';

const route = useRoute();
const router = useRouter();
const { t } = useI18n();

const user = ref(null);
const loading = ref(true);
const error = ref(null);
const showEditModal = ref(false);
const showDeleteModal = ref(false);
const updating = ref(false);
const deleting = ref(false);
const editForm = ref({
  name: '',
  gender: '',
  age: null,
  voice: '',
  notes: '',
  is_active: true,
});

const loadUser = async () => {
  try {
    loading.value = true;
    error.value = null;
    const userId = parseInt(route.params.id);
    user.value = await usersAPI.get(userId);
    editForm.value = {
      name: user.value.name,
      gender: user.value.gender || '',
      age: user.value.age || null,
      voice: user.value.voice || '',
      notes: user.value.notes || '',
      is_active: user.value.is_active,
    };
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('userDetail.loadError');
    console.error('Error loading user:', err);
  } finally {
    loading.value = false;
  }
};

const updateUser = async () => {
  try {
    updating.value = true;
    const userId = parseInt(route.params.id);
    user.value = await usersAPI.update(userId, editForm.value);
    showEditModal.value = false;
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('userDetail.updateError');
    console.error('Error updating user:', err);
  } finally {
    updating.value = false;
  }
};

const deleteUser = async () => {
  try {
    deleting.value = true;
    const userId = parseInt(route.params.id);
    await usersAPI.delete(userId);
    router.push('/users');
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('userDetail.deleteError');
    console.error('Error deleting user:', err);
    showDeleteModal.value = false;
  } finally {
    deleting.value = false;
  }
};

const startSession = () => {
  router.push({
    name: 'Communicate',
    query: { userId: user.value.id },
  });
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

onMounted(() => {
  loadUser();
});
</script>

