from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_database
from app.schemas.user import UserCreate, Token
from app.services.user_service import UserService

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

    # Create access token
    access_token = user_service.create_access_token(user)

    return {"access_token": access_token, "token_type": "bearer"}

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

    # Create access token
    access_token = user_service.create_access_token(user)

    return {"access_token": access_token, "token_type": "bearer"}
