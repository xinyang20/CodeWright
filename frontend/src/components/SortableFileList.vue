<template>
  <div class="sortable-file-list">
    <div v-if="files.length === 0" class="empty-files">
      <el-empty description="暂无文件">
        <el-button type="primary" @click="$emit('upload')">
          上传第一个文件
        </el-button>
      </el-empty>
    </div>
    
    <div v-else class="file-items" ref="fileListRef">
      <div 
        v-for="file in sortedFiles" 
        :key="file.id" 
        class="file-item"
        :data-id="file.id"
      >
        <div class="drag-handle">
          <el-icon><Rank /></el-icon>
        </div>
        
        <div class="file-info">
          <div class="file-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="file-details">
            <div class="file-name">{{ file.display_name || file.original_filename }}</div>
            <div class="file-meta">
              <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
              <span class="file-type">{{ getFileExtension(file.original_filename) }}</span>
              <span class="file-language">
                <el-tag
                  :color="getLanguageColor(getFileLanguage(file))"
                  size="small"
                  class="language-tag"
                >
                  {{ getLanguageDisplayName(getFileLanguage(file)) }}
                </el-tag>
              </span>
              <span class="file-time">{{ formatDate(file.created_at) }}</span>
              <span class="file-order">顺序: {{ file.order_index }}</span>
            </div>
          </div>
        </div>
        
        <div class="file-actions">
          <el-button type="text" size="small" @click="$emit('preview', file)">
            <el-icon><View /></el-icon>
            预览
          </el-button>
          <el-button type="text" size="small" @click="$emit('setLanguage', file)">
            <el-icon><Setting /></el-icon>
            语言
          </el-button>
          <el-button type="text" size="small" @click="$emit('rename', file)">
            <el-icon><Edit /></el-icon>
            重命名
          </el-button>
          <el-button type="text" size="small" danger @click="$emit('remove', file)">
            <el-icon><Delete /></el-icon>
            移除
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import Sortable from 'sortablejs'
import {
  Document,
  View,
  Edit,
  Delete,
  Rank,
  Setting
} from '@element-plus/icons-vue'
import type { ProjectFile } from '@/types'
import {
  getLanguageByExtension,
  getLanguageDisplayName,
  getLanguageColor
} from '@/utils/languageMapping'

// Props
interface Props {
  files: ProjectFile[]
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  upload: []
  preview: [file: ProjectFile]
  setLanguage: [file: ProjectFile]
  rename: [file: ProjectFile]
  remove: [file: ProjectFile]
  reorder: [files: ProjectFile[]]
}>()

// 响应式数据
const fileListRef = ref<HTMLElement>()
let sortableInstance: Sortable | null = null

// 按顺序排序的文件列表
const sortedFiles = computed(() => {
  return [...props.files].sort((a, b) => a.order_index - b.order_index)
})

// 初始化拖拽排序
const initSortable = () => {
  if (!fileListRef.value) return

  sortableInstance = Sortable.create(fileListRef.value, {
    handle: '.drag-handle',
    animation: 150,
    ghostClass: 'sortable-ghost',
    chosenClass: 'sortable-chosen',
    dragClass: 'sortable-drag',
    onEnd: (evt) => {
      const { oldIndex, newIndex } = evt
      if (oldIndex !== undefined && newIndex !== undefined && oldIndex !== newIndex) {
        // 重新排序文件列表
        const newFiles = [...sortedFiles.value]
        const [movedFile] = newFiles.splice(oldIndex, 1)
        newFiles.splice(newIndex, 0, movedFile)
        
        // 更新顺序索引
        const reorderedFiles = newFiles.map((file, index) => ({
          ...file,
          order_index: index + 1
        }))
        
        // 触发重排序事件
        emit('reorder', reorderedFiles)
      }
    }
  })
}

// 销毁拖拽排序
const destroySortable = () => {
  if (sortableInstance) {
    sortableInstance.destroy()
    sortableInstance = null
  }
}

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 获取文件扩展名
const getFileExtension = (filename: string) => {
  const ext = filename.split('.').pop()
  return ext ? `.${ext}` : ''
}

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取文件语言类型
const getFileLanguage = (file: ProjectFile) => {
  // 如果有手动设置的语言，使用手动设置的
  if (file.language_override) {
    return file.language_override
  }

  // 否则根据文件扩展名自动识别
  const detected = getLanguageByExtension(file.original_filename)
  return detected?.name || 'text'
}

// 监听文件列表变化，重新初始化排序
watch(() => props.files.length, () => {
  if (props.files.length > 0) {
    // 延迟初始化，确保DOM已更新
    setTimeout(() => {
      destroySortable()
      initSortable()
    }, 100)
  }
})

// 组件挂载时初始化
onMounted(() => {
  if (props.files.length > 0) {
    initSortable()
  }
})

// 组件卸载时清理
onUnmounted(() => {
  destroySortable()
})
</script>

<style scoped>
.sortable-file-list {
  width: 100%;
}

.empty-files {
  padding: 40px 0;
  text-align: center;
}

.file-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background-color: #fff;
  transition: all 0.3s ease;
  cursor: move;
}

.file-item:hover {
  border-color: #5c7cfa;
  box-shadow: 0 2px 8px rgba(92, 124, 250, 0.15);
}

.drag-handle {
  margin-right: 12px;
  color: #c0c4cc;
  cursor: grab;
  padding: 4px;
}

.drag-handle:hover {
  color: #5c7cfa;
}

.drag-handle:active {
  cursor: grabbing;
}

.file-info {
  display: flex;
  align-items: center;
  flex: 1;
}

.file-icon {
  margin-right: 12px;
  color: #5c7cfa;
  font-size: 20px;
}

.file-details {
  flex: 1;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #111;
  margin-bottom: 4px;
}

.file-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
}

.file-meta span {
  position: relative;
}

.file-meta span:not(:last-child):after {
  content: '•';
  position: absolute;
  right: -8px;
  color: #d9d9d9;
}

.file-order {
  color: #5c7cfa !important;
  font-weight: 500;
}

.language-tag {
  border: none;
  color: white;
  font-weight: 500;
  font-size: 11px;
}

.file-actions {
  display: flex;
  gap: 8px;
}

/* 拖拽状态样式 */
.sortable-ghost {
  opacity: 0.5;
  background-color: #f8f9ff;
  border-color: #5c7cfa;
}

.sortable-chosen {
  background-color: #f8f9ff;
  border-color: #5c7cfa;
}

.sortable-drag {
  opacity: 0.8;
  transform: rotate(5deg);
}
</style>
