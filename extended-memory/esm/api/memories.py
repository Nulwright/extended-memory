"""Memory Management API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from esm.database import get_db
from esm.schemas import (
    MemoryCreate, MemoryUpdate, MemoryResponse, 
    SearchRequest, SearchResponse
)
from esm.services.memory_service import MemoryService
from esm.api.dependencies import (
    get_memory_service, get_pagination_params, 
    get_filter_params, PaginationParams, FilterParams
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory_data: MemoryCreate,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Create a new memory"""
    try:
        memory = await memory_service.create_memory(memory_data)
        logger.info(f"Created memory {memory.id} for assistant {memory.assistant_id}")
        return memory
    except Exception as e:
        logger.error(f"Failed to create memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create memory"
        )


@router.get("/", response_model=List[MemoryResponse])
async def list_memories(
    assistant_id: Optional[int] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    filters: FilterParams = Depends(get_filter_params),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """List memories with filtering and pagination"""
    try:
        memories = await memory_service.list_memories(
            assistant_id=assistant_id,
            skip=pagination.skip,
            limit=pagination.limit,
            memory_type=filters.memory_type,
            min_importance=filters.min_importance,
            max_importance=filters.max_importance,
            tags=filters.tags,
            include_shared=filters.include_shared
        )
        return memories
    except Exception as e:
        logger.error(f"Failed to list memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memories"
        )


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: int,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get a specific memory by ID"""
    try:
        memory = await memory_service.get_memory(memory_id)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with ID {memory_id} not found"
            )
        return memory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memory"
        )


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: int,
    memory_data: MemoryUpdate,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Update a memory"""
    try:
        memory = await memory_service.update_memory(memory_id, memory_data)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with ID {memory_id} not found"
            )
        logger.info(f"Updated memory {memory_id}")
        return memory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update memory"
        )


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: int,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Delete a memory"""
    try:
        success = await memory_service.delete_memory(memory_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with ID {memory_id} not found"
            )
        logger.info(f"Deleted memory {memory_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory"
        )


@router.get("/{memory_id}/related", response_model=List[MemoryResponse])
async def get_related_memories(
    memory_id: int,
    limit: int = Query(5, ge=1, le=20),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get memories related to a specific memory"""
    try:
        related_memories = await memory_service.get_related_memories(memory_id, limit)
        return related_memories
    except Exception as e:
        logger.error(f"Failed to get related memories for {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve related memories"
        )


@router.post("/{memory_id}/access")
async def record_memory_access(
    memory_id: int,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Record that a memory was accessed"""
    try:
        await memory_service.record_access(memory_id)
        return {"message": "Access recorded"}
    except Exception as e:
        logger.error(f"Failed to record access for memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record access"
        )


@router.get("/assistant/{assistant_id}/stats")
async def get_memory_stats(
    assistant_id: int,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get memory statistics for an assistant"""
    try:
        stats = await memory_service.get_memory_stats(assistant_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get memory stats for assistant {assistant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memory statistics"
        )


@router.post("/bulk-create", response_model=List[MemoryResponse])
async def bulk_create_memories(
    memories_data: List[MemoryCreate],
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Create multiple memories at once"""
    if len(memories_data) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create more than 100 memories at once"
        )
    
    try:
        memories = await memory_service.bulk_create_memories(memories_data)
        logger.info(f"Bulk created {len(memories)} memories")
        return memories
    except Exception as e:
        logger.error(f"Failed to bulk create memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create memories"
        )


@router.delete("/bulk-delete")
async def bulk_delete_memories(
    memory_ids: List[int],
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Delete multiple memories at once"""
    if len(memory_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete more than 100 memories at once"
        )
    
    try:
        deleted_count = await memory_service.bulk_delete_memories(memory_ids)
        logger.info(f"Bulk deleted {deleted_count} memories")
        return {"deleted_count": deleted_count}
    except Exception as e:
        logger.error(f"Failed to bulk delete memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memories"
        )