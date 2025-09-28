"""Text Summarization Service"""

import asyncio
import logging
import openai
from typing import Optional
from functools import lru_cache

from esm.config import get_settings
from esm.utils.text_processing import clean_and_process_text

logger = logging.getLogger(__name__)


class SummarizationService:
    """Service for text summarization"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        if self.settings.openai_api_key:
            openai.api_key = self.settings.openai_api_key
            self.client = openai
            logger.info("Summarization client initialized")
        else:
            logger.warning("OpenAI API key not provided, summarization will use fallback method")
    
    async def summarize_text(self, text: str, max_length: int = 200) -> Optional[str]:
        """Summarize text using AI or extractive method"""
        try:
            # Clean and process text
            processed_text = clean_and_process_text(text)
            
            # Skip summarization for short text
            if len(processed_text) < 300:
                return None
            
            # Use AI summarization if available
            if self.client:
                return await self._ai_summarize(processed_text, max_length)
            else:
                return self._extractive_summarize(processed_text, max_length)
                
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return self._extractive_summarize(text, max_length)
    
    async def _ai_summarize(self, text: str, max_length: int) -> Optional[str]:
        """Use OpenAI for AI-powered summarization"""
        try:
            # Truncate text if too long
            if len(text) > 12000:  # Conservative token limit
                text = text[:12000] + "..."
            
            prompt = f"""Summarize the following text in a clear, concise manner. 
Keep the summary under {max_length} characters and focus on the key points:

{text}

Summary:"""
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_length // 3,  # Rough token estimate
                temperature=0.3
            )
            
            if response and response.choices:
                summary = response.choices[0].message.content.strip()
                
                # Ensure summary is within length limit
                if len(summary) > max_length:
                    summary = summary[:max_length - 3] + "..."
                
                logger.debug(f"AI generated summary: {len(summary)} chars")
                return summary
            
            logger.error("No summary in AI response")
            return None
            
        except Exception as e:
            logger.error(f"AI summarization failed: {e}")
            return None
    
    @lru_cache(maxsize=100)
    def _extractive_summarize(self, text: str, max_length: int) -> str:
        """Fallback extractive summarization"""
        try:
            # Simple extractive summarization
            sentences = self._split_into_sentences(text)
            
            if not sentences:
                return text[:max_length] + ("..." if len(text) > max_length else "")
            
            # Score sentences by position and keyword density
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                # Position score (earlier sentences get higher scores)
                position_score = 1.0 - (i / len(sentences)) * 0.5
                
                # Length score (prefer medium-length sentences)
                length_score = min(len(sentence) / 100, 1.0) * 0.8
                
                # Keyword density score (simple word frequency)
                words = sentence.lower().split()
                common_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
                keyword_score = len([w for w in words if w not in common_words]) / len(words) if words else 0
                
                total_score = position_score + length_score + keyword_score
                scored_sentences.append((sentence, total_score))
            
            # Sort by score and select top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            
            # Build summary within length limit
            summary_parts = []
            current_length = 0
            
            for sentence, score in scored_sentences:
                if current_length + len(sentence) + 1 <= max_length:
                    summary_parts.append(sentence)
                    current_length += len(sentence) + 1
                else:
                    break
            
            # Join sentences in original order
            if summary_parts:
                # Restore original order
                original_positions = []
                for part in summary_parts:
                    for i, sentence in enumerate(sentences):
                        if sentence == part:
                            original_positions.append((i, part))
                            break
                
                original_positions.sort(key=lambda x: x[0])
                summary = " ".join([part for pos, part in original_positions])
            else:
                summary = sentences[0] if sentences else text[:max_length]
            
            # Ensure within length limit
            if len(summary) > max_length:
                summary = summary[:max_length - 3] + "..."
            
            logger.debug(f"Extractive summary: {len(summary)} chars")
            return summary
            
        except Exception as e:
            logger.error(f"Extractive summarization failed: {e}")
            return text[:max_length] + ("..." if len(text) > max_length else "")
    
    def _split_into_sentences(self, text: str) -> list:
        """Simple sentence splitting"""
        try:
            # Basic sentence splitting on periods, exclamation marks, question marks
            import re
            
            # Split on sentence endings followed by whitespace and capital letter
            sentences = re.split(r'[.!?]+\s+(?=[A-Z])', text)
            
            # Clean up sentences
            cleaned_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 10:  # Filter very short fragments
                    cleaned_sentences.append(sentence)
            
            return cleaned_sentences
            
        except Exception as e:
            logger.error(f"Sentence splitting failed: {e}")
            return [text]  # Return original text as single sentence
    
    async def batch_summarize(self, texts: list, max_length: int = 200) -> list:
        """Summarize multiple texts"""
        try:
            summaries = []
            
            # Process in smaller batches to respect rate limits
            batch_size = 5
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Create tasks for parallel processing
                tasks = [self.summarize_text(text, max_length) for text in batch]
                batch_summaries = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Handle exceptions
                for j, summary in enumerate(batch_summaries):
                    if isinstance(summary, Exception):
                        logger.error(f"Batch summarization failed for item {i+j}: {summary}")
                        summaries.append(None)
                    else:
                        summaries.append(summary)
                
                # Small delay between batches
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.5)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Batch summarization failed: {e}")
            return [None] * len(texts)
    
    def get_summary_stats(self, original_text: str, summary: str) -> dict:
        """Get statistics about summarization"""
        try:
            if not summary:
                return {
                    "compression_ratio": 0,
                    "original_length": len(original_text),
                    "summary_length": 0,
                    "status": "failed"
                }
            
            compression_ratio = len(summary) / len(original_text) if original_text else 0
            
            return {
                "compression_ratio": round(compression_ratio, 3),
                "original_length": len(original_text),
                "summary_length": len(summary),
                "original_sentences": len(self._split_into_sentences(original_text)),
                "summary_sentences": len(self._split_into_sentences(summary)),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate summary stats: {e}")
            return {"status": "error", "error": str(e)}


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


### 📁 PATH: esm/services/shared_service.py
```python
"""Shared Memory Service"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from esm.models import Memory, SharedMemory, Assistant
from esm.schemas import MemoryResponse, SharedCategory
from esm.database import get_db_context

