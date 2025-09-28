import { Memory } from './memory'

export type SearchType = 'keyword' | 'semantic' | 'hybrid'

export interface SearchRequest {
  query: string
  assistant_id?: number
  memory_type?: string
  search_type?: SearchType
  limit?: number
  min_importance?: number
  tags?: string[]
  include_shared?: boolean
  date_from?: string
  date_to?: string
}

export interface SearchResult {
  memory: Memory
  score: number
  match_type: string
  highlight?: string
}

export interface SearchResponse {
  results: SearchResult[]
  total_count: number
  execution_time_ms: number
  search_type: SearchType
  query: string
}

export interface SearchSuggestion {
  query: string
  count: number
}

export interface PopularTag {
  tag: string
  count: number
}