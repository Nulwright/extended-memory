```python
"""Real-time Notification Service"""

import asyncio
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from esm.schemas import WSMessage

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing real-time notifications"""
    
    def __init__(self, connection_manager=None):
        self.connection_manager = connection_manager
    
    async def notify_memory_created(
        self,
        memory_id: int,
        assistant_id: int,
        content_preview: str,
        memory_type: str
    ):
        """Notify about new memory creation"""
        try:
            message = WSMessage(
                type="memory_created",
                data={
                    "memory_id": memory_id,
                    "assistant_id": assistant_id,
                    "content_preview": content_preview[:200] + "..." if len(content_preview) > 200 else content_preview,
                    "memory_type": memory_type,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            if self.connection_manager:
                # Notify subscribers of this assistant
                await self.connection_manager.send_to_assistant_subscribers(
                    message.json(), 
                    assistant_id
                )
                
                logger.debug(f"Notified memory creation: {memory_id}")
            
        except Exception as e:
            logger.error(f"Failed to notify memory creation: {e}")
    
    async def notify_memory_updated(
        self,
        memory_id: int,
        assistant_id: int,
        update_fields: List[str]
    ):
        """Notify about memory update"""
        try:
            message = WSMessage(
                type="memory_updated",
                data={
                    "memory_id": memory_id,
                    "assistant_id": assistant_id,
                    "updated_fields": update_fields,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
            
            if self.connection_manager:
                await self.connection_manager.send_to_assistant_subscribers(
                    message.json(), 
                    assistant_id
                )
                
                logger.debug(f"Notified memory update: {memory_id}")
            
        except Exception as e:
            logger.error(f"Failed to notify memory update: {e}")
    
    async def notify_memory_deleted(self, memory_id: int, assistant_id: int):
        """Notify about memory deletion"""
        try:
            message = WSMessage(
                type="memory_deleted",
                data={
                    "memory_id": memory_id,
                    "assistant_id": assistant_id,
                    "deleted_at": datetime.utcnow().isoformat()
                }
            )
            
            if self.connection_manager:
                await self.connection_manager.send_to_assistant_subscribers(
                    message.json(), 
                    assistant_id
                )
                
                logger.debug(f"Notified memory deletion: {memory_id}")
            
        except Exception as e:
            logger.error(f"Failed to notify memory deletion: {e}")
    
    async def notify_search_performed(
        self,
        query: str,
        results_count: int,
        search_type: str,
        assistant_id: Optional[int] = None
    ):
        """Notify about search operation"""
        try:
            message = WSMessage(
                type="search_performed",
                data={
                    "query": query,
                    "results_count": results_count,
                    "search_type": search_type,
                    "assistant_id": assistant_id,
                    "performed_at": datetime.utcnow().isoformat()
                }
            )
            
            if self.connection_manager:
                if assistant_id:
                    await self.connection_manager.send_to_assistant_subscribers(
                        message.json(), 
                        assistant_id
                    )
                else:
                    # Broadcast to all connections if no specific assistant
                    await self.connection_manager.broadcast(message.json())
                
                logger.debug(f"Notified search: '{query}' -> {results_count} results")
            
        except Exception as e:
            logger.error(f"Failed to notify search: {e}")
    
    async def notify_memory_shared(
        self,
        memory_id: int,
        assistant_id: int,
        shared_category: str
    ):
        """Notify about memory being shared"""
        try:
            message = WSMessage(
                type="memory_shared",
                data={
                    "memory_id": memory_id,
                    "assistant_id": assistant_id,
                    "shared_category": shared_category,
                    "shared_at": datetime.utcnow().isoformat()
                }
            )
            
            if self.connection_manager:
                # Broadcast to all connections since it affects shared memories
                await self.connection_manager.broadcast(message.json())
                
                logger.debug(f"Notified memory sharing: {memory_id}")
            
        except Exception as e:
            logger.error(f"Failed to notify memory sharing: {e}")
    
    async def notify_export_completed(
        self,
        export_id: str,
        record_count: int,
        file_size: int,
        format: str
    ):
        """Notify about export completion"""
        try:
            message = WSMessage(
                type="export_completed",
                data={
                    "export_id": export_id,
                    "record_count": record_count,
                    "file_size": file_size,
                    "format": format,
                    "download_url": f"/api/v1/export/{export_id}/download",
                    "completed_at": datetime.utcnow().isoformat()
                }
            )
            
            if self.connection_manager:
                await self.connection_manager.broadcast(message.json())
                
                logger.debug(f"Notified export completion: {export_id}")
            
        except Exception as e:
            logger.error(f"Failed to notify export completion: {e}")
    
    async def notify_system_status(
        self,
        status: str,
        message: str,
        severity: str = "info"
    ):
        """Notify about system status changes"""
        try:
            ws_message = WSMessage(
                type="system_status",
                data={
                    "status": status,
                    "message": message,
                    "severity": severity,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            if self.connection_manager:
                await self.connection_manager.broadcast(ws_message.json())
                
                logger.info(f"System status notification: {status} - {message}")
            
        except Exception as e:
            logger.error(f"Failed to notify system status: {e}")
    
    async def send_personal_notification(
        self,
        client_id: str,
        notification_type: str,
        data: Dict[str, Any]
    ):
        """Send notification to specific client"""
        try:
            message = WSMessage(
                type=notification_type,
                data=data
            )
            
            if self.connection_manager:
                await self.connection_manager.send_personal_message(
                    message.json(), 
                    client_id
                )
                
                logger.debug(f"Sent personal notification to {client_id}: {notification_type}")
            
        except Exception as e:
            logger.error(f"Failed to send personal notification: {e}")
    
    async def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification service statistics"""
        try:
            if not self.connection_manager:
                return {"status": "unavailable"}
            
            return {
                "status": "active",
                "total_connections": self.connection_manager.get_connection_count(),
                "assistant_subscriptions": {
                    aid: self.connection_manager.get_assistant_subscriber_count(aid)
                    for aid in self.connection_manager.assistant_subscriptions.keys()
                },
                "uptime": "available",  # Could track actual uptime
                "messages_sent": "not_tracked"  # Could implement message counting
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification stats: {e}")
            return {"status": "error", "error": str(e)}
