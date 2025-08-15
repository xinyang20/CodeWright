<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑章节' : '添加章节'"
    width="80%"
    :before-close="handleClose"
    class="section-editor-dialog"
  >
    <div class="section-editor" v-loading="loading">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        label-position="top"
      >
        <!-- 章节标题 -->
        <el-form-item label="章节标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请输入章节标题"
            maxlength="200"
            show-word-limit
            clearable
          />
        </el-form-item>

        <!-- 章节图片 -->
        <el-form-item label="章节图片">
          <div class="image-upload-section">
            <div v-if="currentImage" class="current-image">
              <img :src="getImageUrl(currentImage)" alt="章节图片" class="preview-image" />
              <div class="image-actions">
                <el-button type="text" size="small" @click="removeImage">
                  <el-icon><Delete /></el-icon>
                  移除图片
                </el-button>
              </div>
            </div>
            <div v-else class="upload-area">
              <el-upload
                ref="uploadRef"
                class="image-uploader"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleImageChange"
                accept="image/*"
                drag
              >
                <div class="upload-content">
                  <el-icon class="upload-icon"><Plus /></el-icon>
                  <div class="upload-text">
                    <p>点击或拖拽上传图片</p>
                    <p class="upload-hint">支持 JPG、PNG、GIF 格式，大小不超过 10MB</p>
                  </div>
                </div>
              </el-upload>
            </div>
          </div>
        </el-form-item>

        <!-- 章节内容 -->
        <el-form-item label="章节内容" prop="body_markdown">
          <div class="content-editor">
            <div class="editor-toolbar">
              <el-button-group size="small">
                <el-button 
                  :type="editorMode === 'edit' ? 'primary' : ''"
                  @click="editorMode = 'edit'"
                >
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button 
                  :type="editorMode === 'preview' ? 'primary' : ''"
                  @click="editorMode = 'preview'"
                >
                  <el-icon><View /></el-icon>
                  预览
                </el-button>
                <el-button 
                  :type="editorMode === 'split' ? 'primary' : ''"
                  @click="editorMode = 'split'"
                >
                  <el-icon><Grid /></el-icon>
                  分屏
                </el-button>
              </el-button-group>
              
              <div class="toolbar-right">
                <el-button type="text" size="small" @click="insertMarkdownTemplate">
                  <el-icon><Document /></el-icon>
                  插入模板
                </el-button>
              </div>
            </div>

            <div class="editor-content" :class="`mode-${editorMode}`">
              <!-- 编辑模式 -->
              <div v-if="editorMode === 'edit' || editorMode === 'split'" class="editor-pane">
                <el-input
                  v-model="form.body_markdown"
                  type="textarea"
                  :rows="20"
                  placeholder="请输入章节内容，支持 Markdown 语法..."
                  class="markdown-editor"
                />
              </div>

              <!-- 预览模式 -->
              <div v-if="editorMode === 'preview' || editorMode === 'split'" class="preview-pane">
                <div class="markdown-preview" v-html="renderedMarkdown"></div>
              </div>
            </div>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage, type FormInstance, type FormRules, type UploadFile } from 'element-plus'
import {
  Plus,
  Delete,
  Edit,
  View,
  Grid,
  Document
} from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

// Props
interface Props {
  modelValue: boolean
  projectId: number
  section?: any
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': [section: any]
}>()

// 响应式数据
const visible = ref(false)
const loading = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const uploadRef = ref()
const editorMode = ref<'edit' | 'preview' | 'split'>('edit')

// 表单数据
const form = reactive({
  title: '',
  body_markdown: '',
  image_file_id: null as number | null
})

// 当前图片信息
const currentImage = ref<any>(null)
const pendingImageFile = ref<File | null>(null)

// 计算属性
const isEdit = computed(() => !!props.section)

// Markdown 渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

// 渲染的 Markdown 内容
const renderedMarkdown = computed(() => {
  if (!form.body_markdown) return '<p class="empty-content">暂无内容</p>'
  
  const rendered = md.render(form.body_markdown)
  return DOMPurify.sanitize(rendered)
})

