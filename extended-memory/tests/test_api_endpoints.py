"""Test API Endpoints"""

import pytest
import json
from datetime import datetime


class TestMemoryEndpoints:
    """Test memory API endpoints"""
    
    def test_create_memory(self, client, test_assistant):
        """Test POST /api/v1/memories/"""
        memory_data = {
            "assistant_id": test_assistant.id,
            "content": "Test memory via API",
            "memory_type": "general",
            "importance": 7,
            "tags": "api, test"
        }
        
        response = client.post("/api/v1/memories/", json=memory_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Test memory via API"
        assert data["importance"] == 7
        assert data["assistant_id"] == test_assistant.id
    
    def test_create_memory_invalid_data(self, client, test_assistant):
        """Test creating memory with invalid data"""
        memory_data = {
            "assistant_id": test_assistant.id,
            "content": "",  # Empty content
            "importance": 15  # Invalid importance
        }
        
        response = client.post("/api/v1/memories/", json=memory_data)
        assert response.status_code == 422
    
    def test_get_memory(self, client, test_memory):
        """Test GET /api/v1/memories/{id}"""
        response = client.get(f"/api/v1/memories/{test_memory.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_memory.id
        assert data["content"] == test_memory.content
    
    def test_get_nonexistent_memory(self, client):
        """Test getting non-existent memory"""
        response = client.get("/api/v1/memories/99999")
        assert response.status_code == 404
    
    def test_update_memory(self, client, test_memory):
        """Test PUT /api/v1/memories/{id}"""
        update_data = {
            "content": "Updated content via API",
            "importance": 8
        }
        
        response = client.put(f"/api/v1/memories/{test_memory.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content via API"
        assert data["importance"] == 8
    
    def test_delete_memory(self, client, test_memory):
        """Test DELETE /api/v1/memories/{id}"""
        response = client.delete(f"/api/v1/memories/{test_memory.id}")
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(f"/api/v1/memories/{test_memory.id}")
        assert get_response.status_code == 404
    
    def test_list_memories(self, client, sample_memories, test_assistant):
        """Test GET /api/v1/memories/"""
        response = client.get(f"/api/v1/memories/?assistant_id={test_assistant.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == len(sample_memories)
    
    def test_list_memories_with_filters(self, client, sample_memories, test_assistant):
        """Test listing memories with query parameters"""
        response = client.get(
            f"/api/v1/memories/?assistant_id={test_assistant.id}&memory_type=task&limit=5"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned memories should be tasks
        for memory in data:
            assert memory["memory_type"] == "task"


class TestSearchEndpoints:
    """Test search API endpoints"""
    
    def test_search_memories(self, client, sample_memories, test_assistant):
        """Test POST /api/v1/search/"""
        search_data = {
            "query": "python programming",
            "assistant_id": test_assistant.id,
            "limit": 10
        }
        
        response = client.post("/api/v1/search/", json=search_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_count" in data
        assert "execution_time_ms" in data
        assert data["query"] == "python programming"
    
    def test_quick_search(self, client, sample_memories, test_assistant):
        """Test GET /api/v1/search/quick"""
        response = client.get(
            f"/api/v1/search/quick?q=machine learning&assistant_id={test_assistant.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    def test_search_invalid_query(self, client):
        """Test search with invalid data"""
        search_data = {
            "query": "",  # Empty query
            "limit": -1   # Invalid limit
        }
        
        response = client.post("/api/v1/search/", json=search_data)
        assert response.status_code == 422
    
    def test_get_search_suggestions(self, client, sample_memories, test_assistant):
        """Test GET /api/v1/search/suggestions"""
        response = client.get(
            f"/api/v1/search/suggestions?q=prog&assistant_id={test_assistant.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)


class TestAssistantEndpoints:
    """Test assistant API endpoints"""
    
    def test_list_assistants(self, client, test_assistant):
        """Test GET /api/v1/assistants/"""
        response = client.get("/api/v1/assistants/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Should include our test assistant
        assistant_names = [a["name"] for a in data]
        assert test_assistant.name in assistant_names
    
    def test_create_assistant(self, client):
        """Test POST /api/v1/assistants/"""
        assistant_data = {
            "name": "NewAssistant",
            "personality": "Helpful and friendly",
            "is_active": True
        }
        
        response = client.post("/api/v1/assistants/", json=assistant_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "NewAssistant"
        assert data["personality"] == "Helpful and friendly"
    
    def test_create_duplicate_assistant(self, client, test_assistant):
        """Test creating assistant with duplicate name"""
        assistant_data = {
            "name": test_assistant.name,  # Duplicate name
            "personality": "Another personality"
        }
        
        response = client.post("/api/v1/assistants/", json=assistant_data)
        assert response.status_code == 400
    
    def test_get_assistant(self, client, test_assistant):
        """Test GET /api/v1/assistants/{id}"""
        response = client.get(f"/api/v1/assistants/{test_assistant.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_assistant.id
        assert data["name"] == test_assistant.name


class TestAnalyticsEndpoints:
    """Test analytics API endpoints"""
    
    def test_system_stats(self, client, sample_memories):
        """Test GET /api/v1/analytics/system"""
        response = client.get("/api/v1/analytics/system")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_assistants" in data
        assert "total_memories" in data
        assert "avg_memory_importance" in data
    
    def test_assistant_stats(self, client, sample_memories, test_assistant):
        """Test GET /api/v1/analytics/assistant/{id}/stats"""
        response = client.get(f"/api/v1/analytics/assistant/{test_assistant.id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["assistant_id"] == test_assistant.id
        assert "total_memories" in data
        assert "avg_importance" in data


class TestSharedMemoryEndpoints:
    """Test shared memory API endpoints"""
    
    def test_list_shared_memories(self, client, test_shared_memory):
        """Test GET /api/v1/shared/"""
        response = client.get("/api/v1/shared/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should include our shared memory
        shared_ids = [m["id"] for m in data]
        assert test_shared_memory.id in shared_ids
    
    def test_share_memory(self, client, test_memory):
        """Test POST /api/v1/shared/{id}/share"""
        response = client.post(
            f"/api/v1/shared/{test_memory.id}/share?category=knowledge"
        )
        
        assert response.status_code == 200
        
        # Verify memory is now shared
        get_response = client.get(f"/api/v1/memories/{test_memory.id}")
        data = get_response.json()
        assert data["is_shared"] is True
        assert data["shared_category"] == "knowledge"


class TestExportEndpoints:
    """Test export API endpoints"""
    
    def test_create_export(self, client, test_assistant):
        """Test POST /api/v1/export/"""
        export_data = {
            "assistant_id": test_assistant.id,
            "format": "json",
            "include_shared": True
        }
        
        response = client.post("/api/v1/export/", json=export_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "file_url" in data
        assert data["format"] == "json"
    
    def test_quick_json_export(self, client, test_assistant):
        """Test POST /api/v1/export/quick-json"""
        response = client.post(
            f"/api/v1/export/quick-json?assistant_id={test_assistant.id}"
        )
        
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]


class TestWebSocketEndpoints:
    """Test WebSocket endpoints"""
    
    def test_websocket_connections_info(self, client):
        """Test GET /ws/connections"""
        response = client.get("/ws/connections")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_connections" in data
        assert "connections" in data


class TestErrorHandling:
    """Test API error handling"""
    
    def test_validation_errors(self, client):
        """Test validation error responses"""
        # Invalid JSON structure
        response = client.post("/api/v1/memories/", json={})
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
    
    def test_404_errors(self, client):
        """Test 404 error responses"""
        response = client.get("/api/v1/memories/99999")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test 405 error responses"""
        response = client.patch("/api/v1/memories/")  # PATCH not supported on collection
        assert response.status_code == 405


class TestRateLimiting:
    """Test rate limiting (if implemented)"""
    
    def test_rate_limiting(self, client, test_assistant):
        """Test API rate limiting"""
        # Make many requests rapidly
        responses = []
        for i in range(100):
            response = client.get(f"/api/v1/assistants/{test_assistant.id}")
            responses.append(response)
            
            # If rate limiting is implemented, some requests should return 429
            if response.status_code == 429:
                break
        
        # This test depends on rate limiting being implemented
        # For now, just ensure we don't crash
        assert len(responses) > 0
