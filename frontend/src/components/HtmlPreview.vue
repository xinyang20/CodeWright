<template>
  <el-dialog
    v-model="visible"
    title="PDF 预览"
    width="95%"
    :before-close="handleClose"
    class="html-preview-dialog"
  >
    <div class="pdf-preview" v-loading="loading">
      <div class="toolbar">
        <div class="toolbar-left">
          <span class="mode-badge">PDF</span>
          <span class="toolbar-label">预览与导出使用同一套 LaTeX PDF 生成链路</span>
        </div>

        <div class="toolbar-center">
          <span class="project-title">{{ project?.project_name }}</span>
        </div>

        <div class="toolbar-right">
          <el-button type="text" size="small" @click="refreshPreview">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button type="text" size="small" :loading="exporting" @click="exportPdf">
            <el-icon><Download /></el-icon>
            下载 PDF
          </el-button>
        </div>
      </div>

      <div ref="contentArea" class="content-area">
        <div v-if="pageNumbers.length === 0 && !loading" class="preview-empty">
          PDF 预览尚未生成
        </div>
        <div v-else class="pdf-pages">
          <div
            v-for="pageNumber in pageNumbers"
            :key="pageNumber"
            class="pdf-page"
          >
            <canvas
              :ref="(element) => setPageCanvas(pageNumber, element)"
              class="pdf-page-canvas"
            ></canvas>
            <div class="page-number">第 {{ pageNumber }} / {{ pageCount }} 页</div>
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
import { nextTick, ref, watch, onBeforeUnmount, type ComponentPublicInstance } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download } from '@element-plus/icons-vue'
import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.mjs?url'
import type { PDFDocumentProxy } from 'pdfjs-dist'
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

const visible = ref(false)
const loading = ref(false)
const exporting = ref(false)
const contentArea = ref<HTMLElement>()
const pageNumbers = ref<number[]>([])
const pageCount = ref(0)
const pageCanvases = new Map<number, HTMLCanvasElement>()
let renderToken = 0
let activePdfDocument: PDFDocumentProxy | null = null

watch(() => props.modelValue, (newValue) => {
  visible.value = newValue
  if (newValue && props.project) {
    generatePreview()
  }
}, { immediate: true })

watch(() => props.project?.id, () => {
  if (visible.value && props.project) {
    generatePreview()
  }
})

watch(() => props.exportOptions, () => {
  if (visible.value && props.project) {
    generatePreview()
  }
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
  pageNumbers.value = []
  pageCount.value = 0
  pageCanvases.clear()
  if (activePdfDocument) {
    activePdfDocument.destroy()
    activePdfDocument = null
  }
}

const generatePreview = async () => {
  if (!props.project) return

  try {
    loading.value = true
    const pdf = await projectApi.previewProjectPdf(props.project.id, currentOptions())
    await renderPdf(pdf, renderToken + 1)
  } catch (error) {
    console.error('生成PDF预览失败:', error)
    ElMessage.error(error instanceof Error ? error.message : 'PDF 预览失败')
    clearPreview()
  } finally {
    loading.value = false
  }
}

const ensurePdfJs = async () => {
  const promiseWithResolvers = Promise as typeof Promise & {
    withResolvers?: <T>() => {
      promise: Promise<T>
      resolve: (value: T | PromiseLike<T>) => void
      reject: (reason?: unknown) => void
    }
  }

  // pdf.js 5 relies on this modern API; define it before dynamically loading pdf.js.
  if (!promiseWithResolvers.withResolvers) {
    promiseWithResolvers.withResolvers = <T>() => {
      let resolve!: (value: T | PromiseLike<T>) => void
      let reject!: (reason?: unknown) => void
      const promise = new Promise<T>((promiseResolve, promiseReject) => {
        resolve = promiseResolve
        reject = promiseReject
      })
      return { promise, resolve, reject }
    }
  }

  const pdfjs = await import('pdfjs-dist')
  pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerUrl
  return pdfjs
}

const renderPdf = async (pdf: Blob, token: number) => {
  renderToken = token
  if (activePdfDocument) {
    await activePdfDocument.destroy()
    activePdfDocument = null
  }

  pageNumbers.value = []
  pageCount.value = 0
  pageCanvases.clear()

  const pdfjs = await ensurePdfJs()
  const data = new Uint8Array(await pdf.arrayBuffer())
  const loadingTask = pdfjs.getDocument({ data })
  const pdfDocument = await loadingTask.promise
  if (renderToken !== token) {
    await pdfDocument.destroy()
    return
  }

  activePdfDocument = pdfDocument
  pageCount.value = pdfDocument.numPages
  pageNumbers.value = Array.from({ length: pdfDocument.numPages }, (_, index) => index + 1)
  await nextTick()

  const availableWidth = Math.max((contentArea.value?.clientWidth || 960) - 72, 480)
  const pixelRatio = window.devicePixelRatio || 1

  for (let pageNumber = 1; pageNumber <= pdfDocument.numPages; pageNumber += 1) {
    if (renderToken !== token) return

    const page = await pdfDocument.getPage(pageNumber)
    const baseViewport = page.getViewport({ scale: 1 })
    const scale = Math.min(availableWidth / baseViewport.width, 1.65)
    const viewport = page.getViewport({ scale })
    const canvas = pageCanvases.get(pageNumber)
    const context = canvas?.getContext('2d')
    if (!canvas || !context) continue

    canvas.width = Math.floor(viewport.width * pixelRatio)
    canvas.height = Math.floor(viewport.height * pixelRatio)
    canvas.style.width = `${viewport.width}px`
    canvas.style.height = `${viewport.height}px`
    context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0)

    await page.render({
      canvas,
      canvasContext: context,
      viewport
    }).promise
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

const setPageCanvas = (pageNumber: number, element: Element | ComponentPublicInstance | null) => {
  if (element instanceof HTMLCanvasElement) {
    pageCanvases.set(pageNumber, element)
  } else {
    pageCanvases.delete(pageNumber)
  }
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
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: #e9eef5;
}

.pdf-pages {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 28px;
}

.pdf-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.pdf-page-canvas {
  max-width: 100%;
  background: #fff;
  border-radius: 2px;
  box-shadow: 0 10px 30px rgba(16, 32, 51, 0.18);
}

.page-number {
  color: var(--cw-text-muted);
  font-size: 12px;
}

.preview-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--cw-text-muted);
  font-size: 14px;
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
