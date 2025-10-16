from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base service class with common business logic operations."""
    
    def __init__(self, repository: BaseRepository):
        self.repository = repository
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single record by ID."""
        obj = self.repository.get(db, id)
        return obj
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[List] = None,
        order_by: Optional[Any] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination and filtering."""
        return self.repository.get_multi(
            db, 
            skip=skip, 
            limit=limit, 
            filters=filters, 
            order_by=order_by
        )
    
    def count(self, db: Session, *, filters: Optional[List] = None) -> int:
        """Count records with optional filtering."""
        return self.repository.count(db, filters=filters)
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        return self.repository.create(db, obj_in=obj_in)
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """Update an existing record."""
        return self.repository.update(db, db_obj=db_obj, obj_in=obj_in)
    
    def delete(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """Delete a record by ID."""
        return self.repository.delete(db, id=id)
