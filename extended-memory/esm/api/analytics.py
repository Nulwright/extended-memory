"""Analytics API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime, timedelta
from typing import Optional
import logging

from esm.schemas import MemoryStatsResponse, SearchAnalytics, SystemStats
from esm.services.analytics_service import AnalyticsService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_analytics_service() -> AnalyticsService:
    """Get analytics service dependency"""
    return AnalyticsService()


@router.get("/system", response_model=SystemStats)
async def get_system_stats(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get overall system statistics"""
    try:
        stats = await analytics_service.get_system_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics"
        )


@router.get("/assistant/{assistant_id}/stats", response_model=MemoryStatsResponse)
async def get_assistant_stats(
    assistant_id: int,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get statistics for a specific assistant"""
    try:
        stats = await analytics_service.get_assistant_stats(assistant_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assistant with ID {assistant_id} not found"
            )
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stats for assistant {assistant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve assistant statistics"
        )


@router.get("/search", response_model=SearchAnalytics)
async def get_search_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    assistant_id: Optional[int] = Query(None, description="Filter by assistant"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get search analytics"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analytics = await analytics_service.get_search_analytics(
            start_date=start_date,
            end_date=end_date,
            assistant_id=assistant_id
        )
        return analytics
    except Exception as e:
        logger.error(f"Failed to get search analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve search analytics"
        )


@router.get("/memory-trends")
async def get_memory_trends(
    days: int = Query(30, ge=1, le=365),
    assistant_id: Optional[int] = Query(None),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get memory creation and access trends"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        trends = await analytics_service.get_memory_trends(
            start_date=start_date,
            end_date=end_date,
            assistant_id=assistant_id
        )
        return {"trends": trends, "period_days": days}
    except Exception as e:
        logger.error(f"Failed to get memory trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memory trends"
        )


@router.get("/top-memories")
async def get_top_memories(
    metric: str = Query("access_count", regex="^(access_count|importance|recent)$"),
    limit: int = Query(10, ge=1, le=50),
    assistant_id: Optional[int] = Query(None),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get top memories by various metrics"""
    try:
        memories = await analytics_service.get_top_memories(
            metric=metric,
            limit=limit,
            assistant_id=assistant_id
        )
        return {"top_memories": memories, "metric": metric}
    except Exception as e:
        logger.error(f"Failed to get top memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top memories"
        )


@router.get("/tag-analytics")
async def get_tag_analytics(
    limit: int = Query(20, ge=1, le=100),
    assistant_id: Optional[int] = Query(None),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get tag usage analytics"""
    try:
        tag_stats = await analytics_service.get_tag_analytics(
            limit=limit,
            assistant_id=assistant_id
        )
        return {"tag_analytics": tag_stats}
    except Exception as e:
        logger.error(f"Failed to get tag analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tag analytics"
        )


@router.get("/shared-analytics")
async def get_shared_analytics(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get shared memory analytics"""
    try:
        shared_stats = await analytics_service.get_shared_analytics()
        return {"shared_analytics": shared_stats}
    except Exception as e:
        logger.error(f"Failed to get shared analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shared memory analytics"
        )


@router.get("/daily-activity")
async def get_daily_activity(
    days: int = Query(7, ge=1, le=90),
    assistant_id: Optional[int] = Query(None),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get daily activity statistics"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        activity = await analytics_service.get_daily_activity(
            start_date=start_date,
            end_date=end_date,
            assistant_id=assistant_id
        )
        return {"daily_activity": activity, "period_days": days}
    except Exception as e:
        logger.error(f"Failed to get daily activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve daily activity"
        )