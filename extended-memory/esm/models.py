"""SQLAlchemy Database Models"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

Base = declarative_base()


class Assistant(Base):
    """AI Assistant model"""
    __tablename__ = "assistants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    personality = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    memories = relationship("Memory", back_populates="assistant")
    memory_stats = relationship("MemoryStats", back_populates="assistant")


class Memory(Base):
    """Core memory storage model"""
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(Integer, ForeignKey("assistants.id"), nullable=False)
    
    # Content
    content = Column(Text, nullable=False)
    summary = Column(Text)
    memory_type = Column(String(50), default="general")
    
    # Metadata
    importance = Column(Integer, default=5)  # 1-10 scale
    tags = Column(Text)  # JSON string of tags
    source = Column(String(100))
    context = Column(Text)
    
    # Sharing
    is_shared = Column(Boolean, default=False)
    shared_category = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    accessed_at = Column(DateTime(timezone=True))
    
    # Search optimization
    access_count = Column(Integer, default=0)
    
    # Relationships
    assistant = relationship("Assistant", back_populates="memories")
    embeddings = relationship("MemoryEmbedding", back_populates="memory")
    
    # Indices for performance
    __table_args__ = (
        Index('ix_memories_assistant_type', 'assistant_id', 'memory_type'),
        Index('ix_memories_created_at', 'created_at'),
        Index('ix_memories_importance', 'importance'),
        Index('ix_memories_shared', 'is_shared', 'shared_category'),
    )


class MemoryEmbedding(Base):
    """Vector embeddings for memories"""
    __tablename__ = "memory_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False)
    
    # Vector data (stored as JSON string)
    embedding_vector = Column(Text)  # JSON array
    embedding_model = Column(String(50), default="text-embedding-ada-002")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    memory = relationship("Memory", back_populates="embeddings")


class SharedMemory(Base):
    """Shared memories accessible by multiple assistants"""
    __tablename__ = "shared_memories"
    
    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False)
    
    # Sharing metadata
    category = Column(String(50), nullable=False)
    access_level = Column(String(20), default="read")  # read, write
    
    # Usage tracking
    last_accessed_by = Column(Integer, ForeignKey("assistants.id"))
    access_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MemoryStats(Base):
    """Memory usage statistics"""
    __tablename__ = "memory_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(Integer, ForeignKey("assistants.id"), nullable=False)
    
    # Statistics
    total_memories = Column(Integer, default=0)
    total_shared_memories = Column(Integer, default=0)
    avg_importance = Column(Float, default=5.0)
    most_used_type = Column(String(50))
    
    # Activity metrics
    memories_created_today = Column(Integer, default=0)
    memories_accessed_today = Column(Integer, default=0)
    
    # Timestamps
    date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assistant = relationship("Assistant", back_populates="memory_stats")
    
    # Unique constraint
    __table_args__ = (
        Index('ix_memory_stats_assistant_date', 'assistant_id', 'date'),
    )


class SearchLog(Base):
    """Search query logging for analytics"""
    __tablename__ = "search_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(Integer, ForeignKey("assistants.id"))
    
    # Search data
    query = Column(Text, nullable=False)
    search_type = Column(String(20))  # keyword, semantic, hybrid
    results_count = Column(Integer)
    
    # Performance metrics
    execution_time_ms = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indices
    __table_args__ = (
        Index('ix_search_logs_created_at', 'created_at'),
        Index('ix_search_logs_assistant_id', 'assistant_id'),
    )