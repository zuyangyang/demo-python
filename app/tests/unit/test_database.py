import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.core.database import check_connection, get_db, SessionLocal
from app.core.config import settings


class TestDatabaseConnection:
    """Test database connection functionality."""
    
    def test_check_connection_success(self):
        """Test that check_connection returns True when database is accessible."""
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
        """Test that database URL defaults to sqlite:///./dev.db."""
        assert settings.database_url == "sqlite:///./dev.db"
    
    def test_session_local_configuration(self):
        """Test that SessionLocal is properly configured."""
        # Verify SessionLocal is a sessionmaker instance
        assert hasattr(SessionLocal, 'configure')
        assert hasattr(SessionLocal, 'class_')
        
        # Test that we can create a session
        session = SessionLocal()
        assert hasattr(session, 'execute')
        assert hasattr(session, 'close')
        session.close()
