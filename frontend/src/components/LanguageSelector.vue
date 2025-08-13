<template>
  <el-dialog
    v-model="visible"
    title="设置语言类型"
    width="600px"
    :before-close="handleClose"
  >
    <div class="language-selector">
      <div class="current-info">
        <div class="file-info">
          <div class="file-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="file-details">
            <div class="file-name">{{ file?.display_name || file?.original_filename }}</div>
            <div class="file-meta">
              <span>当前语言：</span>
              <el-tag 
                :color="getLanguageColor(currentLanguage)" 
                size="small"
                class="language-tag"
              >
                {{ getLanguageDisplayName(currentLanguage) }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <el-divider />

      <div class="language-selection">
        <div class="auto-detect">
          <h4>自动识别</h4>
          <div class="auto-language">
            <el-radio 
              v-model="selectedLanguage" 
              :value="autoDetectedLanguage"
              @change="handleLanguageChange"
            >
              <div class="language-option">
                <span class="language-name">{{ getLanguageDisplayName(autoDetectedLanguage) }}</span>
                <span class="language-desc">（根据文件扩展名自动识别）</span>
              </div>
            </el-radio>
          </div>
        </div>

        <el-divider />

        <div class="manual-select">
          <h4>手动选择</h4>
          <div class="language-categories">
            <el-tabs v-model="activeCategory" @tab-change="handleCategoryChange">
              <el-tab-pane label="编程语言" name="programming">
                <div class="language-grid">
                  <div 
                    v-for="language in programmingLanguages" 
                    :key="language.name"
                    class="language-item"
                    :class="{ active: selectedLanguage === language.name }"
                    @click="selectLanguage(language.name)"
                  >
                    <div class="language-color" :style="{ backgroundColor: language.color }"></div>
                    <span class="language-name">{{ language.displayName }}</span>
                  </div>
                </div>
              </el-tab-pane>
              
              <el-tab-pane label="标记语言" name="markup">
                <div class="language-grid">
                  <div 
                    v-for="language in markupLanguages" 
                    :key="language.name"
                    class="language-item"
                    :class="{ active: selectedLanguage === language.name }"
                    @click="selectLanguage(language.name)"
                  >
                    <div class="language-color" :style="{ backgroundColor: language.color }"></div>
                    <span class="language-name">{{ language.displayName }}</span>
                  </div>
                </div>
              </el-tab-pane>
              
              <el-tab-pane label="配置文件" name="config">
                <div class="language-grid">
                  <div 
                    v-for="language in configLanguages" 
                    :key="language.name"
                    class="language-item"
                    :class="{ active: selectedLanguage === language.name }"
                    @click="selectLanguage(language.name)"
                  >
                    <div class="language-color" :style="{ backgroundColor: language.color }"></div>
                    <span class="language-name">{{ language.displayName }}</span>
                  </div>
                </div>
              </el-tab-pane>
              
              <el-tab-pane label="其他" name="other">
                <div class="language-grid">
                  <div 
                    v-for="language in otherLanguages" 
                    :key="language.name"
                    class="language-item"
                    :class="{ active: selectedLanguage === language.name }"
                    @click="selectLanguage(language.name)"
                  >
                    <div class="language-color" :style="{ backgroundColor: language.color }"></div>
                    <span class="language-name">{{ language.displayName }}</span>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </div>
      </div>
    </div>
    
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
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Document } from '@element-plus/icons-vue'
import type { ProjectFile } from '@/types'
import { 
  getLanguageByExtension, 
  getLanguagesByCategory,
  getLanguageDisplayName,
  getLanguageColor,
  type LanguageInfo
} from '@/utils/languageMapping'

// Props
interface Props {
  modelValue: boolean
  file: ProjectFile | null
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: [file: ProjectFile, language: string]
}>()

// 响应式数据
const visible = ref(false)
const loading = ref(false)
const selectedLanguage = ref('')
const activeCategory = ref('programming')

// 计算属性
const autoDetectedLanguage = computed(() => {
  if (!props.file) return 'text'
  const detected = getLanguageByExtension(props.file.original_filename)
  return detected?.name || 'text'
})

const currentLanguage = computed(() => {
  return props.file?.language_override || autoDetectedLanguage.value
})

const programmingLanguages = computed(() => getLanguagesByCategory('programming'))
const markupLanguages = computed(() => getLanguagesByCategory('markup'))
const configLanguages = computed(() => getLanguagesByCategory('config'))
const otherLanguages = computed(() => {
  const data = getLanguagesByCategory('data')
  const document = getLanguagesByCategory('document')
  const image = getLanguagesByCategory('image')
  return [...data, ...document, ...image]
})

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  visible.value = newValue
  if (newValue && props.file) {
    // 初始化选择的语言
    selectedLanguage.value = currentLanguage.value
  }
})

// 监听 visible 变化
watch(visible, (newValue) => {
  emit('update:modelValue', newValue)
})

// 选择语言
const selectLanguage = (languageName: string) => {
  selectedLanguage.value = languageName
}

// 处理语言变化
const handleLanguageChange = () => {
  // 语言变化时的处理逻辑
}

// 处理分类变化
const handleCategoryChange = () => {
  // 分类变化时的处理逻辑
}

// 处理关闭
const handleClose = () => {
  visible.value = false
}

// 处理提交
const handleSubmit = async () => {
  if (!props.file) return

  try {
    loading.value = true
    
    // 触发成功事件，让父组件处理实际的API调用
    emit('success', props.file, selectedLanguage.value)
    
  } catch (error) {
    console.error('设置语言类型失败:', error)
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
.language-selector {
  max-height: 500px;
  overflow-y: auto;
}

.current-info {
  margin-bottom: 16px;
}

.file-info {
  display: flex;
  align-items: center;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.file-icon {
  margin-right: 12px;
  color: #5c7cfa;
  font-size: 20px;
}

.file-details {
  flex: 1;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #111;
  margin-bottom: 4px;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.language-tag {
  border: none;
  color: white;
  font-weight: 500;
}

.auto-detect h4,
.manual-select h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #111;
}

.auto-language {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background-color: #fafafa;
}

.language-option {
  display: flex;
  flex-direction: column;
}

.language-name {
  font-weight: 500;
  color: #111;
}

.language-desc {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.language-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
  margin-top: 12px;
}

.language-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background-color: #fff;
  cursor: pointer;
  transition: all 0.3s ease;
}

.language-item:hover {
  border-color: #5c7cfa;
  background-color: #f8f9ff;
}

.language-item.active {
  border-color: #5c7cfa;
  background-color: #5c7cfa;
  color: white;
}

.language-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
  flex-shrink: 0;
}

.language-item.active .language-color {
  background-color: white !important;
}

.language-item .language-name {
  font-size: 13px;
}

.dialog-footer {
  text-align: right;
}
</style>
