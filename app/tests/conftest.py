import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import clear_tables


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_database():
    """Clear database before each test to ensure test isolation."""
    clear_tables()
    yield
    # Clean up after test if needed


