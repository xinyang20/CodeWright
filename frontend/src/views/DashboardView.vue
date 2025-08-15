<template>
  <div class="dashboard">
    <!-- 页面头部 -->
    <div class="header">
      <div class="header-left">
        <h1>控制台</h1>
        <p class="welcome-text">欢迎使用 CodeWright，{{ authStore.user?.username }}！</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="$router.push('/projects/create')">
          <el-icon><Plus /></el-icon>
          创建项目
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="24">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon code-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ stats.codeProjects }}</div>
                <div class="stat-label">代码项目</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon manual-icon">
                <el-icon><Notebook /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ stats.manualProjects }}</div>
                <div class="stat-label">操作文档</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon export-icon">
                <el-icon><Download /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ stats.totalExports }}</div>
                <div class="stat-label">导出次数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon file-icon">
                <el-icon><Folder /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ stats.totalFiles }}</div>
                <div class="stat-label">上传文件</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 主要内容区域 -->
    <el-row :gutter="24" class="main-content">
      <!-- 我的项目 -->
      <el-col :span="14">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>我的项目</span>
              <div class="card-actions">
                <el-button type="text" size="small" @click="$router.push('/projects')">
                  查看全部
                </el-button>
              </div>
            </div>
          </template>

          <div v-loading="projectsLoading" class="projects-section">
            <div v-if="recentProjects.length === 0 && !projectsLoading" class="empty-state">
              <el-empty description="暂无项目">
                <el-button type="primary" @click="$router.push('/projects/create')">
                  创建第一个项目
                </el-button>
              </el-empty>
            </div>

            <div v-else class="project-list">
              <div
                v-for="project in recentProjects"
                :key="project.id"
                class="project-item"
                @click="$router.push(`/projects/${project.id}`)"
              >
                <div class="project-info">
                  <div class="project-header">
                    <span class="project-name">{{ project.project_name }}</span>
                    <el-tag
                      :type="project.project_type === 'code' ? 'primary' : 'success'"
                      size="small"
                    >
                      {{ project.project_type === 'code' ? '代码文件' : '操作文档' }}
                    </el-tag>
                  </div>
                  <div class="project-meta">
                    <span class="project-date">
                      更新于 {{ formatDate(project.updated_at) }}
                    </span>
                  </div>
                </div>
                <div class="project-actions">
                  <el-button type="text" size="small">
                    <el-icon><ArrowRight /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 最近活动 -->
      <el-col :span="10">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>最近活动</span>
              <div class="card-actions">
                <el-button type="text" size="small" @click="refreshActivities">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </template>

          <div v-loading="activitiesLoading" class="activities-section">
            <div v-if="recentActivities.length === 0 && !activitiesLoading" class="empty-state">
              <el-empty description="暂无活动记录" />
            </div>

            <div v-else class="activity-timeline">
              <div
                v-for="activity in recentActivities"
                :key="activity.id"
                class="activity-item"
              >
                <div class="activity-icon" :class="getActivityIconClass(activity.type)">
                  <el-icon>
                    <component :is="getActivityIcon(activity.type)" />
                  </el-icon>
                </div>
                <div class="activity-content">
                  <div class="activity-title">{{ activity.title }}</div>
                  <div class="activity-description">{{ activity.description }}</div>
                  <div class="activity-time">{{ formatDate(activity.created_at) }}</div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 导出历史 -->
    <el-row :gutter="24" class="export-row">
      <el-col :span="24">
        <el-card class="export-history-card">
          <template #header>
            <div class="card-header">
              <div class="card-title">
                <el-icon><Download /></el-icon>
                <span>导出历史</span>
              </div>
              <div class="card-actions">
                <el-button type="text" size="small" @click="refreshExportHistory">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </template>

          <ExportHistory
            :show-stats="true"
            @refresh="refreshExportHistory"
            @download="handleExportDownload"
            @view-detail="handleExportViewDetail"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Document,
  Notebook,
  Download,
  Folder,
  ArrowRight,
  Refresh,
  Edit,
  Upload,
  View
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { projectApi } from '@/utils/api'
import type { Project } from '@/types'
import ExportHistory from '@/components/ExportHistory.vue'

const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const projectsLoading = ref(false)
const activitiesLoading = ref(false)
const recentProjects = ref<Project[]>([])
const recentActivities = ref<any[]>([])

// 统计数据
const stats = reactive({
  codeProjects: 0,
  manualProjects: 0,
  totalExports: 0,
  totalFiles: 0
})

// 获取最近项目
const fetchRecentProjects = async () => {
  try {
    projectsLoading.value = true
    const response = await projectApi.getProjects({ page: 1, page_size: 5 })

    if (response.code === 0) {
      const data = response.data
      recentProjects.value = data.projects || []

      // 更新统计数据
      stats.codeProjects = data.projects?.filter((p: Project) => p.project_type === 'code').length || 0
      stats.manualProjects = data.projects?.filter((p: Project) => p.project_type === 'manual').length || 0
    } else {
      ElMessage.error(response.message || '获取项目列表失败')
    }
  } catch (error) {
    console.error('获取项目列表失败:', error)
    ElMessage.error('获取项目列表失败')
  } finally {
    projectsLoading.value = false
  }
}

