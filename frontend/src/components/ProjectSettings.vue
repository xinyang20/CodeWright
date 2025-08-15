<template>
  <el-dialog
    v-model="visible"
    title="项目配置"
    width="800px"
    :before-close="handleClose"
    class="project-settings-dialog"
  >
    <div class="project-settings" v-loading="loading">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        label-position="left"
      >
        <!-- 基本信息 -->
        <el-card class="settings-card">
          <template #header>
            <span>基本信息</span>
          </template>
          
          <el-form-item label="项目名称" prop="project_name">
            <el-input
              v-model="form.project_name"
              placeholder="请输入项目名称"
              maxlength="100"
              show-word-limit
              clearable
            />
          </el-form-item>
          
          <el-form-item label="项目类型">
            <el-tag :type="form.project_type === 'code' ? 'primary' : 'success'" size="large">
              {{ form.project_type === 'code' ? '代码文件' : '操作文档' }}
            </el-tag>
          </el-form-item>
          
          <el-form-item label="创建时间">
            <span class="form-text">{{ formatDate(form.created_at) }}</span>
          </el-form-item>
          
          <el-form-item label="更新时间">
            <span class="form-text">{{ formatDate(form.updated_at) }}</span>
          </el-form-item>
        </el-card>

        <!-- 代码文件项目配置 -->
        <el-card v-if="form.project_type === 'code'" class="settings-card">
          <template #header>
            <span>代码文件配置</span>
          </template>
          
          <el-form-item label="语法高亮">
            <el-switch
              v-model="form.settings.enable_syntax_highlight"
              active-text="启用"
              inactive-text="禁用"
            />
            <div class="form-help">启用后将在预览和导出时显示语法高亮</div>
          </el-form-item>
          
          <el-form-item label="显示行号">
            <el-switch
              v-model="form.settings.show_line_numbers"
              active-text="显示"
              inactive-text="隐藏"
            />
            <div class="form-help">在代码预览和导出时显示行号</div>
          </el-form-item>
          
          <el-form-item label="代码主题">
            <el-select v-model="form.settings.code_theme" placeholder="选择代码主题">
              <el-option label="默认" value="default" />
              <el-option label="GitHub" value="github" />
              <el-option label="VS Code" value="vscode" />
              <el-option label="Atom" value="atom" />
            </el-select>
            <div class="form-help">选择代码高亮的主题样式</div>
          </el-form-item>
          
          <el-form-item label="文件排序">
            <el-radio-group v-model="form.settings.file_sort_order">
              <el-radio label="manual">手动排序</el-radio>
              <el-radio label="name">按名称排序</el-radio>
              <el-radio label="type">按类型排序</el-radio>
              <el-radio label="size">按大小排序</el-radio>
            </el-radio-group>
            <div class="form-help">设置文件列表的默认排序方式</div>
          </el-form-item>
        </el-card>

        <!-- 操作文档项目配置 -->
        <el-card v-if="form.project_type === 'manual'" class="settings-card">
          <template #header>
            <span>操作文档配置</span>
          </template>
          
          <el-form-item label="自动保存">
            <el-switch
              v-model="form.settings.auto_save"
              active-text="启用"
              inactive-text="禁用"
            />
            <div class="form-help">编辑章节时自动保存内容</div>
          </el-form-item>
          
          <el-form-item label="保存间隔">
            <el-input-number
              v-model="form.settings.auto_save_interval"
              :min="10"
              :max="300"
              :step="10"
              :disabled="!form.settings.auto_save"
            />
            <span class="form-unit">秒</span>
            <div class="form-help">自动保存的时间间隔</div>
          </el-form-item>
          
          <el-form-item label="编辑器模式">
            <el-radio-group v-model="form.settings.editor_mode">
              <el-radio label="edit">编辑模式</el-radio>
              <el-radio label="preview">预览模式</el-radio>
              <el-radio label="split">分屏模式</el-radio>
            </el-radio-group>
            <div class="form-help">设置章节编辑器的默认模式</div>
          </el-form-item>
          
          <el-form-item label="章节编号">
            <el-switch
              v-model="form.settings.show_section_numbers"
              active-text="显示"
              inactive-text="隐藏"
            />
            <div class="form-help">在章节标题前显示编号</div>
          </el-form-item>
        </el-card>

        <!-- 导出配置 -->
        <el-card class="settings-card">
          <template #header>
            <span>导出配置</span>
          </template>
          
          <el-form-item label="包含目录">
            <el-switch
              v-model="form.settings.export_include_toc"
              active-text="包含"
              inactive-text="不包含"
            />
            <div class="form-help">PDF导出时是否包含目录页</div>
          </el-form-item>
          
          <el-form-item label="包含统计">
            <el-switch
              v-model="form.settings.export_include_summary"
              active-text="包含"
              inactive-text="不包含"
            />
            <div class="form-help">PDF导出时是否包含统计信息</div>
          </el-form-item>
          
          <el-form-item label="添加水印">
            <el-switch
              v-model="form.settings.export_watermark"
              active-text="添加"
              inactive-text="不添加"
            />
            <div class="form-help">PDF导出时是否添加水印</div>
          </el-form-item>
          
          <el-form-item label="页面格式">
            <el-select v-model="form.settings.export_page_format" placeholder="选择页面格式">
              <el-option label="A4" value="A4" />
              <el-option label="A3" value="A3" />
              <el-option label="Letter" value="Letter" />
              <el-option label="Legal" value="Legal" />
            </el-select>
            <div class="form-help">PDF导出的页面格式</div>
          </el-form-item>
        </el-card>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button @click="resetSettings">重置</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          保存配置
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { Project } from '@/types'

