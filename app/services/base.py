from sqlalchemy.orm import Session
from app.core.database import get_db

class BaseService:
    """Base service class with common functionality."""

    def __init__(self, db: Session):
        self.db = db
