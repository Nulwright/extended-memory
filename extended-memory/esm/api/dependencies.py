"""FastAPI Dependencies"""

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional, Annotated
import logging

from esm.database import get_db
from esm.models import Assistant
from esm.services.search_service import SearchService
from esm.services.memory_service import MemoryService

logger = logging.getLogger(__name__)


def get_memory_service(db: Session = Depends(get_db)) -> MemoryService:
    """Get memory service dependency"""
    return MemoryService(db)


def get_search_service() -> SearchService:
    """Get search service dependency"""
    return SearchService()


def get_assistant_by_id(
    assistant_id: int,
    db: Session = Depends(get_db)
) -> Assistant:
    """Get assistant by ID dependency"""
    assistant = db.query(Assistant).filter(Assistant.id == assistant_id).first()
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assistant with ID {assistant_id} not found"
        )
    return assistant


def get_assistant_by_name(
    assistant_name: str,
    db: Session = Depends(get_db)
) -> Assistant:
    """Get assistant by name dependency"""
    assistant = db.query(Assistant).filter(Assistant.name == assistant_name).first()
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assistant '{assistant_name}' not found"
        )
    return assistant


def validate_api_key(
    x_api_key: Annotated[Optional[str], Header()] = None
) -> Optional[str]:
    """Validate API key (placeholder for future authentication)"""
    # For now, we'll skip API key validation
    # This can be implemented when authentication is needed
    return x_api_key


def get_current_user(
    api_key: Optional[str] = Depends(validate_api_key)
) -> dict:
    """Get current user (placeholder for future user management)"""
    # For now, return a default user
    return {"id": 1, "username": "default_user", "is_active": True}


def check_assistant_access(
    assistant: Assistant = Depends(get_assistant_by_id),
    current_user: dict = Depends(get_current_user)
) -> Assistant:
    """Check if current user has access to the assistant"""
    # For now, allow access to all assistants
    # This can be expanded with proper access control later
    if not assistant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assistant is not active"
        )
    return assistant


class PaginationParams:
    """Pagination parameters"""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 50,
    ):
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skip must be non-negative"
            )
        if limit <= 0 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 1000"
            )
        
        self.skip = skip
        self.limit = limit


def get_pagination_params(
    skip: int = 0,
    limit: int = 50
) -> PaginationParams:
    """Get pagination parameters dependency"""
    return PaginationParams(skip=skip, limit=limit)


class FilterParams:
    """Common filtering parameters"""
    
    def __init__(
        self,
        memory_type: Optional[str] = None,
        min_importance: Optional[int] = None,
        max_importance: Optional[int] = None,
        tags: Optional[str] = None,
        include_shared: bool = True
    ):
        self.memory_type = memory_type
        self.min_importance = min_importance
        self.max_importance = max_importance
        self.tags = tags.split(",") if tags else None
        self.include_shared = include_shared


def get_filter_params(
    memory_type: Optional[str] = None,
    min_importance: Optional[int] = None,
    max_importance: Optional[int] = None,
    tags: Optional[str] = None,
    include_shared: bool = True
) -> FilterParams:
    """Get filtering parameters dependency"""
    return FilterParams(
        memory_type=memory_type,
        min_importance=min_importance,
        max_importance=max_importance,
        tags=tags,
        include_shared=include_shared
    )