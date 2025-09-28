import { apiClient } from './api'
import { 
  Memory, 
  CreateMemoryRequest, 
  UpdateMemoryRequest, 
  MemoryFilters,
  MemoryStats
} from '@/types/memory'

export const memoryService = {
  // Get all memories with filters
  getMemories: (filters: MemoryFilters = {}) => 
    apiClient.get<Memory[]>('/memories', filters),

  // Get single memory by ID
  getMemory: (id: number) => 
    apiClient.get<Memory>(`/memories/${id}`),

  // Create new memory
  createMemory: (data: CreateMemoryRequest) => 
    apiClient.post<Memory>('/memories', data),

  // Update memory
  updateMemory: (id: number, data: UpdateMemoryRequest) => 
    apiClient.put<Memory>(`/memories/${id}`, data),

  // Delete memory
  deleteMemory: (id: number) => 
    apiClient.delete(`/memories/${id}`),

  // Get related memories
  getRelatedMemories: (id: number, limit = 5) => 
    apiClient.get<Memory[]>(`/memories/${id}/related`, { limit }),

  // Record memory access
  recordAccess: (id: number) => 
    apiClient.post(`/memories/${id}/access`),

  // Get memory statistics
  getMemoryStats: (assistantId: number) => 
    apiClient.get<MemoryStats>(`/memories/assistant/${assistantId}/stats`),

  // Bulk create memories
  bulkCreateMemories: (memories: CreateMemoryRequest[]) => 
    apiClient.post<Memory[]>('/memories/bulk-create', memories),

  // Bulk delete memories
  bulkDeleteMemories: (ids: number[]) => 
    apiClient.delete('/memories/bulk-delete', { data: ids }),

  // Get memory counts by type
  getMemoryTypeCounts: (assistantId?: number) => 
    apiClient.get<Record<string, number>>('/memories/type-counts', { assistant_id: assistantId }),

  // Get recent memories
  getRecentMemories: (assistantId?: number, limit = 10) => 
    apiClient.get<Memory[]>('/memories/recent', { assistant_id: assistantId, limit }),

  // Get most important memories
  getMostImportantMemories: (assistantId?: number, limit = 10) => 
    apiClient.get<Memory[]>('/memories/important', { assistant_id: assistantId, limit }),

  // Get most accessed memories
  getMostAccessedMemories: (assistantId?: number, limit = 10) => 
    apiClient.get<Memory[]>('/memories/accessed', { assistant_id: assistantId, limit }),
}