// 获取最近活动（模拟数据，后续可以从后端获取）
const fetchRecentActivities = async () => {
  try {
    activitiesLoading.value = true

    // 模拟活动数据
    const mockActivities = [
      {
        id: 1,
        type: 'create',
        title: '创建了新项目',
        description: '项目名称：示例代码项目',
        created_at: new Date(Date.now() - 1000 * 60 * 30) // 30分钟前
      },
      {
        id: 2,
        type: 'upload',
        title: '上传了文件',
        description: '上传了 3 个代码文件',
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 2) // 2小时前
      },
      {
        id: 3,
        type: 'export',
        title: '导出了PDF',
        description: '成功导出项目文档',
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 24) // 1天前
      },
      {
        id: 4,
        type: 'edit',
        title: '编辑了项目',
        description: '修改了项目配置',
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2) // 2天前
      }
    ]

    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 500))

    recentActivities.value = mockActivities

    // 更新统计数据（模拟）
    stats.totalExports = 15
    stats.totalFiles = 42

  } catch (error) {
    console.error('获取活动记录失败:', error)
  } finally {
    activitiesLoading.value = false
  }
}

// 刷新活动
const refreshActivities = () => {
  fetchRecentActivities()
}

// 刷新导出历史
const refreshExportHistory = () => {
  // ExportHistory组件会自动刷新
}

// 处理导出文件下载
const handleExportDownload = (exportItem: any) => {
  // TODO: 实现文件下载功能
  ElMessage.info('下载功能开发中...')
}

// 处理查看导出详情
const handleExportViewDetail = (exportItem: any) => {
  // TODO: 实现查看详情功能
  ElMessage.info('详情查看功能开发中...')
}

// 获取活动图标
const getActivityIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    create: Plus,
    upload: Upload,
    export: Download,
    edit: Edit,
    view: View
  }
  return iconMap[type] || Document
}

// 获取活动图标样式类
const getActivityIconClass = (type: string) => {
  const classMap: Record<string, string> = {
    create: 'create-icon',
    upload: 'upload-icon',
    export: 'export-icon',
    edit: 'edit-icon',
    view: 'view-icon'
  }
  return classMap[type] || 'default-icon'
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

// 组件挂载时获取数据
onMounted(() => {
  fetchRecentProjects()
  fetchRecentActivities()
})
</script>

<style scoped>
.dashboard {
  padding: 24px;
  background-color: #f5f5f5;
  min-height: calc(100vh - 60px);
}

/* 页面头部 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: #1f2937;
}

.welcome-text {
  margin: 0;
  color: #6b7280;
  font-size: 16px;
}

/* 统计卡片 */
.stats-cards {
  margin-bottom: 24px;
}

.stat-card {
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
}

.code-icon {
  background-color: #dbeafe;
  color: #2563eb;
}

.manual-icon {
  background-color: #dcfce7;
  color: #16a34a;
}

.export-icon {
  background-color: #fef3c7;
  color: #d97706;
}

.file-icon {
  background-color: #f3e8ff;
  color: #7c3aed;
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

/* 主要内容区域 */
.main-content {
  margin-top: 24px;
}

.content-card {
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  height: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #1f2937;
}

.card-actions {
  display: flex;
  gap: 8px;
}

/* 项目列表 */
.projects-section {
  height: 420px;
  overflow-y: auto;
}

.project-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.project-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: #ffffff;
}

.project-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.project-info {
  flex: 1;
}

.project-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.project-name {
  font-weight: 600;
  color: #1f2937;
  font-size: 16px;
}

.project-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}

.project-date {
  font-size: 14px;
  color: #6b7280;
}

.project-actions {
  display: flex;
  align-items: center;
}

/* 活动时间线 */
.activities-section {
  height: 420px;
  overflow-y: auto;
}

.activity-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.create-icon {
  background-color: #dbeafe;
  color: #2563eb;
}

.upload-icon {
  background-color: #dcfce7;
  color: #16a34a;
}

.export-icon {
  background-color: #fef3c7;
  color: #d97706;
}

.edit-icon {
  background-color: #f3e8ff;
  color: #7c3aed;
}

.view-icon {
  background-color: #fce7f3;
  color: #ec4899;
}

.default-icon {
  background-color: #f3f4f6;
  color: #6b7280;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.activity-description {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
}

.activity-time {
  font-size: 12px;
  color: #9ca3af;
}

/* 导出历史样式 */
.export-row {
  margin-top: 24px;
}

.export-history-card {
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.export-history-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom: none;
}

.export-history-card :deep(.el-card__header .card-title) {
  color: white;
}

.export-history-card :deep(.el-card__header .el-button) {
  color: white;
}

.export-history-card :deep(.el-card__header .el-button:hover) {
  color: #f0f0f0;
}

/* 空状态 */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-content .el-col:first-child {
    margin-bottom: 24px;
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 16px;
  }

  .header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .stats-cards .el-col {
    margin-bottom: 16px;
  }

  .content-card {
    height: auto;
    min-height: 400px;
  }

  .projects-section,
  .activities-section {
    height: auto;
    max-height: 400px;
  }
}
</style>
