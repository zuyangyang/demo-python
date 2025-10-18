import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine
import json

# Create tables in test database
Base.metadata.drop_all(bind=engine)  # Clear any existing data
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_refresh_token():
    """Test refresh token functionality."""
    print("Testing refresh token functionality...")

    # First, register a user
    register_response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123",
        "role": "designer"
    })

    if register_response.status_code != 201:
        print(f"Failed to register user: {register_response.text}")
        return False

    register_data = register_response.json()
    refresh_token = register_data.get("refresh_token")

    if not refresh_token:
        print("No refresh token in registration response")
        return False

    print(f"Received refresh token: {refresh_token[:20]}...")

    # Test refresh token
    refresh_response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })

    print(f"Refresh token response status: {refresh_response.status_code}")
    if refresh_response.status_code == 200:
        refresh_data = refresh_response.json()
        print(f"Refresh successful: {refresh_data['token_type']}")
        assert "access_token" in refresh_data
        assert refresh_data["token_type"] == "bearer"
        print("Refresh token test passed!")
        return True
    else:
        print(f"Refresh failed: {refresh_response.text}")
        return False

def test_invalid_refresh_token():
    """Test invalid refresh token."""
    print("Testing invalid refresh token...")

    # Test with invalid refresh token
    refresh_response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": "invalid_token"
    })

    print(f"Invalid refresh token response status: {refresh_response.status_code}")
    if refresh_response.status_code == 401:
        print("Invalid refresh token correctly rejected")
        return True
    else:
        print(f"Invalid refresh token not rejected: {refresh_response.text}")
        return False

if __name__ == "__main__":
    # Run tests
    refresh_success = test_refresh_token()
    invalid_refresh_success = test_invalid_refresh_token()

    if refresh_success and invalid_refresh_success:
        print("All refresh token tests passed!")
    else:
        print("Some refresh token tests failed!")
        sys.exit(1)
