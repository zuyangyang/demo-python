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

def test_register_user():
    """Test user registration endpoint."""
    print("Testing user registration...")

    # Test valid registration
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123",
        "role": "designer"
    })

    print(f"Registration response status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"Registration successful: {data['token_type']}")
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        return True
    else:
        print(f"Registration failed: {response.text}")
        return False

def test_duplicate_registration():
    """Test duplicate user registration."""
    print("Testing duplicate registration...")

    # Test duplicate username registration
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test2@example.com",
        "password": "TestPass456",
        "role": "designer"
    })

    print(f"Duplicate username response status: {response.status_code}")
    if response.status_code == 400:
        print("Duplicate username correctly rejected")
        return True
    else:
        print(f"Duplicate username not rejected: {response.text}")
        return False

def test_login_user():
    """Test user login endpoint."""
    print("Testing user login...")

    # Test valid login
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123",
        "role": "designer"
    })

    print(f"Login response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Login successful: {data['token_type']}")
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        return True
    else:
        print(f"Login failed: {response.text}")
        return False

def test_invalid_login():
    """Test invalid user login."""
    print("Testing invalid login...")

    # Test invalid login with wrong password
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "WrongPass123",  # Valid format but wrong password
        "role": "designer"
    })

    print(f"Invalid login response status: {response.status_code}")
    if response.status_code == 401:
        print("Invalid login correctly rejected")
        return True
    else:
        print(f"Invalid login not rejected: {response.text}")
        return False

if __name__ == "__main__":
    # Run tests
    register_success = test_register_user()
    duplicate_success = test_duplicate_registration()
    login_success = test_login_user()
    invalid_login_success = test_invalid_login()

    if register_success and duplicate_success and login_success and invalid_login_success:
        print("All authentication endpoint tests passed!")
    else:
        print("Some authentication endpoint tests failed!")
        sys.exit(1)
