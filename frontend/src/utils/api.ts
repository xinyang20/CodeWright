import axios, { type AxiosInstance, type AxiosResponse } from 'axios'
import type { 
  ApiResponse, 
  LoginRequest, 
  RegisterRequest, 
  ProjectCreateRequest,
  ProjectListResponse,
  UserListResponse,
  AdminStats,
  TemplateInfo,
  ExportHistory,
  ExportJob,
  SystemSettings,
  HighlightMapping,
  Announcement
} from '@/types'

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
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
    const requestUrl = error.config?.url || ''
    const isAuthRequest = requestUrl.includes('/auth/token') || requestUrl.includes('/auth/register')

    if (error.response?.status === 401 && !isAuthRequest) {
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

  uploadFileToProject: (projectId: number, file: File): Promise<ApiResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/projects/${projectId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  previewProjectHtml: (id: number, options?: any): Promise<string> => {
    const config = {
      responseType: 'text' as const,
      transformResponse: [(data: string) => data],
      timeout: 30000
    }
    return (options
      ? api.post(`/projects/${id}/preview`, options, config)
      : api.get(`/projects/${id}/preview`, config)) as unknown as Promise<string>
  },

  previewProjectPdf: async (id: number, options: any = {}): Promise<Blob> => {
    const blob = await api.post(`/projects/${id}/preview/pdf`, options, {
      responseType: 'blob',
      timeout: 300000
    }) as unknown as Blob
    return parsePdfBlobResponse(blob, 'PDF 预览失败')
  },

  submitExportJob: (id: number, options: any = {}): Promise<ApiResponse<ExportJob>> =>
    api.post(`/projects/${id}/export`, options),

  // 导出项目为PDF
  exportProjectPdf: async (id: number, options: any = {}): Promise<Blob> => {
    const blob = await api.post(`/projects/${id}/export/pdf`, options, {
      responseType: 'blob',
      timeout: 300000
    }) as unknown as Blob
    return parsePdfBlobResponse(blob, 'PDF 导出失败')
  },

  getManualSections: (projectId: number): Promise<ApiResponse> =>
    api.get(`/projects/${projectId}/sections`),

  createManualSection: (projectId: number, data: any): Promise<ApiResponse> =>
    api.post(`/projects/${projectId}/sections`, data),

  updateManualSection: (projectId: number, sectionId: number, data: any): Promise<ApiResponse> =>
    api.put(`/projects/${projectId}/sections/${sectionId}`, data),

  deleteManualSection: (projectId: number, sectionId: number): Promise<ApiResponse> =>
    api.delete(`/projects/${projectId}/sections/${sectionId}`),

  reorderManualSections: (projectId: number, sectionOrders: any[]): Promise<ApiResponse> =>
    api.put(`/projects/${projectId}/sections/reorder`, sectionOrders)
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
    api.put(`/projects/${projectId}/files/reorder`, fileOrders),

  // 获取代码高亮CSS
  getHighlightCss: (): Promise<ApiResponse> =>
    api.get('/files/highlight/css')
}

// 导出相关API
export const exportApi = {
  exportProject: (projectId: number, options: any = {}): Promise<ApiResponse<ExportJob>> => 
    api.post(`/exports/projects/${projectId}/export`, options),
  
  getExportStatus: (jobId: string): Promise<ApiResponse<ExportJob>> => 
    api.get(`/exports/${jobId}`),

  getHistory: (params?: { project_id?: number }): Promise<ApiResponse<{ histories: ExportHistory[] }>> =>
    api.get('/exports/history', { params }),
  
  downloadExport: (exportId: number): string => 
    `${api.defaults.baseURL}/exports/download/${exportId}`,

  downloadJob: (jobId: string): string =>
    `${api.defaults.baseURL}/exports/${jobId}/download`,

  downloadJobFile: async (jobId: string): Promise<Blob> => {
    const blob = await api.get(`/exports/${jobId}/download`, {
      responseType: 'blob'
    }) as unknown as Blob
    return parsePdfBlobResponse(blob, '导出文件下载失败')
  }
}

const parsePdfBlobResponse = async (blob: Blob, fallbackMessage: string): Promise<Blob> => {
  const contentType = blob.type || ''
  if (contentType.includes('application/json') || contentType.includes('text/plain')) {
    const text = await blob.text()
    try {
      const payload = JSON.parse(text)
      throw new Error(payload.message || payload.detail || fallbackMessage)
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new Error(text || fallbackMessage)
      }
      throw error
    }
  }

  const signature = await blob.slice(0, 5).text()
  if (signature === '%PDF-') {
    return blob
  }

  throw new Error(fallbackMessage)
}

// 管理员相关API
export const adminApi = {
  getStats: (): Promise<ApiResponse<AdminStats>> =>
    api.get('/admin/stats'),

  getUsers: (params?: {
    page?: number
    page_size?: number
    search?: string
  }): Promise<ApiResponse<UserListResponse>> =>
    api.get('/admin/users', { params }),

  updateUserStatus: (userId: number, isActive: boolean): Promise<ApiResponse> =>
    api.put(`/admin/users/${userId}/status`, null, {
      params: { is_active: isActive }
    })
}

// 设置相关API
export const settingsApi = {
  getTemplates: (): Promise<ApiResponse<{ templates: TemplateInfo[] }>> =>
    api.get('/settings/templates'),

  getPublishedTemplates: (): Promise<ApiResponse<{ templates: TemplateInfo[] }>> =>
    api.get('/settings/templates/published'),

  createTemplate: (data: {
    name: string
    version: string
    description?: string
    file: File
  }): Promise<ApiResponse> => {
    const formData = new FormData()
    formData.append('name', data.name)
    formData.append('version', data.version)
    formData.append('description', data.description || '')
    formData.append('file', data.file)
    return api.post('/settings/templates', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  updateTemplateStatus: (templateId: number, status: 'draft' | 'published'): Promise<ApiResponse> =>
    api.put(`/settings/templates/${templateId}/status`, null, {
      params: { status }
    }),

  getSystemSettings: (): Promise<ApiResponse<SystemSettings>> =>
    api.get('/settings/system'),

  updateSystemSetting: (key: keyof SystemSettings, value: SystemSettings[keyof SystemSettings]): Promise<ApiResponse<SystemSettings>> =>
    api.put(`/settings/system/${key}`, value),

  getHighlightMapping: (): Promise<ApiResponse<{ mappings: HighlightMapping[] }>> =>
    api.get('/settings/highlight-mapping'),

  updateHighlightMapping: (mappings: HighlightMapping[]): Promise<ApiResponse<{ mappings: HighlightMapping[] }>> =>
    api.put('/settings/highlight-mapping', mappings),

  getAnnouncements: (): Promise<ApiResponse<{ announcements: Announcement[] }>> =>
    api.get('/settings/announcements'),

  getPublishedAnnouncements: (): Promise<ApiResponse<{ announcements: Announcement[] }>> =>
    api.get('/settings/announcements/published'),

  createAnnouncement: (data: Pick<Announcement, 'title' | 'body_markdown' | 'status'>): Promise<ApiResponse<Announcement>> =>
    api.post('/settings/announcements', data),

  updateAnnouncement: (
    announcementId: number,
    data: Partial<Pick<Announcement, 'title' | 'body_markdown' | 'status'>>
  ): Promise<ApiResponse<Announcement>> =>
    api.put(`/settings/announcements/${announcementId}`, data),

  deleteAnnouncement: (announcementId: number): Promise<ApiResponse> =>
    api.delete(`/settings/announcements/${announcementId}`)
}

export default api
