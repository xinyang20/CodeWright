<template>
  <el-dialog
    v-model="visible"
    title="重命名文件"
    width="500px"
    :before-close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
    >
      <el-form-item label="原文件名">
        <el-input
          :value="originalFilename"
          disabled
          class="disabled-input"
        />
      </el-form-item>
      
      <el-form-item label="显示名称" prop="display_name">
        <el-input
          v-model="form.display_name"
          placeholder="请输入显示名称"
          maxlength="255"
          show-word-limit
          clearable
        />
        <div class="form-tip">
          显示名称将在项目中显示，不会影响原始文件名
        </div>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleSubmit"
          :loading="loading"
        >
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { ProjectFile } from '@/types'

// Props
interface Props {
  modelValue: boolean
  file: ProjectFile | null
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: [file: ProjectFile, newDisplayName: string]
}>()

// 响应式数据
const visible = ref(false)
const loading = ref(false)
const formRef = ref<FormInstance>()
const originalFilename = ref('')

// 表单数据
const form = reactive({
  display_name: ''
})

// 表单验证规则
const rules: FormRules = {
  display_name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' },
    { min: 1, max: 255, message: '显示名称长度在 1 到 255 个字符', trigger: 'blur' }
  ]
}

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  visible.value = newValue
  if (newValue && props.file) {
    // 初始化表单数据
    originalFilename.value = props.file.original_filename
    form.display_name = props.file.display_name || props.file.original_filename
  }
})

// 监听 visible 变化
watch(visible, (newValue) => {
  emit('update:modelValue', newValue)
})

// 处理关闭
const handleClose = () => {
  visible.value = false
  // 重置表单
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

// 处理提交
const handleSubmit = async () => {
  if (!formRef.value || !props.file) return

  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    loading.value = true
    
    // 触发成功事件，让父组件处理实际的API调用
    emit('success', props.file, form.display_name)
    
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    loading.value = false
  }
}

// 暴露方法给父组件
defineExpose({
  close: handleClose
})
</script>

<style scoped>
.disabled-input :deep(.el-input__inner) {
  background-color: #f5f7fa;
  color: #909399;
}

.form-tip {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.dialog-footer {
  text-align: right;
}
</style>
