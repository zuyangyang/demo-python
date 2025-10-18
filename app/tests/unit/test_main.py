import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert "health" in data
    assert data["message"] == "Welcome to Multi-User Task Assignment System API"

def test_health_check_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "message" in data
    assert "version" in data
    assert "debug" in data

def test_cors_headers():
    """Test CORS headers are present."""
    response = client.options("/")
    assert response.status_code == 200

    # Check for CORS headers
    headers = response.headers
    assert "access-control-allow-origin" in headers
    assert "access-control-allow-methods" in headers
    assert "access-control-allow-headers" in headers

def test_process_time_header():
    """Test process time header is added."""
    response = client.get("/")
    assert response.status_code == 200

    # Check for process time header
    assert "x-process-time" in response.headers
    assert float(response.headers["x-process-time"]) >= 0

def test_api_exception_handler():
    """Test custom API exception handler."""
    from app.core.exceptions import NotFoundException

    @app.get("/test-not-found")
    async def test_not_found():
        raise NotFoundException("Test resource not found")

    response = client.get("/test-not-found")
    assert response.status_code == 404

    data = response.json()
    assert "error" in data
    assert data["error"]["message"] == "Test resource not found"
    assert "details" in data["error"]

def test_http_exception_handler():
    """Test HTTP exception handler."""
    @app.get("/test-http-exception")
    async def test_http_exception():
        raise HTTPException(status_code=422, detail="Validation error")

    response = client.get("/test-http-exception")
    assert response.status_code == 422

    data = response.json()
    assert "error" in data
    assert data["error"]["message"] == "Validation error"

def test_general_exception_handler():
    """Test general exception handler."""
    @app.get("/test-general-exception")
    async def test_general_exception():
        raise ValueError("Unexpected error")

    response = client.get("/test-general-exception")
    assert response.status_code == 500

    data = response.json()
    assert "error" in data
    assert data["error"]["message"] == "Internal server error"
