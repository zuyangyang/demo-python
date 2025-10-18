from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional
from app.models.user import UserRole
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., max_length=100)

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.DESIGNER

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        # Check for at least one lowercase letter
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        # Check for at least one digit
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    """Schema for updating a user."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=100)
    role: Optional[UserRole] = None

class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    role: UserRole
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema for token data."""
    username: Optional[str] = None
    user_id: Optional[int] = None
