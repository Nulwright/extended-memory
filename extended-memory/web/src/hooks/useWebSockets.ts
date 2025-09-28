import { useEffect, useRef, useState, useCallback } from 'react'
import { WebSocketMessage } from '@/types/api'

interface UseWebSocketOptions {
  enabled?: boolean
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  onMessage?: (message: WebSocketMessage) => void
}

export const useWebSocket = (url: string, options: UseWebSocketOptions = {}) => {
  const {
    enabled = true,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onOpen,
    onClose,
    onError,
    onMessage,
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const clientIdRef = useRef<string>(generateClientId())

  // Generate unique client ID
  function generateClientId() {
    return `client-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
  }

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return
    }

    try {
      setConnectionState('connecting')
      
      // Construct WebSocket URL with client ID
      const wsUrl = new URL(url, window.location.origin)
      wsUrl.protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      wsUrl.searchParams.set('client_id', clientIdRef.current)
      
      const ws = new WebSocket(wsUrl.toString())
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        setConnectionState('connected')
        reconnectAttemptsRef.current = 0
        onOpen?.()
        
        // Send connection info
        ws.send(JSON.stringify({
          type: 'connection_info',
          data: {
            client_id: clientIdRef.current,
            timestamp: new Date().toISOString(),
          }
        }))
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)
          onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        setConnectionState('disconnected')
        wsRef.current = null
        onClose?.()

        // Attempt reconnection if enabled
        if (reconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        }
      }

      ws.onerror = (error) => {
        setConnectionState('error')
        onError?.(error)
        console.error('WebSocket error:', error)
      }

    } catch (error) {
      setConnectionState('error')
      console.error('Failed to create WebSocket connection:', error)
    }
  }, [enabled, url, reconnect, reconnectInterval, maxReconnectAttempts, onOpen, onClose, onError, onMessage])

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setIsConnected(false)
    setConnectionState('disconnected')
  }, [])

  // Send message
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
      return true
    }
    return false
  }, [])

  // Send ping
  const sendPing = useCallback(() => {
    return sendMessage({
      type: 'ping',
      data: { timestamp: new Date().toISOString() }
    })
  }, [sendMessage])

  // Initialize connection
  useEffect(() => {
    if (enabled) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [enabled, connect, disconnect])

  // Periodic ping to keep connection alive
  useEffect(() => {
    if (!isConnected) return

    const pingInterval = setInterval(() => {
      sendPing()
    }, 30000) // Ping every 30 seconds

    return () => clearInterval(pingInterval)
  }, [isConnected, sendPing])

  return {
    isConnected,
    connectionState,
    lastMessage,
    sendMessage,
    sendPing,
    connect,
    disconnect,
  }
}