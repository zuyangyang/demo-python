from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.base import BaseService
from app.services.user_service import UserService

class TaskService(BaseService):
    """Service class for task-related operations."""

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Get a task by ID."""
        return self.db.query(Task).filter(Task.id == task_id).first()

    def get_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        assigned_to_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        project_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Task]:
        """Get a list of tasks with optional filtering."""
        query = self.db.query(Task)

        # Apply filters
        if assigned_to_id is not None:
            query = query.filter(Task.assigned_to_id == assigned_to_id)

        if status is not None:
            query = query.filter(Task.status == status)

        if priority is not None:
            query = query.filter(Task.priority == priority)

        if project_id is not None:
            # We'll add project support later
            pass

        if search is not None:
            query = query.filter(
                and_(
                    Task.title.contains(search) | Task.description.contains(search)
                )
            )

        return query.offset(skip).limit(limit).all()

    def create_task(self, task_create: TaskCreate, created_by_id: int) -> Task:
        """Create a new task."""
        db_task = Task(
            title=task_create.title,
            description=task_create.description,
            status=task_create.status,
            priority=task_create.priority,
            category=task_create.category,
            due_date=task_create.due_date,
            assigned_to_id=task_create.assigned_to_id,
            created_by_id=created_by_id
        )

        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)

        return db_task

    def update_task(self, task_id: int, task_update: TaskUpdate) -> Optional[Task]:
        """Update a task."""
        db_task = self.get_task_by_id(task_id)
        if not db_task:
            return None

        # Update task fields
        if task_update.title is not None:
            db_task.title = task_update.title
        if task_update.description is not None:
            db_task.description = task_update.description
        if task_update.status is not None:
            db_task.status = task_update.status
        if task_update.priority is not None:
            db_task.priority = task_update.priority
        if task_update.category is not None:
            db_task.category = task_update.category
        if task_update.due_date is not None:
            db_task.due_date = task_update.due_date
        if task_update.assigned_to_id is not None:
            db_task.assigned_to_id = task_update.assigned_to_id

        self.db.commit()
        self.db.refresh(db_task)

        return db_task

    def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        db_task = self.get_task_by_id(task_id)
        if not db_task:
            return False

        self.db.delete(db_task)
        self.db.commit()
        return True

    def update_task_status(self, task_id: int, status: TaskStatus) -> Optional[Task]:
        """Update task status."""
        db_task = self.get_task_by_id(task_id)
        if not db_task:
            return None

        db_task.status = status
        self.db.commit()
        self.db.refresh(db_task)

        return db_task

    def assign_task(self, task_id: int, assigned_to_id: int) -> Optional[Task]:
        """Assign task to a user."""
        db_task = self.get_task_by_id(task_id)
        if not db_task:
            return None

        # Verify user exists
        user_service = UserService(self.db)
        user = user_service.get_user_by_id(assigned_to_id)
        if not user:
            return None

        db_task.assigned_to_id = assigned_to_id
        self.db.commit()
        self.db.refresh(db_task)

        return db_task
