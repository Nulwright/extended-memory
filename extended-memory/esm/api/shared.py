"""Shared Memory API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import logging

from esm.schemas import MemoryResponse, SharedCategory
from esm.services.shared_service import SharedService
from esm.api.dependencies import get_pagination_params, PaginationParams

router = APIRouter()
logger = logging.getLogger(__name__)


def get_shared_service() -> SharedService:
    """Get shared service dependency"""
    return SharedService()


@router.get("/", response_model=List[MemoryResponse])
async def list_shared_memories(
    category: Optional[SharedCategory] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    shared_service: SharedService = Depends(get_shared_service)
):
    """List shared memories"""
    try:
        memories = await shared_service.list_shared_memories(
            category=category,
            skip=pagination.skip,
            limit=pagination.limit
        )
        return memories
    except Exception as e:
        logger.error(f"Failed to list shared memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shared memories"
        )


@router.get("/categories")
async def get_shared_categories(
    shared_service: SharedService = Depends(get_shared_service)
):
    """Get all shared memory categories with counts"""
    try:
        categories = await shared_service.get_shared_categories()
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Failed to get shared categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get shared categories"
        )


@router.post("/{memory_id}/share")
async def share_memory(
    memory_id: int,
    category: SharedCategory,
    shared_service: SharedService = Depends(get_shared_service)
):
    """Share a memory"""
    try:
        result = await shared_service.share_memory(memory_id, category)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with ID {memory_id} not found"
            )
        logger.info(f"Shared memory {memory_id} in category {category}")
        return {"message": "Memory shared successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to share memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to share memory"
        )


@router.delete("/{memory_id}/unshare")
async def unshare_memory(
    memory_id: int,
    shared_service: SharedService = Depends(get_shared_service)
):
    """Unshare a memory"""
    try:
        result = await shared_service.unshare_memory(memory_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with ID {memory_id} not found or not shared"
            )
        logger.info(f"Unshared memory {memory_id}")
        return {"message": "Memory unshared successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unshare memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unshare memory"
        )


@router.get("/{memory_id}/access-history")
async def get_access_history(
    memory_id: int,
    shared_service: SharedService = Depends(get_shared_service)
):
    """Get access history for a shared memory"""
    try:
        history = await shared_service.get_access_history(memory_id)
        return {"access_history": history}
    except Exception as e:
        logger.error(f"Failed to get access history for memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get access history"
        )


@router.get("/most-accessed")
async def get_most_accessed_shared(
    limit: int = Query(10, ge=1, le=50),
    shared_service: SharedService = Depends(get_shared_service)
):
    """Get most accessed shared memories"""
    try:
        memories = await shared_service.get_most_accessed_shared(limit)
        return {"most_accessed": memories}
    except Exception as e:
        logger.error(f"Failed to get most accessed shared memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get most accessed memories"
        )


@router.get("/recent")
async def get_recently_shared(
    limit: int = Query(10, ge=1, le=50),
    shared_service: SharedService = Depends(get_shared_service)
):
    """Get recently shared memories"""
    try:
        memories = await shared_service.get_recently_shared(limit)
        return {"recently_shared": memories}
    except Exception as e:
        logger.error(f"Failed to get recently shared memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recently shared memories"
        )