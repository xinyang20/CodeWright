<template>
  <el-dialog
    v-model="visible"
    title="PDF 预览"
    width="95%"
    :before-close="handleClose"
    class="html-preview-dialog"
  >
    <div class="pdf-preview">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-radio-group v-model="previewMode" size="small" @change="handleModeChange">
            <el-radio-button value="pdf">PDF</el-radio-button>
            <el-radio-button value="html">HTML</el-radio-button>
          </el-radio-group>
          <span class="toolbar-label">{{ modeHint }}</span>
        </div>

        <div class="toolbar-center">
          <span class="project-title">{{ project?.project_name }}</span>
        </div>

        <div class="toolbar-right">
          <el-button type="text" size="small" :disabled="loading" @click="refreshPreview">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button
            type="text"
            size="small"
            :loading="exporting"
            :disabled="loading || exporting"
            @click="exportPdf"
          >
            <el-icon><Download /></el-icon>
            下载 PDF
          </el-button>
        </div>
      </div>

      <div ref="contentArea" class="content-area">
        <!-- PDF mode: hand the blob URL to the browser's native PDF viewer.
             This avoids the 9.6 MB pdfjs-dist worker bundle entirely. -->
        <iframe
          v-show="previewMode === 'pdf' && pdfBlobUrl"
          class="pdf-frame"
          :src="pdfBlobUrl || ''"
          :title="`${project?.project_name || ''} PDF 预览`"
        />

        <!-- HTML mode: show iframe whenever we have srcdoc, regardless of loading. -->
        <iframe
          v-if="previewMode === 'html' && htmlSrcdoc"
          class="html-frame"
          sandbox="allow-same-origin"
          :srcdoc="htmlSrcdoc"
        />

        <!-- Empty state: only when truly idle. -->
        <div
          v-if="!loading && !hasContent && loadingPhase === 'idle'"
          class="preview-empty"
        >
          {{ previewMode === 'pdf' ? 'PDF 预览尚未生成，点击"刷新"重新尝试' : 'HTML 预览尚未生成，点击"刷新"重新尝试' }}
        </div>

        <!-- Centered loading overlay covering compile + parse phases. -->
        <div v-if="loading" class="preview-loading-overlay" role="status" aria-live="polite">
          <div class="preview-loading-card">
            <el-icon class="preview-loading-spinner is-loading">
              <Loading />
            </el-icon>
            <p class="preview-loading-title">{{ loadingTitle }}</p>
            <p class="preview-loading-hint">{{ loadingHint }}</p>
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
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download, Loading } from '@element-plus/icons-vue'
import type { Project } from '@/types'
import { projectApi } from '@/utils/api'

