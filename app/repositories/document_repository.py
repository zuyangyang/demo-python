from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from datetime import datetime, timezone
import uuid
import base64

from app.models.document import Document, DocumentUpdate
from app.schemas.document import DocumentCreate, DocumentUpdate as DocumentUpdateSchema
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
    
    def add_document_update(
        self, 
        db: Session, 
        *, 
        document_id: str, 
        op_id: str, 
        actor_id: str, 
        delta_b64: str
    ) -> int:
        """
        Add a document update with atomic sequence assignment.
        
        Args:
            db: Database session
            document_id: ID of the document
            op_id: Unique operation ID for deduplication
            actor_id: ID of the actor making the update
            delta_b64: Base64 encoded delta data
            
        Returns:
            The assigned sequence number
            
        Raises:
            IntegrityError: If op_id already exists
        """
        # Decode base64 delta
        try:
            delta_blob = base64.b64decode(delta_b64)
        except Exception as e:
            raise ValueError(f"Invalid base64 delta data: {e}")
        
        # Get next sequence number atomically
        # Use a transaction to ensure atomicity
        with db.begin_nested():
            # Get the maximum sequence number for this document
            max_seq_result = db.execute(
                text("SELECT COALESCE(MAX(seq), 0) FROM document_updates WHERE document_id = :doc_id"),
                {"doc_id": document_id}
            ).scalar()
            
            next_seq = (max_seq_result or 0) + 1
            
            # Create the update record
            update_id = str(uuid.uuid4())
            update = DocumentUpdate(
                id=update_id,
                document_id=document_id,
                seq=next_seq,
                op_id=op_id,
                actor_id=actor_id,
                delta_blob=delta_blob
            )
            
            db.add(update)
            db.flush()  # Flush to check for op_id uniqueness constraint
            
            return next_seq
    
    def get_document_updates_after_version(
        self, 
        db: Session, 
        *, 
        document_id: str, 
        after_version: int
    ) -> List[DocumentUpdate]:
        """
        Get all document updates after a specific version.
        
        Args:
            db: Database session
            document_id: ID of the document
            after_version: Version number to get updates after
            
        Returns:
            List of updates ordered by sequence number
        """
        return db.query(DocumentUpdate)\
            .filter(
                and_(
                    DocumentUpdate.document_id == document_id,
                    DocumentUpdate.seq > after_version
                )
            )\
            .order_by(DocumentUpdate.seq)\
            .all()
    
    def get_document_latest_sequence(self, db: Session, *, document_id: str) -> int:
        """
        Get the latest sequence number for a document.
        
        Args:
            db: Database session
            document_id: ID of the document
            
        Returns:
            Latest sequence number, or 0 if no updates exist
        """
        result = db.execute(
            text("SELECT COALESCE(MAX(seq), 0) FROM document_updates WHERE document_id = :doc_id"),
            {"doc_id": document_id}
        ).scalar()
        
        return result if result is not None else 0
