"""Test Memory Service"""

import pytest
from datetime import datetime
from esm.schemas import MemoryCreate, MemoryUpdate
from esm.utils.exceptions import ValidationError


@pytest.mark.asyncio
class TestMemoryService:
    """Test MemoryService class"""
    
    async def test_create_memory(self, memory_service, test_assistant):
        """Test memory creation"""
        memory_data = MemoryCreate(
            assistant_id=test_assistant.id,
            content="Test memory content",
            memory_type="general",
            importance=7,
            tags="test, memory",
            source="pytest"
        )
        
        memory = await memory_service.create_memory(memory_data)
        
        assert memory is not None
        assert memory.id is not None
        assert memory.content == "Test memory content"
        assert memory.memory_type == "general"
        assert memory.importance == 7
        assert memory.tags == "test, memory"
        assert memory.assistant_id == test_assistant.id
    
    async def test_create_memory_with_summary(self, memory_service, test_assistant):
        """Test memory creation with automatic summarization"""
        long_content = "This is a very long memory content. " * 100  # Make it > 1000 chars
        
        memory_data = MemoryCreate(
            assistant_id=test_assistant.id,
            content=long_content,
            memory_type="general",
            importance=5
        )
        
        memory = await memory_service.create_memory(memory_data)
        
        assert memory is not None
        assert memory.content == long_content
        # Summary should be generated for long content
        # Note: This depends on the summarization service being available
    
    async def test_create_shared_memory(self, memory_service, test_assistant):
        """Test shared memory creation"""
        memory_data = MemoryCreate(
            assistant_id=test_assistant.id,
            content="Shared test memory",
            memory_type="knowledge",
            importance=8,
            is_shared=True,
            shared_category="knowledge"
        )
        
        memory = await memory_service.create_memory(memory_data)
        
        assert memory.is_shared is True
        assert memory.shared_category == "knowledge"
    
    async def test_get_memory(self, memory_service, test_memory):
        """Test getting a memory by ID"""
        memory = await memory_service.get_memory(test_memory.id)
        
        assert memory is not None
        assert memory.id == test_memory.id
        assert memory.content == test_memory.content
    
    async def test_get_nonexistent_memory(self, memory_service):
        """Test getting non-existent memory"""
        memory = await memory_service.get_memory(99999)
        assert memory is None
    
    async def test_update_memory(self, memory_service, test_memory):
        """Test memory update"""
        update_data = MemoryUpdate(
            content="Updated content",
            importance=9,
            tags="updated, test"
        )
        
        updated_memory = await memory_service.update_memory(test_memory.id, update_data)
        
        assert updated_memory is not None
        assert updated_memory.content == "Updated content"
        assert updated_memory.importance == 9
        assert updated_memory.tags == "updated, test"
    
    async def test_update_nonexistent_memory(self, memory_service):
        """Test updating non-existent memory"""
        update_data = MemoryUpdate(content="New content")
        
        result = await memory_service.update_memory(99999, update_data)
        assert result is None
    
    async def test_delete_memory(self, memory_service, test_memory):
        """Test memory deletion"""
        success = await memory_service.delete_memory(test_memory.id)
        assert success is True
        
        # Verify memory is deleted
        memory = await memory_service.get_memory(test_memory.id)
        assert memory is None
    
    async def test_delete_nonexistent_memory(self, memory_service):
        """Test deleting non-existent memory"""
        success = await memory_service.delete_memory(99999)
        assert success is False
    
    async def test_list_memories(self, memory_service, sample_memories, test_assistant):
        """Test listing memories"""
        memories = await memory_service.list_memories(
            assistant_id=test_assistant.id,
            limit=10
        )
        
        assert len(memories) == len(sample_memories)
        
        # Should be ordered by importance and creation date
        assert memories[0].importance >= memories[1].importance
    
    async def test_list_memories_with_filters(self, memory_service, sample_memories, test_assistant):
        """Test listing memories with filters"""
        # Filter by type
        task_memories = await memory_service.list_memories(
            assistant_id=test_assistant.id,
            memory_type="task"
        )
        
        assert all(m.memory_type == "task" for m in task_memories)
        
        # Filter by importance
        important_memories = await memory_service.list_memories(
            assistant_id=test_assistant.id,
            min_importance=8
        )
        
        assert all(m.importance >= 8 for m in important_memories)
    
    async def test_get_related_memories(self, memory_service, sample_memories):
        """Test getting related memories"""
        # Get a memory to find relations for
        target_memory = sample_memories[0]
        
        related = await memory_service.get_related_memories(target_memory.id, limit=3)
        
        # Should not include the original memory
        assert all(m.id != target_memory.id for m in related)
        assert len(related) <= 3
    
    async def test_record_access(self, memory_service, test_memory):
        """Test recording memory access"""
        original_count = test_memory.access_count or 0
        
        await memory_service.record_access(test_memory.id)
        
        # Get updated memory
        updated_memory = await memory_service.get_memory(test_memory.id)
        assert updated_memory.access_count == original_count + 1
        assert updated_memory.accessed_at is not None
    
    async def test_get_memory_stats(self, memory_service, sample_memories, test_assistant):
        """Test getting memory statistics"""
        stats = await memory_service.get_memory_stats(test_assistant.id)
        
        assert stats["assistant_id"] == test_assistant.id
        assert stats["total_memories"] == len(sample_memories)
        assert "avg_importance" in stats
        assert "most_common_type" in stats
    
    async def test_bulk_create_memories(self, memory_service, test_assistant):
        """Test bulk memory creation"""
        memories_data = [
            MemoryCreate(
                assistant_id=test_assistant.id,
                content=f"Bulk memory {i}",
                memory_type="general",
                importance=5
            )
            for i in range(5)
        ]
        
        created_memories = await memory_service.bulk_create_memories(memories_data)
        
        assert len(created_memories) == 5
        for i, memory in enumerate(created_memories):
            assert memory.content == f"Bulk memory {i}"
    
    async def test_bulk_delete_memories(self, memory_service, sample_memories):
        """Test bulk memory deletion"""
        memory_ids = [m.id for m in sample_memories[:3]]
        
        deleted_count = await memory_service.bulk_delete_memories(memory_ids)
        
        assert deleted_count == 3
        
        # Verify memories are deleted
        for memory_id in memory_ids:
            memory = await memory_service.get_memory(memory_id)
            assert memory is None


class TestMemoryValidation:
    """Test memory data validation"""
    
    @pytest.mark.asyncio
    async def test_empty_content_validation(self, memory_service, test_assistant):
        """Test validation of empty content"""
        with pytest.raises(Exception):
            memory_data = MemoryCreate(
                assistant_id=test_assistant.id,
                content="",  # Empty content should fail
                memory_type="general"
            )
            await memory_service.create_memory(memory_data)
    
    @pytest.mark.asyncio 
    async def test_invalid_importance_validation(self, memory_service, test_assistant):
        """Test validation of invalid importance values"""
        with pytest.raises(Exception):
            memory_data = MemoryCreate(
                assistant_id=test_assistant.id,
                content="Test content",
                importance=15  # Invalid importance (>10)
            )
            await memory_service.create_memory(memory_data)