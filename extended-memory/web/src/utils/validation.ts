import { VALIDATION } from './constants'

export interface ValidationResult {
  isValid: boolean
  errors: string[]
}

// Validate memory content
export const validateMemoryContent = (content: string): ValidationResult => {
  const errors: string[] = []
  
  if (!content || content.trim().length === 0) {
    errors.push('Memory content is required')
  } else if (content.length < VALIDATION.MEMORY_CONTENT_MIN) {
    errors.push(`Memory content must be at least ${VALIDATION.MEMORY_CONTENT_MIN} characters`)
  } else if (content.length > VALIDATION.MEMORY_CONTENT_MAX) {
    errors.push(`Memory content cannot exceed ${VALIDATION.MEMORY_CONTENT_MAX} characters`)
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  }
}

// Validate memory importance
export const validateImportance = (importance: number): ValidationResult => {
  const errors: string[] = []
  
  if (!Number.isInteger(importance)) {
    errors.push('Importance must be a whole number')
  } else if (importance < 1 || importance > 10) {
    errors.push('Importance must be between 1 and 10')
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  }
}

// Validate memory tags
export const validateTags = (tags: string): ValidationResult => {
  const errors: string[] = []
  
  if (tags && tags.length > VALIDATION.MEMORY_TAGS_MAX) {
    errors.push(`Tags cannot exceed ${VALIDATION.MEMORY_TAGS_MAX} characters`)
  }
  
  // Check for valid tag format (comma-separated)
  if (tags) {
    const tagList = tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0)
    
    if (tagList.length > 20) {
      errors.push('Cannot have more than 20 tags')
    }
    
    for (const tag of tagList) {
      if (tag.length > 50) {
        errors.push('Individual tags cannot exceed 50 characters')
      }
      
      if (!/^[a-zA-Z0-9\s\-_]+$/.test(tag)) {
        errors.push('Tags can only contain letters, numbers, spaces, hyphens, and underscores')
      }
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  }
}

// Validate assistant name
export const validateAssistantName = (name: string): ValidationResult => {
  const errors: string[] = []
  
  if (!name || name.trim().length === 0) {
    errors.push('Assistant name is required')
  } else {
    const trimmedName = name.trim()
    
    if (trimmedName.length < VALIDATION.ASSISTANT_NAME_MIN) {
      errors.push(`Assistant name must be at least ${VALIDATION.ASSISTANT_NAME_MIN} character`)
    } else if (trimmedName.length > VALIDATION.ASSISTANT_NAME_MAX) {
      errors.push(`Assistant name cannot exceed ${VALIDATION.ASSISTANT_NAME_MAX} characters`)
    }
    
    if (!/^[a-zA-Z0-9\s\-_]+$/.test(trimmedName)) {
      errors.push('Assistant name can only contain letters, numbers, spaces, hyphens, and underscores')
    }
    
    if (!/^[a-zA-Z]/.test(trimmedName)) {
      errors.push('Assistant name must start with a letter')
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  }
}

// Validate search query
export const validateSearchQuery = (query: string): ValidationResult => {
  const errors: string[] = []
  
  if (!query || query.trim().length === 0) {
    errors.push('Search query is required')
  } else {
    const trimmedQuery = query.trim()
    
    if (trimmedQuery.length < VALIDATION.SEARCH_QUERY_MIN) {
      errors.push(`Search query must be at least ${VALIDATION.SEARCH_QUERY_MIN} character`)
    } else if (trimmedQuery.length > VALIDATION.SEARCH_QUERY_MAX) {
      errors.push(`Search query cannot exceed ${VALIDATION.SEARCH_QUERY_MAX} characters`)
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  }
}

// Validate email format
export const validateEmail = (email: string): ValidationResult => {
  const errors: string[] = []
  
  if (!email || email.trim().length === 0) {
    errors.push('Email is required')
  } else {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email.trim())) {
      errors.push('Please enter a valid email address')
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  }
}

// Validate URL format
export const validateUrl = (url: string): ValidationResult => {
  const errors: string[] = []
  
  if (url && url.trim().length > 0) {
    try {
      new URL(url.trim())
    } catch {
      errors.push('Please enter a valid URL')
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  }
}

// Validate date range
export const validateDateRange = (startDate: string, endDate: string): ValidationResult => {
  const errors: string[] = []
  
  if (startDate && endDate) {
    const start = new Date(startDate)
    const end = new Date(endDate)
    
    if (isNaN(start.getTime())) {
      errors.push('Start date is invalid')
    }
    
    if (isNaN(end.getTime())) {
      errors.push('End date is invalid')
    }
    
    if (start > end) {
      errors.push('Start date must be before end date')
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  }
}

// Generic required field validation
export const validateRequired = (value: any, fieldName: string): ValidationResult => {
  const errors: string[] = []
  
  if (value === null || value === undefined || 
      (typeof value === 'string' && value.trim().length === 0) ||
      (Array.isArray(value) && value.length === 0)) {
    errors.push(`${fieldName} is required`)
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  }
}

// Validate positive number
export const validatePositiveNumber = (value: number, fieldName: string): ValidationResult => {
  const errors: string[] = []
  
  if (!Number.isFinite(value)) {
    errors.push(`${fieldName} must be a valid number`)
  } else if (value <= 0) {
    errors.push(`${fieldName} must be positive`)
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  }
}

// Combine multiple validation results
export const combineValidationResults = (...results: ValidationResult[]): ValidationResult => {
  const allErrors = results.flatMap(result => result.errors)
  
  return {
    isValid: allErrors.length === 0,
    errors: allErrors,
  }
}