// 表单验证规则
const rules: FormRules = {
  title: [
    { required: true, message: '请输入章节标题', trigger: 'blur' },
    { min: 1, max: 200, message: '标题长度在 1 到 200 个字符', trigger: 'blur' }
  ],
  body_markdown: [
    { required: true, message: '请输入章节内容', trigger: 'blur' }
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
const initForm = () => {
  if (props.section) {
    // 编辑模式
    form.title = props.section.title || ''
    form.body_markdown = props.section.body_markdown || ''
    form.image_file_id = props.section.image_file?.id || null
    currentImage.value = props.section.image_file || null
  } else {
    // 新建模式
    form.title = ''
    form.body_markdown = ''
    form.image_file_id = null
    currentImage.value = null
  }
  pendingImageFile.value = null
}

// 处理图片上传
const handleImageChange = (file: UploadFile) => {
  const rawFile = file.raw
  if (!rawFile) return

  // 验证文件类型
  if (!rawFile.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }

  // 验证文件大小 (10MB)
  if (rawFile.size > 10 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 10MB')
    return
  }

  pendingImageFile.value = rawFile
  
  // 创建预览
  const reader = new FileReader()
  reader.onload = (e) => {
    currentImage.value = {
      id: null,
      original_filename: rawFile.name,
      preview_url: e.target?.result as string
    }
  }
  reader.readAsDataURL(rawFile)
}

// 移除图片
const removeImage = () => {
  currentImage.value = null
  pendingImageFile.value = null
  form.image_file_id = null
  uploadRef.value?.clearFiles()
}

// 获取图片URL
const getImageUrl = (image: any) => {
  if (image.preview_url) {
    return image.preview_url
  }
  if (image.storage_path) {
    return `/uploads/${image.storage_path.split('/').pop()}`
  }
  return ''
}

// 插入 Markdown 模板
const insertMarkdownTemplate = () => {
  const template = `## 操作步骤

1. 第一步操作说明
2. 第二步操作说明
3. 第三步操作说明

### 注意事项

- 注意事项1
- 注意事项2

### 相关说明

这里是详细的说明内容...
`
  
  if (form.body_markdown) {
    form.body_markdown += '\n\n' + template
  } else {
    form.body_markdown = template
  }
}

// 保存章节
const handleSave = async () => {
  try {
    const valid = await formRef.value?.validate()
    if (!valid) return

    saving.value = true

    let imageFileId = form.image_file_id

    // 如果有新图片，先上传图片
    if (pendingImageFile.value) {
      try {
        const { fileApi } = await import('@/utils/api')
        const uploadResponse = await fileApi.uploadFile(pendingImageFile.value)

        if (uploadResponse.code === 0) {
          imageFileId = uploadResponse.data.file_id
        } else {
          throw new Error(uploadResponse.message || '图片上传失败')
        }
      } catch (uploadError) {
        ElMessage.error('图片上传失败')
        return
      }
    }

    // 准备保存数据
    const saveData = {
      title: form.title,
      body_markdown: form.body_markdown,
      image_file_id: imageFileId
    }

    // 创建或更新章节
    const { manualApi } = await import('@/utils/api')
    let response

    if (isEdit.value && props.section) {
      response = await manualApi.updateSection(props.section.id, saveData)
    } else {
      response = await manualApi.createSection(props.projectId, saveData)
    }

    if (response.code === 0) {
      ElMessage.success(isEdit.value ? '章节更新成功' : '章节创建成功')
      emit('saved', response.data)
      handleClose()
    } else {
      ElMessage.error(response.message || '保存失败')
    }

  } catch (error) {
    console.error('保存章节失败:', error)
    ElMessage.error('保存失败')
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
    removeImage()
  })
}
</script>

<style scoped>
.section-editor-dialog {
  --el-dialog-content-font-size: 14px;
}

.section-editor-dialog :deep(.el-dialog) {
  margin-top: 2vh;
  margin-bottom: 2vh;
  height: 96vh;
  display: flex;
  flex-direction: column;
}

.section-editor-dialog :deep(.el-dialog__body) {
  flex: 1;
  padding: 20px;
  overflow: hidden;
}

.section-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 图片上传区域 */
.image-upload-section {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
}

.current-image {
  position: relative;
  background: #fafafa;
}

.preview-image {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  display: block;
}

.image-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 4px;
  padding: 4px;
}

