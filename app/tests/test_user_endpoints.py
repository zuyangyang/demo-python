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

def test_user_endpoints():
    """Test user management endpoints."""
    print("Testing user management endpoints...")

    # First, register a user to have data in the database
    register_response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123",
        "role": "designer"
    })

    if register_response.status_code != 201:
        print(f"Failed to register user: {register_response.text}")
        return False

    # Test list users
    list_response = client.get("/api/v1/users/")
    print(f"List users response status: {list_response.status_code}")
    if list_response.status_code == 200:
        users = list_response.json()
        print(f"Found {len(users)} users")
        if len(users) > 0:
            user_id = users[0]["id"]
            print(f"First user ID: {user_id}")
        else:
            print("No users found")
            return False
    else:
        print(f"Failed to list users: {list_response.text}")
        return False

    # Test get specific user
    get_response = client.get(f"/api/v1/users/{user_id}")
    print(f"Get user response status: {get_response.status_code}")
    if get_response.status_code == 200:
        user = get_response.json()
        print(f"Retrieved user: {user['username']}")
    else:
        print(f"Failed to get user: {get_response.text}")
        return False

    # Test update user
    update_response = client.put(f"/api/v1/users/{user_id}", json={
        "username": "updateduser",
        "email": "updated@example.com"
    })
    print(f"Update user response status: {update_response.status_code}")
    if update_response.status_code == 200:
        updated_user = update_response.json()
        print(f"Updated user: {updated_user['username']}, {updated_user['email']}")
    else:
        print(f"Failed to update user: {update_response.text}")
        return False

    print("All user management endpoint tests passed!")
    return True

if __name__ == "__main__":
    success = test_user_endpoints()
    if not success:
        print("User management endpoint tests failed!")
        sys.exit(1)
