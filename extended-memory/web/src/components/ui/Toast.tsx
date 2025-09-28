import React from 'react'
import toast, { Toaster as HotToaster, Toast as HotToast } from 'react-hot-toast'
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react'
import { cn } from '@/utils/cn'

// Enhanced toast function with predefined styles
export const showToast = {
  success: (message: string) => {
    toast.custom((t) => (
      <ToastContent
        type="success"
        message={message}
        toast={t}
      />
    ))
  },
  
  error: (message: string) => {
    toast.custom((t) => (
      <ToastContent
        type="error"
        message={message}
        toast={t}
      />
    ))
  },
  
  warning: (message: string) => {
    toast.custom((t) => (
      <ToastContent
        type="warning"
        message={message}
        toast={t}
      />
    ))
  },
  
  info: (message: string) => {
    toast.custom((t) => (
      <ToastContent
        type="info"
        message={message}
        toast={t}
      />
    ))
  },
  
  promise: <T,>(
    promise: Promise<T>,
    msgs: {
      loading: string
      success: string | ((data: T) => string)
      error: string | ((error: any) => string)
    }
  ) => {
    return toast.promise(promise, {
      loading: msgs.loading,
      success: msgs.success,
      error: msgs.error,
    })
  },
}

interface ToastContentProps {
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  toast: HotToast
}

const ToastContent: React.FC<ToastContentProps> = ({ type, message, toast }) => {
  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertCircle,
    info: Info,
  }

  const colors = {
    success: 'text-success-600',
    error: 'text-error-600',
    warning: 'text-warning-600',
    info: 'text-primary-600',
  }

  const bgColors = {
    success: 'bg-success-50 border-success-200',
    error: 'bg-error-50 border-error-200',
    warning: 'bg-warning-50 border-warning-200',
    info: 'bg-primary-50 border-primary-200',
  }

  const Icon = icons[type]

  return (
    <div
      className={cn(
        'flex items-center space-x-3 rounded-lg border p-4 shadow-lg backdrop-blur-sm',
        'animate-in slide-in-from-top-2 duration-300',
        bgColors[type],
        toast.visible ? 'animate-in' : 'animate-out'
      )}
    >
      <Icon className={cn('h-5 w-5 flex-shrink-0', colors[type])} />
      <p className="text-sm font-medium text-gray-900 flex-1">{message}</p>
      <button
        onClick={() => toast.dismiss(toast.id)}
        className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

// Custom Toaster component
export const Toaster: React.FC = () => {
  return (
    <HotToaster
      position="top-right"
      toastOptions={{
        duration: 4000,
        className: 'bg-transparent shadow-none',
      }}
    />
  )
}