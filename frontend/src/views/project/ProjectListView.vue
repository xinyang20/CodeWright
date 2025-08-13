<template>
  <div class="project-list">
    <!-- 页面头部 -->
    <div class="header">
      <h1>我的项目</h1>
      <div class="header-actions">
        <el-button type="primary" @click="$router.push('/projects/create')">
          <el-icon><Plus /></el-icon>
          创建项目
        </el-button>
      </div>
    </div>

    <!-- 筛选器 -->
    <div class="filters">
      <el-radio-group v-model="filters.project_type" @change="handleFilterChange">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="code">代码文件</el-radio-button>
        <el-radio-button value="manual">操作文档</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 项目列表 -->
    <div class="project-grid" v-loading="loading">
      <div v-if="projects.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无项目">
          <el-button type="primary" @click="$router.push('/projects/create')">
            创建第一个项目
          </el-button>
        </el-empty>
      </div>

      <div v-else class="project-cards">
        <el-card
          v-for="project in projects"
          :key="project.id"
          class="project-card"
          shadow="hover"
          @click="handleProjectClick(project)"
        >
          <template #header>
            <div class="card-header">
              <span class="project-name">{{ project.project_name }}</span>
              <el-dropdown @command="handleCommand" trigger="click" @click.stop>
                <el-button type="text" size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="`edit-${project.id}`">编辑</el-dropdown-item>
                    <el-dropdown-item :command="`delete-${project.id}`" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>

          <div class="card-content">
            <div class="project-type">
              <el-tag :type="project.project_type === 'code' ? 'primary' : 'success'" size="small">
                {{ project.project_type === 'code' ? '代码文件' : '操作文档' }}
              </el-tag>
            </div>
            <div class="project-meta">
              <p class="created-time">创建时间：{{ formatDate(project.created_at) }}</p>
              <p class="updated-time">更新时间：{{ formatDate(project.updated_at) }}</p>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="pagination.total > 0">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :page-sizes="[10, 20, 50]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MoreFilled } from '@element-plus/icons-vue'
import type { Project, ProjectListResponse } from '@/types'
import { projectApi } from '@/utils/api'

// 响应式数据
const loading = ref(false)
const projects = ref<Project[]>([])

// 筛选器
const filters = reactive({
  project_type: ''
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0,
  total_pages: 0
})

// 获取项目列表
const fetchProjects = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...(filters.project_type && { project_type: filters.project_type })
    }

    const response = await projectApi.getProjects(params)
    if (response.code === 0) {
      const data = response.data as ProjectListResponse
      projects.value = data.projects
      pagination.total = data.total
      pagination.total_pages = data.total_pages
    } else {
      ElMessage.error(response.message || '获取项目列表失败')
    }
  } catch (error) {
    console.error('获取项目列表失败:', error)
    ElMessage.error('获取项目列表失败')
  } finally {
    loading.value = false
  }
}

// 处理筛选器变化
const handleFilterChange = () => {
  pagination.page = 1
  fetchProjects()
}

// 处理分页大小变化
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  fetchProjects()
}

// 处理页码变化
const handleCurrentChange = (page: number) => {
  pagination.page = page
  fetchProjects()
}

// 处理项目点击
const handleProjectClick = (project: Project) => {
  // 跳转到项目详情页
  window.location.href = `/projects/${project.id}`
}

// 处理下拉菜单命令
const handleCommand = async (command: string) => {
  const [action, projectId] = command.split('-')
  const id = parseInt(projectId)

  if (action === 'edit') {
    // 跳转到项目编辑页（暂时跳转到详情页）
    window.location.href = `/projects/${id}`
  } else if (action === 'delete') {
    try {
      await ElMessageBox.confirm(
        '确定要删除这个项目吗？删除后无法恢复。',
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )

      const response = await projectApi.deleteProject(id)
      if (response.code === 0) {
        ElMessage.success('项目删除成功')
        fetchProjects() // 重新获取列表
      } else {
        ElMessage.error(response.message || '删除失败')
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除项目失败:', error)
        ElMessage.error('删除项目失败')
      }
    }
  }
}

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 组件挂载时获取数据
onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.project-list {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h1 {
  margin: 0;
  color: #111;
  font-size: 28px;
  font-weight: 600;
}

.filters {
  margin-bottom: 24px;
}

.project-grid {
  min-height: 400px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.project-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.project-card {
  cursor: pointer;
  transition: transform 0.2s ease;
  border-radius: 8px;
}

.project-card:hover {
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-name {
  font-weight: 600;
  font-size: 16px;
  color: #111;
}

.card-content {
  padding-top: 8px;
}

.project-type {
  margin-bottom: 12px;
}

.project-meta p {
  margin: 4px 0;
  font-size: 12px;
  color: #666;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}
</style>
