// Memory types with display information
export const MEMORY_TYPES = {
  general: { label: 'General', icon: '📝', color: 'bg-gray-100 text-gray-800' },
  conversation: { label: 'Conversation', icon: '💬', color: 'bg-blue-100 text-blue-800' },
  fact: { label: 'Fact', icon: '💡', color: 'bg-yellow-100 text-yellow-800' },
  task: { label: 'Task', icon: '✅', color: 'bg-green-100 text-green-800' },
  project: { label: 'Project', icon: '🚀', color: 'bg-purple-100 text-purple-800' },
  personal: { label: 'Personal', icon: '👤', color: 'bg-pink-100 text-pink-800' },
  code: { label: 'Code', icon: '💻', color: 'bg-indigo-100 text-indigo-800' },
  reference: { label: 'Reference', icon: '📚', color: 'bg-orange-100 text-orange-800' },
}

// Shared categories with display information
export const SHARED_CATEGORIES = {
  knowledge: { label: 'Knowledge Base', icon: '📚', description: 'Shared facts and information' },
  tasks: { label: 'Tasks & Reminders', icon: '✅', description: 'Shared tasks and reminders' },
  projects: { label: 'Projects', icon: '🚀', description: 'Project-related information' },
  contacts: { label: 'Contacts', icon: '👤', description: 'Contact information and notes' },
  resources: { label: 'Resources', icon: '🔗', description: 'Useful resources and links' },
  templates: { label: 'Templates', icon: '📋', description: 'Templates and examples' },
}

// Search types
export const SEARCH_TYPES = {
  keyword: { label: 'Keyword', description: 'Text-based search' },
  semantic: { label: 'Semantic', description: 'AI-powered meaning search' },
  hybrid: { label: 'Hybrid', description: 'Combined keyword + semantic' },
}

// Importance levels with colors
export const IMPORTANCE_LEVELS = {
  1: { label: 'Very Low', color: 'text-gray-400', bg: 'bg-gray-100' },
  2: { label: 'Low', color: 'text-gray-500', bg: 'bg-gray-200' },
  3: { label: 'Below Normal', color: 'text-blue-400', bg: 'bg-blue-100' },
  4: { label: 'Normal', color: 'text-blue-500', bg: 'bg-blue-200' },
  5: { label: 'Medium', color: 'text-green-500', bg: 'bg-green-200' },
  6: { label: 'Above Normal', color: 'text-yellow-500', bg: 'bg-yellow-200' },
  7: { label: 'High', color: 'text-orange-500', bg: 'bg-orange-200' },
  8: { label: 'Very High', color: 'text-red-500', bg: 'bg-red-200' },
  9: { label: 'Critical', color: 'text-red-600', bg: 'bg-red-300' },
  10: { label: 'Emergency', color: 'text-red-700', bg: 'bg-red-400' },
}

// API endpoints
export const API_ENDPOINTS = {
  MEMORIES: '/memories',
  SEARCH: '/search',
  ASSISTANTS: '/assistants',
  SHARED: '/shared',
  ANALYTICS: '/analytics',
  EXPORT: '/export',
  WEBSOCKET: '/ws/connect',
}

// Default values
export const DEFAULTS = {
  MEMORY_IMPORTANCE: 5,
  MEMORY_TYPE: 'general' as const,
  SEARCH_LIMIT: 20,
  SEARCH_TYPE: 'hybrid' as const,
  PAGINATION_LIMIT: 50,
}

// UI constants
export const UI = {
  SIDEBAR_WIDTH: 256,
  HEADER_HEIGHT: 64,
  MOBILE_BREAKPOINT: 768,
  ANIMATION_DURATION: 200,
  DEBOUNCE_DELAY: 300,
  TOAST_DURATION: 4000,
}

// Validation rules
export const VALIDATION = {
  MEMORY_CONTENT_MIN: 5,
  MEMORY_CONTENT_MAX: 50000,
  MEMORY_TAGS_MAX: 500,
  ASSISTANT_NAME_MIN: 1,
  ASSISTANT_NAME_MAX: 50,
  SEARCH_QUERY_MIN: 1,
  SEARCH_QUERY_MAX: 500,
}

// Date formats
export const DATE_FORMATS = {
  DISPLAY: 'MMM d, yyyy',
  DISPLAY_WITH_TIME: 'MMM d, yyyy h:mm a',
  ISO: "yyyy-MM-dd'T'HH:mm:ss",
  TIME_ONLY: 'h:mm a',
  RELATIVE: 'relative', // Used with date-fns formatDistance
}

// Export formats
export const EXPORT_FORMATS = {
  json: { label: 'JSON', extension: '.json', mime: 'application/json' },
  csv: { label: 'CSV', extension: '.csv', mime: 'text/csv' },
  txt: { label: 'Text', extension: '.txt', mime: 'text/plain' },
}

// WebSocket message types
export const WS_MESSAGE_TYPES = {
  MEMORY_CREATED: 'memory_created',
  MEMORY_UPDATED: 'memory_updated',
  MEMORY_DELETED: 'memory_deleted',
  MEMORY_SHARED: 'memory_shared',
  SEARCH_PERFORMED: 'search_performed',
  EXPORT_COMPLETED: 'export_completed',
  SYSTEM_STATUS: 'system_status',
  CONNECTION_ESTABLISHED: 'connection_established',
  PING: 'ping',
  PONG: 'pong',
}

// Feature flags (could be moved to environment config)
export const FEATURES = {
  REAL_TIME_UPDATES: true,
  ADVANCED_SEARCH: true,
  MEMORY_SHARING: true,
  ANALYTICS: true,
  EXPORT_IMPORT: true,
  DARK_MODE: true,
  NOTIFICATIONS: true,
  BROWSER_EXTENSION: true,
}