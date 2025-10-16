from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentOut, DocumentListResponse
from app.repositories.document_repository import DocumentRepository
from app.core.exceptions import DocumentNotFoundError


class DocumentService:
    """Service for document business logic operations."""
    
    def __init__(self, repository: DocumentRepository):
        self.repository = repository
    
    def create_document(
        self, 
        db: Session, 
        *, 
        title: str, 
        owner_id: Optional[str] = None
    ) -> DocumentOut:
        """Create a new document."""
        document = self.repository.create_document(
            db, 
            title=title, 
            owner_id=owner_id
        )
        return DocumentOut.model_validate(document)
    
    def get_document(self, db: Session, *, document_id: str) -> DocumentOut:
        """Get a document by ID."""
        document = self.repository.get_document(db, document_id)
        if not document:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")
        return DocumentOut.model_validate(document)
    
    def get_documents(
        self, 
        db: Session, 
        *, 
        query: Optional[str] = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> DocumentListResponse:
        """Get documents with filtering and pagination."""
        documents = self.repository.get_documents(
            db,
            query=query,
            include_deleted=include_deleted,
            page=page,
            page_size=page_size
        )
        
        total = self.repository.count_documents(
            db,
            query=query,
            include_deleted=include_deleted
        )
        
        return DocumentListResponse(
            items=[DocumentOut.model_validate(doc) for doc in documents],
            page=page,
            page_size=page_size,
            total=total
        )
    
    def update_document(
        self, 
        db: Session, 
        *, 
        document_id: str, 
        title: Optional[str] = None,
        deleted: Optional[bool] = None
    ) -> DocumentOut:
        """Update a document's title and/or deleted status."""
        document = self.repository.update_document(
            db,
            document_id=document_id,
            title=title,
            deleted=deleted
        )
        
        if not document:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")
        
        return DocumentOut.model_validate(document)
    
    def delete_document(self, db: Session, *, document_id: str) -> None:
        """Soft delete a document."""
        document = self.repository.soft_delete_document(db, document_id=document_id)
        if not document:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")
