import axios, { type AxiosInstance, type AxiosResponse } from 'axios'
import type { 
  ApiResponse, 
  LoginRequest, 
  RegisterRequest, 
  ProjectCreateRequest,
  ProjectListResponse 
} from '@/types'

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token过期或无效，清除本地存储并跳转到登录页
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error.response?.data || error)
  }
)

// 认证相关API
export const authApi = {
  login: (data: LoginRequest): Promise<ApiResponse> => 
    api.post('/auth/token', data),
  
  register: (data: RegisterRequest): Promise<ApiResponse> => 
    api.post('/auth/register', data),
  
  getCurrentUser: (): Promise<ApiResponse> => 
    api.get('/users/me')
}

// 项目相关API
export const projectApi = {
  createProject: (data: ProjectCreateRequest): Promise<ApiResponse> => 
    api.post('/projects', data),
  
  getProjects: (params?: {
    project_type?: string
    page?: number
    page_size?: number
  }): Promise<ApiResponse<ProjectListResponse>> => 
    api.get('/projects', { params }),
  
  getProject: (id: number): Promise<ApiResponse> => 
    api.get(`/projects/${id}`),
  
  updateProject: (id: number, data: any): Promise<ApiResponse> => 
    api.put(`/projects/${id}`, data),
  
  deleteProject: (id: number): Promise<ApiResponse> =>
    api.delete(`/projects/${id}`),

  // 导出项目为PDF
  exportProjectPdf: (id: number, options: any = {}): Promise<any> =>
    api.post(`/projects/${id}/export/pdf`, options, { responseType: 'blob' })
}

// 文件相关API
export const fileApi = {
  // 上传文件
  uploadFile: (file: File): Promise<ApiResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取用户文件列表
  getUserFiles: (): Promise<ApiResponse> =>
    api.get('/files'),

  // 删除文件
  deleteFile: (fileId: number): Promise<ApiResponse> =>
    api.delete(`/files/${fileId}`),

  // 预览文件
  previewFile: (fileId: number, language?: string): Promise<ApiResponse> =>
    api.get(`/files/${fileId}/preview`, {
      params: language ? { language } : {}
    }),

  // 将文件添加到项目
  addFileToProject: (projectId: number, fileId: number): Promise<ApiResponse> =>
    api.post(`/projects/${projectId}/files/${fileId}`),

  // 获取项目文件列表
  getProjectFiles: (projectId: number): Promise<ApiResponse> =>
    api.get(`/projects/${projectId}/files`),

  // 从项目中移除文件
  removeFileFromProject: (projectId: number, fileId: number): Promise<ApiResponse> =>
    api.delete(`/projects/${projectId}/files/${fileId}`),

  // 更新项目文件信息
  updateProjectFile: (projectId: number, fileId: number, data: any): Promise<ApiResponse> =>
    api.put(`/projects/${projectId}/files/${fileId}`, data),

  // 重新排序项目文件
  reorderProjectFiles: (projectId: number, fileOrders: any[]): Promise<ApiResponse> =>
    api.put(`/projects/${projectId}/reorder-files`, fileOrders),

  // 项目配置相关
  getProjectSettings: (projectId: number): Promise<ApiResponse> =>
    api.get(`/projects/${projectId}/settings`),

  updateProjectSettings: (projectId: number, settings: any): Promise<ApiResponse> =>
    api.put(`/projects/${projectId}/settings`, settings),

  resetProjectSettings: (projectId: number): Promise<ApiResponse> =>
    api.post(`/projects/${projectId}/settings/reset`),

  // 导出历史相关
  getProjectExportHistory: (projectId: number, params?: any): Promise<ApiResponse> =>
    api.get(`/projects/${projectId}/exports`, { params }),

  getUserExportHistory: (params?: any): Promise<ApiResponse> =>
    api.get('/exports', { params }),

  getExportStatistics: (): Promise<ApiResponse> =>
    api.get('/exports/statistics'),

  deleteExportRecord: (exportId: number): Promise<ApiResponse> =>
    api.delete(`/exports/${exportId}`),

  getExportDetail: (exportId: number): Promise<ApiResponse> =>
    api.get(`/exports/${exportId}`),

  // 获取代码高亮CSS
  getHighlightCss: (): Promise<ApiResponse> =>
    api.get('/files/highlight/css')
}

// 操作文档相关API
export const manualApi = {
  // 创建章节
  createSection: (projectId: number, data: {
    title: string
    body_markdown?: string
    image_file_id?: number
  }): Promise<ApiResponse> =>
    api.post(`/manual/projects/${projectId}/sections`, data),

  // 获取项目章节列表
  getProjectSections: (projectId: number): Promise<ApiResponse> =>
    api.get(`/manual/projects/${projectId}/sections`),

  // 获取章节详情
  getSection: (sectionId: number): Promise<ApiResponse> =>
    api.get(`/manual/sections/${sectionId}`),

  // 更新章节
  updateSection: (sectionId: number, data: {
    title?: string
    body_markdown?: string
    image_file_id?: number
  }): Promise<ApiResponse> =>
    api.put(`/manual/sections/${sectionId}`, data),

  // 删除章节
  deleteSection: (sectionId: number): Promise<ApiResponse> =>
    api.delete(`/manual/sections/${sectionId}`),

  // 重新排序章节
  reorderSections: (projectId: number, sections: Array<{
    id: number
    order_index: number
  }>): Promise<ApiResponse> =>
    api.put(`/manual/projects/${projectId}/sections/reorder`, { sections })
}

// 导出相关API
export const exportApi = {
  exportProject: (projectId: number): Promise<ApiResponse> =>
    api.post(`/projects/${projectId}/export`),

  getExportStatus: (jobId: string): Promise<ApiResponse> =>
    api.get(`/exports/${jobId}`),

  downloadExport: (jobId: string): string =>
    `${api.defaults.baseURL}/exports/${jobId}/download`
}

export default api
