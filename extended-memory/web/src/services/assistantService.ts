import { apiClient } from './api'
import { 
  Assistant, 
  CreateAssistantRequest, 
  UpdateAssistantRequest 
} from '@/types/memory'

export const assistantService = {
  // Get all assistants
  getAssistants: (includeInactive = false) => 
    apiClient.get<Assistant[]>('/assistants', { include_inactive: includeInactive }),

  // Get single assistant by ID
  getAssistant: (id: number) => 
    apiClient.get<Assistant>(`/assistants/${id}`),

  // Create new assistant
  createAssistant: (data: CreateAssistantRequest) => 
    apiClient.post<Assistant>('/assistants', data),

  // Update assistant
  updateAssistant: (id: number, data: UpdateAssistantRequest) => 
    apiClient.put<Assistant>(`/assistants/${id}`, data),

  // Delete assistant
  deleteAssistant: (id: number) => 
    apiClient.delete(`/assistants/${id}`),

  // Get memory count for assistant
  getMemoryCount: (id: number) => 
    apiClient.get<{ assistant_id: number; memory_count: number }>(`/assistants/${id}/memories/count`),

  // Activate assistant
  activateAssistant: (id: number) => 
    apiClient.post(`/assistants/${id}/activate`),

  // Deactivate assistant
  deactivateAssistant: (id: number) => 
    apiClient.post(`/assistants/${id}/deactivate`),

  // Get assistant statistics
  getAssistantStats: (id: number) => 
    apiClient.get(`/analytics/assistant/${id}/stats`),

  // Get assistant activity
  getAssistantActivity: (id: number, days = 30) => 
    apiClient.get(`/analytics/assistant/${id}/activity`, { days }),
}