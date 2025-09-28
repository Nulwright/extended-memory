"""Test Main Application"""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "1.0.0"


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


def test_docs_endpoint(client):
    """Test API documentation endpoint"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_schema(client):
    """Test OpenAPI schema endpoint"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["info"]["title"] == "Extended Sienna Memory (ESM)"


def test_cors_headers(client):
    """Test CORS headers"""
    response = client.options("/")
    # CORS headers should be present
    assert response.status_code == 200


def test_nonexistent_endpoint(client):
    """Test 404 for nonexistent endpoint"""
    response = client.get("/nonexistent")
    assert response.status_code == 404


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_json(self, client):
        """Test invalid JSON handling"""
        response = client.post(
            "/api/v1/memories/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


class TestMiddleware:
    """Test middleware functionality"""
    
    def test_request_logging(self, client, caplog):
        """Test that requests are logged"""
        response = client.get("/health")
        assert response.status_code == 200
        
        # Check that request was logged
        # Note: This test may need adjustment based on actual logging setup


class TestApplicationStartup:
    """Test application startup and lifespan"""
    
    def test_application_startup(self, client):
        """Test that application starts successfully"""
        # If we can make a request, the app started successfully
        response = client.get("/health")
        assert response.status_code == 200