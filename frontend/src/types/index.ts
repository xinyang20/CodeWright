// 通用响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data?: T
  detail?: any
}

// 用户相关类型
export interface User {
  id: number
  username: string
  role: 'user' | 'admin'
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

// 项目相关类型
export interface Project {
  id: number
  project_name: string
  project_type: 'code' | 'manual'
  owner_id: number
  config_json: string
  created_at: string
  updated_at: string
}

export interface ProjectCreateRequest {
  project_name: string
  project_type: 'code' | 'manual'
  code_options?: {
    formatting: string[]
    layout: string
    font_size: string
    export_options: string[]
  }
  manual_options?: {
    template: string
    default_sections: string[]
  }
}

export interface ProjectListResponse {
  projects: Project[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 文件相关类型
export interface UploadedFile {
  id: number
  original_filename: string
  storage_path: string
  file_size: number
  file_type: string
  uploader_id: number
  created_at: string
}

export interface ProjectFile {
  id: number
  file_id: number
  display_name: string
  original_filename: string
  file_size: number
  file_type: string
  language_override?: string
  include_in_export: boolean
  order_index: number
  created_at: string
}

export interface FileListResponse {
  files: UploadedFile[]
}

export interface ProjectFileListResponse {
  files: ProjectFile[]
}

// 导出相关类型
export interface ExportJob {
  id: number
  project_id: number
  job_id: string
  status: 'queued' | 'processing' | 'success' | 'failed'
  progress: number
  result_file_path?: string
  error_message?: string
  created_at: string
  updated_at: string
}
