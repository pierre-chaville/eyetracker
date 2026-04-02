<template>
  <div v-if="choice" class="w-full h-full flex flex-col items-center justify-center p-2 overflow-hidden">
    <!-- ARASAAC Pictogram -->
    <img
      v-if="choice.pictogram_url"
      :src="choice.pictogram_url"
      :alt="choice.text || ''"
      class="max-h-[55%] max-w-[80%] object-contain mb-1"
      loading="eager"
      @error="($event.target as HTMLImageElement).style.display = 'none'"
    />

    <!-- Emoji icon fallback -->
    <div v-else-if="choice.icon" class="text-6xl mb-2">
      {{ choice.icon }}
    </div>

    <!-- Text -->
    <div v-if="choice.text" :class="[
      'text-center font-semibold leading-tight',
      choice.pictogram_url ? 'text-lg' : 'text-3xl',
      isHighlighted
        ? 'text-primary-700 dark:text-primary-300'
        : 'text-gray-700 dark:text-gray-300'
    ]">
      {{ choice.text }}
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Choice } from '../types/api';

interface Props {
  choice?: Choice | null
  isHighlighted?: boolean
}

withDefaults(defineProps<Props>(), {
  choice: null,
  isHighlighted: false,
});
</script>

