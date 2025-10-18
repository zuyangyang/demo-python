from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.task import TaskStatus, TaskPriority
from app.schemas.user import UserResponse

class TaskBase(BaseModel):
    """Base task schema with common fields."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: TaskStatus = TaskStatus.TO_DO
    priority: TaskPriority = TaskPriority.MEDIUM
    category: Optional[str] = Field(None, max_length=50)
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    assigned_to_id: Optional[int] = None

class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    category: Optional[str] = Field(None, max_length=50)
    due_date: Optional[datetime] = None
    assigned_to_id: Optional[int] = None

class TaskResponse(TaskBase):
    """Schema for task response."""
    id: int
    assigned_to_id: Optional[int] = None
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TaskWithAssigneeResponse(TaskResponse):
    """Schema for task response with assignee details."""
    assigned_to: Optional[UserResponse] = None
    created_by: UserResponse

    class Config:
        from_attributes = True
