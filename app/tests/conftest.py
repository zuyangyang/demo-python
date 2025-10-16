import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import clear_tables
from app.core.config import settings


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_database():
    """Clear database before each test to ensure test isolation."""
    # Clear storage before each test
    clear_tables()
    yield
    # Additional cleanup after test if needed
    pass


