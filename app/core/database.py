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
