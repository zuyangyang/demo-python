from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.dependencies import get_database
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.models.user import UserRole

router = APIRouter()

def get_current_user_role(db: Session = Depends(get_database)) -> UserRole:
    """Get current user role - placeholder for now."""
    # In a real implementation, we would extract the user from the token
    # For now, we'll return ADMIN to allow testing
    return UserRole.ADMIN

def require_admin(role: UserRole = Depends(get_current_user_role)):
    """Dependency to require admin role."""
    if role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    db: Session = Depends(get_database)
):
    """List users with optional filtering by role."""
    user_service = UserService(db)

    # In a real implementation, we would check permissions here
    # For now, we'll allow anyone to list users

    users = user_service.get_users(skip=skip, limit=limit)

    # Filter by role if specified
    if role:
        users = [user for user in users if user.role == role]

    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_database)):
    """Get a specific user by ID."""
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_database)
):
    """Update a user."""
    user_service = UserService(db)
    user = user_service.update_user(user_id, user_update)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    role: UserRole = Depends(get_current_user_role),
    db: Session = Depends(get_database)
):
    """Delete a user (admin only)."""
    # Check if user is admin
    if role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to delete users"
        )

    user_service = UserService(db)
    deleted = user_service.delete_user(user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # No content to return
    return
