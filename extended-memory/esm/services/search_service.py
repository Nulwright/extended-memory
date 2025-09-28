"""Search Service for Memory Retrieval"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Tuple
import time
import json
from datetime import datetime

from esm.schemas import SearchRequest, SearchResponse, SearchResult, SearchType, MemoryResponse
from esm.database import get_db_context
from esm.models import Memory, MemoryEmbedding, SearchLog, Assistant
from esm.services.embedding_service import EmbeddingService
from esm.integrations.typesense_client import TypesenseClient
from esm.utils.text_processing import extract_keywords, highlight_text
from esm.utils.vector_utils import cosine_similarity

logger = logging.getLogger(__name__)


class SearchService:
    """Service for memory search operations"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.typesense_client = TypesenseClient()
    
    async def initialize_indices(self):
        """Initialize search indices"""
        try:
            await self.typesense_client.initialize_collections()
            logger.info("Search indices initialized")
        except Exception as e:
            logger.error(f"Failed to initialize search indices: {e}")
            raise
    
    async def search_memories(self, request: SearchRequest) -> SearchResponse:
        """Search memories using hybrid approach"""
        start_time = time.time()
        
        try:
            # Extract keywords from query
            keywords = extract_keywords(request.query)
            
            # Perform search based on type
            if request.search_type == SearchType.KEYWORD:
                results = await self._keyword_search(request, keywords)
            elif request.search_type == SearchType.SEMANTIC:
                results = await self._semantic_search(request)
            else:  # HYBRID
                results = await self._hybrid_search(request, keywords)
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000
            
            # Log search
            await self._log_search(request, len(results), execution_time)
            
            # Create response
            response = SearchResponse(
                results=results,
                total_count=len(results),
                execution_time_ms=execution_time,
                search_type=request.search_type,
                query=request.query
            )
            
            logger.info(f"Search '{request.query}' returned {len(results)} results in {execution_time:.2f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Search failed for query '{request.query}': {e}")
            raise
    
    async def _keyword_search(self, request: SearchRequest, keywords: List[str]) -> List[SearchResult]:
        """Perform keyword-based search"""
        try:
            with get_db_context() as db:
                # Build base query
                query = db.query(Memory).join(Assistant)
                
                # Filter by assistant if specified
                if request.assistant_id:
                    query = query.filter(
                        (Memory.assistant_id == request.assistant_id) | 
                        (Memory.is_shared == True if request.include_shared else False)
                    )
                elif request.include_shared:
                    # Include all memories if no assistant specified and shared included
                    pass
                else:
                    # This case shouldn't normally happen
                    return []
                
                # Apply filters
                if request.memory_type:
                    query = query.filter(Memory.memory_type == request.memory_type)
                
                if request.min_importance:
                    query = query.filter(Memory.importance >= request.min_importance)
                
                if request.tags:
                    for tag in request.tags:
                        query = query.filter(Memory.tags.contains(tag))
                
                if request.date_from:
                    query = query.filter(Memory.created_at >= request.date_from)
                
                if request.date_to:
                    query = query.filter(Memory.created_at <= request.date_to)
                
                # Keyword matching
                search_conditions = []
                for keyword in keywords:
                    search_conditions.append(Memory.content.contains(keyword))
                    if Memory.summary:
                        search_conditions.append(Memory.summary.contains(keyword))
                    if Memory.tags:
                        search_conditions.append(Memory.tags.contains(keyword))
                
                if search_conditions:
                    from sqlalchemy import or_
                    query = query.filter(or_(*search_conditions))
                
                # Order by relevance (importance + access count + recency)
                query = query.order_by(
                    (Memory.importance * 0.3 + 
                     Memory.access_count * 0.2 + 
                     (1.0 / ((func.now() - Memory.created_at).total_seconds() / 86400 + 1)) * 0.5).desc()
                )
                
                memories = query.limit(request.limit).all()
                
                # Create search results with keyword highlighting
                results = []
                for memory in memories:
                    # Calculate keyword match score
                    score = self._calculate_keyword_score(memory, keywords)
                    
                    # Generate highlight
                    highlight = highlight_text(memory.content, keywords)
                    
                    result = SearchResult(
                        memory=MemoryResponse.from_orm(memory),
                        score=score,
                        match_type="keyword",
                        highlight=highlight
                    )
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            raise
    
    async def _semantic_search(self, request: SearchRequest) -> List[SearchResult]:
        """Perform semantic vector search"""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(request.query)
            if not query_embedding:
                logger.warning("Failed to generate query embedding, falling back to keyword search")
                keywords = extract_keywords(request.query)
                return await self._keyword_search(request, keywords)
            
            with get_db_context() as db:
                # Get memories with embeddings
                query = db.query(Memory, MemoryEmbedding).join(
                    MemoryEmbedding, Memory.id == MemoryEmbedding.memory_id
                ).join(Assistant)
                
                # Apply filters (same as keyword search)
                if request.assistant_id:
                    query = query.filter(
                        (Memory.assistant_id == request.assistant_id) | 
                        (Memory.is_shared == True if request.include_shared else False)
                    )
                
                if request.memory_type:
                    query = query.filter(Memory.memory_type == request.memory_type)
                
                if request.min_importance:
                    query = query.filter(Memory.importance >= request.min_importance)
                
                if request.tags:
                    for tag in request.tags:
                        query = query.filter(Memory.tags.contains(tag))
                
                if request.date_from:
                    query = query.filter(Memory.created_at >= request.date_from)
                
                if request.date_to:
                    query = query.filter(Memory.created_at <= request.date_to)
                
                memory_embeddings = query.all()
                
                # Calculate similarity scores
                scored_memories = []
                for memory, embedding in memory_embeddings:
                    try:
                        stored_vector = json.loads(embedding.embedding_vector)
                        similarity = cosine_similarity(query_embedding, stored_vector)
                        
                        # Weight similarity with importance
                        weighted_score = similarity * 0.7 + (memory.importance / 10) * 0.3
                        
                        scored_memories.append((memory, weighted_score, similarity))
                        
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Failed to decode embedding for memory {memory.id}: {e}")
                        continue
                
                # Sort by score and take top results
                scored_memories.sort(key=lambda x: x[1], reverse=True)
                top_memories = scored_memories[:request.limit]
                
                # Create search results
                results = []
                for memory, weighted_score, similarity in top_memories:
                    # Only include results with reasonable similarity
                    if similarity > 0.1:  # Threshold for semantic relevance
                        result = SearchResult(
                            memory=MemoryResponse.from_orm(memory),
                            score=similarity,
                            match_type="semantic",
                            highlight=None  # Could add semantic highlighting here
                        )
                        results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise
    
    async def _hybrid_search(self, request: SearchRequest, keywords: List[str]) -> List[SearchResult]:
        """Perform hybrid keyword + semantic search"""
        try:
            # Run both searches in parallel
            keyword_task = self._keyword_search(request, keywords)
            semantic_task = self._semantic_search(request)
            
            keyword_results, semantic_results = await asyncio.gather(
                keyword_task, semantic_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(keyword_results, Exception):
                logger.error(f"Keyword search failed in hybrid: {keyword_results}")
                keyword_results = []
            
            if isinstance(semantic_results, Exception):
                logger.error(f"Semantic search failed in hybrid: {semantic_results}")
                semantic_results = []
            
            # Combine and deduplicate results
            combined_results = {}
            
            # Add keyword results
            for result in keyword_results:
                memory_id = result.memory.id
                combined_results[memory_id] = SearchResult(
                    memory=result.memory,
                    score=result.score * 0.6,  # Weight keyword results
                    match_type="keyword",
                    highlight=result.highlight
                )
            
            # Add semantic results (boost existing, add new)
            for result in semantic_results:
                memory_id = result.memory.id
                if memory_id in combined_results:
                    # Combine scores for memories found in both
                    existing = combined_results[memory_id]
                    combined_score = existing.score + (result.score * 0.4)
                    combined_results[memory_id] = SearchResult(
                        memory=result.memory,
                        score=min(combined_score, 1.0),  # Cap at 1.0
                        match_type="both",
                        highlight=existing.highlight
                    )
                else:
                    # Add new semantic result
                    combined_results[memory_id] = SearchResult(
                        memory=result.memory,
                        score=result.score * 0.4,  # Weight semantic results
                        match_type="semantic",
                        highlight=None
                    )
            
            # Sort by combined score and limit
            final_results = list(combined_results.values())
            final_results.sort(key=lambda x: x.score, reverse=True)
            
            return final_results[:request.limit]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise
    
    async def get_search_suggestions(self, query: str, assistant_id: Optional[int], limit: int) -> List[str]:
        """Get search query suggestions"""
        try:
            with get_db_context() as db:
                # Get recent search queries
                search_query = db.query(SearchLog.query).distinct()
                
                if assistant_id:
                    search_query = search_query.filter(SearchLog.assistant_id == assistant_id)
                
                # Find queries that contain the input
                search_query = search_query.filter(SearchLog.query.contains(query))
                search_query = search_query.order_by(SearchLog.created_at.desc())
                
                suggestions = search_query.limit(limit).all()
                return [s[0] for s in suggestions]
                
        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []
    
    async def get_recent_queries(self, assistant_id: Optional[int], limit: int) -> List[Dict[str, Any]]:
        """Get recent search queries"""
        try:
            with get_db_context() as db:
                query = db.query(SearchLog)
                
                if assistant_id:
                    query = query.filter(SearchLog.assistant_id == assistant_id)
                
                recent_searches = query.order_by(SearchLog.created_at.desc()).limit(limit).all()
                
                return [
                    {
                        "query": search.query,
                        "search_type": search.search_type,
                        "results_count": search.results_count,
                        "created_at": search.created_at
                    }
                    for search in recent_searches
                ]
                
        except Exception as e:
            logger.error(f"Failed to get recent queries: {e}")
            return []
    
    async def get_popular_tags(self, assistant_id: Optional[int], limit: int) -> List[Dict[str, Any]]:
        """Get most popular tags"""
        try:
            with get_db_context() as db:
                query = db.query(Memory.tags)
                
                if assistant_id:
                    query = query.filter(
                        (Memory.assistant_id == assistant_id) | (Memory.is_shared == True)
                    )
                
                memories_with_tags = query.filter(Memory.tags.isnot(None)).all()
                
                # Count tag occurrences
                tag_counts = {}
                for (tags_str,) in memories_with_tags:
                    if tags_str:
                        # Split tags (assuming comma-separated)
                        tags = [tag.strip() for tag in tags_str.split(',')]
                        for tag in tags:
                            if tag:
                                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                # Sort by count and return top tags
                popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
                return [
                    {"tag": tag, "count": count}
                    for tag, count in popular_tags[:limit]
                ]
                
        except Exception as e:
            logger.error(f"Failed to get popular tags: {e}")
            return []
    
    def _calculate_keyword_score(self, memory: Memory, keywords: List[str]) -> float:
        """Calculate keyword match score for a memory"""
        score = 0.0
        total_keywords = len(keywords)
        
        if total_keywords == 0:
            return 0.0
        
        content_lower = memory.content.lower()
        summary_lower = (memory.summary or "").lower()
        tags_lower = (memory.tags or "").lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Content matches (highest weight)
            if keyword_lower in content_lower:
                score += 0.6
            
            # Summary matches
            if keyword_lower in summary_lower:
                score += 0.3
            
            # Tag matches
            if keyword_lower in tags_lower:
                score += 0.1
        
        # Normalize score
        return min(score / total_keywords, 1.0)
    
    async def _log_search(self, request: SearchRequest, results_count: int, execution_time: float):
        """Log search query for analytics"""
        try:
            with get_db_context() as db:
                search_log = SearchLog(
                    assistant_id=request.assistant_id,
                    query=request.query,
                    search_type=request.search_type.value,
                    results_count=results_count,
                    execution_time_ms=execution_time
                )
                
                db.add(search_log)
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to log search: {e}")