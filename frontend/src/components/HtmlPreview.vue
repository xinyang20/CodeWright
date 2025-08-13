<template>
  <el-dialog
    v-model="visible"
    title="HTML 预览"
    width="95%"
    :before-close="handleClose"
    class="html-preview-dialog"
  >
    <div class="html-preview" v-loading="loading">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button-group>
            <el-button 
              :type="viewMode === 'preview' ? 'primary' : ''"
              size="small"
              @click="viewMode = 'preview'"
            >
              <el-icon><View /></el-icon>
              预览
            </el-button>
            <el-button 
              :type="viewMode === 'source' ? 'primary' : ''"
              size="small"
              @click="viewMode = 'source'"
            >
              <el-icon><Document /></el-icon>
              源码
            </el-button>
            <el-button 
              :type="viewMode === 'split' ? 'primary' : ''"
              size="small"
              @click="viewMode = 'split'"
            >
              <el-icon><Grid /></el-icon>
              分屏
            </el-button>
          </el-button-group>
        </div>
        
        <div class="toolbar-center">
          <span class="project-title">{{ project?.project_name }}</span>
        </div>
        
        <div class="toolbar-right">
          <el-button type="text" size="small" @click="refreshPreview">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button type="text" size="small" @click="exportPdf">
            <el-icon><Download /></el-icon>
            导出 PDF
          </el-button>
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="content-area">
        <!-- 预览模式 -->
        <div v-if="viewMode === 'preview'" class="preview-only">
          <iframe 
            ref="previewFrame"
            class="preview-iframe"
            :srcdoc="htmlContent"
            @load="handleIframeLoad"
          ></iframe>
        </div>

        <!-- 源码模式 -->
        <div v-else-if="viewMode === 'source'" class="source-only">
          <div class="source-container">
            <pre><code v-html="highlightedHtml"></code></pre>
          </div>
        </div>

        <!-- 分屏模式 -->
        <div v-else class="split-view">
          <div class="split-left">
            <div class="panel-header">源码</div>
            <div class="source-container">
              <pre><code v-html="highlightedHtml"></code></pre>
            </div>
          </div>
          <div class="split-divider"></div>
          <div class="split-right">
            <div class="panel-header">预览</div>
            <iframe 
              ref="previewFrameSplit"
              class="preview-iframe"
              :srcdoc="htmlContent"
            ></iframe>
          </div>
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
import { 
  View, 
  Document, 
  Grid, 
  Refresh, 
  Download 
} from '@element-plus/icons-vue'
import hljs from 'highlight.js'
import 'highlight.js/styles/default.css'
import type { Project, ProjectFile } from '@/types'
import { projectApi, fileApi } from '@/utils/api'

// Props
interface Props {
  modelValue: boolean
  project: Project | null
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

// 响应式数据
const visible = ref(false)
const loading = ref(false)
const viewMode = ref<'preview' | 'source' | 'split'>('preview')
const htmlContent = ref('')
const sourceCode = ref('')
const previewFrame = ref<HTMLIFrameElement>()
const previewFrameSplit = ref<HTMLIFrameElement>()

// 计算属性
const highlightedHtml = computed(() => {
  if (!sourceCode.value) return ''
  return hljs.highlight(sourceCode.value, { language: 'html' }).value
})

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  visible.value = newValue
  if (newValue && props.project) {
    generatePreview()
  }
})

// 监听 visible 变化
watch(visible, (newValue) => {
  emit('update:modelValue', newValue)
  if (!newValue) {
    // 清理数据
    htmlContent.value = ''
    sourceCode.value = ''
  }
})

// 生成HTML预览
const generatePreview = async () => {
  if (!props.project) return

  try {
    loading.value = true
    
    // 获取项目文件列表
    const filesResponse = await fileApi.getProjectFiles(props.project.id)
    if (filesResponse.code !== 0) {
      throw new Error(filesResponse.message || '获取项目文件失败')
    }
    
    const files = filesResponse.data.files
    if (files.length === 0) {
      ElMessage.warning('项目中没有文件')
      return
    }
    
    // 生成HTML内容
    const html = await buildHtmlContent(files)
    htmlContent.value = html
    sourceCode.value = html
    
  } catch (error) {
    console.error('生成预览失败:', error)
    ElMessage.error('生成预览失败')
  } finally {
    loading.value = false
  }
}

