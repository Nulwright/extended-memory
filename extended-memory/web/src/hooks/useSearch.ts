## 📁 PATH: web/src/hooks/useSearch.ts
```typescript
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { searchService } from '@/services/searchService'
import { SearchRequest, SearchResponse } from '@/types/search'
import { useState, useCallback, useEffect } from 'react'
import { useDebounce } from './useDebounce'

// Query keys
const SEARCH_KEYS = {
  all: ['search'] as const,
  queries: () => [...SEARCH_KEYS.all, 'query'] as const,
  query: (request: SearchRequest) => [...SEARCH_KEYS.queries(), request] as const,
  suggestions: (query: string, assistantId?: number) => 
    [...SEARCH_KEYS.all, 'suggestions', query, assistantId] as const,
  recentQueries: (assistantId?: number) => 
    [...SEARCH_KEYS.all, 'recent', assistantId] as const,
  popularTags: (assistantId?: number) => 
    [...SEARCH_KEYS.all, 'tags', assistantId] as const,
}

// Search memories
export const useSearchMemories = (request: SearchRequest, options?: any) => {
  return useQuery({
    queryKey: SEARCH_KEYS.query(request),
    queryFn: () => searchService.searchMemories(request),
    enabled: !!request.query && request.query.length > 0,
    ...options,
  })
}

// Search suggestions
export const useSearchSuggestions = (query: string, assistantId?: number, options?: any) => {
  const debouncedQuery = useDebounce(query, 300)
  
  return useQuery({
    queryKey: SEARCH_KEYS.suggestions(debouncedQuery, assistantId),
    queryFn: () => searchService.getSearchSuggestions(debouncedQuery, assistantId),
    enabled: debouncedQuery.length > 2,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  })
}

// Recent queries
export const useRecentQueries = (assistantId?: number, options?: any) => {
  return useQuery({
    queryKey: SEARCH_KEYS.recentQueries(assistantId),
    queryFn: () => searchService.getRecentQueries(assistantId),
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  })
}

// Popular tags
export const usePopularTags = (assistantId?: number, options?: any) => {
  return useQuery({
    queryKey: SEARCH_KEYS.popularTags(assistantId),
    queryFn: () => searchService.getPopularTags(assistantId),
    staleTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  })
}

// Advanced search hook with state management
export const useAdvancedSearch = (initialRequest?: Partial<SearchRequest>) => {
  const [searchRequest, setSearchRequest] = useState<SearchRequest>({
    query: '',
    search_type: 'hybrid',
    limit: 20,
    include_shared: true,
    ...initialRequest,
  })

  const [searchHistory, setSearchHistory] = useState<SearchRequest[]>([])
  const queryClient = useQueryClient()

  // Debounced query for auto-search
  const debouncedQuery = useDebounce(searchRequest.query, 500)

  // Execute search
  const searchQuery = useQuery({
    queryKey: SEARCH_KEYS.query(searchRequest),
    queryFn: () => searchService.searchMemories(searchRequest),
    enabled: !!debouncedQuery && debouncedQuery.length > 0,
    keepPreviousData: true,
    staleTime: 30 * 1000, // 30 seconds
  })

  // Save search query
  const saveQueryMutation = useMutation({
    mutationFn: (query: string) => 
      searchService.saveSearchQuery(query, searchRequest.assistant_id),
    onSuccess: () => {
      // Invalidate recent queries
      queryClient.invalidateQueries(SEARCH_KEYS.recentQueries(searchRequest.assistant_id))
    },
  })

  // Update search request
  const updateSearchRequest = useCallback((updates: Partial<SearchRequest>) => {
    setSearchRequest(prev => ({
      ...prev,
      ...updates,
    }))
  }, [])

  // Execute search manually
  const executeSearch = useCallback((request?: Partial<SearchRequest>) => {
    const finalRequest = { ...searchRequest, ...request }
    setSearchRequest(finalRequest)
    
    // Add to history
    setSearchHistory(prev => [
      finalRequest,
      ...prev.filter(item => item.query !== finalRequest.query).slice(0, 9)
    ])

    // Save query if it's substantial
    if (finalRequest.query.length > 2) {
      saveQueryMutation.mutate(finalRequest.query)
    }

    // Force refetch
    queryClient.invalidateQueries(SEARCH_KEYS.query(finalRequest))
  }, [searchRequest, queryClient, saveQueryMutation])

  // Clear search
  const clearSearch = useCallback(() => {
    setSearchRequest(prev => ({
      ...prev,
      query: '',
    }))
  }, [])

  // Reset filters
  const resetFilters = useCallback(() => {
    setSearchRequest(prev => ({
      query: prev.query,
      assistant_id: prev.assistant_id,
      search_type: 'hybrid',
      limit: 20,
      include_shared: true,
    }))
  }, [])

  return {
    searchRequest,
    searchResults: searchQuery.data,
    isSearching: searchQuery.isLoading,
    searchError: searchQuery.error,
    searchHistory,
    updateSearchRequest,
    executeSearch,
    clearSearch,
    resetFilters,
    refetch: searchQuery.refetch,
  }
}