<template>
  <div class="file-upload">
    <el-upload
      ref="uploadRef"
      class="upload-dragger"
      drag
      :multiple="true"
      :auto-upload="false"
      :on-change="handleFileChange"
      :on-remove="handleFileRemove"
      :before-upload="beforeUpload"
      :accept="acceptedTypes"
      :show-file-list="true"
      :file-list="fileList"
    >
      <div class="upload-content">
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">
          <p class="upload-title">将文件拖拽到此处，或<em>点击上传</em></p>
          <p class="upload-hint">
            支持的文件类型：{{ supportedExtensions.join(', ') }}
          </p>
          <p class="upload-hint">
            单个文件大小不超过 10MB
          </p>
        </div>
      </div>
    </el-upload>

    <div class="upload-actions" v-if="fileList.length > 0">
      <el-button @click="clearFiles">清空</el-button>
      <el-button 
        type="primary" 
        @click="handleUpload"
        :loading="uploading"
        :disabled="fileList.length === 0"
      >
        上传文件 ({{ fileList.length }})
      </el-button>
    </div>

    <!-- 上传进度 -->
    <div class="upload-progress" v-if="uploading">
      <el-progress 
        :percentage="uploadProgress" 
        :status="uploadStatus"
        :stroke-width="8"
      />
      <p class="progress-text">{{ progressText }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, type UploadInstance, type UploadFile, type UploadFiles } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { fileApi } from '@/utils/api'

// Props
interface Props {
  projectId?: number
  autoAddToProject?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoAddToProject: false
})

// Emits
const emit = defineEmits<{
  success: [files: any[]]
  error: [error: string]
}>()

// 响应式数据
const uploadRef = ref<UploadInstance>()
const fileList = ref<UploadFile[]>([])
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref<'success' | 'exception' | ''>('')
const progressText = ref('')

// 支持的文件扩展名
const supportedExtensions = [
  '.py', '.java', '.js', '.ts', '.md', '.txt', '.c', '.cpp', '.h', '.hpp',
  '.css', '.html', '.xml', '.json', '.yml', '.yaml', '.sql', '.sh', '.bat',
  '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'
]

// 接受的文件类型
const acceptedTypes = computed(() => supportedExtensions.join(','))

// 文件变化处理
const handleFileChange = (file: UploadFile, files: UploadFiles) => {
  fileList.value = files
}

// 文件移除处理
const handleFileRemove = (file: UploadFile, files: UploadFiles) => {
  fileList.value = files
}

// 上传前验证
const beforeUpload = (file: File) => {
  // 检查文件扩展名
  const fileName = file.name.toLowerCase()
  const hasValidExtension = supportedExtensions.some(ext => fileName.endsWith(ext))
  
  if (!hasValidExtension) {
    ElMessage.error(`不支持的文件类型: ${file.name}`)
    return false
  }

  // 检查文件大小 (10MB)
  const maxSize = 10 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error(`文件 ${file.name} 大小超过 10MB 限制`)
    return false
  }

  return true
}

// 清空文件列表
const clearFiles = () => {
  fileList.value = []
  uploadRef.value?.clearFiles()
}

// 上传文件
const handleUpload = async () => {
  if (fileList.value.length === 0) return

  try {
    uploading.value = true
    uploadProgress.value = 0
    uploadStatus.value = ''
    
    const uploadedFiles = []
    const totalFiles = fileList.value.length
    
    for (let i = 0; i < fileList.value.length; i++) {
      const fileItem = fileList.value[i]
      const file = fileItem.raw
      
      if (!file) continue

      progressText.value = `正在上传 ${fileItem.name} (${i + 1}/${totalFiles})`
      
      try {
        // 上传文件
        const response = await fileApi.uploadFile(file)
        
        if (response.code === 0) {
          uploadedFiles.push(response.data)
          
          // 如果需要自动添加到项目
          if (props.autoAddToProject && props.projectId) {
            await fileApi.addFileToProject(props.projectId, response.data.file_id)
          }
        } else {
          throw new Error(response.message || '上传失败')
        }
      } catch (error) {
        console.error(`上传文件 ${fileItem.name} 失败:`, error)
        ElMessage.error(`上传文件 ${fileItem.name} 失败`)
      }
      
      // 更新进度
      uploadProgress.value = Math.round(((i + 1) / totalFiles) * 100)
    }
    
    if (uploadedFiles.length > 0) {
      uploadStatus.value = 'success'
      progressText.value = `成功上传 ${uploadedFiles.length} 个文件`
      ElMessage.success(`成功上传 ${uploadedFiles.length} 个文件`)
      emit('success', uploadedFiles)
      
      // 清空文件列表
      setTimeout(() => {
        clearFiles()
        uploading.value = false
        uploadProgress.value = 0
      }, 1500)
    } else {
      uploadStatus.value = 'exception'
      progressText.value = '上传失败'
      emit('error', '所有文件上传失败')
    }
    
  } catch (error) {
    console.error('上传过程出错:', error)
    uploadStatus.value = 'exception'
    progressText.value = '上传失败'
    ElMessage.error('上传过程出错')
    emit('error', '上传过程出错')
  } finally {
    if (uploadStatus.value !== 'success') {
      uploading.value = false
    }
  }
}

// 暴露方法给父组件
defineExpose({
  clearFiles,
  handleUpload
})
</script>

<style scoped>
.file-upload {
  width: 100%;
}

.upload-dragger {
  width: 100%;
}

.upload-dragger :deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  background-color: #fafafa;
  transition: all 0.3s ease;
}

.upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: #5c7cfa;
  background-color: #f8f9ff;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-text {
  text-align: center;
}

.upload-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #111;
}

.upload-title em {
  color: #5c7cfa;
  font-style: normal;
}

.upload-hint {
  margin: 4px 0;
  font-size: 12px;
  color: #666;
}

.upload-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

.upload-progress {
  margin-top: 16px;
}

.progress-text {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
  text-align: center;
}
</style>
