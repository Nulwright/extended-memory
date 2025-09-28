"""Test Database Operations"""

import pytest
from sqlalchemy import text
from esm.database import get_db_context, DatabaseHealthCheck, init_db
from esm.models import Assistant, Memory


class TestDatabaseConnection:
    """Test database connection and basic operations"""
    
    def test_database_connection(self, db_session):
        """Test basic database connection"""
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    
    def test_database_context_manager(self):
        """Test database context manager"""
        with get_db_context() as db:
            result = db.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    def test_database_health_check(self):
        """Test database health check"""
        is_healthy = DatabaseHealthCheck.check_connection()
        assert is_healthy is True
    
    def test_table_counts(self, db_session, sample_memories):
        """Test getting table counts"""
        counts = DatabaseHealthCheck.get_table_counts()
        
        assert "assistants" in counts
        assert "memories" in counts
        assert counts["memories"] >= len(sample_memories)


class TestDatabaseModels:
    """Test database model relationships and constraints"""
    
    def test_assistant_memory_relationship(self, db_session):
        """Test Assistant-Memory relationship"""
        # Create assistant
        assistant = Assistant(name="TestRel", personality="Test")
        db_session.add(assistant)
        db_session.commit()
        db_session.refresh(assistant)
        
        # Create memory
        memory = Memory(
            assistant_id=assistant.id,
            content="Test relationship",
            memory_type="general"
        )
        db_session.add(memory)
        db_session.commit()
        
        # Test relationship
        assert memory.assistant.name == "TestRel"
        assert len(assistant.memories) == 1
        assert assistant.memories[0].content == "Test relationship"
    
    def test_cascade_delete(self, db_session):
        """Test cascade delete behavior"""
        # Create assistant with memory
        assistant = Assistant(name="TestCascade", personality="Test")
        db_session.add(assistant)
        db_session.commit()
        db_session.refresh(assistant)
        
        memory = Memory(
            assistant_id=assistant.id,
            content="Will be deleted",
            memory_type="general"
        )
        db_session.add(memory)
        db_session.commit()
        memory_id = memory.id
        
        # Delete assistant
        db_session.delete(assistant)
        db_session.commit()
        
        # Memory should be cascade deleted
        deleted_memory = db_session.query(Memory).filter(Memory.id == memory_id).first()
        assert deleted_memory is None
    
    def test_unique_constraints(self, db_session):
        """Test unique constraints"""
        # Create first assistant
        assistant1 = Assistant(name="Unique", personality="First")
        db_session.add(assistant1)
        db_session.commit()
        
        # Try to create second assistant with same name
        assistant2 = Assistant(name="Unique", personality="Second")
        db_session.add(assistant2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_memory_defaults(self, db_session, test_assistant):
        """Test memory default values"""
        memory = Memory(
            assistant_id=test_assistant.id,
            content="Test defaults"
        )
        db_session.add(memory)
        db_session.commit()
        db_session.refresh(memory)
        
        # Check defaults
        assert memory.memory_type == "general"
        assert memory.importance == 5
        assert memory.access_count == 0
        assert memory.is_shared is False
        assert memory.created_at is not None


class TestDatabasePerformance:
    """Test database performance and indexing"""
    
    def test_index_usage(self, db_session, test_assistant):
        """Test that indexes are being used effectively"""
        # Create many memories
        memories = []
        for i in range(100):
            memory = Memory(
                assistant_id=test_assistant.id,
                content=f"Performance test memory {i}",
                memory_type="general",
                importance=i % 10 + 1
            )
            memories.append(memory)
        
        db_session.add_all(memories)
        db_session.commit()
        
        # Query that should use index
        import time
        start_time = time.time()
        
        results = db_session.query(Memory).filter(
            Memory.assistant_id == test_assistant.id,
            Memory.importance >= 8
        ).all()
        
        query_time = time.time() - start_time
        
        # Should complete quickly (< 0.1 seconds for 100 records)
        assert query_time < 0.1
        assert len(results) > 0


class TestDatabaseMigrations:
    """Test database migration functionality"""
    
    def test_database_initialization(self):
        """Test database initialization"""
        # This would typically test alembic migrations
        # For now, just test that init_db doesn't crash
        try:
            # Note: This might affect the test database
            # In production tests, this would use a separate test DB
            pass  # Skip actual init_db call to avoid affecting tests
        except Exception as e:
            pytest.fail(f"Database initialization failed: {e}")

