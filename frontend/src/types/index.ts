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
    template_id?: number | null
  }
  manual_options?: {
    template: string
    template_id?: number | null
    default_sections: string[]
    software_name?: string
    version?: string
    developer?: string
    enable_global_variables?: boolean
  }
}

export interface ProjectListResponse {
  projects: Project[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ManualSection {
  id: number
  project_id: number
  title: string
  image_file_id?: number | null
  image_filename?: string | null
  image_url?: string | null
  body_markdown: string
  order_index: number
  created_at: string
  updated_at: string
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
  project_name?: string
  job_id: string
  status: 'queued' | 'processing' | 'success' | 'failed'
  progress: number
  result_file_path?: string
  error_message?: string
  error_log_url?: string | null
  created_at: string
  updated_at: string
  download_url?: string
}

export interface ExportHistory {
  id: number
  project_id: number
  project_name: string
  exporter: 'code' | 'manual'
  status: 'success' | 'failed'
  duration_ms?: number
  file_path?: string
  created_at: string
}

export interface AdminStats {
  users: {
    total: number
    active: number
    admin: number
    recent: number
  }
  projects: {
    total: number
    code: number
    manual: number
    recent: number
  }
  files: {
    total: number
    total_size: number
    average_size: number
  }
  exports: {
    total: number
    successful: number
    failed: number
    success_rate: number
    recent: number
  }
}

export interface UserListResponse {
  users: User[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface TemplateInfo {
  id: number
  name: string
  version: string
  description?: string
  status: 'draft' | 'published'
  created_at: string
  updated_at: string
}

export interface PdfStyleSetting {
  latex_engine: string
  document_class: string
  font_size: string
  page_geometry: string
  main_font: string
  mono_font: string
  line_stretch: string
  header_latex: string
  footer_latex: string
  preamble_latex: string
}

export interface UploadSetting {
  max_upload_size_mb: number
  allowed_extensions: string[]
  max_project_size_mb: number
}

export interface ManualSetting {
  enable_global_variables: boolean
}

export interface SystemSettings {
  pdf_style: PdfStyleSetting
  upload: UploadSetting
  manual: ManualSetting
}

export interface HighlightMapping {
  id?: number
  suffix: string
  language: string
  enabled: boolean
  updated_at?: string
}

export interface Announcement {
  id: number
  title: string
  body_markdown: string
  status: 'draft' | 'published' | 'archived'
  published_at?: string | null
  created_at: string
  updated_at: string
}
