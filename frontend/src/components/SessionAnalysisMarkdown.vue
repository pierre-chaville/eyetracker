<template>
  <div
    v-if="html"
    class="session-analysis-md text-gray-800 dark:text-gray-200 text-sm leading-relaxed"
    v-html="html"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const props = defineProps<{
  source: string;
}>();

const html = computed(() => {
  const src = props.source?.trim();
  if (!src) return '';
  const out = marked(src, { async: false });
  if (typeof out !== 'string') return '';
  return DOMPurify.sanitize(out);
});
</script>

<style scoped>
.session-analysis-md :deep(h1) {
  font-size: 1.375rem;
  font-weight: 700;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  line-height: 1.3;
}
.session-analysis-md :deep(h2) {
  font-size: 1.125rem;
  font-weight: 600;
  margin-top: 0.875rem;
  margin-bottom: 0.375rem;
  line-height: 1.35;
}
.session-analysis-md :deep(h3) {
  font-size: 1rem;
  font-weight: 600;
  margin-top: 0.75rem;
  margin-bottom: 0.25rem;
}
.session-analysis-md :deep(p) {
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
}
.session-analysis-md :deep(ul),
.session-analysis-md :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.25rem;
}
.session-analysis-md :deep(li) {
  margin: 0.25rem 0;
}
.session-analysis-md :deep(code) {
  font-size: 0.875em;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  background: rgb(243 244 246);
}
.dark .session-analysis-md :deep(code) {
  background: rgb(55 65 81);
}
.session-analysis-md :deep(pre) {
  margin: 0.75rem 0;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  background: rgb(243 244 246);
  font-size: 0.8125rem;
}
.dark .session-analysis-md :deep(pre) {
  background: rgb(31 41 55);
}
.session-analysis-md :deep(pre code) {
  padding: 0;
  background: transparent;
}
.session-analysis-md :deep(blockquote) {
  margin: 0.75rem 0;
  padding-left: 1rem;
  border-left: 4px solid rgb(99 102 241);
  color: rgb(107 114 128);
}
.dark .session-analysis-md :deep(blockquote) {
  color: rgb(156 163 175);
}
.session-analysis-md :deep(a) {
  color: rgb(79 70 229);
  text-decoration: underline;
}
.dark .session-analysis-md :deep(a) {
  color: rgb(165 180 252);
}
.session-analysis-md :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.75rem 0;
  font-size: 0.875rem;
}
.session-analysis-md :deep(th),
.session-analysis-md :deep(td) {
  border: 1px solid rgb(229 231 235);
  padding: 0.375rem 0.5rem;
  text-align: left;
}
.dark .session-analysis-md :deep(th),
.dark .session-analysis-md :deep(td) {
  border-color: rgb(75 85 99);
}
.session-analysis-md :deep(th) {
  font-weight: 600;
  background: rgb(249 250 251);
}
.dark .session-analysis-md :deep(th) {
  background: rgb(55 65 81);
}
</style>
