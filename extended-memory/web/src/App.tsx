import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import Dashboard from '@/components/Dashboard'
import MemoryList from '@/components/MemoryList'
import MemoryDetail from '@/components/MemoryDetail'
import Search from '@/components/Search'
import Analytics from '@/components/Analytics'
import Settings from '@/components/Settings'
import SharedMemories from '@/components/SharedMemories'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useLocalStorage } from '@/hooks/useLocalStorage'
import { cn } from '@/utils/cn'

function App() {
  const [theme, setTheme] = useLocalStorage('esm-theme', 'light')
  const [selectedAssistant, setSelectedAssistant] = useLocalStorage('esm-selected-assistant', null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  // WebSocket connection for real-time updates
  const { isConnected, lastMessage } = useWebSocket('/ws/connect', {
    enabled: true,
    reconnect: true,
  })

  // Apply theme to document
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      console.log('WebSocket message:', lastMessage)
      // Handle real-time updates here
      // For example, invalidate queries, show notifications, etc.
    }
  }, [lastMessage])

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }

  return (
    <div className={cn('min-h-screen bg-background', theme)}>
      <Layout
        selectedAssistant={selectedAssistant}
        onAssistantChange={setSelectedAssistant}
        theme={theme}
        onThemeToggle={toggleTheme}
        sidebarOpen={sidebarOpen}
        onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
        isConnected={isConnected}
      >
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route 
            path="/dashboard" 
            element={
              <Dashboard 
                selectedAssistant={selectedAssistant}
                onAssistantChange={setSelectedAssistant}
              />
            } 
          />
          <Route 
            path="/memories" 
            element={
              <MemoryList 
                selectedAssistant={selectedAssistant}
              />
            } 
          />
          <Route 
            path="/memories/:id" 
            element={<MemoryDetail />} 
          />
          <Route 
            path="/search" 
            element={
              <Search 
                selectedAssistant={selectedAssistant}
              />
            } 
          />
          <Route 
            path="/shared" 
            element={<SharedMemories />} 
          />
          <Route 
            path="/analytics" 
            element={
              <Analytics 
                selectedAssistant={selectedAssistant}
              />
            } 
          />
          <Route 
            path="/settings" 
            element={
              <Settings 
                theme={theme}
                onThemeChange={setTheme}
                selectedAssistant={selectedAssistant}
                onAssistantChange={setSelectedAssistant}
              />
            } 
          />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Layout>
    </div>
  )
}

export default App