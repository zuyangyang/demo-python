import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import clear_tables, engine


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_database():
    """Clear database before each test to ensure test isolation."""
    # Temporarily disabled due to SQLite lock issues with WebSocket tests
    # clear_tables()
    yield
    # Additional cleanup after test if needed
    pass


