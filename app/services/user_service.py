from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.services.base import BaseService
from typing import Optional, List
from datetime import timedelta

class UserService(BaseService):
    """Service class for user-related operations."""

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get a list of users with pagination."""
        return self.db.query(User).offset(skip).limit(limit).all()

    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user."""
        # Hash the password
        hashed_password = get_password_hash(user_create.password)

        # Create the user object
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            password_hash=hashed_password,
            role=user_create.role
        )

        # Add to database
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return db_user

    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update a user."""
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None

        # Update user fields
        if user_update.username is not None:
            db_user.username = user_update.username
        if user_update.email is not None:
            db_user.email = user_update.email
        if user_update.role is not None:
            db_user.role = user_update.role

        self.db.commit()
        self.db.refresh(db_user)

        return db_user

    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return False

        self.db.delete(db_user)
        self.db.commit()
        return True

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password."""
        user = self.get_user_by_username(username)
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    def create_access_token(self, user: User) -> str:
        """Create an access token for a user."""
        token_data = {
            "sub": user.username,
            "user_id": user.id
        }
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        return create_access_token(data=token_data, expires_delta=access_token_expires)
