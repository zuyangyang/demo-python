import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import TaskService

# Create a test database in memory
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """Create a database session for testing."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role=UserRole.DESIGNER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def test_create_task(db_session, sample_user):
    """Test creating a task."""
    task_service = TaskService(db_session)

    task_create = TaskCreate(
        title="Test Task",
        description="This is a test task",
        status=TaskStatus.TO_DO,
        priority=TaskPriority.MEDIUM,
        category="Development"
    )

    task = task_service.create_task(task_create, sample_user.id)

    assert task.title == "Test Task"
    assert task.description == "This is a test task"
    assert task.status == TaskStatus.TO_DO
    assert task.priority == TaskPriority.MEDIUM
    assert task.category == "Development"
    assert task.created_by_id == sample_user.id
    assert task.id is not None

def test_get_task_by_id(db_session, sample_user):
    """Test getting a task by ID."""
    task_service = TaskService(db_session)

    # Create a task first
    task_create = TaskCreate(
        title="Test Task",
        description="This is a test task"
    )

    created_task = task_service.create_task(task_create, sample_user.id)

    # Get the task by ID
    retrieved_task = task_service.get_task_by_id(created_task.id)

    assert retrieved_task is not None
    assert retrieved_task.id == created_task.id
    assert retrieved_task.title == "Test Task"

def test_get_task_by_id_not_found(db_session):
    """Test getting a task by ID when it doesn't exist."""
    task_service = TaskService(db_session)

    task = task_service.get_task_by_id(99999)

    assert task is None

def test_get_tasks(db_session, sample_user):
    """Test getting a list of tasks."""
    task_service = TaskService(db_session)

    # Create multiple tasks
    for i in range(3):
        task_create = TaskCreate(
            title=f"Test Task {i}",
            description=f"This is test task {i}"
        )
        task_service.create_task(task_create, sample_user.id)

    # Get all tasks
    tasks = task_service.get_tasks()

    assert len(tasks) == 3

    # Test pagination
    tasks_paginated = task_service.get_tasks(skip=1, limit=1)
    assert len(tasks_paginated) == 1

def test_update_task(db_session, sample_user):
    """Test updating a task."""
    task_service = TaskService(db_session)

    # Create a task first
    task_create = TaskCreate(
        title="Original Task",
        description="This is the original task"
    )

    created_task = task_service.create_task(task_create, sample_user.id)

    # Update the task
    task_update = TaskUpdate(
        title="Updated Task",
        description="This is the updated task",
        status=TaskStatus.IN_PROGRESS
    )

    updated_task = task_service.update_task(created_task.id, task_update)

    assert updated_task is not None
    assert updated_task.title == "Updated Task"
    assert updated_task.description == "This is the updated task"
    assert updated_task.status == TaskStatus.IN_PROGRESS

def test_update_task_not_found(db_session):
    """Test updating a task that doesn't exist."""
    task_service = TaskService(db_session)

    task_update = TaskUpdate(title="Updated Task")

    updated_task = task_service.update_task(99999, task_update)

    assert updated_task is None

def test_delete_task(db_session, sample_user):
    """Test deleting a task."""
    task_service = TaskService(db_session)

    # Create a task first
    task_create = TaskCreate(
        title="Task to Delete",
        description="This task will be deleted"
    )

    created_task = task_service.create_task(task_create, sample_user.id)

    # Delete the task
    deleted = task_service.delete_task(created_task.id)

    assert deleted is True

    # Try to get the deleted task
    retrieved_task = task_service.get_task_by_id(created_task.id)
    assert retrieved_task is None

def test_delete_task_not_found(db_session):
    """Test deleting a task that doesn't exist."""
    task_service = TaskService(db_session)

    deleted = task_service.delete_task(99999)

    assert deleted is False

def test_update_task_status(db_session, sample_user):
    """Test updating task status."""
    task_service = TaskService(db_session)

    # Create a task first
    task_create = TaskCreate(
        title="Task for Status Update",
        description="This task will have its status updated"
    )

    created_task = task_service.create_task(task_create, sample_user.id)

    # Update the task status
    updated_task = task_service.update_task_status(created_task.id, TaskStatus.DONE)

    assert updated_task is not None
    assert updated_task.status == TaskStatus.DONE

def test_assign_task(db_session, sample_user):
    """Test assigning a task to a user."""
    task_service = TaskService(db_session)

    # Create a task first
    task_create = TaskCreate(
        title="Task to Assign",
        description="This task will be assigned"
    )

    created_task = task_service.create_task(task_create, sample_user.id)

    # Assign the task to the user
    assigned_task = task_service.assign_task(created_task.id, sample_user.id)

    assert assigned_task is not None
    assert assigned_task.assigned_to_id == sample_user.id

def test_assign_task_not_found(db_session, sample_user):
    """Test assigning a task that doesn't exist."""
    task_service = TaskService(db_session)

    assigned_task = task_service.assign_task(99999, sample_user.id)

    assert assigned_task is None
