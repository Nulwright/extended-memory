import { format, formatDistanceToNow, isToday, isYesterday, parseISO } from 'date-fns'

// Format date for display
export const formatDate = (dateString: string | Date, includeTime = false): string => {
  try {
    const date = typeof dateString === 'string' ? parseISO(dateString) : dateString
    
    if (isToday(date)) {
      return includeTime ? format(date, 'h:mm a') : 'Today'
    }
    
    if (isYesterday(date)) {
      return includeTime ? `Yesterday ${format(date, 'h:mm a')}` : 'Yesterday'
    }
    
    return includeTime 
      ? format(date, 'MMM d, yyyy h:mm a')
      : format(date, 'MMM d, yyyy')
  } catch (error) {
    console.error('Error formatting date:', error)
    return 'Invalid date'
  }
}

// Format relative time (e.g., "2 hours ago")
export const formatRelativeTime = (dateString: string | Date): string => {
  try {
    const date = typeof dateString === 'string' ? parseISO(dateString) : dateString
    return formatDistanceToNow(date, { addSuffix: true })
  } catch (error) {
    console.error('Error formatting relative time:', error)
    return 'Unknown time'
  }
}

// Format file size
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

// Format number with commas
export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat().format(num)
}

// Format percentage
export const formatPercentage = (value: number, decimals = 1): string => {
  return `${(value * 100).toFixed(decimals)}%`
}

// Format duration in milliseconds to human readable
export const formatDuration = (ms: number): string => {
  if (ms < 1000) {
    return `${Math.round(ms)}ms`
  }
  
  const seconds = ms / 1000
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`
  }
  
  const minutes = seconds / 60
  if (minutes < 60) {
    return `${minutes.toFixed(1)}m`
  }
  
  const hours = minutes / 60
  return `${hours.toFixed(1)}h`
}

// Truncate text with ellipsis
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength).trim() + '...'
}

// Format importance level
export const formatImportance = (importance: number): string => {
  const levels = [
    'Very Low', 'Low', 'Below Normal', 'Normal', 'Medium',
    'Above Normal', 'High', 'Very High', 'Critical', 'Emergency'
  ]
  return levels[Math.max(0, Math.min(9, importance - 1))] || 'Unknown'
}

// Format memory type for display
export const formatMemoryType = (type: string): string => {
  const formatted = type.replace(/_/g, ' ').toLowerCase()
  return formatted.charAt(0).toUpperCase() + formatted.slice(1)
}

// Format tags array to string
export const formatTags = (tags: string | string[]): string => {
  if (Array.isArray(tags)) {
    return tags.join(', ')
  }
  return tags || ''
}

// Parse tags string to array
export const parseTags = (tagsString: string): string[] => {
  if (!tagsString) return []
  return tagsString
    .split(',')
    .map(tag => tag.trim())
    .filter(tag => tag.length > 0)
}

// Format search score
export const formatSearchScore = (score: number): string => {
  return `${(score * 100).toFixed(1)}%`
}

// Format API error message
export const formatErrorMessage = (error: any): string => {
  if (typeof error === 'string') return error
  
  if (error?.response?.data?.detail) {
    return error.response.data.detail
  }
  
  if (error?.response?.data?.error) {
    return error.response.data.error
  }
  
  if (error?.message) {
    return error.message
  }
  
  return 'An unexpected error occurred'
}

// Format validation errors
export const formatValidationErrors = (errors: any[]): string => {
  if (!Array.isArray(errors)) return 'Validation error'
  
  return errors
    .map(error => `${error.field}: ${error.message}`)
    .join(', ')
}

// Capitalize first letter
export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

// Convert camelCase to Title Case
export const camelToTitle = (str: string): string => {
  return str
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim()
}

// Generate initials from name
export const getInitials = (name: string): string => {
  return name
    .split(' ')
    .map(part => part.charAt(0).toUpperCase())
    .slice(0, 2)
    .join('')
}

// Format URL for display (remove protocol, truncate if too long)
export const formatUrl = (url: string, maxLength = 50): string => {
  try {
    const formatted = url.replace(/^https?:\/\//, '').replace(/\/$/, '')
    return truncateText(formatted, maxLength)
  } catch (error) {
    return truncateText(url, maxLength)
  }
}