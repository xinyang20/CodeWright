<template>
  <div class="admin" v-loading="loading">
    <div class="page-header">
      <div>
        <h1>管理员面板</h1>
        <p>系统用户、模板、公告、PDF 样式与代码高亮规则</p>
      </div>
      <el-button @click="refreshAll">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <el-row :gutter="20" class="metric-row" v-if="stats">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card><div class="metric"><span>用户</span><strong>{{ stats.users.total }}</strong></div></el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card><div class="metric"><span>项目</span><strong>{{ stats.projects.total }}</strong></div></el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card><div class="metric"><span>文件</span><strong>{{ stats.files.total }}</strong></div></el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card><div class="metric"><span>导出成功率</span><strong>{{ stats.exports.success_rate.toFixed(0) }}%</strong></div></el-card>
      </el-col>
    </el-row>

    <el-card>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="用户管理" name="users">
          <div class="toolbar">
            <el-input v-model="userSearch" clearable placeholder="搜索用户名" @keyup.enter="fetchUsers" @clear="fetchUsers" />
            <el-button type="primary" @click="fetchUsers">搜索</el-button>
          </div>

          <el-table :data="users" stripe>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="role" label="角色" width="120">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">{{ row.role }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="140">
              <template #default="{ row }">
                <el-switch
                  v-model="row.is_active"
                  :disabled="row.role === 'admin'"
                  active-text="启用"
                  inactive-text="禁用"
                  @change="(value) => updateUserStatus(row.id, Boolean(value))"
                />
              </template>
            </el-table-column>
            <el-table-column label="创建时间" width="190">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
          </el-table>

          <div class="pagination">
            <el-pagination
              v-model:current-page="userPage"
              v-model:page-size="userPageSize"
              :total="userTotal"
              layout="total, prev, pager, next"
              @current-change="fetchUsers"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="模板管理" name="templates">
          <el-form :inline="true" :model="templateForm" class="template-form">
            <el-form-item label="名称">
              <el-input v-model="templateForm.name" placeholder="模板名称" />
            </el-form-item>
            <el-form-item label="版本">
              <el-input v-model="templateForm.version" placeholder="1.0.0" />
            </el-form-item>
            <el-form-item label="说明">
              <el-input v-model="templateForm.description" placeholder="模板说明" />
            </el-form-item>
            <el-form-item>
              <input type="file" accept=".html" @change="handleTemplateFileChange" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="createTemplate">上传模板</el-button>
            </el-form-item>
          </el-form>

          <el-table :data="templates" stripe>
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="version" label="版本" width="120" />
            <el-table-column prop="description" label="说明" />
            <el-table-column label="状态" width="150">
              <template #default="{ row }">
                <el-select v-model="row.status" size="small" @change="(value: 'draft' | 'published') => updateTemplateStatus(row.id, value)">
                  <el-option label="草稿" value="draft" />
                  <el-option label="已发布" value="published" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="更新时间" width="190">
              <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="系统设置" name="settings">
          <el-row :gutter="20">
            <el-col :xs="24" :lg="8">
              <el-card class="sub-card">
                <template #header>PDF LaTeX 样式</template>
                <el-form label-position="top">
                  <el-form-item label="LaTeX 引擎">
                    <el-select v-model="pdfStyleForm.latex_engine">
                      <el-option label="XeLaTeX" value="xelatex" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="文档类">
                    <el-input v-model="pdfStyleForm.document_class" placeholder="article" />
                  </el-form-item>
                  <el-form-item label="基础字号">
                    <el-input v-model="pdfStyleForm.font_size" />
                  </el-form-item>
                  <el-form-item label="geometry 参数">
                    <el-input v-model="pdfStyleForm.page_geometry" placeholder="a4paper,margin=2cm" />
                  </el-form-item>
                  <el-form-item label="中文主字体">
                    <el-input v-model="pdfStyleForm.main_font" placeholder="PingFang SC" />
                  </el-form-item>
                  <el-form-item label="等宽字体">
                    <el-input v-model="pdfStyleForm.mono_font" placeholder="Menlo" />
                  </el-form-item>
                  <el-form-item label="行距">
                    <el-input v-model="pdfStyleForm.line_stretch" placeholder="1.25" />
                  </el-form-item>
                  <el-form-item label="页眉 LaTeX">
                    <el-input v-model="pdfStyleForm.header_latex" type="textarea" :rows="2" placeholder="可留空" />
                  </el-form-item>
                  <el-form-item label="页脚 LaTeX">
                    <el-input v-model="pdfStyleForm.footer_latex" type="textarea" :rows="2" />
                  </el-form-item>
                  <el-form-item label="自定义导言区 LaTeX">
                    <el-input v-model="pdfStyleForm.preamble_latex" type="textarea" :rows="5" placeholder="例如 \\usepackage{titlesec}" />
                    <div class="form-tip">内容会直接写入导言区，请提交合法 LaTeX。</div>
                  </el-form-item>
                  <el-button type="primary" @click="savePdfStyle">保存 LaTeX 样式</el-button>
                </el-form>
              </el-card>
            </el-col>

            <el-col :xs="24" :lg="8">
              <el-card class="sub-card">
                <template #header>上传限制</template>
                <el-form label-position="top">
                  <el-form-item label="单文件上限 MB">
                    <el-input-number v-model="uploadForm.max_upload_size_mb" :min="1" :max="100" />
                  </el-form-item>
                  <el-form-item label="项目总量上限 MB">
                    <el-input-number v-model="uploadForm.max_project_size_mb" :min="1" :max="1000" />
                  </el-form-item>
                  <el-form-item label="允许后缀">
                    <el-input v-model="allowedExtensionsText" type="textarea" :rows="5" />
                    <div class="form-tip">用逗号或换行分隔，例如 .py, .java, .png</div>
                  </el-form-item>
                  <el-button type="primary" @click="saveUploadSetting">保存上传限制</el-button>
                </el-form>
              </el-card>
            </el-col>

            <el-col :xs="24" :lg="8">
              <el-card class="sub-card">
                <template #header>手册默认行为</template>
                <el-form label-position="top">
                  <el-form-item label="全局变量替换">
                    <el-switch v-model="manualForm.enable_global_variables" active-text="启用" inactive-text="关闭" />
                  </el-form-item>
                  <el-button type="primary" @click="saveManualSetting">保存手册设置</el-button>
                </el-form>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="公告管理" name="announcements">
          <el-form :model="announcementForm" label-position="top" class="announcement-form">
            <el-row :gutter="16">
              <el-col :xs="24" :lg="8">
                <el-form-item label="标题">
                  <el-input v-model="announcementForm.title" maxlength="200" show-word-limit />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :lg="4">
                <el-form-item label="状态">
                  <el-select v-model="announcementForm.status">
                    <el-option label="草稿" value="draft" />
                    <el-option label="发布" value="published" />
                    <el-option label="下线" value="archived" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :lg="12">
                <el-form-item label="正文 Markdown">
                  <el-input v-model="announcementForm.body_markdown" type="textarea" :rows="3" />
                </el-form-item>
              </el-col>
            </el-row>
            <div class="form-actions">
              <el-button @click="resetAnnouncementForm">清空</el-button>
              <el-button type="primary" @click="saveAnnouncement">{{ announcementForm.id ? '更新公告' : '创建公告' }}</el-button>
            </div>
          </el-form>

          <el-table :data="announcements" stripe>
            <el-table-column prop="title" label="标题" />
            <el-table-column prop="status" label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="announcementTagType(row.status)">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="发布时间" width="190">
              <template #default="{ row }">{{ row.published_at ? formatDate(row.published_at) : '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="{ row }">
                <el-button text type="primary" @click="editAnnouncement(row)">编辑</el-button>
                <el-button text type="danger" @click="deleteAnnouncement(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="高亮映射" name="highlight">
          <div class="mapping-toolbar">
            <el-input v-model="newMapping.suffix" placeholder=".vue" />
            <el-input v-model="newMapping.language" placeholder="html" />
            <el-switch v-model="newMapping.enabled" active-text="启用" inactive-text="禁用" />
            <el-button @click="addMapping">添加映射</el-button>
            <el-button type="primary" @click="saveMappings">保存全部</el-button>
          </div>

          <el-table :data="highlightMappings" stripe>
            <el-table-column label="后缀" width="160">
              <template #default="{ row }">
                <el-input v-model="row.suffix" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="Pygments 语言">
              <template #default="{ row }">
                <el-input v-model="row.language" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="启用" width="120">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { adminApi, settingsApi } from '@/utils/api'