interface Props {
  modelValue: boolean
  project: Project | null
  exportOptions?: Record<string, any>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

type PreviewMode = 'pdf' | 'html'

type LoadingPhase = 'idle' | 'compiling'

const visible = ref(false)
const loading = ref(false)
const loadingPhase = ref<LoadingPhase>('idle')
const loadingElapsed = ref(0)
const exporting = ref(false)
const contentArea = ref<HTMLElement>()
const previewMode = ref<PreviewMode>('pdf')
const htmlSrcdoc = ref<string>('')
const pdfBlobUrl = ref<string>('')
let renderToken = 0
let loadingTimer: ReturnType<typeof setInterval> | null = null

const modeHint = computed(() => {
  return previewMode.value === 'pdf'
    ? '预览与导出使用同一套 LaTeX PDF 生成链路'
    : 'HTML 预览来自服务端模板渲染，便于排查样式与变量替换'
})

const hasContent = computed(() => {
  return previewMode.value === 'pdf'
    ? Boolean(pdfBlobUrl.value)
    : Boolean(htmlSrcdoc.value)
})

const loadingTitle = computed(() => {
  const verb = previewMode.value === 'pdf' ? '正在生成 PDF 预览' : '正在生成 HTML 预览'
  const elapsed = loadingElapsed.value
  if (elapsed === 0) {
    return `${verb}，请稍候…`
  }
  return `${verb}，已耗时 ${elapsed}s`
})

const loadingHint = computed(() => {
  const elapsed = loadingElapsed.value
  if (previewMode.value !== 'pdf') {
    return '后端正在渲染模板，请稍候。'
  }
  if (elapsed < 8) {
    return '后端正在用 xelatex 编译，第一次约 5–15 秒。关闭"目录"可减半。'
  }
  if (elapsed < 30) {
    return '正在调用 xelatex 编译，请耐心等待。'
  }
  return '项目较大或文件较多，xelatex 编译可能持续数十秒。'
})

const startLoadingTimer = () => {
  stopLoadingTimer()
  loadingElapsed.value = 0
  loadingTimer = setInterval(() => {
    loadingElapsed.value += 1
  }, 1000)
}

const stopLoadingTimer = () => {
  if (loadingTimer) {
    clearInterval(loadingTimer)
    loadingTimer = null
  }
}

let pendingPreviewTimer: ReturnType<typeof setTimeout> | null = null

const schedulePreview = (delayMs = 80) => {
  if (!visible.value || !props.project) return
  if (pendingPreviewTimer) {
    clearTimeout(pendingPreviewTimer)
  }
  pendingPreviewTimer = setTimeout(() => {
    pendingPreviewTimer = null
    generatePreview()
  }, delayMs)
}

watch(() => props.modelValue, (newValue) => {
  visible.value = newValue
  if (newValue && props.project) {
    // Set loading immediately so the dialog body shows the spinner the moment it mounts.
    loading.value = true
    startLoadingTimer()
    // Tiny delay coalesces the immediate dialog-open watcher with any synchronous
    // option-change watchers that fire in the same tick.
    schedulePreview(0)
  }
}, { immediate: true })

watch(() => props.project?.id, () => {
  schedulePreview(0)
})

watch(() => props.exportOptions, () => {
  schedulePreview(150)
}, { deep: true })

watch(visible, (newValue) => {
  emit('update:modelValue', newValue)
  if (!newValue) {
    clearPreview()
  }
})

const currentOptions = () => props.exportOptions || {}

const clearPreview = () => {
  renderToken += 1
  loading.value = false
  loadingPhase.value = 'idle'
  stopLoadingTimer()
  if (pendingPreviewTimer) {
    clearTimeout(pendingPreviewTimer)
    pendingPreviewTimer = null
  }
  htmlSrcdoc.value = ''
  if (pdfBlobUrl.value) {
    URL.revokeObjectURL(pdfBlobUrl.value)
    pdfBlobUrl.value = ''
  }
}

const handleModeChange = () => {
  if (visible.value && props.project) {
    generatePreview()
  }
}

const generatePreview = async () => {
  if (!props.project) return

  const token = renderToken + 1
  renderToken = token
  const projectId = props.project.id
  const mode = previewMode.value

  try {
    loading.value = true
    loadingPhase.value = 'compiling'
    startLoadingTimer()
    if (mode === 'pdf') {
      htmlSrcdoc.value = ''
      const pdf = await projectApi.previewProjectPdf(projectId, currentOptions())
      if (renderToken !== token) return
      // Replace any previous blob URL before installing the new one so the
      // browser doesn't keep two PDFs around.
      const previousUrl = pdfBlobUrl.value
      pdfBlobUrl.value = URL.createObjectURL(pdf)
      if (previousUrl) {
        URL.revokeObjectURL(previousUrl)
      }
    } else {
      const html = await projectApi.previewProjectHtml(projectId, currentOptions())
      if (renderToken !== token) return
      htmlSrcdoc.value = html
    }
  } catch (error) {
    if (renderToken !== token) return
    console.error('生成预览失败:', error)
    ElMessage.error(error instanceof Error ? error.message : '预览失败')
    clearPreview()
  } finally {
    if (renderToken === token) {
      loading.value = false
      loadingPhase.value = 'idle'
      stopLoadingTimer()
    }
  }
}

const refreshPreview = () => {
  generatePreview()
}

const exportPdf = async () => {
  if (!props.project) return

  try {
    exporting.value = true
    ElMessage.info('正在生成PDF，请稍候...')
    const blob = await projectApi.exportProjectPdf(props.project.id, currentOptions())
    downloadPdfBlob(blob, `${props.project.project_name}.pdf`)
    ElMessage.success('PDF导出成功')
  } catch (error) {
    console.error('导出PDF失败:', error)
    ElMessage.error(error instanceof Error ? error.message : '导出PDF失败')
  } finally {
    exporting.value = false
  }
}

const downloadPdfBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const handleClose = () => {
  visible.value = false
}

defineExpose({
  close: handleClose,
  refresh: refreshPreview
})

onBeforeUnmount(() => {
  clearPreview()
})
</script>

<style scoped>
:global(.html-preview-dialog.el-dialog),
:global(.html-preview-dialog .el-dialog) {
  width: 94vw !important;
  max-width: 94vw;
  margin-top: 3vh;
  margin-bottom: 3vh;
  height: 94vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:global(.html-preview-dialog .el-dialog__header),
:global(.html-preview-dialog .el-dialog__footer) {
  flex: 0 0 auto;
}

:global(.html-preview-dialog .el-dialog__body) {
  flex: 1 1 auto;
  min-height: 0;
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

:global(.html-preview-dialog .el-dialog__footer) {
  padding: 0;
}

.pdf-preview,
:global(.html-preview-dialog .pdf-preview) {
  height: 100%;
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--cw-border);
  background-color: var(--cw-surface-soft);
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-right {
  justify-content: flex-end;
}

.mode-badge {
  padding: 4px 9px;
  border-radius: 999px;
  background: var(--cw-blue-50);
  color: var(--cw-blue-700);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.toolbar-label {
  color: var(--cw-text-muted);
  font-size: 13px;
}

.project-title {
  font-weight: 600;
  color: var(--cw-text);
}

.content-area {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: #e9eef5;
}

.pdf-frame {
  width: 100%;
  height: 100%;
  min-height: 70vh;
  border: 0;
  background: #fff;
}

.preview-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--cw-text-muted);
  font-size: 14px;
}

.preview-loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(248, 250, 252, 0.92);
  z-index: 10;
  pointer-events: none;
}

.preview-loading-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 28px 36px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 32px rgba(16, 32, 51, 0.12);
  pointer-events: auto;
  max-width: 420px;
  text-align: center;
}

.preview-loading-spinner {
  font-size: 36px;
  color: var(--cw-blue-600, #147ED6);
}

.preview-loading-spinner.is-loading {
  animation: preview-loading-rotate 1s linear infinite;
}

.preview-loading-title {
  margin: 0;
  font-weight: 600;
  font-size: 14px;
  color: var(--cw-text, #102033);
}

.preview-loading-hint {
  margin: 0;
  font-size: 12px;
  color: var(--cw-text-muted, #667587);
  line-height: 1.5;
}

@keyframes preview-loading-rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.html-frame {
  width: 100%;
  height: 100%;
  min-height: 60vh;
  border: 0;
  background: #fff;
}

.dialog-footer {
  text-align: right;
  padding: 10px 16px;
  border-top: 1px solid var(--cw-border);
}

@media (max-width: 720px) {
  .toolbar {
    grid-template-columns: 1fr;
    align-items: stretch;
  }

  .toolbar-center {
    order: -1;
  }

  .toolbar-right {
    justify-content: flex-start;
  }
}
</style>
