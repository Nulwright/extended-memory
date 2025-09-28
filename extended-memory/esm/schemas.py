"""Pydantic Schemas for API Request/Response Models"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MemoryType(str, Enum):
    """Memory type enumeration"""
    GENERAL = "general"
    CONVERSATION = "conversation"
    FACT = "fact"
    TASK = "task"
    PROJECT = "project"
    PERSONAL = "personal"
    CODE = "code"
    REFERENCE = "reference"


class SharedCategory(str, Enum):
    """Shared memory category enumeration"""
    KNOWLEDGE = "knowledge"
    TASKS = "tasks"
    PROJECTS = "projects"
    CONTACTS = "contacts"
    RESOURCES = "resources"
    TEMPLATES = "templates"


class SearchType(str, Enum):
    """Search type enumeration"""
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    
    class Config:
        from_attributes = True
        use_enum_values = True


# Assistant schemas
class AssistantBase(BaseSchema):
    """Base assistant schema"""
    name: str = Field(..., min_length=1, max_length=50)
    personality: Optional[str] = Field(None, max_length=1000)
    is_active: bool = True


class AssistantCreate(AssistantBase):
    """Schema for creating an assistant"""
    pass


class AssistantUpdate(BaseSchema):
    """Schema for updating an assistant"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    personality: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class AssistantResponse(AssistantBase):
    """Schema for assistant response"""
    id: int
    created_at: datetime
    updated_at: datetime


# Memory schemas
class MemoryBase(BaseSchema):
    """Base memory schema"""
    content: str = Field(..., min_length=1, max_length=50000)
    summary: Optional[str] = Field(None, max_length=1000)
    memory_type: MemoryType = MemoryType.GENERAL
    importance: int = Field(5, ge=1, le=10)
    tags: Optional[str] = Field(None, max_length=500)
    source: Optional[str] = Field(None, max_length=100)
    context: Optional[str] = Field(None, max_length=1000)
    is_shared: bool = False
    shared_category: Optional[SharedCategory] = None
    
    @validator('shared_category')
    def validate_shared_category(cls, v, values):
        """Validate shared category is provided when is_shared is True"""
        if values.get('is_shared') and not v:
            raise ValueError('shared_category is required when is_shared is True')
        if not values.get('is_shared') and v:
            raise ValueError('shared_category should not be set when is_shared is False')
        return v


class MemoryCreate(MemoryBase):
    """Schema for creating a memory"""
    assistant_id: int


class MemoryUpdate(BaseSchema):
    """Schema for updating a memory"""
    content: Optional[str] = Field(None, min_length=1, max_length=50000)
    summary: Optional[str] = Field(None, max_length=1000)
    memory_type: Optional[MemoryType] = None
    importance: Optional[int] = Field(None, ge=1, le=10)
    tags: Optional[str] = Field(None, max_length=500)
    source: Optional[str] = Field(None, max_length=100)
    context: Optional[str] = Field(None, max_length=1000)
    is_shared: Optional[bool] = None
    shared_category: Optional[SharedCategory] = None


class MemoryResponse(MemoryBase):
    """Schema for memory response"""
    id: int
    assistant_id: int
    access_count: int
    created_at: datetime
    updated_at: datetime
    accessed_at: Optional[datetime] = None
    assistant: Optional[AssistantResponse] = None


# Search schemas
class SearchRequest(BaseSchema):
    """Schema for search requests"""
    query: str = Field(..., min_length=1, max_length=500)
    assistant_id: Optional[int] = None
    memory_type: Optional[MemoryType] = None
    search_type: SearchType = SearchType.HYBRID
    limit: int = Field(10, ge=1, le=100)
    min_importance: Optional[int] = Field(None, ge=1, le=10)
    tags: Optional[List[str]] = None
    include_shared: bool = True
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class SearchResult(BaseSchema):
    """Schema for individual search result"""
    memory: MemoryResponse
    score: float = Field(..., ge=0.0, le=1.0)
    match_type: str  # "keyword", "semantic", "both"
    highlight: Optional[str] = None


class SearchResponse(BaseSchema):
    """Schema for search response"""
    results: List[SearchResult]
    total_count: int
    execution_time_ms: float
    search_type: SearchType
    query: str


# Analytics schemas
class MemoryStatsResponse(BaseSchema):
    """Schema for memory statistics"""
    assistant_id: int
    assistant_name: str
    total_memories: int
    total_shared_memories: int
    avg_importance: float
    most_used_type: Optional[str] = None
    memories_created_today: int
    memories_accessed_today: int
    date: datetime


class SearchAnalytics(BaseSchema):
    """Schema for search analytics"""
    total_searches: int
    avg_execution_time_ms: float
    most_common_queries: List[Dict[str, Any]]
    search_type_distribution: Dict[str, int]
    results_distribution: Dict[str, int]


class SystemStats(BaseSchema):
    """Schema for system statistics"""
    total_assistants: int
    total_memories: int
    total_shared_memories: int
    total_searches_today: int
    avg_memory_importance: float
    memory_type_distribution: Dict[str, int]
    shared_category_distribution: Dict[str, int]


# Export schemas
class ExportRequest(BaseSchema):
    """Schema for export requests"""
    assistant_id: Optional[int] = None
    format: str = Field("json", regex="^(json|csv|txt)$")
    include_shared: bool = True
    memory_type: Optional[MemoryType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ExportResponse(BaseSchema):
    """Schema for export response"""
    file_url: str
    file_size: int
    record_count: int
    format: str
    created_at: datetime


# WebSocket schemas
class WSMessage(BaseSchema):
    """Schema for WebSocket messages"""
    type: str  # "memory_created", "memory_updated", "search_performed"
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSConnectionInfo(BaseSchema):
    """Schema for WebSocket connection info"""
    client_id: str
    assistant_id: Optional[int] = None
    connected_at: datetime
    last_activity: datetime


# Error schemas
class ErrorResponse(BaseSchema):
    """Schema for error responses"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class ValidationErrorResponse(BaseSchema):
    """Schema for validation error responses"""
    error: str = "Validation Error"
    details: List[Dict[str, Any]]


# Health check schema
class HealthResponse(BaseSchema):
    """Schema for health check response"""
    status: str
    version: str
    timestamp: float
    database: bool
    search: bool
    dependencies: Dict[str, bool]