import type {
  AdminStats,
  Announcement,
  HighlightMapping,
  PdfStyleSetting,
  SystemSettings,
  TemplateInfo,
  UploadSetting,
  User,
  UserListResponse
} from '@/types'

const loading = ref(false)
const activeTab = ref('users')
const stats = ref<AdminStats | null>(null)
const users = ref<User[]>([])
const userSearch = ref('')
const userPage = ref(1)
const userPageSize = ref(10)
const userTotal = ref(0)
const templates = ref<TemplateInfo[]>([])
const announcements = ref<Announcement[]>([])
const highlightMappings = ref<HighlightMapping[]>([])
const selectedTemplateFile = ref<File | null>(null)
const allowedExtensionsText = ref('')

const templateForm = reactive({
  name: '',
  version: '1.0.0',
  description: ''
})

const defaultPdfStyle: PdfStyleSetting = {
  latex_engine: 'xelatex',
  document_class: 'article',
  font_size: '12pt',
  page_geometry: 'a4paper,margin=2cm',
  main_font: 'PingFang SC',
  mono_font: 'Menlo',
  line_stretch: '1.25',
  header_latex: '',
  footer_latex: '\\thepage',
  preamble_latex: ''
}

const pdfStyleForm = reactive<PdfStyleSetting>({ ...defaultPdfStyle })

