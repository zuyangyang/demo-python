import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse
from app.core.database import Base, engine
import sqlalchemy

def test_user_model_creation():
    """Test user model creation."""
    print("Testing user model creation...")

    # Create a user instance
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role=UserRole.DESIGNER
    )

    print(f"User created: {user.username}, {user.email}, {user.role}")
    print("User model creation test passed!")

def test_user_schema_validation():
    """Test user schema validation."""
    print("Testing user schema validation...")

    # Test valid user creation data
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123",
        "role": "designer"
    }

    user_create = UserCreate(**user_data)
    print(f"UserCreate schema validation passed: {user_create.username}, {user_create.email}")

    # Test invalid email
    try:
        invalid_user_data = user_data.copy()
        invalid_user_data["email"] = "invalid-email"
        UserCreate(**invalid_user_data)
        print("ERROR: Invalid email should have failed validation")
    except ValueError as e:
        print(f"Email validation correctly failed: {e}")

    # Test weak password
    try:
        invalid_user_data = user_data.copy()
        invalid_user_data["password"] = "weak"
        UserCreate(**invalid_user_data)
        print("ERROR: Weak password should have failed validation")
    except ValueError as e:
        print(f"Password validation correctly failed: {e}")

    print("User schema validation test passed!")

if __name__ == "__main__":
    test_user_model_creation()
    test_user_schema_validation()
    print("All tests passed!")
