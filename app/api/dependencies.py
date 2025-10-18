from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

# Database dependency
def get_database(db: Session = Depends(get_db)) -> Session:
    """Get database session dependency."""
    return db
