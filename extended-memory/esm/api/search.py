"""Search API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
import logging

from esm.schemas import SearchRequest, SearchResponse, MemoryType, SearchType
from esm.services.search_service import SearchService
from esm.api.dependencies import get_search_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=SearchResponse)
async def search_memories(
    search_request: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """Search memories using hybrid keyword + semantic search"""
    try:
        results = await search_service.search_memories(search_request)
        logger.info(f"Search '{search_request.query}' returned {len(results.results)} results")
        return results
    except Exception as e:
        logger.error(f"Search failed for query '{search_request.query}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )


@router.get("/quick")
async def quick_search(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    assistant_id: Optional[int] = Query(None, description="Limit to specific assistant"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    search_type: SearchType = Query(SearchType.HYBRID, description="Type of search"),
    search_service: SearchService = Depends(get_search_service)
):
    """Quick search endpoint for simple queries"""
    try:
        search_request = SearchRequest(
            query=q,
            assistant_id=assistant_id,
            limit=limit,
            search_type=search_type
        )
        results = await search_service.search_memories(search_request)
        return results
    except Exception as e:
        logger.error(f"Quick search failed for query '{q}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Quick search failed"
        )


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=100),
    assistant_id: Optional[int] = Query(None),
    limit: int = Query(5, ge=1, le=20),
    search_service: SearchService = Depends(get_search_service)
):
    """Get search query suggestions based on existing memories"""
    try:
        suggestions = await search_service.get_search_suggestions(q, assistant_id, limit)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Failed to get search suggestions for '{q}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get search suggestions"
        )


@router.get("/recent-queries")
async def get_recent_queries(
    assistant_id: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    search_service: SearchService = Depends(get_search_service)
):
    """Get recent search queries"""
    try:
        queries = await search_service.get_recent_queries(assistant_id, limit)
        return {"recent_queries": queries}
    except Exception as e:
        logger.error(f"Failed to get recent queries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recent queries"
        )


@router.get("/popular-tags")
async def get_popular_tags(
    assistant_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    search_service: SearchService = Depends(get_search_service)
):
    """Get most popular tags"""
    try:
        tags = await search_service.get_popular_tags(assistant_id, limit)
        return {"popular_tags": tags}
    except Exception as e:
        logger.error(f"Failed to get popular tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get popular tags"
        )