.image-actions .el-button {
  color: white;
  border: none;
  background: transparent;
}

.image-actions .el-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.upload-area {
  padding: 0;
}

.image-uploader {
  width: 100%;
}

.image-uploader :deep(.el-upload) {
  width: 100%;
  border: none;
}

.image-uploader :deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  border: none;
  border-radius: 0;
  background: #fafafa;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #8c939d;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.upload-text p {
  margin: 0;
  line-height: 1.5;
}

.upload-hint {
  font-size: 12px;
  color: #a8abb2;
}

/* 内容编辑器 */
.content-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.editor-content {
  display: flex;
  flex: 1;
  min-height: 500px;
}

.editor-content.mode-edit .editor-pane,
.editor-content.mode-preview .preview-pane {
  width: 100%;
}

.editor-content.mode-split .editor-pane,
.editor-content.mode-split .preview-pane {
  width: 50%;
}

.editor-pane {
  border-right: 1px solid #dcdfe6;
}

.editor-content.mode-preview .editor-pane,
.editor-content.mode-edit .preview-pane {
  display: none;
}

.markdown-editor {
  border: none;
  border-radius: 0;
}

.markdown-editor :deep(.el-textarea__inner) {
  border: none;
  border-radius: 0;
  resize: none;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  padding: 16px;
}

.preview-pane {
  background: white;
  overflow-y: auto;
}

.markdown-preview {
  padding: 16px;
  line-height: 1.6;
  color: #333;
}

.markdown-preview :deep(h1),
.markdown-preview :deep(h2),
.markdown-preview :deep(h3),
.markdown-preview :deep(h4),
.markdown-preview :deep(h5),
.markdown-preview :deep(h6) {
  margin: 1.5em 0 0.5em 0;
  font-weight: 600;
  line-height: 1.4;
}

.markdown-preview :deep(h1) { font-size: 2em; }
.markdown-preview :deep(h2) { font-size: 1.5em; }
.markdown-preview :deep(h3) { font-size: 1.25em; }
.markdown-preview :deep(h4) { font-size: 1.1em; }
.markdown-preview :deep(h5) { font-size: 1em; }
.markdown-preview :deep(h6) { font-size: 0.9em; }

.markdown-preview :deep(p) {
  margin: 0.8em 0;
}

.markdown-preview :deep(ul),
.markdown-preview :deep(ol) {
  margin: 0.8em 0;
  padding-left: 2em;
}

.markdown-preview :deep(li) {
  margin: 0.2em 0;
}

.markdown-preview :deep(blockquote) {
  margin: 1em 0;
  padding: 0.5em 1em;
  border-left: 4px solid #ddd;
  background: #f9f9f9;
  color: #666;
}

.markdown-preview :deep(code) {
  background: #f1f1f1;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.9em;
}

.markdown-preview :deep(pre) {
  background: #f6f8fa;
  padding: 1em;
  border-radius: 6px;
  overflow-x: auto;
  margin: 1em 0;
}

.markdown-preview :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-preview :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}

.markdown-preview :deep(th),
.markdown-preview :deep(td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.markdown-preview :deep(th) {
  background: #f5f5f5;
  font-weight: 600;
}

.empty-content {
  color: #999;
  font-style: italic;
  text-align: center;
  padding: 2em;
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .section-editor-dialog {
    width: 95% !important;
  }

  .editor-content.mode-split {
    flex-direction: column;
  }

  .editor-content.mode-split .editor-pane,
  .editor-content.mode-split .preview-pane {
    width: 100%;
    min-height: 200px;
  }

  .editor-pane {
    border-right: none;
    border-bottom: 1px solid #dcdfe6;
  }

  .editor-toolbar {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }

  .toolbar-right {
    justify-content: center;
  }
}
</style>
