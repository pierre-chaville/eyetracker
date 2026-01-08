<template>
  <div class="relative" ref="containerRef">
    <button
      @click.stop="toggleMenu"
      class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
      :title="$t('common.settings')"
    >
      <GlobeAltIcon class="w-6 h-6 text-gray-600 dark:text-gray-300" />
    </button>

    <!-- Dropdown Menu -->
    <Transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        class="absolute bottom-full left-0 mb-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 py-1 z-50"
      >
        <button
          @click.stop="setLocale('en')"
          :class="[
            'w-full text-left px-4 py-2 text-sm transition-colors',
            currentLocale === 'en' 
              ? 'bg-primary-100 dark:bg-gray-700 text-primary-700 dark:text-white' 
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
          ]"
        >
          <span class="mr-2">🇬🇧</span> English
        </button>
        <button
          @click.stop="setLocale('fr')"
          :class="[
            'w-full text-left px-4 py-2 text-sm transition-colors',
            currentLocale === 'fr' 
              ? 'bg-primary-100 dark:bg-gray-700 text-primary-700 dark:text-white' 
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
          ]"
        >
          <span class="mr-2">🇫🇷</span> Français
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useI18n } from 'vue-i18n';
import { GlobeAltIcon } from '@heroicons/vue/24/outline';

const { locale } = useI18n();
const isOpen = ref(false);
const containerRef = ref(null);

const currentLocale = computed(() => locale.value);

const toggleMenu = (event) => {
  event.stopPropagation();
  isOpen.value = !isOpen.value;
};

const closeMenu = () => {
  isOpen.value = false;
};

const setLocale = (lang) => {
  locale.value = lang;
  localStorage.setItem('locale', lang);
  closeMenu();
};

// Handle click outside
const handleClickOutside = (event) => {
  if (containerRef.value && !containerRef.value.contains(event.target)) {
    closeMenu();
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

