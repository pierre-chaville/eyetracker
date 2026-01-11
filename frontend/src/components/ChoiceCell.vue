<template>
  <div v-if="choice" class="w-full h-full flex flex-col items-center justify-center p-2">
    <!-- Icon if available -->
    <div v-if="choice.icon" class="text-4xl mb-2">
      {{ choice.icon }}
    </div>
    
    <!-- Text -->
    <div v-if="choice.text" :class="[
      'text-center font-medium',
      isHighlighted 
        ? 'text-primary-700 dark:text-primary-300' 
        : 'text-gray-700 dark:text-gray-300'
    ]">
      {{ choice.text }}
    </div>
  </div>
</template>

<script setup>
defineProps({
  choice: {
    type: Object,
    default: null,
  },
  isHighlighted: {
    type: Boolean,
    default: false,
  },
});
</script>

