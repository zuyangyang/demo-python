from typing import List, Optional, Union
from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentOut, DocumentListResponse
from app.repositories.document_repository import DocumentRepository
from app.repositories.memory_document_repository import MemoryDocumentRepository
from app.core.storage_factory import get_document_repository
from app.core.exceptions import DocumentNotFoundError


class DocumentService:
    """Service for document business logic operations."""
    
    def __init__(self, repository: Union[DocumentRepository, MemoryDocumentRepository]):
        self.repository = repository
    
    def create_document(
        self, 
        db: Optional[Session], 
        *, 
        title: str, 
        owner_id: Optional[str] = None
    ) -> DocumentOut:
        """Create a new document."""
        document = self.repository.create_document(
            title=title, 
            owner_id=owner_id
        )
        return DocumentOut.model_validate(document)
    
    def get_document(self, db: Optional[Session], *, document_id: str) -> DocumentOut:
        """Get a document by ID."""
        document = self.repository.get_document(document_id)
        if not document:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")
        return DocumentOut.model_validate(document)
    
    def get_documents(
        self, 
        db: Optional[Session], 
        *, 
        query: Optional[str] = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> DocumentListResponse:
        """Get documents with filtering and pagination."""
        documents = self.repository.get_documents(
            query=query,
            include_deleted=include_deleted,
            page=page,
            page_size=page_size
        )
        
        total = self.repository.count_documents(
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
        db: Optional[Session], 
        *, 
        document_id: str, 
        title: Optional[str] = None,
        deleted: Optional[bool] = None
    ) -> DocumentOut:
        """Update a document's title and/or deleted status."""
        document = self.repository.update_document(
            document_id=document_id,
            title=title,
            deleted=deleted
        )
        
        if not document:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")
        
        return DocumentOut.model_validate(document)
    
    def delete_document(self, db: Optional[Session], *, document_id: str) -> None:
        """Soft delete a document."""
        document = self.repository.soft_delete_document(document_id=document_id)
        if not document:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")
