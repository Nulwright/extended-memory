"""WebSocket API for Real-time Updates"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional, Dict, Set
import logging
import json
import asyncio
from datetime import datetime

from esm.services.notification_service import NotificationService
from esm.schemas import WSMessage, WSConnectionInfo

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        # Store connections by client_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store assistant subscriptions
        self.assistant_subscriptions: Dict[int, Set[str]] = {}
        # Store connection info
        self.connection_info: Dict[str, WSConnectionInfo] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, assistant_id: Optional[int] = None):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        # Track assistant subscription
        if assistant_id:
            if assistant_id not in self.assistant_subscriptions:
                self.assistant_subscriptions[assistant_id] = set()
            self.assistant_subscriptions[assistant_id].add(client_id)
        
        # Store connection info
        self.connection_info[client_id] = WSConnectionInfo(
            client_id=client_id,
            assistant_id=assistant_id,
            connected_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        logger.info(f"Client {client_id} connected (assistant: {assistant_id})")
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            # Remove from assistant subscriptions
            info = self.connection_info.get(client_id)
            if info and info.assistant_id:
                assistant_subs = self.assistant_subscriptions.get(info.assistant_id, set())
                assistant_subs.discard(client_id)
                if not assistant_subs:
                    del self.assistant_subscriptions[info.assistant_id]
            
            # Remove connection
            del self.active_connections[client_id]
            if client_id in self.connection_info:
                del self.connection_info[client_id]
            
            logger.info(f"Client {client_id} disconnected")
    
    async def send_personal_message(self, message: str, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_text(message)
                
                # Update last activity
                if client_id in self.connection_info:
                    self.connection_info[client_id].last_activity = datetime.utcnow()
            except:
                # Connection might be dead, remove it
                self.disconnect(client_id)
    
    async def send_to_assistant_subscribers(self, message: str, assistant_id: int):
        """Send message to all clients subscribed to an assistant"""
        if assistant_id in self.assistant_subscriptions:
            clients = self.assistant_subscriptions[assistant_id].copy()
            for client_id in clients:
                await self.send_personal_message(message, client_id)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        if self.active_connections:
            clients = list(self.active_connections.keys())
            for client_id in clients:
                await self.send_personal_message(message, client_id)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
    
    def get_assistant_subscriber_count(self, assistant_id: int) -> int:
        """Get number of subscribers for an assistant"""
        return len(self.assistant_subscriptions.get(assistant_id, set()))


# Global connection manager
manager = ConnectionManager()


def get_notification_service() -> NotificationService:
    """Get notification service dependency"""
    return NotificationService(manager)


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str = Query(..., description="Unique client identifier"),
    assistant_id: Optional[int] = Query(None, description="Assistant ID to subscribe to"),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket, client_id, assistant_id)
    
    try:
        # Send welcome message
        welcome_msg = WSMessage(
            type="connection_established",
            data={
                "client_id": client_id,
                "assistant_id": assistant_id,
                "message": "Connected to ESM WebSocket"
            }
        )
        await websocket.send_text(welcome_msg.json())
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            
            try:
                # Parse incoming message
                message_data = json.loads(data)
                message_type = message_data.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    pong_msg = WSMessage(
                        type="pong",
                        data={"timestamp": datetime.utcnow().isoformat()}
                    )
                    await websocket.send_text(pong_msg.json())
                
                elif message_type == "subscribe_assistant":
                    # Update assistant subscription
                    new_assistant_id = message_data.get("assistant_id")
                    if new_assistant_id:
                        # Remove from old subscription
                        old_info = manager.connection_info.get(client_id)
                        if old_info and old_info.assistant_id:
                            old_subs = manager.assistant_subscriptions.get(old_info.assistant_id, set())
                            old_subs.discard(client_id)
                        
                        # Add to new subscription
                        if new_assistant_id not in manager.assistant_subscriptions:
                            manager.assistant_subscriptions[new_assistant_id] = set()
                        manager.assistant_subscriptions[new_assistant_id].add(client_id)
                        
                        # Update connection info
                        manager.connection_info[client_id].assistant_id = new_assistant_id
                        
                        response_msg = WSMessage(
                            type="subscription_updated",
                            data={"assistant_id": new_assistant_id}
                        )
                        await websocket.send_text(response_msg.json())
                
                elif message_type == "get_stats":
                    # Send connection statistics
                    stats_msg = WSMessage(
                        type="connection_stats",
                        data={
                            "total_connections": manager.get_connection_count(),
                            "assistant_subscribers": {
                                aid: manager.get_assistant_subscriber_count(aid)
                                for aid in manager.assistant_subscriptions.keys()
                            }
                        }
                    )
                    await websocket.send_text(stats_msg.json())
                
                else:
                    # Handle unknown message type
                    error_msg = WSMessage(
                        type="error",
                        data={"message": f"Unknown message type: {message_type}"}
                    )
                    await websocket.send_text(error_msg.json())
                
                # Update last activity
                if client_id in manager.connection_info:
                    manager.connection_info[client_id].last_activity = datetime.utcnow()
                    
            except json.JSONDecodeError:
                error_msg = WSMessage(
                    type="error",
                    data={"message": "Invalid JSON message"}
                )
                await websocket.send_text(error_msg.json())
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)


@router.get("/connections")
async def get_connection_info():
    """Get information about active WebSocket connections"""
    return {
        "total_connections": manager.get_connection_count(),
        "connections": [
            {
                "client_id": info.client_id,
                "assistant_id": info.assistant_id,
                "connected_at": info.connected_at,
                "last_activity": info.last_activity
            }
            for info in manager.connection_info.values()
        ],
        "assistant_subscribers": {
            aid: manager.get_assistant_subscriber_count(aid)
            for aid in manager.assistant_subscriptions.keys()
        }
    }


@router.post("/broadcast")
async def broadcast_message(
    message: str,
    message_type: str = "broadcast"
):
    """Broadcast a message to all connected clients"""
    broadcast_msg = WSMessage(
        type=message_type,
        data={"message": message}
    )
    await manager.broadcast(broadcast_msg.json())
    return {"message": "Broadcast sent", "connections": manager.get_connection_count()}


@router.post("/notify/{assistant_id}")
async def notify_assistant_subscribers(
    assistant_id: int,
    message: str,
    message_type: str = "notification"
):
    """Send notification to all clients subscribed to an assistant"""
    notification_msg = WSMessage(
        type=message_type,
        data={
            "assistant_id": assistant_id,
            "message": message
        }
    )
    await manager.send_to_assistant_subscribers(notification_msg.json(), assistant_id)
    
    subscriber_count = manager.get_assistant_subscriber_count(assistant_id)
    return {
        "message": "Notification sent",
        "assistant_id": assistant_id,
        "subscribers_notified": subscriber_count
    }


# Export manager for use in other services
def get_websocket_manager():
    """Get the WebSocket connection manager"""
    return manager