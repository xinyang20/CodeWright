<template>
  <div class="export-history" v-loading="loading">
    <!-- 统计信息 -->
    <div class="stats-section" v-if="showStats">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-statistic title="总导出次数" :value="statistics.total_exports" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="成功导出" :value="statistics.successful_exports" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="失败导出" :value="statistics.failed_exports" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="成功率" :value="statistics.success_rate" suffix="%" />
        </el-col>
      </el-row>
    </div>

    <!-- 导出历史列表 -->
    <div class="history-list">
      <!-- 空状态 -->
      <div v-if="exports.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无导出记录">
          <el-button type="primary" @click="$emit('refresh')">
            刷新记录
          </el-button>
        </el-empty>
      </div>

      <!-- 导出记录 -->
      <div v-else class="export-items">
        <div
          v-for="exportItem in exports"
          :key="exportItem.id"
          class="export-item"
          :class="`status-${exportItem.status}`"
        >
          <div class="export-header">
            <div class="export-info">
              <div class="export-title">
                <el-icon class="export-icon">
                  <Document v-if="exportItem.export_type === 'pdf'" />
                  <Files v-else />
                </el-icon>
                <span class="file-name">{{ exportItem.file_name }}</span>
                <el-tag
                  :type="getStatusType(exportItem.status)"
                  size="small"
                  class="status-tag"
                >
                  {{ getStatusText(exportItem.status) }}
                </el-tag>
              </div>
              <div class="export-meta">
                <span class="export-time">{{ formatDate(exportItem.created_at) }}</span>
                <span v-if="exportItem.file_size" class="file-size">
                  {{ formatFileSize(exportItem.file_size) }}
                </span>
                <span v-if="exportItem.processing_time" class="processing-time">
                  耗时 {{ formatDuration(exportItem.processing_time) }}
                </span>
              </div>
            </div>
            <div class="export-actions">
              <el-button
                v-if="exportItem.status === 'completed'"
                type="text"
                size="small"
                @click="downloadExport(exportItem)"
              >
                <el-icon><Download /></el-icon>
                下载
              </el-button>
              <el-button
                type="text"
                size="small"
                @click="viewExportDetail(exportItem)"
              >
                <el-icon><View /></el-icon>
                详情
              </el-button>
              <el-button
                type="text"
                size="small"
                @click="deleteExport(exportItem)"
                class="danger"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>

          <!-- 进度条（处理中状态） -->
          <div v-if="exportItem.status === 'processing'" class="export-progress">
            <el-progress
              :percentage="exportItem.progress"
              :status="exportItem.progress === 100 ? 'success' : ''"
              :stroke-width="6"
            />
          </div>

          <!-- 错误信息 -->
          <div v-if="exportItem.status === 'failed' && exportItem.error_message" class="export-error">
            <el-alert
              :title="exportItem.error_message"
              type="error"
              :closable="false"
              show-icon
            />
          </div>

          <!-- 详细信息（展开状态） -->
          <div v-if="exportItem.expanded" class="export-details">
            <el-descriptions :column="2" size="small" border>
              <el-descriptions-item label="导出类型">
                {{ exportItem.export_type.toUpperCase() }}
              </el-descriptions-item>
              <el-descriptions-item label="导出格式">
                {{ exportItem.export_format }}
              </el-descriptions-item>
              <el-descriptions-item label="文件数量" v-if="exportItem.total_files > 0">
                {{ exportItem.total_files }} 个
              </el-descriptions-item>
              <el-descriptions-item label="章节数量" v-if="exportItem.total_sections > 0">
                {{ exportItem.total_sections }} 个
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatDateTime(exportItem.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="完成时间" v-if="exportItem.completed_at">
                {{ formatDateTime(exportItem.completed_at) }}
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 展开/收起按钮 -->
          <div class="export-footer">
            <el-button
              type="text"
              size="small"
              @click="toggleExpand(exportItem)"
              class="expand-btn"
            >
              <el-icon>
                <component :is="exportItem.expanded ? 'ArrowUp' : 'ArrowDown'" />
              </el-icon>
              {{ exportItem.expanded ? '收起' : '展开详情' }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- 加载更多 -->
      <div v-if="hasMore" class="load-more">
        <el-button @click="loadMore" :loading="loadingMore">
          加载更多
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  Files,
  Download,
  View,
  Delete,
  ArrowUp,
  ArrowDown
} from '@element-plus/icons-vue'

// Props
interface Props {
  projectId?: number
  showStats?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showStats: false
})

// Emits
const emit = defineEmits<{
  'refresh': []
  'download': [exportItem: any]
  'view-detail': [exportItem: any]
}>()

