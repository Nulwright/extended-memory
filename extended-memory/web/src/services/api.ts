import axios, { AxiosResponse, AxiosError } from 'axios'
import toast from 'react-hot-toast'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('esm-auth-token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Add request timestamp for debugging
    config.metadata = { startTime: Date.now() }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log response time in development
    if (process.env.NODE_ENV === 'development' && response.config.metadata) {
      const duration = Date.now() - response.config.metadata.startTime
      console.log(`API ${response.config.method?.toUpperCase()} ${response.config.url}: ${duration}ms`)
    }
    
    return response
  },
  (error: AxiosError) => {
    // Handle different error types
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response
      
      switch (status) {
        case 400:
          toast.error(data?.detail || 'Bad request')
          break
        case 401:
          toast.error('Authentication required')
          // Redirect to login or refresh token
          break
        case 403:
          toast.error('Access denied')
          break
        case 404:
          toast.error(data?.detail || 'Resource not found')
          break
        case 422:
          // Validation errors
          if (data?.details && Array.isArray(data.details)) {
            data.details.forEach((error: any) => {
              toast.error(`${error.field}: ${error.message}`)
            })
          } else {
            toast.error(data?.error || 'Validation error')
          }
          break
        case 429:
          toast.error('Too many requests. Please slow down.')
          break
        case 500:
          toast.error('Internal server error. Please try again.')
          break
        default:
          toast.error(data?.error || 'An error occurred')
      }
    } else if (error.request) {
      // Network error
      toast.error('Network error. Please check your connection.')
    } else {
      // Request setup error
      toast.error('Request failed. Please try again.')
    }
    
    return Promise.reject(error)
  }
)

// Generic API methods
export const apiClient = {
  get: <T = any>(url: string, params?: any) => 
    api.get<T>(url, { params }).then(res => res.data),
  
  post: <T = any>(url: string, data?: any) => 
    api.post<T>(url, data).then(res => res.data),
  
  put: <T = any>(url: string, data?: any) => 
    api.put<T>(url, data).then(res => res.data),
  
  patch: <T = any>(url: string, data?: any) => 
    api.patch<T>(url, data).then(res => res.data),
  
  delete: <T = any>(url: string) => 
    api.delete<T>(url).then(res => res.data),
}

// Health check
export const healthCheck = () => {
  return axios.get('/health', { baseURL: '' })
    .then(res => res.data)
    .catch(() => ({ status: 'unhealthy', error: 'Connection failed' }))
}

export default api