// 构建HTML内容
const buildHtmlContent = async (files: ProjectFile[]) => {
  const sortedFiles = files
    .filter(f => f.include_in_export)
    .sort((a, b) => a.order_index - b.order_index)
  
  let htmlParts = []
  
  // HTML头部
  htmlParts.push(`<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${props.project?.project_name || '代码文档'}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #5c7cfa;
        }
        .header h1 {
            color: #5c7cfa;
            margin: 0;
            font-size: 2.5em;
        }
        .toc {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .toc h2 {
            margin-top: 0;
            color: #5c7cfa;
        }
        .toc ul {
            list-style: none;
            padding: 0;
        }
        .toc li {
            margin: 8px 0;
        }
        .toc a {
            color: #5c7cfa;
            text-decoration: none;
            padding: 4px 8px;
            border-radius: 4px;
            transition: background-color 0.3s;
        }
        .toc a:hover {
            background-color: #e3f2fd;
        }
        .file-section {
            margin-bottom: 40px;
            border: 1px solid #e4e7ed;
            border-radius: 8px;
            overflow: hidden;
        }
        .file-header {
            background-color: #5c7cfa;
            color: white;
            padding: 12px 20px;
            font-weight: 600;
        }
        .file-content {
            background-color: #f8f9fa;
        }
        .file-content pre {
            margin: 0;
            padding: 20px;
            overflow-x: auto;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            line-height: 1.5;
        }
        .highlight {
            background-color: transparent;
        }
        .linenos {
            color: #666;
            background-color: #f0f0f0;
            padding-right: 8px;
            border-right: 1px solid #ddd;
            user-select: none;
        }
    </style>
</head>
<body>`)

  // 页面头部
  htmlParts.push(`
    <div class="header">
        <h1>${props.project?.project_name || '代码文档'}</h1>
        <p>生成时间：${new Date().toLocaleString('zh-CN')}</p>
    </div>`)

  // 目录
  if (sortedFiles.length > 1) {
    htmlParts.push(`
    <div class="toc">
        <h2>目录</h2>
        <ul>`)
    
    sortedFiles.forEach((file, index) => {
      const fileName = file.display_name || file.original_filename
      htmlParts.push(`            <li><a href="#file-${index}">${fileName}</a></li>`)
    })
    
    htmlParts.push(`        </ul>
    </div>`)
  }

  // 文件内容
  for (let i = 0; i < sortedFiles.length; i++) {
    const file = sortedFiles[i]
    const fileName = file.display_name || file.original_filename
    
    try {
      // 获取文件预览
      const previewResponse = await fileApi.previewFile(
        file.file_id, 
        file.language_override
      )
      
      if (previewResponse.code === 0) {
        const previewData = previewResponse.data
        
        htmlParts.push(`
    <div class="file-section" id="file-${i}">
        <div class="file-header">
            ${fileName}
        </div>
        <div class="file-content">
            ${previewData.highlighted_html || `<pre><code>${previewData.content}</code></pre>`}
        </div>
    </div>`)
      }
    } catch (error) {
      console.error(`获取文件 ${fileName} 预览失败:`, error)
      htmlParts.push(`
    <div class="file-section" id="file-${i}">
        <div class="file-header">
            ${fileName}
        </div>
        <div class="file-content">
            <pre><code>无法加载文件内容</code></pre>
        </div>
    </div>`)
    }
  }

  // HTML尾部
  htmlParts.push(`
</body>
</html>`)

  return htmlParts.join('')
}

// 刷新预览
const refreshPreview = () => {
  generatePreview()
}

// 导出PDF
const exportPdf = async () => {
  if (!props.project) return

  try {
    ElMessage.info('正在生成PDF，请稍候...')

    // 使用默认导出选项
    const exportOptions = {
      include_toc: true,
      include_summary: true,
      watermark: false
    }

    const response = await projectApi.exportProjectPdf(props.project.id, exportOptions)

    // 创建下载链接
    const blob = new Blob([response], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${props.project.project_name}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    ElMessage.success('PDF导出成功')
  } catch (error) {
    console.error('导出PDF失败:', error)
    ElMessage.error('导出PDF失败')
  }
}

// 处理iframe加载
const handleIframeLoad = () => {
  // iframe加载完成后的处理
}

// 处理关闭
const handleClose = () => {
  visible.value = false
}

// 暴露方法给父组件
defineExpose({
  close: handleClose,
  refresh: refreshPreview
})
</script>

<style scoped>
.html-preview-dialog :deep(.el-dialog) {
  margin-top: 2vh;
  margin-bottom: 2vh;
  height: 96vh;
  display: flex;
  flex-direction: column;
}

.html-preview-dialog :deep(.el-dialog__body) {
  flex: 1;
  padding: 0;
  overflow: hidden;
}

.html-preview {
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

.project-title {
  font-weight: 600;
  color: #111;
}

.content-area {
  flex: 1;
  overflow: hidden;
}

.preview-only,
.source-only {
  height: 100%;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background-color: #fff;
}

.source-container {
  height: 100%;
  overflow: auto;
  background-color: #f8f9fa;
}

.source-container pre {
  margin: 0;
  padding: 16px;
  height: 100%;
  overflow: auto;
}

.split-view {
  display: flex;
  height: 100%;
}

.split-left,
.split-right {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.split-divider {
  width: 4px;
  background-color: #e4e7ed;
  cursor: col-resize;
}

.panel-header {
  padding: 8px 12px;
  background-color: #f0f0f0;
  border-bottom: 1px solid #e4e7ed;
  font-size: 12px;
  font-weight: 600;
  color: #666;
}

.split-left .source-container,
.split-right .preview-iframe {
  flex: 1;
}

.dialog-footer {
  text-align: right;
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
}
</style>
