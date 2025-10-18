from sqlalchemy import Column, String, Enum
from app.models.base import BaseModel
from enum import Enum as PyEnum

class UserRole(PyEnum):
    ADMIN = "admin"
    TEAM_LEAD = "team_lead"
    DESIGNER = "designer"

class User(BaseModel):
    """User model for the task assignment system."""
    __tablename__ = "users"

    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.DESIGNER)
