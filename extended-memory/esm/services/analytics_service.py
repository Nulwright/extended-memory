python"""Analytics Service for Memory and Usage Statistics"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, text
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from esm.models import Memory, Assistant, MemoryStats, SearchLog, SharedMemory
from esm.schemas import MemoryStatsResponse, SearchAnalytics, SystemStats
from esm.database import get_db_context

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics and reporting"""
    
    async def get_system_stats(self) -> SystemStats:
        """Get overall system statistics"""
        try:
            with get_db_context() as db:
                # Basic counts
                total_assistants = db.query(Assistant).count()
                total_memories = db.query(Memory).count()
                total_shared_memories = db.query(Memory).filter(Memory.is_shared == True).count()
                
                # Today's searches
                today = datetime.utcnow().date()
                total_searches_today = db.query(SearchLog).filter(
                    func.date(SearchLog.created_at) == today
                ).count()
                
                # Average importance
                avg_importance_result = db.query(func.avg(Memory.importance)).scalar()
                avg_memory_importance = float(avg_importance_result) if avg_importance_result else 0.0
                
                # Memory type distribution
                memory_type_stats = db.query(
                    Memory.memory_type,
                    func.count(Memory.id).label('count')
                ).group_by(Memory.memory_type).all()
                
                memory_type_distribution = {mt[0]: mt[1] for mt in memory_type_stats}
                
                # Shared category distribution
                shared_category_stats = db.query(
                    Memory.shared_category,
                    func.count(Memory.id).label('count')
                ).filter(
                    and_(Memory.is_shared == True, Memory.shared_category.isnot(None))
                ).group_by(Memory.shared_category).all()
                
                shared_category_distribution = {sc[0]: sc[1] for sc in shared_category_stats}
                
                return SystemStats(
                    total_assistants=total_assistants,
                    total_memories=total_memories,
                    total_shared_memories=total_shared_memories,
                    total_searches_today=total_searches_today,
                    avg_memory_importance=avg_memory_importance,
                    memory_type_distribution=memory_type_distribution,
                    shared_category_distribution=shared_category_distribution
                )
                
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            raise
    
    async def get_assistant_stats(self, assistant_id: int) -> Optional[MemoryStatsResponse]:
        """Get statistics for a specific assistant"""
        try:
            with get_db_context() as db:
                # Check if assistant exists
                assistant = db.query(Assistant).filter(Assistant.id == assistant_id).first()
                if not assistant:
                    return None
                
                # Basic memory counts
                total_memories = db.query(Memory).filter(Memory.assistant_id == assistant_id).count()
                total_shared_memories = db.query(Memory).filter(
                    and_(Memory.assistant_id == assistant_id, Memory.is_shared == True)
                ).count()
                
                # Average importance
                avg_importance_result = db.query(func.avg(Memory.importance)).filter(
                    Memory.assistant_id == assistant_id
                ).scalar()
                avg_importance = float(avg_importance_result) if avg_importance_result else 5.0
                
                # Most used memory type
                most_used_type_result = db.query(
                    Memory.memory_type,
                    func.count(Memory.id).label('count')
                ).filter(Memory.assistant_id == assistant_id).group_by(
                    Memory.memory_type
                ).order_by(desc('count')).first()
                
                most_used_type = most_used_type_result[0] if most_used_type_result else None
                
                # Today's activity
                today = datetime.utcnow().date()
                memories_created_today = db.query(Memory).filter(
                    and_(
                        Memory.assistant_id == assistant_id,
                        func.date(Memory.created_at) == today
                    )
                ).count()
                
                memories_accessed_today = db.query(Memory).filter(
                    and_(
                        Memory.assistant_id == assistant_id,
                        func.date(Memory.accessed_at) == today
                    )
                ).count()
                
                return MemoryStatsResponse(
                    assistant_id=assistant_id,
                    assistant_name=assistant.name,
                    total_memories=total_memories,
                    total_shared_memories=total_shared_memories,
                    avg_importance=avg_importance,
                    most_used_type=most_used_type,
                    memories_created_today=memories_created_today,
                    memories_accessed_today=memories_accessed_today,
                    date=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Failed to get assistant stats for {assistant_id}: {e}")
            raise
    
    async def get_search_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        assistant_id: Optional[int] = None
    ) -> SearchAnalytics:
        """Get search analytics for a time period"""
        try:
            with get_db_context() as db:
                # Base query
                query = db.query(SearchLog).filter(
                    and_(
                        SearchLog.created_at >= start_date,
                        SearchLog.created_at <= end_date
                    )
                )
                
                if assistant_id:
                    query = query.filter(SearchLog.assistant_id == assistant_id)
                
                searches = query.all()
                
                if not searches:
                    return SearchAnalytics(
                        total_searches=0,
                        avg_execution_time_ms=0.0,
                        most_common_queries=[],
                        search_type_distribution={},
                        results_distribution={}
                    )
                
                # Calculate metrics
                total_searches = len(searches)
                avg_execution_time = sum(s.execution_time_ms or 0 for s in searches) / total_searches
                
                # Most common queries
                query_counts = {}
                for search in searches:
                    query_counts[search.query] = query_counts.get(search.query, 0) + 1
                
                most_common_queries = [
                    {"query": query, "count": count}
                    for query, count in sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                ]
                
                # Search type distribution
                type_counts = {}
                for search in searches:
                    search_type = search.search_type or "unknown"
                    type_counts[search_type] = type_counts.get(search_type, 0) + 1
                
                # Results distribution (bucketed)
                result_buckets = {"0": 0, "1-5": 0, "6-20": 0, "21+": 0}
                for search in searches:
                    count = search.results_count or 0
                    if count == 0:
                        result_buckets["0"] += 1
                    elif count <= 5:
                        result_buckets["1-5"] += 1
                    elif count <= 20:
                        result_buckets["6-20"] += 1
                    else:
                        result_buckets["21+"] += 1
                
                return SearchAnalytics(
                    total_searches=total_searches,
                    avg_execution_time_ms=avg_execution_time,
                    most_common_queries=most_common_queries,
                    search_type_distribution=type_counts,
                    results_distribution=result_buckets
                )
                
        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            raise
    
    async def get_memory_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        assistant_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get memory creation and access trends over time"""
        try:
            with get_db_context() as db:
                # Daily memory creation
                creation_query = db.query(
                    func.date(Memory.created_at).label('date'),
                    func.count(Memory.id).label('created_count')
                ).filter(
                    and_(
                        Memory.created_at >= start_date,
                        Memory.created_at <= end_date
                    )
                ).group_by(func.date(Memory.created_at))
                
                if assistant_id:
                    creation_query = creation_query.filter(Memory.assistant_id == assistant_id)
                
                creation_data = creation_query.all()
                
                # Daily memory access
                access_query = db.query(
                    func.date(Memory.accessed_at).label('date'),
                    func.count(Memory.id).label('access_count')
                ).filter(
                    and_(
                        Memory.accessed_at >= start_date,
                        Memory.accessed_at <= end_date
                    )
                ).group_by(func.date(Memory.accessed_at))
                
                if assistant_id:
                    access_query = access_query.filter(Memory.assistant_id == assistant_id)
                
                access_data = access_query.all()
                
                # Combine data by date
                trends = {}
                
                for date, count in creation_data:
                    trends[str(date)] = {"date": str(date), "created": count, "accessed": 0}
                
                for date, count in access_data:
                    if str(date) in trends:
                        trends[str(date)]["accessed"] = count
                    else:
                        trends[str(date)] = {"date": str(date), "created": 0, "accessed": count}
                
                # Sort by date
                sorted_trends = sorted(trends.values(), key=lambda x: x["date"])
                
                return sorted_trends
                
        except Exception as e:
            logger.error(f"Failed to get memory trends: {e}")
            return []
    
    async def get_top_memories(
        self,
        metric: str = "access_count",
        limit: int = 10,
        assistant_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get top memories by various metrics"""
        try:
            with get_db_context() as db:
                query = db.query(Memory)
                
                if assistant_id:
                    query = query.filter(Memory.assistant_id == assistant_id)
                
                # Order by specified metric
                if metric == "access_count":
                    query = query.order_by(desc(Memory.access_count))
                elif metric == "importance":
                    query = query.order_by(desc(Memory.importance))
                elif metric == "recent":
                    query = query.order_by(desc(Memory.created_at))
                else:
                    query = query.order_by(desc(Memory.access_count))
                
                memories = query.limit(limit).all()
                
                return [
                    {
                        "id": memory.id,
                        "content_preview": memory.content[:150] + "..." if len(memory.content) > 150 else memory.content,
                        "memory_type": memory.memory_type,
                        "importance": memory.importance,
                        "access_count": memory.access_count or 0,
                        "is_shared": memory.is_shared,
                        "shared_category": memory.shared_category,
                        "created_at": memory.created_at,
                        "accessed_at": memory.accessed_at
                    }
                    for memory in memories
                ]
                
        except Exception as e:
            logger.error(f"Failed to get top memories: {e}")
            return []
    
    async def get_tag_analytics(
        self,
        limit: int = 20,
        assistant_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get tag usage analytics"""
        try:
            with get_db_context() as db:
                query = db.query(Memory.tags).filter(Memory.tags.isnot(None))
                
                if assistant_id:
                    query = query.filter(Memory.assistant_id == assistant_id)
                
                memories_with_tags = query.all()
                
                # Count tag occurrences
                tag_counts = {}
                tag_importance_sum = {}
                tag_access_sum = {}
                
                for (tags_str,) in memories_with_tags:
                    if tags_str:
                        # Get the full memory for additional stats
                        memory = db.query(Memory).filter(Memory.tags == tags_str).first()
                        if memory:
                            tags = [tag.strip() for tag in tags_str.split(',')]
                            for tag in tags:
                                if tag:
                                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                                    tag_importance_sum[tag] = tag_importance_sum.get(tag, 0) + memory.importance
                                    tag_access_sum[tag] = tag_access_sum.get(tag, 0) + (memory.access_count or 0)
                
                # Calculate analytics for each tag
                tag_analytics = []
                for tag, count in tag_counts.items():
                    avg_importance = tag_importance_sum[tag] / count
                    total_accesses = tag_access_sum[tag]
                    
                    tag_analytics.append({
                        "tag": tag,
                        "usage_count": count,
                        "avg_importance": round(avg_importance, 2),
                        "total_accesses": total_accesses,
                        "avg_accesses": round(total_accesses / count, 2) if count > 0 else 0
                    })
                
                # Sort by usage count
                tag_analytics.sort(key=lambda x: x["usage_count"], reverse=True)
                
                return tag_analytics[:limit]
                
        except Exception as e:
            logger.error(f"Failed to get tag analytics: {e}")
            return []
    
    async def get_shared_analytics(self) -> Dict[str, Any]:
        """Get shared memory analytics"""
        try:
            with get_db_context() as db:
                # Basic shared memory stats
                total_shared = db.query(Memory).filter(Memory.is_shared == True).count()
                total_memories = db.query(Memory).count()
                
                sharing_percentage = (total_shared / total_memories * 100) if total_memories > 0 else 0
                
                # Category breakdown
                category_stats = db.query(
                    Memory.shared_category,
                    func.count(Memory.id).label('count'),
                    func.avg(Memory.importance).label('avg_importance')
                ).filter(
                    and_(Memory.is_shared == True, Memory.shared_category.isnot(None))
                ).group_by(Memory.shared_category).all()
                
                category_breakdown = [
                    {
                        "category": cat[0],
                        "count": cat[1],
                        "avg_importance": round(float(cat[2]), 2) if cat[2] else 0
                    }
                    for cat in category_stats
                ]
                
                # Most accessed shared memories
                top_shared = db.query(Memory).filter(
                    Memory.is_shared == True
                ).order_by(desc(Memory.access_count)).limit(5).all()
                
                # Recent sharing activity
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_shared = db.query(Memory).filter(
                    and_(
                        Memory.is_shared == True,
                        Memory.updated_at >= week_ago
                    )
                ).count()
                
                return {
                    "total_shared_memories": total_shared,
                    "total_memories": total_memories,
                    "sharing_percentage": round(sharing_percentage, 2),
                    "category_breakdown": category_breakdown,
                    "recently_shared_week": recent_shared,
                    "top_accessed_shared": [
                        {
                            "id": m.id,
                            "content_preview": m.content[:100] + "..." if len(m.content) > 100 else m.content,
                            "access_count": m.access_count or 0,
                            "category": m.shared_category,
                            "importance": m.importance
                        }
                        for m in top_shared
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get shared analytics: {e}")
            return {}
    
    async def get_daily_activity(
        self,
        start_date: datetime,
        end_date: datetime,
        assistant_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get daily activity statistics"""
        try:
            with get_db_context() as db:
                # Generate date range
                current_date = start_date.date()
                end_date_only = end_date.date()
                activity_data = []
                
                while current_date <= end_date_only:
                    # Memories created
                    created_query = db.query(Memory).filter(
                        func.date(Memory.created_at) == current_date
                    )
                    
                    # Memories accessed
                    accessed_query = db.query(Memory).filter(
                        func.date(Memory.accessed_at) == current_date
                    )
                    
                    # Searches performed
                    searches_query = db.query(SearchLog).filter(
                        func.date(SearchLog.created_at) == current_date
                    )
                    
                    if assistant_id:
                        created_query = created_query.filter(Memory.assistant_id == assistant_id)
                        accessed_query = accessed_query.filter(Memory.assistant_id == assistant_id)
                        searches_query = searches_query.filter(SearchLog.assistant_id == assistant_id)
                    
                    memories_created = created_query.count()
                    memories_accessed = accessed_query.count()
                    searches_performed = searches_query.count()
                    
                    activity_data.append({
                        "date": str(current_date),
                        "memories_created": memories_created,
                        "memories_accessed": memories_accessed,
                        "searches_performed": searches_performed,
                        "total_activity": memories_created + memories_accessed + searches_performed
                    })
                    
                    current_date += timedelta(days=1)
                
                return activity_data
                
        except Exception as e:
            logger.error(f"Failed to get daily activity: {e}")
            return []

