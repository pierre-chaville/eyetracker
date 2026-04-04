<template>
  <div class="space-y-2">
    <p class="text-sm font-semibold text-gray-700 dark:text-gray-300">{{ label }}</p>
    <div class="flex flex-nowrap gap-2 overflow-x-auto pb-1 -mx-1 px-1">
      <button
        v-for="opt in options"
        :key="opt.value"
        type="button"
        @click="toggle(opt.value)"
        :class="[
          'shrink-0 whitespace-nowrap px-4 py-2 rounded-lg text-sm font-medium border-2 transition-all duration-150',
          modelValue === opt.value
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
            : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:border-gray-300',
        ]"
      >
        {{ opt.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
export interface FeedbackOption {
  value: string;
  label: string;
}

const props = defineProps<{
  label: string;
  modelValue: string;
  options: FeedbackOption[];
}>();

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();

const toggle = (value: string) => {
  emit('update:modelValue', props.modelValue === value ? '' : value);
};
</script>
