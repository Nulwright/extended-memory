"""Test Search Service"""

import pytest
from esm.schemas import SearchRequest, SearchType
from esm.services.search_service import SearchService


@pytest.mark.asyncio
class TestSearchService:
    """Test SearchService class"""
    
    async def test_keyword_search(self, search_service, sample_memories, test_assistant):
        """Test keyword-based search"""
        search_request = SearchRequest(
            query="python programming",
            assistant_id=test_assistant.id,
            search_type=SearchType.KEYWORD,
            limit=10
        )
        
        results = await search_service.search_memories(search_request)
        
        assert results is not None
        assert isinstance(results.results, list)
        assert results.search_type == SearchType.KEYWORD
        assert results.query == "python programming"
        
        # Should find the Python-related memory
        python_results = [r for r in results.results if "python" in r.memory.content.lower()]
        assert len(python_results) > 0
    
    async def test_semantic_search(self, search_service, sample_memories, test_assistant):
        """Test semantic search"""
        search_request = SearchRequest(
            query="artificial intelligence",
            assistant_id=test_assistant.id,
            search_type=SearchType.SEMANTIC,
            limit=10
        )
        
        results = await search_service.search_memories(search_request)
        
        assert results is not None
        assert results.search_type == SearchType.SEMANTIC
        
        # Note: Semantic search results depend on embedding service availability
    
    async def test_hybrid_search(self, search_service, sample_memories, test_assistant):
        """Test hybrid search (keyword + semantic)"""
        search_request = SearchRequest(
            query="machine learning",
            assistant_id=test_assistant.id,
            search_type=SearchType.HYBRID,
            limit=10
        )
        
        results = await search_service.search_memories(search_request)
        
        assert results is not None
        assert results.search_type == SearchType.HYBRID
        
        # Should find ML-related memory
        ml_results = [r for r in results.results if "machine learning" in r.memory.content.lower()]
        assert len(ml_results) > 0
    
    async def test_search_with_filters(self, search_service, sample_memories, test_assistant):
        """Test search with filters"""
        search_request = SearchRequest(
            query="*",  # Match all
            assistant_id=test_assistant.id,
            memory_type="task",
            min_importance=5,
            limit=10
        )
        
        results = await search_service.search_memories(search_request)
        
        # All results should be tasks with importance >= 5
        for result in results.results:
            assert result.memory.memory_type == "task"
            assert result.memory.importance >= 5
    
    async def test_search_with_tags(self, search_service, sample_memories, test_assistant):
        """Test search filtering by tags"""
        search_request = SearchRequest(
            query="*",
            assistant_id=test_assistant.id,
            tags=["programming"],
            limit=10
        )
        
        results = await search_service.search_memories(search_request)
        
        # Results should contain memories with programming tag
        programming_results = [
            r for r in results.results 
            if r.memory.tags and "programming" in r.memory.tags
        ]
        assert len(programming_results) > 0
    
    async def test_search_shared_memories(self, search_service, test_shared_memory, test_assistant):
        """Test including shared memories in search"""
        search_request = SearchRequest(
            query="shared",
            assistant_id=test_assistant.id,
            include_shared=True,
            limit=10
        )
        
        results = await search_service.search_memories(search_request)
        
        # Should include shared memories
        shared_results = [r for r in results.results if r.memory.is_shared]
        assert len(shared_results) > 0
    
    async def test_search_exclude_shared(self, search_service, sample_memories, test_shared_memory, test_assistant):
        """Test excluding shared memories from search"""
        search_request = SearchRequest(
            query="*",
            assistant_id=test_assistant.id,
            include_shared=False,
            limit=10
        )
        
        results = await search_service.search_memories(search_request)
        
        # Should not include shared memories
        shared_results = [r for r in results.results if r.memory.is_shared]
        assert len(shared_results) == 0
    
    async def test_search_date_range(self, search_service, sample_memories, test_assistant):
        """Test search with date range"""
        from datetime import datetime, timedelta
        
        # Search for memories from last week
        search_request = SearchRequest(
            query="*",
            assistant_id=test_assistant.id,
            date_from=datetime.utcnow() - timedelta(days=7),
            date_to=datetime.utcnow(),
            limit=10
        )
        
        results = await search_service.search_memories(search_request)
        
        # All results should be within date range
        for result in results.results:
            memory_date = result.memory.created_at
            assert memory_date >= datetime.utcnow() - timedelta(days=7)
            assert memory_date <= datetime.utcnow()
    
    async def test_empty_search_query(self, search_service, test_assistant):
        """Test search with empty query"""
        search_request = SearchRequest(
            query="",
            assistant_id=test_assistant.id,
            limit=10
        )
        
        results = await search_service.search_memories(search_request)
        
        # Should handle empty query gracefully
        assert results is not None
        assert isinstance(results.results, list)
    
    async def test_search_nonexistent_assistant(self, search_service):
        """Test search with non-existent assistant"""
        search_request = SearchRequest(
            query="test",
            assistant_id=99999,  # Non-existent
            limit=10
        )
        
        results = await search_service.search_memories(search_request)
        
        # Should return empty results
        assert len(results.results) == 0
    
    async def test_search_suggestions(self, search_service, sample_memories, test_assistant):
        """Test search suggestions"""
        suggestions = await search_service.get_search_suggestions(
            "prog", test_assistant.id, limit=5
        )
        
        assert isinstance(suggestions, list)
        # Should return relevant suggestions
    
    async def test_popular_tags(self, search_service, sample_memories, test_assistant):
        """Test getting popular tags"""
        tags = await search_service.get_popular_tags(test_assistant.id, limit=10)
        
        assert isinstance(tags, list)
        for tag_info in tags:
            assert "tag" in tag_info
            assert "count" in tag_info
            assert tag_info["count"] > 0


class TestSearchPerformance:
    """Test search performance"""
    
    @pytest.mark.asyncio
    async def test_search_execution_time(self, search_service, sample_memories, test_assistant):
        """Test that search executes within reasonable time"""
        search_request = SearchRequest(
            query="test query",
            assistant_id=test_assistant.id,
            limit=10
        )
        
        results = await search_service.search_memories(search_request)
        
        # Should complete within reasonable time (< 1 second for test data)
        assert results.execution_time_ms < 1000
    
    @pytest.mark.asyncio
    async def test_large_result_set_pagination(self, search_service, test_assistant):
        """Test pagination with large result sets"""
        # This test would require more test data to be meaningful
        search_request = SearchRequest(
            query="*",
            assistant_id=test_assistant.id,
            limit=100  # Large limit
        )
        
        results = await search_service.search_memories(search_request)
        
        # Should handle large limits gracefully
        assert len(results.results) <= 100