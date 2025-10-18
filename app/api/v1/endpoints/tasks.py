from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.dependencies import get_database
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskWithAssigneeResponse
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.models.user import UserRole

router = APIRouter()

def get_current_user(db: Session = Depends(get_database)):
    """Get current user - placeholder for now."""
    # In a real implementation, we would extract the user from the token
    # For now, we'll return a mock user for testing
    user_service = UserService(db)
    user = user_service.get_user_by_id(1)  # Get the first user
    if not user:
        # Create a mock user if none exists
        from app.schemas.user import UserCreate
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="Test1234",
            role=UserRole.ADMIN
        )
        user = user_service.create_user(user_create)
    return user

@router.get("/", response_model=List[TaskWithAssigneeResponse])
async def list_tasks(
    skip: int = 0,
    limit: int = 100,
    assigned_to_id: Optional[int] = None,
    task_status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_database)
):
    """List tasks with optional filtering."""
    task_service = TaskService(db)

    # Convert string status/priority to enum values if provided
    from app.models.task import TaskStatus, TaskPriority
    status_enum = None
    priority_enum = None

    if task_status:
        try:
            status_enum = TaskStatus(task_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {task_status}"
            )

    if priority:
        try:
            priority_enum = TaskPriority(priority)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {priority}"
            )

    tasks = task_service.get_tasks(
        skip=skip,
        limit=limit,
        assigned_to_id=assigned_to_id,
        status=status_enum,
        priority=priority_enum,
        search=search
    )

    return tasks

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_create: TaskCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Create a new task."""
    task_service = TaskService(db)

    # Create the task with current user as creator
    task = task_service.create_task(task_create, current_user.id)

    return task

@router.get("/{task_id}", response_model=TaskWithAssigneeResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_database)
):
    """Get a specific task by ID."""
    task_service = TaskService(db)
    task = task_service.get_task_by_id(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_database)
):
    """Update a task."""
    task_service = TaskService(db)
    task = task_service.update_task(task_id, task_update)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_database)
):
    """Delete a task."""
    task_service = TaskService(db)
    deleted = task_service.delete_task(task_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # No content to return
    return

@router.put("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: int,
    new_status: str = Query(..., description="The new status for the task"),
    db: Session = Depends(get_database)
):
    """Update task status."""
    # Convert string status to enum
    from app.models.task import TaskStatus
    try:
        status_enum = TaskStatus(new_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {new_status}"
        )

    task_service = TaskService(db)
    task = task_service.update_task_status(task_id, status_enum)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task

@router.put("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: int,
    assigned_to_id: int,
    db: Session = Depends(get_database)
):
    """Assign task to a user."""
    task_service = TaskService(db)
    task = task_service.assign_task(task_id, assigned_to_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or user not found"
        )

    return task
