export interface Memory {
  id: number
  assistant_id: number
  content: string
  summary?: string
  memory_type: MemoryType
  importance: number
  tags?: string
  source?: string
  context?: string
  is_shared: boolean
  shared_category?: SharedCategory
  access_count: number
  created_at: string
  updated_at: string
  accessed_at?: string
  assistant?: Assistant
}

export type MemoryType = 
  | 'general'
  | 'conversation'
  | 'fact'
  | 'task'
  | 'project'
  | 'personal'
  | 'code'
  | 'reference'

export type SharedCategory = 
  | 'knowledge'
  | 'tasks'
  | 'projects'
  | 'contacts'
  | 'resources'
  | 'templates'

export interface CreateMemoryRequest {
  assistant_id: number
  content: string
  summary?: string
  memory_type?: MemoryType
  importance?: number
  tags?: string
  source?: string
  context?: string
  is_shared?: boolean
  shared_category?: SharedCategory
}

export interface UpdateMemoryRequest {
  content?: string
  summary?: string
  memory_type?: MemoryType
  importance?: number
  tags?: string
  source?: string
  context?: string
  is_shared?: boolean
  shared_category?: SharedCategory
}

export interface MemoryFilters {
  assistant_id?: number
  memory_type?: MemoryType
  min_importance?: number
  max_importance?: number
  tags?: string[]
  include_shared?: boolean
  skip?: number
  limit?: number
}

export interface MemoryStats {
  assistant_id: number
  assistant_name: string
  total_memories: number
  total_shared_memories: number
  avg_importance: number
  most_used_type?: string
  memories_created_today: number
  memories_accessed_today: number
  date: string
}

export interface Assistant {
  id: number
  name: string
  personality?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateAssistantRequest {
  name: string
  personality?: string
  is_active?: boolean
}

export interface UpdateAssistantRequest {
  name?: string
  personality?: string
  is_active?: boolean
}