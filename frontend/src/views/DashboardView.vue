<template>
  <div class="dashboard" v-loading="loading">
    <div class="page-header">
      <div>
        <h1>控制台</h1>
        <p>欢迎使用 CodeWright，{{ authStore.user?.username }}</p>
      </div>
      <el-button type="primary" @click="$router.push('/projects/create')">
        <el-icon><Plus /></el-icon>
        创建项目
      </el-button>
    </div>

    <el-row :gutter="20" class="metric-row">
      <el-col :xs="24" :sm="8">
        <el-card>
          <div class="metric">
            <span>项目总数</span>
            <strong>{{ projectTotal }}</strong>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card>
          <div class="metric">
            <span>代码项目</span>
            <strong>{{ codeProjectCount }}</strong>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card>
          <div class="metric">
            <span>操作文档</span>
            <strong>{{ manualProjectCount }}</strong>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="14">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近项目</span>
              <el-button text type="primary" @click="$router.push('/projects')">查看全部</el-button>
            </div>
          </template>

          <el-empty v-if="projects.length === 0" description="暂无项目">
            <el-button type="primary" @click="$router.push('/projects/create')">创建第一个项目</el-button>
          </el-empty>

          <div v-else class="project-list">
            <div v-for="project in projects" :key="project.id" class="project-item" @click="$router.push(`/projects/${project.id}`)">
              <div>
                <strong>{{ project.project_name }}</strong>
                <p>{{ formatDate(project.updated_at) }}</p>
              </div>
              <el-tag :type="project.project_type === 'code' ? 'primary' : 'success'" size="small">
                {{ project.project_type === 'code' ? '代码文件' : '操作文档' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card class="side-card">
          <template #header>
            <span>最近导出</span>
          </template>

          <el-empty v-if="histories.length === 0" description="暂无导出记录" />

          <div v-else class="history-list">
            <div v-for="history in histories" :key="history.id" class="history-item">
              <div>
                <strong>{{ history.project_name }}</strong>
                <p>{{ formatDate(history.created_at) }}</p>
              </div>
              <el-tag :type="history.status === 'success' ? 'success' : 'danger'" size="small">
                {{ history.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </div>
          </div>
        </el-card>

        <el-card class="side-card">
          <template #header>
            <span>系统公告</span>
          </template>
          <el-empty v-if="announcements.length === 0" description="暂无公告" />
          <div v-else class="announcement-list">
            <div v-for="announcement in announcements" :key="announcement.id" class="announcement-item">
              <strong>{{ announcement.title }}</strong>
              <p>{{ announcement.body_markdown }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { exportApi, projectApi, settingsApi } from '@/utils/api'
import type { Announcement, ExportHistory, Project, ProjectListResponse } from '@/types'

const authStore = useAuthStore()

const loading = ref(false)
const projects = ref<Project[]>([])
const projectTotal = ref(0)
const histories = ref<ExportHistory[]>([])
const announcements = ref<Announcement[]>([])

const codeProjectCount = computed(() => projects.value.filter(project => project.project_type === 'code').length)
const manualProjectCount = computed(() => projects.value.filter(project => project.project_type === 'manual').length)

const fetchDashboard = async () => {
  loading.value = true
  try {
    const [projectResponse, historyResponse, announcementResponse] = await Promise.all([
      projectApi.getProjects({ page: 1, page_size: 6 }),
      exportApi.getHistory(),
      settingsApi.getPublishedAnnouncements()
    ])

    if (projectResponse.code === 0 && projectResponse.data) {
      const data = projectResponse.data as ProjectListResponse
      projects.value = data.projects
      projectTotal.value = data.total
    }

    if (historyResponse.code === 0 && historyResponse.data) {
      histories.value = historyResponse.data.histories.slice(0, 6)
    }

    if (announcementResponse.code === 0 && announcementResponse.data) {
      announcements.value = announcementResponse.data.announcements.slice(0, 3)
    }
  } catch (error) {
    console.error('获取控制台数据失败:', error)
    ElMessage.error('获取控制台数据失败')
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(fetchDashboard)
</script>

<style scoped>
.dashboard {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header,
.card-header,
.project-item,
.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 6px;
}

.page-header p,
.project-item p,
.history-item p {
  margin: 4px 0 0;
  color: #666;
  font-size: 13px;
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
  font-size: 30px;
  line-height: 1;
}

.project-list,
.history-list,
.announcement-list {
  display: flex;
  flex-direction: column;
}

.project-item,
.history-item,
.announcement-item {
  min-height: 58px;
  padding: 12px 0;
  border-bottom: 1px solid var(--cw-border);
}

.project-item {
  cursor: pointer;
}

.project-item:last-child,
.history-item:last-child,
.announcement-item:last-child {
  border-bottom: none;
}

.side-card {
  margin-bottom: 16px;
}

.announcement-item p {
  margin: 6px 0 0;
  color: #666;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
}
</style>
