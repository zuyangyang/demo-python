from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timezone
import uuid

from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document, DocumentCreate, DocumentUpdate]):
    """Repository for document operations."""
    
    def __init__(self):
        super().__init__(Document)
    
    def create_document(self, db: Session, *, title: str, owner_id: Optional[str] = None) -> Document:
        """Create a new document with generated UUID."""
        document_id = str(uuid.uuid4())
        document = Document(
            id=document_id,
            title=title,
            owner_id=owner_id,
            deleted_at=None
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
    
    def get_document(self, db: Session, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        return db.query(Document).filter(Document.id == document_id).first()
    
    def get_documents(
        self, 
        db: Session, 
        *, 
        query: Optional[str] = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> List[Document]:
        """Get documents with filtering and pagination."""
        filters = []
        
        # Filter by title if query provided
        if query:
            filters.append(Document.title.contains(query))
        
        # Filter by deleted status
        if not include_deleted:
            filters.append(Document.deleted_at.is_(None))
        
        skip = (page - 1) * page_size
        return self.get_multi(
            db,
            skip=skip,
            limit=page_size,
            filters=filters,
            order_by=desc(Document.updated_at)
        )
    
    def count_documents(
        self, 
        db: Session, 
        *, 
        query: Optional[str] = None,
        include_deleted: bool = False
    ) -> int:
        """Count documents with filtering."""
        filters = []
        
        # Filter by title if query provided
        if query:
            filters.append(Document.title.contains(query))
        
        # Filter by deleted status
        if not include_deleted:
            filters.append(Document.deleted_at.is_(None))
        
        return self.count(db, filters=filters)
    
    def update_document(
        self, 
        db: Session, 
        *, 
        document_id: str, 
        title: Optional[str] = None,
        deleted: Optional[bool] = None
    ) -> Optional[Document]:
        """Update a document's title and/or deleted status."""
        document = self.get_document(db, document_id)
        if not document:
            return None
        
        # Update title if provided
        if title is not None:
            document.title = title
        
        # Update deleted status
        if deleted is not None:
            if deleted:
                document.deleted_at = datetime.now(timezone.utc)
            else:
                document.deleted_at = None
        
        # Update the updated_at timestamp
        document.updated_at = datetime.now(timezone.utc)
        
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
    
    def soft_delete_document(self, db: Session, *, document_id: str) -> Optional[Document]:
        """Soft delete a document by setting deleted_at timestamp."""
        return self.update_document(
            db, 
            document_id=document_id, 
            deleted=True
        )
