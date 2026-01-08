<template>
  <button
    @click.stop="toggleTheme"
    class="p-2 rounded-lg hover:bg-gray-700 dark:hover:bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
    :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
  >
    <SunIcon v-if="isDark" class="w-6 h-6 text-gray-300 dark:text-gray-700" />
    <MoonIcon v-else class="w-6 h-6 text-gray-300 dark:text-gray-700" />
  </button>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { SunIcon, MoonIcon } from '@heroicons/vue/24/outline';

const isDark = ref(false);

const checkTheme = () => {
  isDark.value = document.documentElement.classList.contains('dark');
};

const toggleTheme = () => {
  isDark.value = !isDark.value;
  updateTheme();
};

const updateTheme = () => {
  if (isDark.value) {
    document.documentElement.classList.add('dark');
    localStorage.setItem('theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark');
    localStorage.setItem('theme', 'light');
  }
};

onMounted(() => {
  // Always use saved preference, default to light mode
  // Ignore system/browser preference
  const savedTheme = localStorage.getItem('theme');
  
  if (savedTheme === 'dark') {
    document.documentElement.classList.add('dark');
    isDark.value = true;
  } else {
    // Default to light mode
    document.documentElement.classList.remove('dark');
    isDark.value = false;
    if (!savedTheme) {
      localStorage.setItem('theme', 'light');
    }
  }
  
  // Watch for external theme changes (e.g., from other components)
  const observer = new MutationObserver(() => {
    checkTheme();
  });
  
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class']
  });
  
  // Cleanup
  return () => {
    observer.disconnect();
  };
});
</script>

