from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.models.base import Base


# Create SQLite engine with appropriate configuration
engine = create_engine(
    settings.database_url,
    # SQLite-specific configurations
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,  # Allow SQLite to work with multiple threads
    },
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables.
    This should be called on application startup.
    """
    Base.metadata.create_all(bind=engine)


def check_connection() -> bool:
    """
    Check database connection by executing a simple query.
    Returns True if connection is successful, False otherwise.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def clear_tables():
    """
    Clear all data from all tables.
    This should be used for testing purposes only.
    """
    # First, dispose of all existing connections to prevent locks
    engine.dispose()
    
    # Wait a moment for connections to close
    import time
    time.sleep(0.1)
    
    try:
        with engine.connect() as connection:
            # Use PRAGMA to optimize for testing
            connection.execute(text("PRAGMA foreign_keys = OFF"))
            # Delete all data from all tables
            connection.execute(text("DELETE FROM document_updates"))
            connection.execute(text("DELETE FROM document_snapshots"))
            connection.execute(text("DELETE FROM documents"))
            # Reset autoincrement sequences if the table exists
            try:
                connection.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('documents', 'document_snapshots', 'document_updates')"))
            except Exception:
                # sqlite_sequence table doesn't exist yet, that's fine
                pass
            connection.execute(text("PRAGMA foreign_keys = ON"))
            connection.commit()
    except Exception as e:
        # If still locked, try one more time with a longer wait
        time.sleep(0.5)
        engine.dispose()
        with engine.connect() as connection:
            connection.execute(text("PRAGMA foreign_keys = OFF"))
            connection.execute(text("DELETE FROM document_updates"))
            connection.execute(text("DELETE FROM document_snapshots"))
            connection.execute(text("DELETE FROM documents"))
            try:
                connection.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('documents', 'document_snapshots', 'document_updates')"))
            except Exception:
                # sqlite_sequence table doesn't exist yet, that's fine
                pass
            connection.execute(text("PRAGMA foreign_keys = ON"))
            connection.commit()