const uploadForm = reactive<UploadSetting>({
  max_upload_size_mb: 10,
  allowed_extensions: [],
  max_project_size_mb: 100
})

const manualForm = reactive({
  enable_global_variables: true
})

const announcementForm = reactive({
  id: 0,
  title: '',
  body_markdown: '',
  status: 'draft' as Announcement['status']
})

const newMapping = reactive<HighlightMapping>({
  suffix: '',
  language: '',
  enabled: true
})

const refreshAll = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchStats(),
      fetchUsers(),
      fetchTemplates(),
      fetchSettings(),
      fetchAnnouncements(),
      fetchMappings()
    ])
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  const response = await adminApi.getStats()
  if (response.code === 0 && response.data) {
    stats.value = response.data
  }
}

const fetchUsers = async () => {
  const response = await adminApi.getUsers({
    page: userPage.value,
    page_size: userPageSize.value,
    search: userSearch.value || undefined
  })
  if (response.code === 0 && response.data) {
    const data = response.data as UserListResponse
    users.value = data.users
    userTotal.value = data.total
  }
}

const updateUserStatus = async (userId: number, isActive: boolean) => {
  try {
    const response = await adminApi.updateUserStatus(userId, isActive)
    if (response.code === 0) {
      ElMessage.success('用户状态已更新')
    } else {
      ElMessage.error(response.message || '更新用户状态失败')
      fetchUsers()
    }
  } catch (error) {
    console.error('更新用户状态失败:', error)
    ElMessage.error('更新用户状态失败')
    fetchUsers()
  }
}

const fetchTemplates = async () => {
  const response = await settingsApi.getTemplates()
  if (response.code === 0 && response.data) {
    templates.value = response.data.templates
  }
}

const handleTemplateFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  selectedTemplateFile.value = input.files?.[0] || null
}

const createTemplate = async () => {
  if (!templateForm.name || !templateForm.version || !selectedTemplateFile.value) {
    ElMessage.warning('请填写模板信息并选择 HTML 文件')
    return
  }

  try {
    const response = await settingsApi.createTemplate({
      name: templateForm.name,
      version: templateForm.version,
      description: templateForm.description,
      file: selectedTemplateFile.value
    })
    if (response.code === 0) {
      ElMessage.success('模板上传成功')
      templateForm.name = ''
      templateForm.version = '1.0.0'
      templateForm.description = ''
      selectedTemplateFile.value = null
      fetchTemplates()
    } else {
      ElMessage.error(response.message || '模板上传失败')
    }
  } catch (error) {
    console.error('模板上传失败:', error)
    ElMessage.error('模板上传失败')
  }
}

