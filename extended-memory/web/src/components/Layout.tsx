import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Menu, 
  X, 
  Home, 
  Search, 
  Brain, 
  Share2, 
  BarChart3, 
  Settings,
  Sun,
  Moon,
  Wifi,
  WifiOff,
  ChevronDown
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { Button } from './ui/Button'
import { Assistant } from '@/types/memory'
import { useAssistants } from '@/hooks/useAssistants'

interface LayoutProps {
  children: React.ReactNode
  selectedAssistant: Assistant | null
  onAssistantChange: (assistant: Assistant | null) => void
  theme: string
  onThemeToggle: () => void
  sidebarOpen: boolean
  onSidebarToggle: () => void
  isConnected: boolean
}

const Layout: React.FC<LayoutProps> = ({
  children,
  selectedAssistant,
  onAssistantChange,
  theme,
  onThemeToggle,
  sidebarOpen,
  onSidebarToggle,
  isConnected,
}) => {
  const location = useLocation()
  const { data: assistants = [] } = useAssistants()

  const navigationItems = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Memories', href: '/memories', icon: Brain },
    { name: 'Search', href: '/search', icon: Search },
    { name: 'Shared', href: '/shared', icon: Share2 },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Settings', href: '/settings', icon: Settings },
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-50 lg:hidden"
          onClick={onSidebarToggle}
        >
          <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" />
        </div>
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-50 h-full w-64 transform bg-card border-r transition-transform duration-200 ease-in-out lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Sidebar header */}
          <div className="flex h-16 items-center justify-between border-b px-6">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 rounded-lg bg-primary-600 flex items-center justify-center">
                <Brain className="h-5 w-5 text-white" />
              </div>
              <span className="text-lg font-semibold">ESM</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={onSidebarToggle}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Assistant selector */}
          <div className="border-b p-4">
            <div className="relative">
              <select
                value={selectedAssistant?.id || ''}
                onChange={(e) => {
                  const assistant = assistants.find(a => a.id === Number(e.target.value))
                  onAssistantChange(assistant || null)
                }}
                className="w-full appearance-none rounded-md border border-input bg-background px-3 py-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">All Assistants</option>
                {assistants.map((assistant) => (
                  <option key={assistant.id} value={assistant.id}>
                    {assistant.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-4">
            {navigationItems.map((item) => {
              const isActive = location.pathname === item.href
              const Icon = item.icon

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'group flex items-center space-x-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-100 text-primary-900 dark:bg-primary-900 dark:text-primary-100'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'
                  )}
                  onClick={() => {
                    if (window.innerWidth < 1024) {
                      onSidebarToggle()
                    }
                  }}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </nav>

          {/* Connection status */}
          <div className="border-t p-4">
            <div className={cn(
              'flex items-center space-x-2 text-sm',
              isConnected ? 'text-success-600' : 'text-error-600'
            )}>
              {isConnected ? (
                <Wifi className="h-4 w-4" />
              ) : (
                <WifiOff className="h-4 w-4" />
              )}
              <span>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="icon"
                className="lg:hidden"
                onClick={onSidebarToggle}
              >
                <Menu className="h-5 w-5" />
              </Button>
              
              {/* Page title */}
              <div className="hidden sm:block">
                <h1 className="text-xl font-semibold text-foreground">
                  {navigationItems.find(item => item.href === location.pathname)?.name || 'ESM'}
                </h1>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Theme toggle */}
              <Button
                variant="ghost"
                size="icon"
                onClick={onThemeToggle}
              >
                {theme === 'dark' ? (
                  <Sun className="h-5 w-5" />
                ) : (
                  <Moon className="h-5 w-5" />
                )}
              </Button>

              {/* Selected assistant indicator */}
              {selectedAssistant && (
                <div className="hidden sm:flex items-center space-x-2 rounded-md bg-primary-100 px-3 py-1 text-sm text-primary-900 dark:bg-primary-900 dark:text-primary-100">
                  <div className="h-2 w-2 rounded-full bg-primary-600" />
                  <span>{selectedAssistant.name}</span>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1">
          <div className="h-[calc(100vh-4rem)] overflow-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

export default Layout