<template>
  <div class="markdown-editor" :style="{ minHeight: minHeight + 'px' }">
    <div class="markdown-editor__pane">
      <div class="markdown-editor__label">Markdown 编辑</div>
      <el-input
        type="textarea"
        :model-value="modelValue ?? ''"
        :rows="rows"
        :placeholder="placeholder"
        :resize="resize"
        @update:model-value="(value) => emit('update:modelValue', value)"
      />
    </div>
    <div class="markdown-editor__pane markdown-editor__pane--preview">
      <div class="markdown-editor__label">实时预览</div>
      <div class="markdown-editor__preview">
        <MarkdownView :source="modelValue" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import MarkdownView from './MarkdownView.vue'

withDefaults(
  defineProps<{
    modelValue: string
    rows?: number
    placeholder?: string
    minHeight?: number
    resize?: 'none' | 'both' | 'horizontal' | 'vertical'
  }>(),
  {
    rows: 10,
    placeholder: '使用 Markdown 撰写正文，支持代码块、列表、表格、链接等',
    minHeight: 240,
    resize: 'vertical',
  },
)

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void
}>()
</script>

<style scoped>
.markdown-editor {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.markdown-editor__pane {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.markdown-editor__label {
  font-size: 12px;
  color: #909399;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.markdown-editor__preview {
  flex: 1;
  min-height: 200px;
  background: #fafafa;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 12px 16px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .markdown-editor {
    grid-template-columns: 1fr;
  }
}
</style>