const updateTemplateStatus = async (templateId: number, status: 'draft' | 'published') => {
  try {
    const response = await settingsApi.updateTemplateStatus(templateId, status)
    if (response.code === 0) {
      ElMessage.success('模板状态已更新')
    } else {
      ElMessage.error(response.message || '模板状态更新失败')
      fetchTemplates()
    }
  } catch (error) {
    console.error('模板状态更新失败:', error)
    ElMessage.error('模板状态更新失败')
    fetchTemplates()
  }
}

const fetchSettings = async () => {
  const response = await settingsApi.getSystemSettings()
  if (response.code === 0 && response.data) {
    applySettings(response.data)
  }
}

const normalizePdfStyle = (style: Partial<PdfStyleSetting> & Record<string, unknown> = {}): PdfStyleSetting => {
  const legacyMargin = typeof style.page_margin === 'string' ? style.page_margin : ''
  const legacyFontFamily = typeof style.font_family === 'string' ? style.font_family : ''
  const legacyHeader = typeof style.header_text === 'string' ? style.header_text : ''
  const legacyFooter = typeof style.footer_text === 'string' ? style.footer_text : ''

  return {
    ...defaultPdfStyle,
    ...style,
    font_size: typeof style.font_size === 'string' && style.font_size.endsWith('px')
      ? style.font_size.replace('px', 'pt')
      : (style.font_size || defaultPdfStyle.font_size),
    page_geometry: style.page_geometry || (legacyMargin ? `a4paper,margin=${legacyMargin}` : defaultPdfStyle.page_geometry),
    main_font: style.main_font || legacyFontFamily.split(',')[0]?.trim() || defaultPdfStyle.main_font,
    header_latex: style.header_latex || legacyHeader,
    footer_latex: style.footer_latex || (legacyFooter && legacyFooter !== '页码' ? legacyFooter : defaultPdfStyle.footer_latex)
  }
}

const buildPdfStylePayload = (): PdfStyleSetting => ({
  latex_engine: pdfStyleForm.latex_engine,
  document_class: pdfStyleForm.document_class,
  font_size: pdfStyleForm.font_size,
  page_geometry: pdfStyleForm.page_geometry,
  main_font: pdfStyleForm.main_font,
  mono_font: pdfStyleForm.mono_font,
  line_stretch: pdfStyleForm.line_stretch,
  header_latex: pdfStyleForm.header_latex,
  footer_latex: pdfStyleForm.footer_latex,
  preamble_latex: pdfStyleForm.preamble_latex
})

const applySettings = (settings: SystemSettings) => {
  Object.assign(pdfStyleForm, normalizePdfStyle(settings.pdf_style as Partial<PdfStyleSetting> & Record<string, unknown>))
  Object.assign(uploadForm, settings.upload)
  Object.assign(manualForm, settings.manual)
  allowedExtensionsText.value = settings.upload.allowed_extensions.join(', ')
}

const savePdfStyle = async () => {
  const response = await settingsApi.updateSystemSetting('pdf_style', buildPdfStylePayload())
  handleSettingResponse(response, 'LaTeX 样式已保存')
}

const saveUploadSetting = async () => {
  const allowedExtensions = allowedExtensionsText.value
    .split(/[\s,，]+/)
    .map(item => item.trim())
    .filter(Boolean)
    .map(item => item.startsWith('.') ? item : `.${item}`)

  const response = await settingsApi.updateSystemSetting('upload', {
    ...uploadForm,
    allowed_extensions: allowedExtensions
  })
  handleSettingResponse(response, '上传限制已保存')
}

const saveManualSetting = async () => {
  const response = await settingsApi.updateSystemSetting('manual', { ...manualForm })
  handleSettingResponse(response, '手册设置已保存')
}

const handleSettingResponse = (response: { code: number; message: string; data?: SystemSettings }, message: string) => {
  if (response.code === 0 && response.data) {
    applySettings(response.data)
    ElMessage.success(message)
  } else {
    ElMessage.error(response.message || '保存设置失败')
  }
}

