export interface APIResponse<T = any> {
  data?: T
  error?: string
  message?: string
  status: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
  has_more: boolean
}

export interface ErrorResponse {
  error: string
  detail?: string
  code?: string
}

export interface ValidationError {
  field: string
  message: string
  code?: string
}

export interface ValidationErrorResponse {
  error: string
  details: ValidationError[]
}

export interface HealthResponse {
  status: string
  version: string
  timestamp: number
  database: boolean
  search: boolean
  dependencies: Record<string, boolean>
}

export interface SystemStats {
  total_assistants: number
  total_memories: number
  total_shared_memories: number
  total_searches_today: number
  avg_memory_importance: number
  memory_type_distribution: Record<string, number>
  shared_category_distribution: Record<string, number>
}

export interface ExportRequest {
  assistant_id?: number
  format: 'json' | 'csv' | 'txt'
  include_shared?: boolean
  memory_type?: string
  date_from?: string
  date_to?: string
}

export interface ExportResponse {
  file_url: string
  file_size: number
  record_count: number
  format: string
  created_at: string
}

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export interface WebSocketConnectionInfo {
  client_id: string
  assistant_id?: number
  connected_at: string
  last_activity: string
}