import { useQuery, useMutation, useQueryClient } from 'react-query'
import { memoryService } from '@/services/memoryService'
import { 
  Memory, 
  CreateMemoryRequest, 
  UpdateMemoryRequest, 
  MemoryFilters 
} from '@/types/memory'
import toast from 'react-hot-toast'

// Query keys
const MEMORY_KEYS = {
  all: ['memories'] as const,
  lists: () => [...MEMORY_KEYS.all, 'list'] as const,
  list: (filters: MemoryFilters) => [...MEMORY_KEYS.lists(), filters] as const,
  details: () => [...MEMORY_KEYS.all, 'detail'] as const,
  detail: (id: number) => [...MEMORY_KEYS.details(), id] as const,
  related: (id: number) => [...MEMORY_KEYS.all, 'related', id] as const,
  stats: (assistantId: number) => [...MEMORY_KEYS.all, 'stats', assistantId] as const,
  recent: (assistantId?: number) => [...MEMORY_KEYS.all, 'recent', assistantId] as const,
  important: (assistantId?: number) => [...MEMORY_KEYS.all, 'important', assistantId] as const,
  accessed: (assistantId?: number) => [...MEMORY_KEYS.all, 'accessed', assistantId] as const,
}

// Get memories with filters
export const useMemories = (filters: MemoryFilters = {}, options?: any) => {
  return useQuery({
    queryKey: MEMORY_KEYS.list(filters),
    queryFn: () => memoryService.getMemories(filters),
    ...options,
  })
}

// Get single memory
export const useMemory = (id: number, options?: any) => {
  return useQuery({
    queryKey: MEMORY_KEYS.detail(id),
    queryFn: () => memoryService.getMemory(id),
    enabled: !!id,
    ...options,
  })
}

// Get related memories
export const useRelatedMemories = (id: number, limit = 5, options?: any) => {
  return useQuery({
    queryKey: MEMORY_KEYS.related(id),
    queryFn: () => memoryService.getRelatedMemories(id, limit),
    enabled: !!id,
    ...options,
  })
}

// Get memory statistics
export const useMemoryStats = (assistantId: number, options?: any) => {
  return useQuery({
    queryKey: MEMORY_KEYS.stats(assistantId),
    queryFn: () => memoryService.getMemoryStats(assistantId),
    enabled: !!assistantId,
    ...options,
  })
}

// Get recent memories
export const useRecentMemories = (assistantId?: number, limit = 10, options?: any) => {
  return useQuery({
    queryKey: MEMORY_KEYS.recent(assistantId),
    queryFn: () => memoryService.getRecentMemories(assistantId, limit),
    ...options,
  })
}

// Get most important memories
export const useMostImportantMemories = (assistantId?: number, limit = 10, options?: any) => {
  return useQuery({
    queryKey: MEMORY_KEYS.important(assistantId),
    queryFn: () => memoryService.getMostImportantMemories(assistantId, limit),
    ...options,
  })
}

// Get most accessed memories
export const useMostAccessedMemories = (assistantId?: number, limit = 10, options?: any) => {
  return useQuery({
    queryKey: MEMORY_KEYS.accessed(assistantId),
    queryFn: () => memoryService.getMostAccessedMemories(assistantId, limit),
    ...options,
  })
}

// Create memory mutation
export const useCreateMemory = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateMemoryRequest) => memoryService.createMemory(data),
    onSuccess: (newMemory) => {
      // Invalidate and refetch memories
      queryClient.invalidateQueries(MEMORY_KEYS.lists())
      queryClient.invalidateQueries(MEMORY_KEYS.stats(newMemory.assistant_id))
      queryClient.invalidateQueries(MEMORY_KEYS.recent(newMemory.assistant_id))
      
      toast.success('Memory created successfully')
    },
    onError: (error: any) => {
      toast.error(error?.message || 'Failed to create memory')
    },
  })
}

// Update memory mutation
export const useUpdateMemory = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateMemoryRequest }) =>
      memoryService.updateMemory(id, data),
    onSuccess: (updatedMemory) => {
      // Update specific memory in cache
      queryClient.setQueryData(MEMORY_KEYS.detail(updatedMemory.id), updatedMemory)
      
      // Invalidate lists and stats
      queryClient.invalidateQueries(MEMORY_KEYS.lists())
      queryClient.invalidateQueries(MEMORY_KEYS.stats(updatedMemory.assistant_id))
      
      toast.success('Memory updated successfully')
    },
    onError: (error: any) => {
      toast.error(error?.message || 'Failed to update memory')
    },
  })
}

// Delete memory mutation
export const useDeleteMemory = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => memoryService.deleteMemory(id),
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries(MEMORY_KEYS.detail(deletedId))
      
      // Invalidate lists
      queryClient.invalidateQueries(MEMORY_KEYS.lists())
      queryClient.invalidateQueries(MEMORY_KEYS.stats)
      
      toast.success('Memory deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error?.message || 'Failed to delete memory')
    },
  })
}

// Record access mutation
export const useRecordAccess = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => memoryService.recordAccess(id),
    onSuccess: (_, id) => {
      // Invalidate specific memory and accessed lists
      queryClient.invalidateQueries(MEMORY_KEYS.detail(id))
      queryClient.invalidateQueries(MEMORY_KEYS.accessed())
    },
    // Don't show toast for access recording (too noisy)
  })
}

// Bulk delete memories mutation
export const useBulkDeleteMemories = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (ids: number[]) => memoryService.bulkDeleteMemories(ids),
    onSuccess: (result) => {
      // Invalidate all memory queries
      queryClient.invalidateQueries(MEMORY_KEYS.all)
      
      toast.success(`Deleted ${result.deleted_count} memories`)
    },
    onError: (error: any) => {
      toast.error(error?.message || 'Failed to delete memories')
    },
  })
}