// Props
interface Props {
  modelValue: boolean
  project?: Project | null
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': [project: Project]
}>()

// 响应式数据
const visible = ref(false)
const loading = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()

// 表单数据
const form = reactive({
  project_name: '',
  project_type: 'code' as 'code' | 'manual',
  created_at: '',
  updated_at: '',
  settings: {
    // 代码文件配置
    enable_syntax_highlight: true,
    show_line_numbers: true,
    code_theme: 'default',
    file_sort_order: 'manual',
    
    // 操作文档配置
    auto_save: true,
    auto_save_interval: 30,
    editor_mode: 'split',
    show_section_numbers: true,
    
    // 导出配置
    export_include_toc: true,
    export_include_summary: true,
    export_watermark: false,
    export_page_format: 'A4'
  }
})

// 表单验证规则
const rules: FormRules = {
  project_name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 100, message: '项目名称长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  visible.value = newValue
  if (newValue) {
    initForm()
  }
})

// 监听 visible 变化
watch(visible, (newValue) => {
  emit('update:modelValue', newValue)
})

// 初始化表单
const initForm = async () => {
  if (props.project) {
    form.project_name = props.project.project_name || ''
    form.project_type = props.project.project_type || 'code'
    form.created_at = props.project.created_at || ''
    form.updated_at = props.project.updated_at || ''

    // 从后端API获取项目配置
    await loadProjectSettings()
  }
}

