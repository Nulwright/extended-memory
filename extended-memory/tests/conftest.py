"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from esm.database import Base, get_db_session
from esm.models import Memory
from esm.services.memory_service import MemoryService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///memory://test_esm",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine):
    """Create test database session"""
    SessionLocal = async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with SessionLocal() as session:
        yield session


@pytest.fixture
def memory_service():
    """Create memory service instance"""
    return MemoryService()


@pytest.fixture
def sample_memory_data():
    """Sample memory data for testing"""
    return {
        "assistant": "sienna",
        "content": "This is a test memory for the ESM system. It contains some sample content for testing purposes.",
        "type": "note",
        "importance": 7,
        "tags": ["test", "sample", "esm"],
        "metadata": {"source": "test", "test_flag": True}
    }


@pytest.fixture
def sample_memories_data():
    """Multiple sample memories for testing"""
    return [
        {
            "assistant": "sienna",
            "content": "First test memory about databases and optimization techniques.",
            "type": "note",
            "importance": 8,
            "tags": ["database", "optimization"],
            "metadata": {"source": "test"}
        },
        {
            "assistant": "sienna", 
            "content": "Second test memory discussing API design patterns and best practices.",
            "type": "code",
            "importance": 6,
            "tags": ["api", "design", "patterns"],
            "metadata": {"source": "test"}
        },
        {
            "assistant": "vale",
            "content": "Vale's thoughtful reflection on system architecture and scalability concerns.",
            "type": "project",
            "importance": 9,
            "tags": ["architecture", "scalability"],
            "metadata": {"source": "test"}
        }
    ]