import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService

def test_user_service():
    """Test user service functionality."""
    print("Testing user service...")

    # Create an in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)

    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Create user service
    user_service = UserService(db)

    # Test user creation
    user_create = UserCreate(
        username="testuser",
        email="test@example.com",
        password="TestPass123",
        role=UserRole.DESIGNER
    )

    created_user = user_service.create_user(user_create)
    print(f"Created user: {created_user.username}, {created_user.email}")

    # Test user retrieval
    retrieved_user = user_service.get_user_by_id(created_user.id)
    print(f"Retrieved user: {retrieved_user.username}, {retrieved_user.email}")

    # Test user authentication
    authenticated_user = user_service.authenticate_user("testuser", "TestPass123")
    if authenticated_user:
        print(f"User authenticated: {authenticated_user.username}")
    else:
        print("User authentication failed")

    # Test failed authentication
    failed_auth = user_service.authenticate_user("testuser", "WrongPass")
    if failed_auth:
        print("ERROR: Authentication should have failed")
    else:
        print("Authentication correctly failed for wrong password")

    # Test access token creation
    token = user_service.create_access_token(created_user)
    print(f"Access token created: {token[:20]}...")

    # Test user update
    user_update = UserUpdate(
        username="updateduser",
        email="updated@example.com"
    )

    updated_user = user_service.update_user(created_user.id, user_update)
    if updated_user:
        print(f"Updated user: {updated_user.username}, {updated_user.email}")
    else:
        print("User update failed")

    # Test user deletion
    deleted = user_service.delete_user(created_user.id)
    if deleted:
        print("User deleted successfully")
    else:
        print("User deletion failed")

    db.close()
    print("User service test completed!")

if __name__ == "__main__":
    test_user_service()
