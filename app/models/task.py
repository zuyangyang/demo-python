from sqlalchemy import Column, String, Enum, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.user import User
from datetime import datetime
from enum import Enum as PyEnum

class TaskStatus(PyEnum):
    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"

class TaskPriority(PyEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class Task(BaseModel):
    """Task model for the task assignment system."""
    __tablename__ = "tasks"

    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus, name="task_status"), nullable=False, default=TaskStatus.TO_DO)
    priority = Column(Enum(TaskPriority, name="task_priority"), nullable=False, default=TaskPriority.MEDIUM)
    category = Column(String(50))
    due_date = Column(DateTime(timezone=True))

    # Foreign keys
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    created_by_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
