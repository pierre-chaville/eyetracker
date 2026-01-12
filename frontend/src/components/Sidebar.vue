<template>
  <aside
    :class="[
      'fixed left-0 top-0 h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 z-40',
      isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
      isExpanded ? 'w-64' : 'w-20'
    ]"
  >
    <!-- Logo/Brand -->
    <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
      <div v-if="isExpanded" class="flex items-center space-x-3">
        <div class="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
          <EyeIcon class="w-6 h-6 text-white" />
        </div>
        <h1 class="text-xl font-bold text-gray-900 dark:text-white">{{ $t('common.appName') }}</h1>
      </div>
      <div v-else class="flex items-center justify-center w-full">
        <div class="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
          <EyeIcon class="w-6 h-6 text-white" />
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <button
          @click="$emit('toggle')"
          class="hidden md:flex p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          :title="isExpanded ? 'Collapse menu' : 'Expand menu'"
        >
          <Bars3Icon v-if="isExpanded" class="w-5 h-5 text-gray-600 dark:text-gray-300" />
          <ChevronRightIcon v-else class="w-5 h-5 text-gray-600 dark:text-gray-300" />
        </button>
        <button
          @click="$emit('close')"
          class="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <XMarkIcon class="w-5 h-5 text-gray-600 dark:text-gray-300" />
        </button>
      </div>
    </div>

    <!-- Navigation Menu -->
    <nav class="p-4 space-y-2">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        @click="$emit('close')"
        :class="[
          'flex items-center rounded-lg transition-colors',
          isExpanded ? 'px-4 py-3 space-x-3' : 'px-3 py-3 justify-center',
          isActive(item.path)
            ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 font-semibold'
            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
        ]"
        :title="!isExpanded ? item.label : ''"
      >
        <component :is="item.icon" class="w-5 h-5 flex-shrink-0" />
        <span v-if="isExpanded" class="truncate">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- Bottom Actions -->
    <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700">
      <div :class="['flex items-center', isExpanded ? 'justify-center space-x-2' : 'justify-center space-x-1']">
        <ThemeSwitcher />
        <LanguageSwitcher />
      </div>
    </div>
  </aside>

  <!-- Overlay for mobile -->
  <div
    v-if="isOpen"
    @click="$emit('close')"
    class="fixed inset-0 bg-black/50 z-30 md:hidden"
  ></div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import {
  HomeIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  EyeIcon,
  UserGroupIcon,
  WrenchScrewdriverIcon,
  XMarkIcon,
  Bars3Icon,
  ChevronRightIcon,
} from '@heroicons/vue/24/outline';
import ThemeSwitcher from './ThemeSwitcher.vue';
import LanguageSwitcher from './LanguageSwitcher.vue';
import { useI18n } from 'vue-i18n';

defineProps({
  isOpen: {
    type: Boolean,
    default: true,
  },
  isExpanded: {
    type: Boolean,
    default: true,
  },
});

defineEmits(['close', 'toggle']);

const route = useRoute();
const { t } = useI18n();

const menuItems = computed(() => [
  {
    path: '/',
    label: t('sidebar.home'),
    icon: HomeIcon,
  },
  {
    path: '/communicate',
    label: t('sidebar.communicate'),
    icon: ChatBubbleLeftRightIcon,
  },
  {
    path: '/keyboard',
    label: t('sidebar.keyboard'),
    icon: ChatBubbleLeftRightIcon, // Using chat icon as placeholder, can be changed later
  },
  {
    path: '/communication-sessions',
    label: t('sidebar.communicationSessions'),
    icon: DocumentTextIcon,
  },
  {
    path: '/calibration',
    label: t('sidebar.calibration'),
    icon: Cog6ToothIcon,
  },
  {
    path: '/eye-tracking',
    label: t('sidebar.viewEyeTracking'),
    icon: EyeIcon,
  },
  {
    path: '/users',
    label: t('sidebar.users'),
    icon: UserGroupIcon,
  },
  {
    path: '/caregivers',
    label: t('sidebar.caregivers'),
    icon: UserGroupIcon,
  },
  {
    path: '/setup',
    label: t('sidebar.setup'),
    icon: WrenchScrewdriverIcon,
  },
]);

const isActive = (path) => {
  if (path === '/') {
    return route.path === '/';
  }
  return route.path.startsWith(path);
};
</script>

