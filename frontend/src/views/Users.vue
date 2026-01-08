<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
          {{ $t('users.title') }}
        </h1>
        <button
          @click="showCreateModal = true"
          class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors flex items-center space-x-2"
        >
          <PlusIcon class="w-5 h-5" />
          <span>{{ $t('users.createUser') }}</span>
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

      <!-- Users Grid -->
      <div v-else-if="users.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="user in users"
          :key="user.id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow p-6"
        >
          <div class="flex items-start justify-between mb-4">
            <div>
              <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-1">
                {{ user.name }}
              </h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ $t('users.createdAt') }}: {{ formatDate(user.created_at) }}
              </p>
            </div>
            <span
              :class="[
                'px-2 py-1 rounded-full text-xs font-medium',
                user.is_active
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
              ]"
            >
              {{ user.is_active ? $t('users.active') : $t('users.inactive') }}
            </span>
          </div>

          <div class="mb-4">
            <p v-if="user.notes" class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
              {{ user.notes }}
            </p>
            <p v-else class="text-sm text-gray-400 dark:text-gray-500 italic">
              {{ $t('users.noNotes') }}
            </p>
          </div>

          <div class="flex space-x-2">
            <button
              @click="startSession(user)"
              class="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors text-sm font-medium"
            >
              {{ $t('users.start') }}
            </button>
            <button
              @click="$router.push(`/users/${user.id}`)"
              class="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors text-sm font-medium"
            >
              {{ $t('users.view') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-12 text-center">
        <UserGroupIcon class="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4" />
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          {{ $t('users.noUsers') }}
        </h3>
        <p class="text-gray-600 dark:text-gray-400 mb-6">
          {{ $t('users.noUsersDescription') }}
        </p>
        <button
          @click="showCreateModal = true"
          class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
        >
          {{ $t('users.createUser') }}
        </button>
      </div>

      <!-- Create User Modal -->
      <div
        v-if="showCreateModal"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        @click.self="showCreateModal = false"
      >
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            {{ $t('users.createUser') }}
          </h2>
          <form @submit.prevent="createUser">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ $t('users.name') }}
              </label>
              <input
                v-model="newUser.name"
                type="text"
                required
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                :placeholder="$t('users.namePlaceholder')"
              />
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ $t('users.notes') }}
              </label>
              <textarea
                v-model="newUser.notes"
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                :placeholder="$t('users.notesPlaceholder')"
              />
            </div>
            <div class="flex space-x-3">
              <button
                type="button"
                @click="showCreateModal = false"
                class="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
              >
                {{ $t('users.cancel') }}
              </button>
              <button
                type="submit"
                :disabled="creating"
                class="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {{ creating ? $t('users.creating') : $t('users.create') }}
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
import { usersAPI } from '../services/api';
import { PlusIcon, UserGroupIcon } from '@heroicons/vue/24/outline';

const router = useRouter();
const { t } = useI18n();

const users = ref([]);
const loading = ref(true);
const error = ref(null);
const showCreateModal = ref(false);
const creating = ref(false);
const newUser = ref({
  name: '',
  notes: '',
});

const loadUsers = async () => {
  try {
    loading.value = true;
    error.value = null;
    users.value = await usersAPI.list();
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('users.loadError');
    console.error('Error loading users:', err);
  } finally {
    loading.value = false;
  }
};

const createUser = async () => {
  try {
    creating.value = true;
    await usersAPI.create(newUser.value);
    showCreateModal.value = false;
    newUser.value = { name: '', notes: '' };
    await loadUsers();
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('users.createError');
    console.error('Error creating user:', err);
  } finally {
    creating.value = false;
  }
};

const startSession = (user) => {
  // Navigate to communicate page with user context
  router.push({
    name: 'Communicate',
    query: { userId: user.id },
  });
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

onMounted(() => {
  loadUsers();
});
</script>
