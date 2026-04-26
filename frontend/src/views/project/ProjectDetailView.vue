<template>
  <div class="project-detail" v-loading="loading">
    <div class="header">
      <div class="header-left">
        <el-button type="text" @click="$router.back()" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="project-info" v-if="project">
          <h1>{{ project.project_name }}</h1>
          <el-tag :type="project.project_type === 'code' ? 'primary' : 'success'" size="small">
            {{ project.project_type === 'code' ? '代码文件' : '操作文档' }}
          </el-tag>
        </div>
      </div>
      <div class="header-actions" v-if="project">
        <el-button @click="showEditDialog = true">
          <el-icon><Edit /></el-icon>
          编辑项目
        </el-button>
        <el-button type="primary" @click="handlePreview">
          <el-icon><View /></el-icon>
          预览
        </el-button>
        <el-button type="success" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出 PDF
        </el-button>
      </div>
    </div>

    <div class="content" v-if="project">
      <el-row :gutter="24">
        <el-col :xs="24" :lg="16">
          <el-card v-if="project.project_type === 'code'" class="content-card">
            <template #header>
              <div class="card-header">
                <span>代码文件</span>
                <el-button type="primary" size="small" @click="showUploadDialog = true">
                  <el-icon><Plus /></el-icon>
                  上传文件
                </el-button>
              </div>
            </template>

            <SortableFileList
              :files="files"
              @upload="showUploadDialog = true"
              @preview="previewFile"
              @setLanguage="setFileLanguage"
              @rename="editFileName"
              @remove="removeFile"
              @reorder="handleFileReorder"
            />
          </el-card>

          <el-card v-else class="content-card">
            <template #header>
              <div class="card-header">
                <span>文档章节</span>
                <el-button type="primary" size="small" @click="openSectionDialog()">
                  <el-icon><Plus /></el-icon>
                  添加章节
                </el-button>
              </div>
            </template>

            <el-empty v-if="manualSections.length === 0" description="暂无章节">
              <el-button type="primary" @click="openSectionDialog()">添加第一个章节</el-button>
            </el-empty>

            <div v-else class="section-list">
              <div v-for="(section, index) in manualSections" :key="section.id" class="section-item">
                <div class="section-main">
                  <div class="section-order">{{ index + 1 }}</div>
                  <div>
                    <h3>{{ section.title }}</h3>
                    <p>{{ section.body_markdown }}</p>
                    <el-tag v-if="section.image_filename" size="small" type="info">
                      {{ section.image_filename }}
                    </el-tag>
                  </div>
                </div>
                <div class="section-actions">
                  <el-button text :disabled="index === 0" @click="moveSection(index, -1)">上移</el-button>
                  <el-button text :disabled="index === manualSections.length - 1" @click="moveSection(index, 1)">下移</el-button>
                  <el-button text type="primary" @click="openSectionDialog(section)">编辑</el-button>
                  <el-button text type="danger" @click="deleteSection(section)">删除</el-button>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="8">
          <el-card class="info-card">
            <template #header>
              <span>项目信息</span>
            </template>
            <div class="info-item">
              <label>项目名称：</label>
              <span>{{ project.project_name }}</span>
            </div>
            <div class="info-item">
              <label>项目类型：</label>
              <span>{{ project.project_type === 'code' ? '代码文件' : '操作文档' }}</span>
            </div>
            <div class="info-item">
              <label>创建时间：</label>
              <span>{{ formatDate(project.created_at) }}</span>
            </div>
            <div class="info-item">
              <label>更新时间：</label>
              <span>{{ formatDate(project.updated_at) }}</span>
            </div>
          </el-card>

          <el-card class="config-card">
            <template #header>
              <div class="card-header">
                <span>项目配置</span>
                <el-button size="small" type="primary" @click="saveProjectConfig">保存</el-button>
              </div>
            </template>

            <el-form label-position="top" class="config-form">
              <template v-if="project.project_type === 'code'">
                <el-form-item label="代码格式">
                  <el-checkbox-group v-model="configForm.code_options.formatting">
                    <el-checkbox value="line_numbers">显示行号</el-checkbox>
                    <el-checkbox value="continuous_line_numbers">跨文件连续行号</el-checkbox>
                    <el-checkbox value="highlight_syntax">语法高亮</el-checkbox>
                    <el-checkbox value="wrap_lines">自动换行</el-checkbox>
                    <el-checkbox value="file_name_bold">文件名加粗</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
                <el-form-item label="页面布局">
                  <el-radio-group v-model="configForm.code_options.layout">
                    <el-radio value="single_column">单列</el-radio>
                    <el-radio value="double_column">双列</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="字号">
                  <el-select v-model="configForm.code_options.font_size">
                    <el-option label="12px" value="12px" />
                    <el-option label="14px" value="14px" />
                    <el-option label="16px" value="16px" />
                  </el-select>
                </el-form-item>
              </template>

              <template v-else>
                <el-form-item label="文档模板">
                  <el-select v-model="configForm.manual_options.template">
                    <el-option label="标准模板" value="standard" />
                    <el-option label="详细模板" value="detailed" />
                    <el-option label="简洁模板" value="simple" />
                    <el-option
                      v-for="template in publishedTemplates"
                      :key="template.id"
                      :label="`${template.name} v${template.version}`"
                      :value="String(template.id)"
                    />
                  </el-select>
                </el-form-item>
                <el-row :gutter="12">
                  <el-col :xs="24" :sm="8">
                    <el-form-item label="软件名称">
                      <el-input v-model="configForm.manual_options.software_name" placeholder="默认使用项目名称" />
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :sm="8">
                    <el-form-item label="版本号">
                      <el-input v-model="configForm.manual_options.version" placeholder="例如 V1.0.0" />
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :sm="8">
                    <el-form-item label="开发者">
                      <el-input v-model="configForm.manual_options.developer" />
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-form-item label="全局变量替换">
                  <el-switch
                    v-model="configForm.manual_options.enable_global_variables"
                    active-text="启用"
                    inactive-text="关闭"
                  />
                  <div class="config-tip">
                    正文支持 <code v-pre>{{软件名称}}</code>、<code v-pre>{{版本号}}</code>、<code v-pre>{{开发者}}</code>
                  </div>
                </el-form-item>
                <el-form-item label="默认章节">
                  <el-checkbox-group v-model="configForm.manual_options.default_sections">
                    <el-checkbox value="overview">软件概述</el-checkbox>
                    <el-checkbox value="installation">安装说明</el-checkbox>
                    <el-checkbox value="usage">使用说明</el-checkbox>
                    <el-checkbox value="features">功能介绍</el-checkbox>
                    <el-checkbox value="troubleshooting">常见问题</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
              </template>

              <el-form-item label="导出内容">
                <el-checkbox-group v-model="configForm.export_options">
                  <el-checkbox value="include_toc">包含目录</el-checkbox>
                  <el-checkbox value="include_summary">包含统计信息</el-checkbox>
                  <el-checkbox value="watermark">添加水印</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </el-form>
          </el-card>

          <el-card class="history-card">
            <template #header>
              <span>导出历史</span>
            </template>
            <div v-if="currentExportJob" class="export-job">
              <div class="export-job-header">
                <strong>当前导出任务</strong>
                <el-tag size="small" :type="currentExportJob.status === 'failed' ? 'danger' : currentExportJob.status === 'success' ? 'success' : 'warning'">
                  {{ exportStatusText(currentExportJob.status) }}
                </el-tag>
              </div>
              <el-progress :percentage="currentExportJob.progress" />
              <p v-if="currentExportJob.error_message">{{ currentExportJob.error_message }}</p>
            </div>
            <el-empty v-if="exportHistories.length === 0" description="暂无导出记录" />
            <div v-else class="history-list">
              <div v-for="history in exportHistories" :key="history.id" class="history-item">
                <div>
                  <strong>{{ history.status === 'success' ? '导出成功' : '导出失败' }}</strong>
                  <p>{{ formatDate(history.created_at) }}</p>
                </div>
                <el-tag :type="history.status === 'success' ? 'success' : 'danger'" size="small">
                  {{ history.duration_ms || 0 }} ms
                </el-tag>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-dialog v-model="showEditDialog" title="编辑项目" width="500px" :before-close="handleEditDialogClose">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item label="项目名称" prop="project_name">
          <el-input v-model="editForm.project_name" placeholder="请输入项目名称" maxlength="100" show-word-limit />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="handleEditSubmit" :loading="editLoading">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="showUploadDialog" title="上传文件" width="700px" :before-close="handleUploadDialogClose">
      <FileUpload :project-id="project?.id" :auto-add-to-project="true" @success="handleUploadSuccess" @error="handleUploadError" />
    </el-dialog>

    <el-dialog v-model="showSectionDialog" :title="sectionForm.id ? '编辑章节' : '添加章节'" width="720px">
      <el-form label-position="top">
        <el-form-item label="章节标题">
          <el-input v-model="sectionForm.title" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="正文 Markdown">
          <el-input v-model="sectionForm.body_markdown" type="textarea" :rows="8" />
        </el-form-item>
        <el-form-item label="章节截图">
          <div class="image-field">
            <span>{{ sectionForm.image_filename || '未选择截图' }}</span>
            <el-button v-if="sectionForm.image_file_id" text type="danger" @click="clearSectionImage">清除</el-button>
          </div>
          <FileUpload :auto-add-to-project="false" @success="handleSectionImageUploadSuccess" @error="handleUploadError" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showSectionDialog = false">取消</el-button>
          <el-button type="primary" @click="submitSection">保存章节</el-button>
        </div>
      </template>
    </el-dialog>

    <FileRenameDialog v-model="showRenameDialog" :file="currentFile" @success="handleRenameSuccess" />
    <LanguageSelector v-model="showLanguageDialog" :file="currentFile" @success="handleLanguageSuccess" />
    <CodePreview v-model="showPreviewDialog" :file="currentFile" />
    <HtmlPreview v-model="showHtmlPreviewDialog" :project="project" :export-options="currentExportOptions" />
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { ArrowLeft, Edit, View, Download, Plus } from '@element-plus/icons-vue'
import type { ExportHistory, ExportJob, ManualSection, Project, ProjectFile, TemplateInfo } from '@/types'
import { exportApi, projectApi, fileApi, settingsApi } from '@/utils/api'
import FileUpload from '@/components/FileUpload.vue'
import FileRenameDialog from '@/components/FileRenameDialog.vue'
import SortableFileList from '@/components/SortableFileList.vue'
import LanguageSelector from '@/components/LanguageSelector.vue'
import CodePreview from '@/components/CodePreview.vue'
import HtmlPreview from '@/components/HtmlPreview.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const project = ref<Project | null>(null)
const files = ref<ProjectFile[]>([])
const manualSections = ref<ManualSection[]>([])
const exportHistories = ref<ExportHistory[]>([])
const publishedTemplates = ref<TemplateInfo[]>([])
const currentExportJob = ref<ExportJob | null>(null)
const showEditDialog = ref(false)
const showUploadDialog = ref(false)
const showRenameDialog = ref(false)
const showLanguageDialog = ref(false)
const showPreviewDialog = ref(false)
const showHtmlPreviewDialog = ref(false)
const showSectionDialog = ref(false)
const editLoading = ref(false)
const currentFile = ref<ProjectFile | null>(null)
let exportPollingTimer: number | undefined

