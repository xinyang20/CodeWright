<template>
  <div class="section-list" v-loading="loading">
    <!-- 空状态 -->
    <div v-if="sections.length === 0 && !loading" class="empty-state">
      <el-empty description="暂无章节">
        <el-button type="primary" @click="$emit('add-section')">
          添加第一个章节
        </el-button>
      </el-empty>
    </div>

    <!-- 章节列表 -->
    <div v-else class="sections">
      <draggable
        v-model="sections"
        item-key="id"
        handle=".drag-handle"
        @end="handleDragEnd"
        class="draggable-list"
      >
        <template #item="{ element: section, index }">
          <div class="section-item" :key="section.id">
            <div class="section-header">
              <div class="section-left">
                <div class="drag-handle">
                  <el-icon><Rank /></el-icon>
                </div>
                <div class="section-info">
                  <div class="section-title">
                    {{ section.title }}
                  </div>
                  <div class="section-meta">
                    <span class="section-index">第 {{ index + 1 }} 章</span>
                    <span class="section-date">
                      更新于 {{ formatDate(section.updated_at) }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="section-actions">
                <el-button type="text" size="small" @click="$emit('edit-section', section)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button type="text" size="small" @click="$emit('preview-section', section)">
                  <el-icon><View /></el-icon>
                  预览
                </el-button>
                <el-dropdown @command="handleCommand" trigger="click">
                  <el-button type="text" size="small">
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :command="`move-up-${section.id}`" :disabled="index === 0">
                        上移
                      </el-dropdown-item>
                      <el-dropdown-item :command="`move-down-${section.id}`" :disabled="index === sections.length - 1">
                        下移
                      </el-dropdown-item>
                      <el-dropdown-item divided :command="`delete-${section.id}`">
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>

            <!-- 章节内容预览 -->
            <div class="section-content" v-if="section.expanded">
              <div class="content-preview">
                <!-- 图片预览 -->
                <div v-if="section.image_file" class="image-preview">
                  <img :src="getImageUrl(section.image_file)" :alt="section.title" />
                </div>
                
                <!-- 内容预览 -->
                <div class="text-preview">
                  <div v-if="section.body_markdown" class="markdown-content" v-html="renderMarkdown(section.body_markdown)"></div>
                  <div v-else class="empty-content">暂无内容</div>
                </div>
              </div>
            </div>

            <!-- 展开/收起按钮 -->
            <div class="section-footer">
              <el-button 
                type="text" 
                size="small" 
                @click="toggleSection(section)"
                class="expand-btn"
              >
                <el-icon>
                  <component :is="section.expanded ? 'ArrowUp' : 'ArrowDown'" />
                </el-icon>
                {{ section.expanded ? '收起' : '展开预览' }}
              </el-button>
            </div>
          </div>
        </template>
      </draggable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Rank,
  Edit,
  View,
  MoreFilled,
  ArrowUp,
  ArrowDown
} from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

// Props
interface Props {
  sections: any[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
const emit = defineEmits<{
  'add-section': []
  'edit-section': [section: any]
  'preview-section': [section: any]
  'delete-section': [section: any]
  'reorder-sections': [sections: any[]]
}>()

// Markdown 渲染器
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true
})

// 响应式数据
const sections = computed({
  get: () => props.sections.map(section => ({
    ...section,
    expanded: section.expanded || false
  })),
  set: (value) => {
    // 拖拽排序时触发
    emit('reorder-sections', value)
  }
})

// 渲染 Markdown
const renderMarkdown = (markdown: string) => {
  if (!markdown) return ''
  
  // 限制预览长度
  const truncated = markdown.length > 200 ? markdown.substring(0, 200) + '...' : markdown
  const rendered = md.render(truncated)
  return DOMPurify.sanitize(rendered)
}

// 获取图片URL
const getImageUrl = (imageFile: any) => {
  if (imageFile.storage_path) {
    return `/uploads/${imageFile.storage_path.split('/').pop()}`
  }
  return ''
}

// 格式化日期
const formatDate = (date: string | Date) => {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// 切换章节展开状态
const toggleSection = (section: any) => {
  section.expanded = !section.expanded
}

// 处理拖拽结束
const handleDragEnd = () => {
  // 拖拽结束后，sections 的 setter 会自动触发 reorder-sections 事件
}

// 处理下拉菜单命令
const handleCommand = async (command: string) => {
  const [action, sectionId] = command.split('-')
  const id = parseInt(sectionId)
  const section = props.sections.find(s => s.id === id)
  
  if (!section) return

  switch (action) {
    case 'move':
      // 上移或下移逻辑已通过拖拽实现，这里可以添加按钮移动逻辑
      break
    case 'delete':
      try {
        await ElMessageBox.confirm(
          `确定要删除章节"${section.title}"吗？删除后无法恢复。`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        emit('delete-section', section)
      } catch (error) {
        // 用户取消删除
      }
      break
  }
}
</script>

<style scoped>
.section-list {
  min-height: 200px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.sections {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.draggable-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: white;
  transition: all 0.2s ease;
}

.section-item:hover {
  border-color: #c0c4cc;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
}

.section-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.drag-handle {
  cursor: grab;
  color: #c0c4cc;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.drag-handle:hover {
  color: #909399;
  background: #f5f7fa;
}

.drag-handle:active {
  cursor: grabbing;
}

.section-info {
  flex: 1;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.section-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: #909399;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-content {
  border-top: 1px solid #f0f0f0;
  padding: 16px;
  background: #fafafa;
}

.content-preview {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.image-preview img {
  max-width: 200px;
  max-height: 150px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.text-preview {
  flex: 1;
}

.markdown-content {
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin: 0.5em 0;
  font-weight: 600;
}

.markdown-content :deep(p) {
  margin: 0.5em 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.empty-content {
  color: #c0c4cc;
  font-style: italic;
}

.section-footer {
  display: flex;
  justify-content: center;
  padding: 8px 16px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

.expand-btn {
  color: #909399;
}

.expand-btn:hover {
  color: #409eff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .section-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .section-left {
    justify-content: space-between;
  }
  
  .section-actions {
    justify-content: center;
  }
  
  .section-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .content-preview {
    flex-direction: column;
  }
  
  .image-preview img {
    max-width: 100%;
  }
}
</style>
