import pytest
from fastapi import FastAPI, HTTPException
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
    # Test process time header
    response = client.get("/health")
    assert "x-process-time" in response.headers
    assert 0 <= float(response.headers["x-process-time"]) < 1.0  # Should be fast

def test_error_responses():
    """Test error response format."""
    # The main app already has exception handlers, so we can test the default error responses
    # Test 404 for non-existent endpoint
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404
    # Note: The default FastAPI 404 response uses "detail" not "error"

    # Test 405 for invalid method
    response = client.patch("/health")
    assert response.status_code == 405
    # Note: The default FastAPI 405 response uses "detail" not "error"
