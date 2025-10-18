import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_complete_api_flow():
    """Test complete API flow."""
    # Test health check
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

    # Test non-existent endpoint
    response = client.get("/non-existent")
    assert response.status_code == 404

    # Test invalid method
    response = client.patch("/health")
    assert response.status_code == 405

def test_middleware_functionality():
    """Test middleware functionality."""
    # Test CORS preflight
    response = client.options("/health", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

    # Test process time header
    response = client.get("/health")
    assert "x-process-time" in response.headers
    assert 0 <= float(response.headers["x-process-time"]) < 1.0  # Should be fast

def test_error_responses():
    """Test error response format."""
    # Test custom exception
    response = client.get("/test-not-found")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "message" in data["error"]
    assert "details" in data["error"]

    # Test HTTP exception
    response = client.get("/test-http-exception")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "message" in data["error"]

    # Test general exception
    response = client.get("/test-general-exception")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["message"] == "Internal server error"