// 加载项目配置
const loadProjectSettings = async () => {
  if (!props.project) return

  try {
    loading.value = true
    const { projectApi } = await import('@/utils/api')
    const response = await projectApi.getProjectSettings(props.project.id)

    if (response.code === 0) {
      const settings = response.data
      // 更新表单配置
      Object.assign(form.settings, {
        enable_syntax_highlight: settings.enable_syntax_highlight,
        show_line_numbers: settings.show_line_numbers,
        code_theme: settings.code_theme,
        file_sort_order: settings.file_sort_order,
        auto_save: settings.auto_save,
        auto_save_interval: settings.auto_save_interval,
        editor_mode: settings.editor_mode,
        show_section_numbers: settings.show_section_numbers,
        export_include_toc: settings.export_include_toc,
        export_include_summary: settings.export_include_summary,
        export_watermark: settings.export_watermark,
        export_page_format: settings.export_page_format
      })
    }
  } catch (error) {
    console.error('加载项目配置失败:', error)
    // 使用默认配置
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (date: string | Date) => {
  if (!date) return '未知'
  const d = new Date(date)
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 重置设置
const resetSettings = async () => {
  if (!props.project) return

  try {
    const { projectApi } = await import('@/utils/api')
    const response = await projectApi.resetProjectSettings(props.project.id)

    if (response.code === 0) {
      const settings = response.data
      // 更新表单配置
      Object.assign(form.settings, {
        enable_syntax_highlight: settings.enable_syntax_highlight,
        show_line_numbers: settings.show_line_numbers,
        code_theme: settings.code_theme,
        file_sort_order: settings.file_sort_order,
        auto_save: settings.auto_save,
        auto_save_interval: settings.auto_save_interval,
        editor_mode: settings.editor_mode,
        show_section_numbers: settings.show_section_numbers,
        export_include_toc: settings.export_include_toc,
        export_include_summary: settings.export_include_summary,
        export_watermark: settings.export_watermark,
        export_page_format: settings.export_page_format
      })
      ElMessage.success('配置已重置为默认值')
    } else {
      ElMessage.error(response.message || '重置配置失败')
    }
  } catch (error) {
    console.error('重置配置失败:', error)
    ElMessage.error('重置配置失败')
  }
}

// 保存配置
const handleSave = async () => {
  try {
    const valid = await formRef.value?.validate()
    if (!valid) return

    saving.value = true

    if (!props.project) {
      ElMessage.error('项目信息不存在')
      return
    }

    // 调用后端API保存项目配置
    const { projectApi } = await import('@/utils/api')
    const response = await projectApi.updateProjectSettings(props.project.id, form.settings)

    if (response.code === 0) {
      ElMessage.success('项目配置保存成功')
      emit('saved', { ...props.project, project_name: form.project_name } as Project)
      handleClose()
    } else {
      ElMessage.error(response.message || '保存配置失败')
    }

  } catch (error) {
    console.error('保存项目配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  // 重置表单
  nextTick(() => {
    formRef.value?.resetFields()
  })
}
</script>

<style scoped>
.project-settings-dialog {
  --el-dialog-content-font-size: 14px;
}

.project-settings-dialog :deep(.el-dialog) {
  margin-top: 2vh;
  margin-bottom: 2vh;
  height: 96vh;
  display: flex;
  flex-direction: column;
}

.project-settings-dialog :deep(.el-dialog__body) {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.project-settings {
  height: 100%;
}

.settings-card {
  margin-bottom: 20px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.settings-card:last-child {
  margin-bottom: 0;
}

.settings-card :deep(.el-card__header) {
  background: #f5f7fa;
  font-weight: 600;
  color: #303133;
}

.form-text {
  color: #606266;
  font-size: 14px;
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.form-unit {
  margin-left: 8px;
  color: #909399;
  font-size: 14px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #e4e7ed;
  background: #fafafa;
}

/* 表单项样式优化 */
.project-settings :deep(.el-form-item) {
  margin-bottom: 20px;
}

.project-settings :deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
}

.project-settings :deep(.el-input) {
  width: 100%;
}

.project-settings :deep(.el-select) {
  width: 200px;
}

.project-settings :deep(.el-input-number) {
  width: 120px;
}

/* 开关样式 */
.project-settings :deep(.el-switch) {
  margin-right: 12px;
}

/* 单选按钮组样式 */
.project-settings :deep(.el-radio-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.project-settings :deep(.el-radio) {
  margin-right: 0;
}

/* 标签样式 */
.project-settings :deep(.el-tag) {
  font-size: 14px;
  padding: 8px 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .project-settings-dialog {
    width: 95% !important;
  }

  .project-settings-dialog :deep(.el-form-item__label) {
    width: 100px !important;
  }

  .project-settings :deep(.el-select) {
    width: 100%;
  }

  .project-settings :deep(.el-radio-group) {
    flex-direction: column;
    gap: 8px;
  }

  .dialog-footer {
    flex-direction: column-reverse;
    gap: 8px;
  }

  .dialog-footer .el-button {
    width: 100%;
  }
}
</style>
