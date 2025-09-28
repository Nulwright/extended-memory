### 📁 PATH: esm/services/assistant_service.py
```python
"""Assistant Management Service"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging
from datetime import datetime

from esm.models import Assistant, Memory, MemoryStats
from esm.schemas import AssistantCreate, AssistantUpdate, AssistantResponse

logger = logging.getLogger(__name__)


class AssistantService:
    """Service for assistant management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_assistant(self, assistant_data: AssistantCreate) -> AssistantResponse:
        """Create a new assistant"""
        try:
            # Check if assistant name already exists
            existing = self.db.query(Assistant).filter(Assistant.name == assistant_data.name).first()
            if existing:
                raise ValueError(f"Assistant with name '{assistant_data.name}' already exists")
            
            # Create new assistant
            assistant = Assistant(
                name=assistant_data.name,
                personality=assistant_data.personality,
                is_active=assistant_data.is_active
            )
            
            self.db.add(assistant)
            self.db.commit()
            self.db.refresh(assistant)
            
            # Initialize memory stats
            await self._initialize_stats(assistant.id)
            
            logger.info(f"Created assistant: {assistant.name} (ID: {assistant.id})")
            return AssistantResponse.from_orm(assistant)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create assistant: {e}")
            raise
    
    async def list_assistants(self, include_inactive: bool = False) -> List[AssistantResponse]:
        """List all assistants"""
        try:
            query = self.db.query(Assistant)
            
            if not include_inactive:
                query = query.filter(Assistant.is_active == True)
            
            assistants = query.order_by(Assistant.created_at).all()
            
            return [AssistantResponse.from_orm(assistant) for assistant in assistants]
            
        except Exception as e:
            logger.error(f"Failed to list assistants: {e}")
            raise
    
    async def get_assistant(self, assistant_id: int) -> Optional[AssistantResponse]:
        """Get assistant by ID"""
        try:
            assistant = self.db.query(Assistant).filter(Assistant.id == assistant_id).first()
            
            if assistant:
                return AssistantResponse.from_orm(assistant)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get assistant {assistant_id}: {e}")
            raise
    
    async def get_assistant_by_name(self, name: str) -> Optional[AssistantResponse]:
        """Get assistant by name"""
        try:
            assistant = self.db.query(Assistant).filter(Assistant.name == name).first()
            
            if assistant:
                return AssistantResponse.from_orm(assistant)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get assistant by name '{name}': {e}")
            raise
    
    async def update_assistant(self, assistant_id: int, assistant_data: AssistantUpdate) -> Optional[AssistantResponse]:
        """Update an assistant"""
        try:
            assistant = self.db.query(Assistant).filter(Assistant.id == assistant_id).first()
            if not assistant:
                return None
            
            # Check for name conflicts if name is being updated
            if assistant_data.name and assistant_data.name != assistant.name:
                existing = self.db.query(Assistant).filter(
                    Assistant.name == assistant_data.name,
                    Assistant.id != assistant_id
                ).first()
                if existing:
                    raise ValueError(f"Assistant with name '{assistant_data.name}' already exists")
            
            # Update fields that are provided
            update_data = assistant_data.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(assistant, field, value)
            
            assistant.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(assistant)
            
            logger.info(f"Updated assistant {assistant_id}")
            return AssistantResponse.from_orm(assistant)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update assistant {assistant_id}: {e}")
            raise
    
    async def delete_assistant(self, assistant_id: int) -> bool:
        """Delete an assistant and all associated memories"""
        try:
            assistant = self.db.query(Assistant).filter(Assistant.id == assistant_id).first()
            if not assistant:
                return False
            
            # Delete associated memories (this will cascade to embeddings)
            memory_count = self.db.query(Memory).filter(Memory.assistant_id == assistant_id).count()
            self.db.query(Memory).filter(Memory.assistant_id == assistant_id).delete()
            
            # Delete memory stats
            self.db.query(MemoryStats).filter(MemoryStats.assistant_id == assistant_id).delete()
            
            # Delete the assistant
            self.db.delete(assistant)
            self.db.commit()
            
            logger.info(f"Deleted assistant {assistant_id} and {memory_count} associated memories")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete assistant {assistant_id}: {e}")
            raise
    
    async def set_assistant_status(self, assistant_id: int, is_active: bool) -> Optional[AssistantResponse]:
        """Activate or deactivate an assistant"""
        try:
            assistant = self.db.query(Assistant).filter(Assistant.id == assistant_id).first()
            if not assistant:
                return None
            
            assistant.is_active = is_active
            assistant.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(assistant)
            
            status = "activated" if is_active else "deactivated"
            logger.info(f"Assistant {assistant_id} {status}")
            
            return AssistantResponse.from_orm(assistant)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to set assistant {assistant_id} status: {e}")
            raise
    
    async def get_memory_count(self, assistant_id: int) -> int:
        """Get total memory count for an assistant"""
        try:
            count = self.db.query(Memory).filter(Memory.assistant_id == assistant_id).count()
            return count
            
        except Exception as e:
            logger.error(f"Failed to get memory count for assistant {assistant_id}: {e}")
            return 0
    
    async def get_assistant_stats(self, assistant_id: int) -> dict:
        """Get comprehensive statistics for an assistant"""
        try:
            assistant = self.db.query(Assistant).filter(Assistant.id == assistant_id).first()
            if not assistant:
                return {}
            
            # Basic counts
            total_memories = self.db.query(Memory).filter(Memory.assistant_id == assistant_id).count()
            
            shared_memories = self.db.query(Memory).filter(
                Memory.assistant_id == assistant_id,
                Memory.is_shared == True
            ).count()
            
            # Memory type distribution
            memory_types = self.db.query(
                Memory.memory_type,
                func.count(Memory.id).label('count')
            ).filter(Memory.assistant_id == assistant_id).group_by(
                Memory.memory_type
            ).all()
            
            type_distribution = {mt[0]: mt[1] for mt in memory_types}
            
            # Importance distribution
            importance_stats = self.db.query(
                func.avg(Memory.importance).label('avg_importance'),
                func.min(Memory.importance).label('min_importance'),
                func.max(Memory.importance).label('max_importance')
            ).filter(Memory.assistant_id == assistant_id).first()
            
            # Recent activity (last 30 days)
            from datetime import timedelta
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            recent_memories = self.db.query(Memory).filter(
                Memory.assistant_id == assistant_id,
                Memory.created_at >= thirty_days_ago
            ).count()
            
            recent_accesses = self.db.query(Memory).filter(
                Memory.assistant_id == assistant_id,
                Memory.accessed_at >= thirty_days_ago
            ).count()
            
            # Most accessed memories
            top_memories = self.db.query(Memory).filter(
                Memory.assistant_id == assistant_id
            ).order_by(
                Memory.access_count.desc()
            ).limit(5).all()
            
            return {
                "assistant_id": assistant_id,
                "assistant_name": assistant.name,
                "is_active": assistant.is_active,
                "created_at": assistant.created_at,
                "total_memories": total_memories,
                "shared_memories": shared_memories,
                "memory_type_distribution": type_distribution,
                "avg_importance": float(importance_stats.avg_importance) if importance_stats.avg_importance else 0.0,
                "min_importance": importance_stats.min_importance or 0,
                "max_importance": importance_stats.max_importance or 0,
                "recent_memories_30d": recent_memories,
                "recent_accesses_30d": recent_accesses,
                "top_memories": [
                    {
                        "id": m.id,
                        "content_preview": m.content[:100] + "..." if len(m.content) > 100 else m.content,
                        "access_count": m.access_count,
                        "importance": m.importance,
                        "created_at": m.created_at
                    }
                    for m in top_memories
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get assistant stats for {assistant_id}: {e}")
            return {}
    
    async def _initialize_stats(self, assistant_id: int):
        """Initialize memory statistics for a new assistant"""
        try:
            # Create initial stats record
            stats = MemoryStats(
                assistant_id=assistant_id,
                total_memories=0,
                total_shared_memories=0,
                avg_importance=5.0,
                memories_created_today=0,
                memories_accessed_today=0,
                date=datetime.utcnow()
            )
            
            self.db.add(stats)
            self.db.commit()
            
            logger.debug(f"Initialized stats for assistant {assistant_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize stats for assistant {assistant_id}: {e}")
