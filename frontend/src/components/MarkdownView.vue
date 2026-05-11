<template>
  <div class="markdown-view" v-html="rendered" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown'
import 'highlight.js/styles/github.css'

const props = defineProps<{
  source: string | null | undefined
}>()

const rendered = computed(() => renderMarkdown(props.source))
</script>

<style scoped>
.markdown-view :deep(h1),
.markdown-view :deep(h2),
.markdown-view :deep(h3),
.markdown-view :deep(h4) {
  margin: 12px 0 8px;
  color: #102033;
}

.markdown-view :deep(p) {
  margin: 6px 0;
  line-height: 1.6;
}

.markdown-view :deep(ul),
.markdown-view :deep(ol) {
  padding-left: 24px;
  margin: 6px 0;
}

.markdown-view :deep(code) {
  background: #f5f7fa;
  padding: 2px 4px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', Menlo, Consolas, monospace;
  font-size: 13px;
}

.markdown-view :deep(pre) {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.markdown-view :deep(blockquote) {
  border-left: 4px solid #dcdfe6;
  padding-left: 12px;
  color: #606266;
  margin: 8px 0;
}

.markdown-view :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
}

.markdown-view :deep(table th),
.markdown-view :deep(table td) {
  border: 1px solid #dcdfe6;
  padding: 6px 10px;
}
</style>
