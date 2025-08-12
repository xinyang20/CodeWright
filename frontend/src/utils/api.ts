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
    api.delete(`/projects/${id}`)
}

// 文件相关API
export const fileApi = {
  uploadFile: (projectId: number, file: File): Promise<ApiResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/projects/${projectId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
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