// 响应式数据
const loading = ref(false)
const loadingMore = ref(false)
const exports = ref<any[]>([])
const statistics = reactive({
  total_exports: 0,
  successful_exports: 0,
  failed_exports: 0,
  recent_exports: 0,
  success_rate: 0
})

const pagination = reactive({
  limit: 20,
  offset: 0,
  hasMore: true
})

// 计算属性
const hasMore = computed(() => pagination.hasMore)

// 获取状态类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'processing': return 'warning'
    case 'pending': return 'info'
    default: return ''
  }
}

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'processing': return '处理中'
    case 'pending': return '等待中'
    default: return '未知'
  }
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
  
  return d.toLocaleDateString('zh-CN')
}

// 格式化完整日期时间
const formatDateTime = (date: string | Date) => {
  const d = new Date(date)
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化持续时间
const formatDuration = (seconds: number) => {
  if (seconds < 1) return '< 1秒'
  if (seconds < 60) return `${Math.round(seconds)}秒`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  return `${minutes}分${remainingSeconds}秒`
}

// 切换展开状态
const toggleExpand = (exportItem: any) => {
  exportItem.expanded = !exportItem.expanded
}

// 下载导出文件
const downloadExport = (exportItem: any) => {
  emit('download', exportItem)
}

// 查看导出详情
const viewExportDetail = (exportItem: any) => {
  emit('view-detail', exportItem)
}

// 删除导出记录
const deleteExport = async (exportItem: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除导出记录"${exportItem.file_name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    const { projectApi } = await import('@/utils/api')
    const response = await projectApi.deleteExportRecord(exportItem.id)

    if (response.code === 0) {
      ElMessage.success('导出记录删除成功')
      await loadExports(true)
    } else {
      ElMessage.error(response.message || '删除失败')
    }

  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除导出记录失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 加载导出记录
const loadExports = async (reset = false) => {
  try {
    if (reset) {
      loading.value = true
      pagination.offset = 0
      exports.value = []
    } else {
      loadingMore.value = true
    }

    const { projectApi } = await import('@/utils/api')
    const params = {
      limit: pagination.limit,
      offset: pagination.offset
    }

    let response
    if (props.projectId) {
      response = await projectApi.getProjectExportHistory(props.projectId, params)
    } else {
      response = await projectApi.getUserExportHistory(params)
    }

    if (response.code === 0) {
      const newExports = response.data.exports.map((item: any) => ({
        ...item,
        expanded: false
      }))

      if (reset) {
        exports.value = newExports
      } else {
        exports.value.push(...newExports)
      }

      pagination.hasMore = newExports.length === pagination.limit
      pagination.offset += newExports.length
    } else {
      ElMessage.error(response.message || '加载导出记录失败')
    }

  } catch (error) {
    console.error('加载导出记录失败:', error)
    ElMessage.error('加载导出记录失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 加载统计信息
const loadStatistics = async () => {
  if (!props.showStats) return

  try {
    const { projectApi } = await import('@/utils/api')
    const response = await projectApi.getExportStatistics()

    if (response.code === 0) {
      Object.assign(statistics, response.data)
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

// 加载更多
const loadMore = () => {
  loadExports(false)
}

// 组件挂载时加载数据
onMounted(() => {
  loadExports(true)
  loadStatistics()
})

// 暴露方法给父组件
defineExpose({
  refresh: () => loadExports(true)
})
</script>

<style scoped>
.export-history {
  min-height: 200px;
}

.stats-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.export-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.export-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: white;
  transition: all 0.2s ease;
}

.export-item:hover {
  border-color: #c0c4cc;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.export-item.status-completed {
  border-left: 4px solid #67c23a;
}

.export-item.status-failed {
  border-left: 4px solid #f56c6c;
}

.export-item.status-processing {
  border-left: 4px solid #e6a23c;
}

.export-item.status-pending {
  border-left: 4px solid #909399;
}

.export-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
}

.export-info {
  flex: 1;
}

.export-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.export-icon {
  font-size: 18px;
  color: #606266;
}

.file-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.status-tag {
  margin-left: 8px;
}

.export-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: #909399;
}

.export-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.export-actions .danger {
  color: #f56c6c;
}

.export-actions .danger:hover {
  color: #f78989;
}

.export-progress {
  padding: 0 16px 16px;
}

.export-error {
  padding: 0 16px 16px;
}

.export-details {
  padding: 0 16px 16px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

.export-footer {
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

.load-more {
  display: flex;
  justify-content: center;
  padding: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .export-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .export-actions {
    justify-content: center;
  }

  .export-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .stats-section .el-row {
    flex-direction: column;
    gap: 16px;
  }

  .stats-section .el-col {
    width: 100% !important;
  }
}
</style>