const editFormRef = ref<FormInstance>()
const editForm = reactive({ project_name: '' })
const editRules: FormRules = {
  project_name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 100, message: '项目名称长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

const configForm = reactive({
  code_options: {
    formatting: ['line_numbers', 'highlight_syntax', 'wrap_lines', 'file_name_bold'],
    layout: 'single_column',
    font_size: '14px',
    export_options: ['include_toc', 'include_summary'],
    template_id: null as number | null
  },
  manual_options: {
    template: 'standard',
    template_id: null as number | null,
    default_sections: ['overview', 'installation', 'usage'],
    software_name: '',
    version: '',
    developer: '',
    enable_global_variables: true
  },
  export_options: ['include_toc', 'include_summary']
})

const sectionForm = reactive({
  id: 0,
  title: '',
  body_markdown: '',
  image_file_id: null as number | null,
  image_filename: '',
  order_index: 1
})

const fetchProject = async () => {
  try {
    loading.value = true
    const projectId = Number(route.params.id)
    const response = await projectApi.getProject(projectId)
    if (response.code !== 0 || !response.data) {
      ElMessage.error(response.message || '获取项目详情失败')
      router.push('/projects')
      return
    }

    const currentProject = response.data as Project
    project.value = currentProject
    editForm.project_name = currentProject.project_name
    parseProjectConfig(currentProject.config_json)

    if (currentProject.project_type === 'code') {
      await fetchProjectFiles()
    } else {
      await fetchManualSections()
    }
    await fetchExportHistory()
  } catch (error) {
    console.error('获取项目详情失败:', error)
    ElMessage.error('获取项目详情失败')
    router.push('/projects')
  } finally {
    loading.value = false
  }
}

const parseProjectConfig = (configJson: string) => {
  try {
    const config = JSON.parse(configJson || '{}')
    Object.assign(configForm.code_options, config.code_options || {})
    Object.assign(configForm.manual_options, config.manual_options || {})
    if (config.manual_options?.template_id) {
      configForm.manual_options.template = String(config.manual_options.template_id)
    }
    configForm.export_options = config.export_options || config.code_options?.export_options || ['include_toc', 'include_summary']
    configForm.code_options.export_options = configForm.export_options
  } catch (error) {
    configForm.export_options = ['include_toc', 'include_summary']
  }
}

const fetchPublishedTemplates = async () => {
  const response = await settingsApi.getPublishedTemplates()
  if (response.code === 0 && response.data) {
    publishedTemplates.value = response.data.templates
  }
}

const fetchProjectFiles = async () => {
  if (!project.value) return
  const response = await fileApi.getProjectFiles(project.value.id)
  if (response.code === 0 && response.data) {
    files.value = response.data.files
  }
}

const fetchManualSections = async () => {
  if (!project.value) return
  const response = await projectApi.getManualSections(project.value.id)
  if (response.code === 0 && response.data) {
    manualSections.value = response.data.sections
  }
}

const fetchExportHistory = async () => {
  if (!project.value) return
  const response = await exportApi.getHistory({ project_id: project.value.id })
  if (response.code === 0 && response.data) {
    exportHistories.value = response.data.histories
  }
}

const handleEditSubmit = async () => {
  if (!editFormRef.value || !project.value) return

  const valid = await editFormRef.value.validate()
  if (!valid) return

  try {
    editLoading.value = true
    const response = await projectApi.updateProject(project.value.id, {
      project_name: editForm.project_name
    })

    if (response.code === 0) {
      ElMessage.success('项目更新成功')
      project.value.project_name = editForm.project_name
      showEditDialog.value = false
    } else {
      ElMessage.error(response.message || '更新项目失败')
    }
  } catch (error) {
    console.error('更新项目失败:', error)
    ElMessage.error('更新项目失败')
  } finally {
    editLoading.value = false
  }
}

const handleEditDialogClose = () => {
  if (project.value) {
    editForm.project_name = project.value.project_name
  }
  showEditDialog.value = false
}

const saveProjectConfig = async () => {
  if (!project.value) return

  configForm.code_options.export_options = configForm.export_options
  const templateId = Number(configForm.manual_options.template)
  configForm.manual_options.template_id = Number.isFinite(templateId) ? templateId : null
  const response = await projectApi.updateProject(project.value.id, {
    config_json: {
      code_options: configForm.code_options,
      manual_options: configForm.manual_options,
      export_options: configForm.export_options
    }
  })

  if (response.code === 0 && response.data) {
    project.value.config_json = response.data.config_json
    ElMessage.success('配置已保存')
  } else {
    ElMessage.error(response.message || '保存配置失败')
  }
}

const buildExportOptions = () => ({
  include_toc: configForm.export_options.includes('include_toc'),
  include_summary: configForm.export_options.includes('include_summary'),
  watermark: configForm.export_options.includes('watermark'),
  formatting: configForm.code_options.formatting,
  layout: configForm.code_options.layout,
  font_size: configForm.code_options.font_size,
  template: configForm.manual_options.template,
  template_id: Number.isFinite(Number(configForm.manual_options.template)) ? Number(configForm.manual_options.template) : null,
  software_name: configForm.manual_options.software_name,
  version: configForm.manual_options.version,
  developer: configForm.manual_options.developer,
  enable_global_variables: configForm.manual_options.enable_global_variables
})

const currentExportOptions = computed(() => buildExportOptions())

const handlePreview = () => {
  showHtmlPreviewDialog.value = true
}

const handleExport = async () => {
  if (!project.value) return

  try {
    currentExportJob.value = null
    ElMessage.info('正在生成PDF，请稍候...')
    const blob = await projectApi.exportProjectPdf(project.value.id, buildExportOptions())
    downloadPdfBlob(blob, `${project.value.project_name}.pdf`)
    ElMessage.success('PDF导出成功')
    fetchExportHistory()
  } catch (error) {
    console.error('导出PDF失败:', error)
    ElMessage.error(error instanceof Error ? error.message : '导出PDF失败')
    fetchExportHistory()
  }
}

const startExportPolling = (jobId: string) => {
  stopExportPolling()
  exportPollingTimer = window.setInterval(async () => {
    const response = await exportApi.getExportStatus(jobId)
    if (response.code !== 0 || !response.data) return

    currentExportJob.value = response.data
    if (response.data.status === 'success') {
      stopExportPolling()
      await downloadExportJob(response.data)
      ElMessage.success('PDF导出成功')
      fetchExportHistory()
    } else if (response.data.status === 'failed') {
      stopExportPolling()
      ElMessage.error(response.data.error_message || '导出失败')
      fetchExportHistory()
    }
  }, 1000)
}

const stopExportPolling = () => {
  if (exportPollingTimer) {
    window.clearInterval(exportPollingTimer)
    exportPollingTimer = undefined
  }
}

const downloadExportJob = async (job: ExportJob) => {
  if (!project.value) return
  const response = await exportApi.downloadJobFile(job.job_id)
  const blob = response instanceof Blob ? response : new Blob([response], { type: 'application/pdf' })
  downloadPdfBlob(blob, `${project.value.project_name}.pdf`)
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

const openSectionDialog = (section?: ManualSection) => {
  sectionForm.id = section?.id || 0
  sectionForm.title = section?.title || ''
  sectionForm.body_markdown = section?.body_markdown || ''
  sectionForm.image_file_id = section?.image_file_id || null
  sectionForm.image_filename = section?.image_filename || ''
  sectionForm.order_index = section?.order_index || manualSections.value.length + 1
  showSectionDialog.value = true
}

const handleSectionImageUploadSuccess = (uploadedFiles: any[]) => {
  const uploaded = uploadedFiles[0]
  if (!uploaded) return
  sectionForm.image_file_id = uploaded.file_id
  sectionForm.image_filename = uploaded.filename
  ElMessage.success('章节截图已上传')
}

const clearSectionImage = () => {
  sectionForm.image_file_id = null
  sectionForm.image_filename = ''
}

const submitSection = async () => {
  if (!project.value) return
  if (!sectionForm.title.trim() || !sectionForm.body_markdown.trim()) {
    ElMessage.warning('请填写章节标题和正文')
    return
  }

  const payload = {
    title: sectionForm.title,
    body_markdown: sectionForm.body_markdown,
    image_file_id: sectionForm.image_file_id,
    order_index: sectionForm.order_index
  }

  const response = sectionForm.id
    ? await projectApi.updateManualSection(project.value.id, sectionForm.id, payload)
    : await projectApi.createManualSection(project.value.id, payload)

  if (response.code === 0) {
    ElMessage.success('章节已保存')
    showSectionDialog.value = false
    fetchManualSections()
  } else {
    ElMessage.error(response.message || '保存章节失败')
  }
}

const deleteSection = async (section: ManualSection) => {
  if (!project.value) return
  try {
    await ElMessageBox.confirm(`确定删除章节 "${section.title}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const response = await projectApi.deleteManualSection(project.value.id, section.id)
    if (response.code === 0) {
      ElMessage.success('章节已删除')
      fetchManualSections()
    } else {
      ElMessage.error(response.message || '删除章节失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除章节失败:', error)
      ElMessage.error('删除章节失败')
    }
  }
}

const moveSection = async (index: number, direction: -1 | 1) => {
  if (!project.value) return
  const nextIndex = index + direction
  if (nextIndex < 0 || nextIndex >= manualSections.value.length) return

  const reordered = [...manualSections.value]
  const current = reordered[index]
  reordered[index] = reordered[nextIndex]
  reordered[nextIndex] = current
  reordered.forEach((section, sectionIndex) => {
    section.order_index = sectionIndex + 1
  })

  const response = await projectApi.reorderManualSections(
    project.value.id,
    reordered.map(section => ({ section_id: section.id, order_index: section.order_index }))
  )
  if (response.code === 0) {
    manualSections.value = reordered
  } else {
    ElMessage.error(response.message || '章节排序失败')
  }
}

const handleUploadSuccess = (uploadedFiles: any[]) => {
  ElMessage.success(`成功上传 ${uploadedFiles.length} 个文件`)
  fetchProjectFiles()
  showUploadDialog.value = false
}

const handleUploadError = (error: string) => {
  ElMessage.error(error)
}

const handleUploadDialogClose = () => {
  showUploadDialog.value = false
}

const handleFileReorder = async (reorderedFiles: ProjectFile[]) => {
  if (!project.value) return

  try {
    const fileOrders = reorderedFiles.map(file => ({
      file_id: file.file_id,
      order_index: file.order_index
    }))
    const response = await fileApi.reorderProjectFiles(project.value.id, fileOrders)
    if (response.code === 0) {
      files.value = reorderedFiles
      ElMessage.success('文件顺序更新成功')
    } else {
      ElMessage.error(response.message || '更新文件顺序失败')
      fetchProjectFiles()
    }
  } catch (error) {
    console.error('更新文件顺序失败:', error)
    ElMessage.error('更新文件顺序失败')
    fetchProjectFiles()
  }
}

const previewFile = (file: ProjectFile) => {
  currentFile.value = file
  showPreviewDialog.value = true
}

const setFileLanguage = (file: ProjectFile) => {
  currentFile.value = file
  showLanguageDialog.value = true
}

const handleLanguageSuccess = async (file: ProjectFile, language: string) => {
  if (!project.value) return

  const response = await fileApi.updateProjectFile(project.value.id, file.file_id, {
    language_override: language
  })

  if (response.code === 0) {
    ElMessage.success('语言类型设置成功')
    const fileIndex = files.value.findIndex(item => item.id === file.id)
    if (fileIndex !== -1) {
      files.value[fileIndex].language_override = language
    }
    showLanguageDialog.value = false
  } else {
    ElMessage.error(response.message || '设置语言类型失败')
  }
}

const editFileName = (file: ProjectFile) => {
  currentFile.value = file
  showRenameDialog.value = true
}

const handleRenameSuccess = async (file: ProjectFile, newDisplayName: string) => {
  if (!project.value) return

  const response = await fileApi.updateProjectFile(project.value.id, file.file_id, {
    display_name: newDisplayName
  })

  if (response.code === 0) {
    ElMessage.success('文件重命名成功')
    const fileIndex = files.value.findIndex(item => item.id === file.id)
    if (fileIndex !== -1) {
      files.value[fileIndex].display_name = newDisplayName
    }
    showRenameDialog.value = false
  } else {
    ElMessage.error(response.message || '重命名失败')
  }
}

const removeFile = async (file: ProjectFile) => {
  if (!project.value) return

  try {
    await ElMessageBox.confirm(
      `确定要从项目中移除文件 "${file.display_name || file.original_filename}" 吗？`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const response = await fileApi.removeFileFromProject(project.value.id, file.file_id)
    if (response.code === 0) {
      ElMessage.success('文件移除成功')
      files.value = files.value.filter(item => item.id !== file.id)
    } else {
      ElMessage.error(response.message || '移除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('移除文件失败:', error)
      ElMessage.error('移除文件失败')
    }
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const exportStatusText = (status: ExportJob['status']) => {
  if (status === 'queued') return '排队中'
  if (status === 'processing') return '处理中'
  if (status === 'success') return '已完成'
  return '失败'
}

onMounted(async () => {
  await fetchPublishedTemplates()
  await fetchProject()
})

onBeforeUnmount(stopExportPolling)
</script>

<style scoped>
.project-detail {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.header,
.card-header,
.section-item,
.history-item,
.section-main,
.image-field {
  display: flex;
  align-items: center;
}

.header,
.card-header,
.section-item,
.history-item {
  justify-content: space-between;
}

.header {
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--cw-border);
}

.header-left {
  display: flex;
  align-items: flex-start;
}

.back-btn {
  margin-right: 16px;
  padding: 8px;
  margin-top: 8px;
}

.project-info h1 {
  margin: 0 0 8px;
  color: #111;
  font-size: 28px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.content-card,
.info-card,
.config-card,
.history-card {
  margin-bottom: 16px;
  border-radius: 8px;
}

.section-list,
.history-list {
  display: flex;
  flex-direction: column;
}

.section-item,
.history-item {
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid var(--cw-border);
}

.section-item:last-child,
.history-item:last-child {
  border-bottom: none;
}

.section-main {
  gap: 12px;
  min-width: 0;
}

.section-order {
  width: 32px;
  height: 32px;
  border-radius: 16px;
  background: var(--cw-blue-50);
  color: var(--cw-blue-700);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.section-main h3 {
  margin: 0 0 6px;
  font-size: 16px;
}

.section-main p,
.history-item p {
  margin: 0;
  color: #666;
  font-size: 13px;
}

.section-main p {
  max-height: 40px;
  overflow: hidden;
}

.section-actions {
  display: flex;
  flex-shrink: 0;
}

.info-item {
  display: flex;
  margin-bottom: 12px;
  font-size: 14px;
}

.info-item label {
  width: 80px;
  color: #666;
  flex-shrink: 0;
}

.info-item span {
  color: #111;
  flex: 1;
}

.config-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.config-tip {
  margin-top: 4px;
  color: #666;
  font-size: 12px;
}

.export-job {
  padding: 12px;
  margin-bottom: 14px;
  border: 1px solid var(--cw-border);
  border-radius: 8px;
  background: var(--cw-blue-25);
}

.export-job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.dialog-footer {
  text-align: right;
}

.image-field {
  justify-content: space-between;
  width: 100%;
  margin-bottom: 12px;
  color: #666;
}
</style>
