<template>
  <el-dialog
    v-model="visible"
    :title="`预览文件 - ${file?.display_name || file?.original_filename}`"
    width="90%"
    :before-close="handleClose"
    class="code-preview-dialog"
  >
    <div class="code-preview" v-loading="loading">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <el-tag :color="getLanguageColor(previewData?.language)" size="small" class="language-tag">
            {{ getLanguageDisplayName(previewData?.language) }}
          </el-tag>
          <span class="file-info">
            {{ previewData?.line_count }} 行 | {{ formatFileSize(file?.file_size || 0) }}
          </span>
        </div>
        <div class="toolbar-right">
          <el-button type="text" size="small" @click="copyCode">
            <el-icon><CopyDocument /></el-icon>
            复制代码
          </el-button>
          <el-button type="text" size="small" @click="downloadFile">
            <el-icon><Download /></el-icon>
            下载文件
          </el-button>
        </div>
      </div>

      <!-- 代码内容 -->
      <div class="code-container">
        <div 
          v-if="previewData?.highlighted_html" 
          class="highlighted-code"
          v-html="previewData.highlighted_html"
        ></div>
        <div v-else-if="!loading" class="no-preview">
          <el-empty description="无法预览此文件" />
        </div>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument, Download } from '@element-plus/icons-vue'
import type { ProjectFile } from '@/types'
import { fileApi } from '@/utils/api'
import { getLanguageDisplayName, getLanguageColor } from '@/utils/languageMapping'

// Props
interface Props {
  modelValue: boolean
  file: ProjectFile | null
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

// 响应式数据
const visible = ref(false)
const loading = ref(false)
const previewData = ref<any>(null)
const highlightCss = ref('')

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  visible.value = newValue
  if (newValue && props.file) {
    loadPreview()
  }
})

// 监听 visible 变化
watch(visible, (newValue) => {
  emit('update:modelValue', newValue)
  if (!newValue) {
    // 清理数据
    previewData.value = null
  }
})

// 加载文件预览
const loadPreview = async () => {
  if (!props.file) return

  try {
    loading.value = true
    
    // 获取文件预览
    const response = await fileApi.previewFile(
      props.file.file_id, 
      props.file.language_override
    )
    
    if (response.code === 0) {
      previewData.value = response.data
      
      // 加载高亮CSS（如果还没有加载）
      if (!highlightCss.value) {
        await loadHighlightCss()
      }
    } else {
      ElMessage.error(response.message || '预览失败')
    }
  } catch (error) {
    console.error('预览文件失败:', error)
    ElMessage.error('预览文件失败')
  } finally {
    loading.value = false
  }
}

// 加载高亮CSS
const loadHighlightCss = async () => {
  try {
    const response = await fileApi.getHighlightCss()
    if (response.code === 0) {
      highlightCss.value = response.data.css
      
      // 动态添加CSS到页面
      if (highlightCss.value) {
        const styleId = 'highlight-css'
        let styleElement = document.getElementById(styleId)
        
        if (!styleElement) {
          styleElement = document.createElement('style')
          styleElement.id = styleId
          document.head.appendChild(styleElement)
        }
        
        styleElement.textContent = highlightCss.value
      }
    }
  } catch (error) {
    console.error('加载高亮CSS失败:', error)
  }
}

// 复制代码
const copyCode = async () => {
  if (!previewData.value?.content) return

  try {
    await navigator.clipboard.writeText(previewData.value.content)
    ElMessage.success('代码已复制到剪贴板')
  } catch (error) {
    // 降级处理
    const textArea = document.createElement('textarea')
    textArea.value = previewData.value.content
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    ElMessage.success('代码已复制到剪贴板')
  }
}

// 下载文件
const downloadFile = () => {
  if (!previewData.value?.content || !props.file) return

  const blob = new Blob([previewData.value.content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = props.file.original_filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('文件下载成功')
}

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 处理关闭
const handleClose = () => {
  visible.value = false
}

// 组件挂载时加载CSS
onMounted(() => {
  loadHighlightCss()
})

// 暴露方法给父组件
defineExpose({
  close: handleClose
})
</script>

<style scoped>
.code-preview-dialog :deep(.el-dialog) {
  margin-top: 5vh;
  margin-bottom: 5vh;
  height: 90vh;
  display: flex;
  flex-direction: column;
}

.code-preview-dialog :deep(.el-dialog__body) {
  flex: 1;
  padding: 0;
  overflow: hidden;
}

.code-preview {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  background-color: #f8f9fa;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.language-tag {
  border: none;
  color: white;
  font-weight: 500;
}

.file-info {
  font-size: 12px;
  color: #666;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.code-container {
  flex: 1;
  overflow: auto;
  background-color: #fff;
}

.highlighted-code {
  height: 100%;
}

.highlighted-code :deep(.highlight) {
  margin: 0;
  height: 100%;
  overflow: auto;
}

.highlighted-code :deep(.highlight pre) {
  margin: 0;
  padding: 16px;
  background-color: transparent;
  border: none;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.highlighted-code :deep(.highlight .linenos) {
  background-color: #f8f9fa;
  color: #666;
  padding-right: 8px;
  border-right: 1px solid #e4e7ed;
  user-select: none;
}

.no-preview {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.dialog-footer {
  text-align: right;
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
}
</style>