logger = logging.getLogger(__name__)


class SharedService:
    """Service for shared memory management"""
    
    async def list_shared_memories(
        self,
        category: Optional[SharedCategory] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[MemoryResponse]:
        """List shared memories"""
        try:
            with get_db_context() as db:
                query = db.query(Memory).filter(Memory.is_shared == True)
                
                if category:
                    query = query.filter(Memory.shared_category == category)
                
                # Order by importance and recency
                query = query.order_by(
                    desc(Memory.importance),
                    desc(Memory.created_at)
                )
                
                memories = query.offset(skip).limit(limit).all()
                
                return [MemoryResponse.from_orm(memory) for memory in memories]
                
        except Exception as e:
            logger.error(f"Failed to list shared memories: {e}")
            raise
    
    async def get_shared_categories(self) -> List[Dict[str, Any]]:
        """Get all shared memory categories with counts"""
        try:
            with get_db_context() as db:
                categories = db.query(
                    Memory.shared_category,
                    func.count(Memory.id).label('count')
                ).filter(
                    Memory.is_shared == True,
                    Memory.shared_category.isnot(None)
                ).group_by(
                    Memory.shared_category
                ).all()
                
                return [
                    {
                        "category": cat[0],
                        "count": cat[1],
                        "display_name": self._get_category_display_name(cat[0])
                    }
                    for cat in categories
                ]
                
        except Exception as e:
            logger.error(f"Failed to get shared categories: {e}")
            return []
    
    async def share_memory(self, memory_id: int, category: SharedCategory) -> bool:
        """Share a memory with specified category"""
        try:
            with get_db_context() as db:
                memory = db.query(Memory).filter(Memory.id == memory_id).first()
                
                if not memory:
                    return False
                
                # Update memory to be shared
                memory.is_shared = True
                memory.shared_category = category
                memory.updated_at = datetime.utcnow()
                
                # Create shared memory record if it doesn't exist
                existing_shared = db.query(SharedMemory).filter(
                    SharedMemory.memory_id == memory_id
                ).first()
                
                if not existing_shared:
                    shared_memory = SharedMemory(
                        memory_id=memory_id,
                        category=category,
                        access_level="read"
                    )
                    db.add(shared_memory)
                else:
                    existing_shared.category = category
                    existing_shared.updated_at = datetime.utcnow()
                
                db.commit()
                
                logger.info(f"Shared memory {memory_id} in category {category}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to share memory {memory_id}: {e}")
            raise
    
    async def unshare_memory(self, memory_id: int) -> bool:
        """Remove memory from shared status"""
        try:
            with get_db_context() as db:
                memory = db.query(Memory).filter(Memory.id == memory_id).first()
                
                if not memory or not memory.is_shared:
                    return False
                
                # Update memory to not be shared
                memory.is_shared = False
                memory.shared_category = None
                memory.updated_at = datetime.utcnow()
                
                # Remove shared memory record
                db.query(SharedMemory).filter(SharedMemory.memory_id == memory_id).delete()
                
                db.commit()
                
                logger.info(f"Unshared memory {memory_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to unshare memory {memory_id}: {e}")
            raise
    
    async def get_access_history(self, memory_id: int) -> List[Dict[str, Any]]:
        """Get access history for a shared memory"""
        try:
            with get_db_context() as db:
                # Get shared memory record
                shared_memory = db.query(SharedMemory).filter(
                    SharedMemory.memory_id == memory_id
                ).first()
                
                if not shared_memory:
                    return []
                
                # For now, return basic access info
                # In a more complete implementation, you'd track detailed access logs
                return [
                    {
                        "memory_id": memory_id,
                        "category": shared_memory.category,
                        "access_count": shared_memory.access_count,
                        "last_accessed_by": shared_memory.last_accessed_by,
                        "created_at": shared_memory.created_at,
                        "updated_at": shared_memory.updated_at
                    }
                ]
                
        except Exception as e:
            logger.error(f"Failed to get access history for memory {memory_id}: {e}")
            return []
    
    async def get_most_accessed_shared(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most accessed shared memories"""
        try:
            with get_db_context() as db:
                results = db.query(
                    Memory,
                    SharedMemory.access_count
                ).join(
                    SharedMemory, Memory.id == SharedMemory.memory_id
                ).filter(
                    Memory.is_shared == True
                ).order_by(
                    desc(SharedMemory.access_count),
                    desc(Memory.access_count)
                ).limit(limit).all()
                
                return [
                    {
                        "memory": MemoryResponse.from_orm(memory),
                        "shared_access_count": access_count,
                        "total_access_count": memory.access_count
                    }
                    for memory, access_count in results
                ]
                
        except Exception as e:
            logger.error(f"Failed to get most accessed shared memories: {e}")
            return []
    
    async def get_recently_shared(self, limit: int = 10) -> List[MemoryResponse]:
        """Get recently shared memories"""
        try:
            with get_db_context() as db:
                memories = db.query(Memory).filter(
                    Memory.is_shared == True
                ).order_by(
                    desc(Memory.updated_at)
                ).limit(limit).all()
                
                return [MemoryResponse.from_orm(memory) for memory in memories]
                
        except Exception as e:
            logger.error(f"Failed to get recently shared memories: {e}")
            return []
    
    async def get_shared_by_category(self, category: SharedCategory, limit: int = 20) -> List[MemoryResponse]:
        """Get shared memories by category"""
        try:
            with get_db_context() as db:
                memories = db.query(Memory).filter(
                    and_(
                        Memory.is_shared == True,
                        Memory.shared_category == category
                    )
                ).order_by(
                    desc(Memory.importance),
                    desc(Memory.access_count)
                ).limit(limit).all()
                
                return [MemoryResponse.from_orm(memory) for memory in memories]
                
        except Exception as e:
            logger.error(f"Failed to get shared memories by category {category}: {e}")
            return []
    
    async def record_shared_access(self, memory_id: int, assistant_id: Optional[int] = None):
        """Record access to a shared memory"""
        try:
            with get_db_context() as db:
                shared_memory = db.query(SharedMemory).filter(
                    SharedMemory.memory_id == memory_id
                ).first()
                
                if shared_memory:
                    shared_memory.access_count = (shared_memory.access_count or 0) + 1
                    if assistant_id:
                        shared_memory.last_accessed_by = assistant_id
                    shared_memory.updated_at = datetime.utcnow()
                    
                    db.commit()
                    
                    logger.debug(f"Recorded shared access for memory {memory_id}")
                
        except Exception as e:
            logger.error(f"Failed to record shared access for memory {memory_id}: {e}")
    
    async def get_sharing_stats(self) -> Dict[str, Any]:
        """Get overall sharing statistics"""
        try:
            with get_db_context() as db:
                # Total shared memories
                total_shared = db.query(Memory).filter(Memory.is_shared == True).count()
                
                # Category distribution
                category_stats = db.query(
                    Memory.shared_category,
                    func.count(Memory.id).label('count')
                ).filter(
                    Memory.is_shared == True,
                    Memory.shared_category.isnot(None)
                ).group_by(
                    Memory.shared_category
                ).all()
                
                # Top shared memories by access
                top_shared = db.query(Memory).filter(
                    Memory.is_shared == True
                ).order_by(
                    desc(Memory.access_count)
                ).limit(5).all()
                
                # Recent sharing activity
                from datetime import timedelta
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_shared = db.query(Memory).filter(
                    and_(
                        Memory.is_shared == True,
                        Memory.updated_at >= week_ago
                    )
                ).count()
                
                return {
                    "total_shared_memories": total_shared,
                    "category_distribution": {cat[0]: cat[1] for cat in category_stats},
                    "recently_shared_week": recent_shared,
                    "top_accessed": [
                        {
                            "id": m.id,
                            "content_preview": m.content[:100] + "..." if len(m.content) > 100 else m.content,
                            "access_count": m.access_count,
                            "category": m.shared_category
                        }
                        for m in top_shared
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get sharing stats: {e}")
            return {}
    
    def _get_category_display_name(self, category: str) -> str:
        """Get display name for category"""
        display_names = {
            "knowledge": "📚 Knowledge Base",
            "tasks": "✅ Tasks & Reminders", 
            "projects": "🚀 Projects",
            "contacts": "👤 Contacts",
            "resources": "🔗 Resources",
            "templates": "📋 Templates"
        }
        return display_names.get(category, category.title())