const fetchAnnouncements = async () => {
  const response = await settingsApi.getAnnouncements()
  if (response.code === 0 && response.data) {
    announcements.value = response.data.announcements
  }
}

const saveAnnouncement = async () => {
  if (!announcementForm.title.trim() || !announcementForm.body_markdown.trim()) {
    ElMessage.warning('请填写公告标题和正文')
    return
  }

  const payload = {
    title: announcementForm.title,
    body_markdown: announcementForm.body_markdown,
    status: announcementForm.status
  }
  const response = announcementForm.id
    ? await settingsApi.updateAnnouncement(announcementForm.id, payload)
    : await settingsApi.createAnnouncement(payload)

  if (response.code === 0) {
    ElMessage.success('公告已保存')
    resetAnnouncementForm()
    fetchAnnouncements()
  } else {
    ElMessage.error(response.message || '保存公告失败')
  }
}

const editAnnouncement = (announcement: Announcement) => {
  announcementForm.id = announcement.id
  announcementForm.title = announcement.title
  announcementForm.body_markdown = announcement.body_markdown
  announcementForm.status = announcement.status
}

const resetAnnouncementForm = () => {
  announcementForm.id = 0
  announcementForm.title = ''
  announcementForm.body_markdown = ''
  announcementForm.status = 'draft'
}

const deleteAnnouncement = async (announcementId: number) => {
  try {
    await ElMessageBox.confirm('确定删除该公告吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const response = await settingsApi.deleteAnnouncement(announcementId)
    if (response.code === 0) {
      ElMessage.success('公告已删除')
      fetchAnnouncements()
    } else {
      ElMessage.error(response.message || '删除公告失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除公告失败:', error)
      ElMessage.error('删除公告失败')
    }
  }
}

const fetchMappings = async () => {
  const response = await settingsApi.getHighlightMapping()
  if (response.code === 0 && response.data) {
    highlightMappings.value = response.data.mappings
  }
}

const addMapping = () => {
  if (!newMapping.suffix.trim() || !newMapping.language.trim()) {
    ElMessage.warning('请填写后缀和语言')
    return
  }
  const suffix = newMapping.suffix.startsWith('.') ? newMapping.suffix : `.${newMapping.suffix}`
  const existing = highlightMappings.value.find(item => item.suffix === suffix)
  if (existing) {
    existing.language = newMapping.language
    existing.enabled = newMapping.enabled
  } else {
    highlightMappings.value.unshift({
      suffix,
      language: newMapping.language,
      enabled: newMapping.enabled
    })
  }
  newMapping.suffix = ''
  newMapping.language = ''
  newMapping.enabled = true
}

const saveMappings = async () => {
  const response = await settingsApi.updateHighlightMapping(highlightMappings.value)
  if (response.code === 0 && response.data) {
    highlightMappings.value = response.data.mappings
    ElMessage.success('高亮映射已保存')
  } else {
    ElMessage.error(response.message || '保存高亮映射失败')
  }
}

const announcementTagType = (status: Announcement['status']) => {
  if (status === 'published') return 'success'
  if (status === 'archived') return 'info'
  return 'warning'
}

const statusText = (status: Announcement['status']) => {
  if (status === 'published') return '已发布'
  if (status === 'archived') return '已下线'
  return '草稿'
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

onMounted(refreshAll)
</script>

<style scoped>
.admin {
  padding: 24px;
  max-width: 1280px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 6px;
}

.page-header p,
.form-tip {
  margin: 0;
  color: #666;
}

.metric-row {
  margin-bottom: 20px;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric span {
  color: #666;
}

.metric strong {
  font-size: 28px;
}

.toolbar,
.template-form,
.announcement-form,
.mapping-toolbar {
  margin-bottom: 16px;
}

.toolbar,
.mapping-toolbar,
.form-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.toolbar {
  max-width: 420px;
}

.mapping-toolbar {
  max-width: 780px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.sub-card {
  margin-bottom: 16px;
}

.form-tip {
  font-size: 12px;
  margin-top: 4px;
}
</style>
