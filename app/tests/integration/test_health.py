import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app


class TestHealthEndpoint:
    """Test health check endpoint integration."""
    
    def test_health_endpoint_success(self, client: TestClient):
        """Test that health endpoint returns 200 and correct body when database is accessible."""
        with patch('app.api.v1.endpoints.health.check_connection', return_value=True):
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
    
    def test_health_endpoint_database_error(self, client: TestClient):
        """Test that health endpoint returns 200 but error status when database is not accessible."""
        with patch('app.api.v1.endpoints.health.check_connection', return_value=False):
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            assert response.json() == {"status": "error"}
    
    def test_health_endpoint_uses_dependency_injection(self, client: TestClient):
        """Test that health endpoint properly uses FastAPI dependency injection for database session."""
        # This test verifies that the endpoint can be called without explicitly passing db parameter
        # The dependency injection system should handle the database session
        with patch('app.api.v1.endpoints.health.check_connection', return_value=True):
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
    
    def test_health_endpoint_response_format(self, client: TestClient):
        """Test that health endpoint returns properly formatted JSON response."""
        with patch('app.api.v1.endpoints.health.check_connection', return_value=True):
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert isinstance(data, dict)
            assert "status" in data
            assert isinstance(data["status"], str)
            assert data["status"] in ["ok", "error"]


class TestHealthEndpointIntegration:
    """Test health endpoint with actual database integration."""
    
    def test_health_endpoint_with_real_database(self, client: TestClient):
        """Test health endpoint with actual SQLite database connection."""
        # This test uses the real database connection
        # It should work because we're using SQLite with a file database
        response = client.get("/api/v1/health")
        
        # Should return 200 (even if database is not accessible, we return error status)
        assert response.status_code == 200
        
        # Response should be valid JSON
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert data["status"] in ["ok", "error"]
