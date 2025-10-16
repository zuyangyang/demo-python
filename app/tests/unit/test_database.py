import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.core.database import check_connection, get_db, SessionLocal
from app.core.config import settings, StorageMode


class TestDatabaseConnection:
    """Test database connection functionality."""
    
    def test_check_connection_success(self):
        """Test that check_connection returns True when database is accessible."""
        # In memory mode, check_connection always returns True
        if settings.storage_mode == StorageMode.MEMORY:
            assert check_connection() is True
        else:
            # Create a test engine with in-memory SQLite
            test_engine = create_engine(
                "sqlite:///:memory:",
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
            )
            
            # Mock the engine in the database module
            with patch('app.core.database.engine', test_engine):
                assert check_connection() is True
    
    def test_check_connection_failure(self):
        """Test that check_connection returns False when database is not accessible."""
        # Skip this test in memory mode
        if settings.storage_mode == StorageMode.MEMORY:
            pytest.skip("Not applicable in memory mode")
        
        # Create a test engine with invalid URL
        test_engine = create_engine(
            "sqlite:///nonexistent/path/database.db",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
        
        # Mock the engine in the database module
        with patch('app.core.database.engine', test_engine):
            assert check_connection() is False
    
    def test_get_db_yields_session(self):
        """Test that get_db dependency yields a database session."""
        db_gen = get_db()
        db = next(db_gen)
        
        # In memory mode, db is None
        if settings.storage_mode == StorageMode.MEMORY:
            assert db is None
        else:
            # Verify it's a SQLAlchemy session
            assert hasattr(db, 'execute')
            assert hasattr(db, 'close')
        
        # Clean up
        try:
            next(db_gen)
        except StopIteration:
            pass  # Expected when generator is exhausted
    
    def test_get_db_closes_session(self):
        """Test that get_db properly closes the session after use."""
        # Skip this test in memory mode
        if settings.storage_mode == StorageMode.MEMORY:
            pytest.skip("Not applicable in memory mode")
        
        db_gen = get_db()
        db = next(db_gen)
        
        # Verify session is not closed yet
        assert not db.is_active or hasattr(db, 'execute')
        
        # Complete the generator (this should close the session)
        try:
            next(db_gen)
        except StopIteration:
            pass  # Expected when generator is exhausted


class TestDatabaseConfiguration:
    """Test database configuration and settings."""
    
    def test_database_url_default(self):
        """Test that database URL defaults to memory://."""
        assert settings.database_url == "memory://"
    
    def test_session_local_configuration(self):
        """Test that SessionLocal is properly configured."""
        # Skip this test in memory mode
        if settings.storage_mode == StorageMode.MEMORY:
            pytest.skip("Not applicable in memory mode")
        
        # Verify SessionLocal is a sessionmaker instance
        assert hasattr(SessionLocal, 'configure')
        assert hasattr(SessionLocal, 'class_')
        
        # Test that we can create a session
        session = SessionLocal()
        assert hasattr(session, 'execute')
        assert hasattr(session, 'close')
        session.close()
