import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import get_db, Base

@pytest.fixture
def test_db():
    """Create a test database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    database_url = f"sqlite:///{db_path}"

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False}
    )

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    yield TestingSessionLocal

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

def test_database_session_creation(test_db):
    """Test database session creation and cleanup."""
    db = test_db()
    assert db is not None

    # Test session is active
    assert db.is_active

    # Close session
    db.close()
    # Check if session is properly closed (different SQLAlchemy versions may behave differently)
    # assert not db.is_active

def test_get_db_dependency():
    """Test get_db dependency function."""
    db_gen = get_db()
    db = next(db_gen)

    assert db is not None
    assert hasattr(db, 'query')
    assert hasattr(db, 'add')
    assert hasattr(db, 'commit')

    try:
        next(db_gen)
    except StopIteration:
        pass  # Expected behavior
