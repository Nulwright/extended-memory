```python
"""Webhook Handlers for External Service Integration"""

import asyncio
import logging
import json
import hmac
import hashlib
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from fastapi import Request, HTTPException
import httpx

from esm.config import get_settings
from esm.services.memory_service import MemoryService
from esm.schemas import MemoryCreate
from esm.database import get_db_context

logger = logging.getLogger(__name__)


class WebhookHandlers:
    """Handlers for processing webhooks from external services"""
    
    def __init__(self):
        self.settings = get_settings()
        self.registered_handlers = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default webhook handlers"""
        self.registered_handlers.update({
            'github_push': self._handle_github_push,
            'slack_message': self._handle_slack_message,
            'calendar_event': self._handle_calendar_event,
            'note_taking_app': self._handle_note_taking_app,
            'task_update': self._handle_task_update,
            'generic_webhook': self._handle_generic_webhook
        })
    
    async def process_webhook(
        self,
        webhook_type: str,
        payload: Dict[str, Any],
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """Process incoming webhook"""
        try:
            logger.info(f"Processing webhook: {webhook_type}")
            
            # Verify webhook signature if required
            if request and self._requires_signature_verification(webhook_type):
                if not await self._verify_webhook_signature(request, webhook_type):
                    raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
            # Get handler for webhook type
            handler = self.registered_handlers.get(webhook_type)
            if not handler:
                logger.warning(f"No handler found for webhook type: {webhook_type}")
                return {"status": "ignored", "reason": "no_handler"}
            
            # Process webhook
            result = await handler(payload, request)
            
            logger.info(f"Webhook {webhook_type} processed successfully")
            return {"status": "processed", "result": result}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Webhook processing failed for {webhook_type}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_github_push(self, payload: Dict[str, Any], request: Optional[Request] = None) -> Dict[str, Any]:
        """Handle GitHub push webhook"""
        try:
            repository = payload.get('repository', {})
            commits = payload.get('commits', [])
            
            if not commits:
                return {"message": "No commits to process"}
            
            # Create memory entries for significant commits
            processed_commits = []
            
            with get_db_context() as db:
                memory_service = MemoryService(db)
                
                for commit in commits:
                    # Skip merge commits and minor changes
                    if len(commit.get('message', '').split('\n')) < 2:
                        continue
                    
                    # Create memory for the commit
                    memory_content = f"Code commit in {repository.get('name', 'Unknown repo')}:\n"
                    memory_content += f"Message: {commit.get('message')}\n"
                    memory_content += f"Author: {commit.get('author', {}).get('name')}\n"
                    memory_content += f"URL: {commit.get('url')}\n"
                    
                    if commit.get('modified'):
                        memory_content += f"Modified files: {', '.join(commit['modified'][:5])}"
                        if len(commit['modified']) > 5:
                            memory_content += f" and {len(commit['modified']) - 5} more"
                    
                    memory_data = MemoryCreate(
                        assistant_id=1,  # Default to first assistant (could be configurable)
                        content=memory_content,
                        memory_type="code",
                        importance=6,
                        tags=f"github, code, {repository.get('name', 'unknown')}",
                        source="github_webhook",
                        context=f"Repository: {repository.get('full_name')}"
                    )
                    
                    memory = await memory_service.create_memory(memory_data)
                    processed_commits.append({
                        "commit_id": commit.get('id'),
                        "memory_id": memory.id
                    })
            
            return {
                "processed_commits": len(processed_commits),
                "commits": processed_commits
            }
            
        except Exception as e:
            logger.error(f"GitHub webhook handling failed: {e}")
            raise
    
    async def _handle_slack_message(self, payload: Dict[str, Any], request: Optional[Request] = None) -> Dict[str, Any]:
        """Handle Slack message webhook"""
        try:
            # Handle Slack URL verification challenge
            if payload.get('type') == 'url_verification':
                return {"challenge": payload.get('challenge')}
            
            event = payload.get('event', {})
            
            # Skip bot messages and message subtypes we don't care about
            if event.get('bot_id') or event.get('subtype') in ['message_deleted', 'message_changed']:
                return {"message": "Ignored bot message or subtype"}
            
            # Only process messages in certain channels or direct messages
            channel = event.get('channel')
            if not self._should_process_slack_channel(channel):
                return {"message": "Channel not configured for processing"}
            
            # Create memory for important messages
            message_text = event.get('text', '')
            if len(message_text) < 20:  # Skip very short messages
                return {"message": "Message too short"}
            
            with get_db_context() as db:
                memory_service = MemoryService(db)
                
                memory_content = f"Slack message:\n{message_text}"
                
                # Add context about the message
                user_id = event.get('user')
                if user_id:
                    memory_content += f"\nFrom: <@{user_id}>"
                
                if channel:
                    memory_content += f"\nChannel: {channel}"
                
                memory_data = MemoryCreate(
                    assistant_id=1,  # Default assistant
                    content=memory_content,
                    memory_type="conversation",
                    importance=4,
                    tags="slack, conversation",
                    source="slack_webhook",
                    context=f"Slack channel: {channel}"
                )
                
                memory = await memory_service.create_memory(memory_data)
                
                return {
                    "memory_id": memory.id,
                    "message": "Slack message processed"
                }
            
        except Exception as e:
            logger.error(f"Slack webhook handling failed: {e}")
            raise
    
    async def _handle_calendar_event(self, payload: Dict[str, Any], request: Optional[Request] = None) -> Dict[str, Any]:
        """Handle calendar event webhook"""
        try:
            event = payload.get('event', {})
            event_type = payload.get('type', 'unknown')
            
            # Only process certain event types
            if event_type not in ['event_created', 'event_updated', 'event_cancelled']:
                return {"message": f"Event type {event_type} not processed"}
            
            # Extract event details
            title = event.get('title', 'Untitled Event')
            description = event.get('description', '')
            start_time = event.get('start_time')
            end_time = event.get('end_time')
            attendees = event.get('attendees', [])
            
            # Create memory for the event
            with get_db_context() as db:
                memory_service = MemoryService(db)
                
                memory_content = f"Calendar event {event_type}: {title}\n"
                
                if description:
                    memory_content += f"Description: {description}\n"
                
                if start_time:
                    memory_content += f"Start: {start_time}\n"
                
                if end_time:
                    memory_content += f"End: {end_time}\n"
                
                if attendees:
                    memory_content += f"Attendees: {', '.join(attendees[:5])}"
                    if len(attendees) > 5:
                        memory_content += f" and {len(attendees) - 5} more"
                
                importance = 7 if event_type == 'event_created' else 5
                
                memory_data = MemoryCreate(
                    assistant_id=1,  # Default assistant
                    content=memory_content,
                    memory_type="task",
                    importance=importance,
                    tags="calendar, meeting, schedule",
                    source="calendar_webhook",
                    context=f"Calendar event: {event_type}"
                )
                
                memory = await memory_service.create_memory(memory_data)
                
                return {
                    "memory_id": memory.id,
                    "event_type": event_type,
                    "message": "Calendar event processed"
                }
            
        except Exception as e:
            logger.error(f"Calendar webhook handling failed: {e}")
            raise
    
    async def _handle_note_taking_app(self, payload: Dict[str, Any], request: Optional[Request] = None) -> Dict[str, Any]:
        """Handle note-taking app webhook (Notion, Obsidian, etc.)"""
        try:
            note = payload.get('note', {})
            action = payload.get('action', 'created')
            
            title = note.get('title', 'Untitled Note')
            content = note.get('content', '')
            tags = note.get('tags', [])
            created_at = note.get('created_at')
            
            # Skip empty notes
            if not content or len(content.strip()) < 10:
                return {"message": "Note content too short"}
            
            # Create memory for the note
            with get_db_context() as db:
                memory_service = MemoryService(db)
                
                memory_content = f"Note: {title}\n\n{content}"
                
                # Determine importance based on content length and tags
                importance = 5
                if len(content) > 1000:
                    importance += 1
                if any(tag.lower() in ['important', 'urgent', 'todo'] for tag in tags):
                    importance += 2
                
                tag_string = ', '.join(tags) if tags else 'note'
                
                memory_data = MemoryCreate(
                    assistant_id=1,  # Default assistant
                    content=memory_content,
                    memory_type="reference",
                    importance=min(importance, 10),
                    tags=f"note, {tag_string}",
                    source="note_webhook",
                    context=f"Note {action}: {created_at}"
                )
                
                memory = await memory_service.create_memory(memory_data)
                
                return {
                    "memory_id": memory.id,
                    "action": action,
                    "message": "Note processed"
                }
            
        except Exception as e:
            logger.error(f"Note-taking webhook handling failed: {e}")
            raise
    
    async def _handle_task_update(self, payload: Dict[str, Any], request: Optional[Request] = None) -> Dict[str, Any]:
        """Handle task management system webhook"""
        try:
            task = payload.get('task', {})
            action = payload.get('action', 'updated')
            
            title = task.get('title', 'Untitled Task')
            description = task.get('description', '')
            status = task.get('status', 'unknown')
            priority = task.get('priority', 'medium')
            assignee = task.get('assignee', '')
            due_date = task.get('due_date', '')
            
            # Only process certain actions
            if action not in ['created', 'completed', 'assigned', 'high_priority']:
                return {"message": f"Task action {action} not processed"}
            
            # Create memory for the task update
            with get_db_context() as db:
                memory_service = MemoryService(db)
                
                memory_content = f"Task {action}: {title}\n"
                
                if description:
                    memory_content += f"Description: {description}\n"
                
                memory_content += f"Status: {status}\n"
                memory_content += f"Priority: {priority}\n"
                
                if assignee:
                    memory_content += f"Assignee: {assignee}\n"
                
                if due_date:
                    memory_content += f"Due: {due_date}\n"
                
                # Set importance based on priority and action
                importance_map = {
                    ('high', 'created'): 8,
                    ('high', 'completed'): 7,
                    ('medium', 'created'): 6,
                    ('medium', 'completed'): 5,
                    ('low', 'created'): 4,
                    ('low', 'completed'): 3
                }
                
                importance = importance_map.get((priority, action), 5)
                
                memory_data = MemoryCreate(
                    assistant_id=1,  # Default assistant
                    content=memory_content,
                    memory_type="task",
                    importance=importance,
                    tags=f"task, {action}, {priority}",
                    source="task_webhook",
                    context=f"Task {action}: {status}"
                )
                
                memory = await memory_service.create_memory(memory_data)
                
                return {
                    "memory_id": memory.id,
                    "action": action,
                    "priority": priority,
                    "message": "Task update processed"
                }
            
        except Exception as e:
            logger.error(f"Task webhook handling failed: {e}")
            raise
    
    async def _handle_generic_webhook(self, payload: Dict[str, Any], request: Optional[Request] = None) -> Dict[str, Any]:
        """Handle generic webhook"""
        try:
            # Extract common fields
            content = payload.get('content') or payload.get('message') or json.dumps(payload, indent=2)
            title = payload.get('title') or payload.get('subject') or 'Webhook Notification'
            source = payload.get('source') or 'generic_webhook'
            
            # Create memory for generic webhook
            with get_db_context() as db:
                memory_service = MemoryService(db)
                
                memory_content = f"Webhook notification: {title}\n\n{content}"
                
                memory_data = MemoryCreate(
                    assistant_id=1,  # Default assistant
                    content=memory_content,
                    memory_type="general",
                    importance=4,
                    tags="webhook, notification",
                    source=source,
                    context="Generic webhook payload"
                )
                
                memory = await memory_service.create_memory(memory_data)
                
                return {
                    "memory_id": memory.id,
                    "message": "Generic webhook processed"
                }
            
        except Exception as e:
            logger.error(f"Generic webhook handling failed: {e}")
            raise
    
    async def _verify_webhook_signature(self, request: Request, webhook_type: str) -> bool:
        """Verify webhook signature"""
        try:
            # This is a basic implementation - would need to be customized per service
            signature_header = request.headers.get('x-hub-signature-256')
            if not signature_header:
                return False
            
            # Get the raw body
            body = await request.body()
            
            # Get the secret for this webhook type (would be configured)
            secret = self._get_webhook_secret(webhook_type)
            if not secret:
                return False
            
            # Calculate expected signature
            expected_signature = 'sha256=' + hmac.new(
                secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature_header, expected_signature)
            
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False
    
    def _requires_signature_verification(self, webhook_type: str) -> bool:
        """Check if webhook type requires signature verification"""
        # Configure which webhook types require signature verification
        requiring_verification = {'github_push', 'slack_message'}
        return webhook_type in requiring_verification
    
    def _get_webhook_secret(self, webhook_type: str) -> Optional[str]:
        """Get webhook secret for signature verification"""
        # In production, this would read from secure configuration
        webhook_secrets = {
            'github_push': self.settings.secret_key,  # Would be specific GitHub secret
            'slack_message': self.settings.secret_key  # Would be specific Slack secret
        }
        return webhook_secrets.get(webhook_type)
    
    def _should_process_slack_channel(self, channel: str) -> bool:
        """Check if Slack channel should be processed"""
        # Configure which Slack channels to process
        # This could be made configurable
        processed_channels = {'general', 'important', 'notifications'}
        return channel in processed_channels
    
    async def send_webhook(self, url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Send outgoing webhook"""
        try:
            default_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'ESM-Webhook/1.0'
            }
            
            if headers:
                default_headers.update(headers)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=default_headers,
                    timeout=30.0
                )
                
                return {
                    "status_code": response.status_code,
                    "success": 200 <= response.status_code < 300,
                    "response": response.text if len(response.text) < 1000 else response.text[:1000] + "...",
                    "url": url
                }
                
        except Exception as e:
            logger.error(f"Failed to send webhook to {url}: {e}")
            return {
                "status_code": 0,
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def register_handler(self, webhook_type: str, handler: Callable):
        """Register custom webhook handler"""
        self.registered_handlers[webhook_type] = handler
        logger.info(f"Registered custom handler for webhook type: {webhook_type}")
    
    def list_handlers(self) -> Dict[str, str]:
        """List registered webhook handlers"""
        return {
            webhook_type: handler.__name__ 
            for webhook_type, handler in self.registered_handlers.items()
        }
