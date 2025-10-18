from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.dependencies import get_database
from app.schemas.user import UserCreate, Token
from app.services.user_service import UserService
from app.core.security import verify_token

class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str

router = APIRouter()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user_create: UserCreate, db: Session = Depends(get_database)):
    """Register a new user and return an access token."""
    user_service = UserService(db)

    # Check if user already exists
    existing_user = user_service.get_user_by_username(user_create.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    existing_user = user_service.get_user_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create the user
    user = user_service.create_user(user_create)

    # Create access and refresh tokens
    access_token = user_service.create_access_token(user)
    refresh_token = user_service.create_refresh_token(user)

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

@router.post("/login", response_model=Token)
async def login_user(form_data: UserCreate, db: Session = Depends(get_database)):
    """Authenticate user and return access token."""
    user_service = UserService(db)

    # Authenticate user
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access and refresh tokens
    access_token = user_service.create_access_token(user)
    refresh_token = user_service.create_refresh_token(user)

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_database)):
    """Refresh access token using refresh token."""
    user_service = UserService(db)

    # Create new access token using refresh token
    new_access_token = user_service.refresh_access_token(request.refresh_token)
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # We don't create a new refresh token here - the client should keep using the same one
    # until it expires, at which point they need to re-authenticate
    return {"access_token": new_access_token, "token_type": "bearer"}
