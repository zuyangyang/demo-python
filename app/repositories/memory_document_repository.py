"""
In-memory document repository implementation.
Provides the same interface as SQLite repository but uses in-memory storage.
"""

from typing import List, Optional
from datetime import datetime, timezone
import uuid
import base64

from app.core.memory_storage import memory_storage, MemoryDocument, MemoryDocumentSnapshot, MemoryDocumentUpdate
from app.schemas.document import DocumentCreate, DocumentUpdate as DocumentUpdateSchema


class MemoryDocumentRepository:
    """In-memory repository for document operations."""
    
    def create_document(self, *, title: str, owner_id: Optional[str] = None) -> MemoryDocument:
        """Create a new document with generated UUID."""
        return memory_storage.create_document(title=title, owner_id=owner_id)
    
    def get_document(self, document_id: str) -> Optional[MemoryDocument]:
        """Get a document by ID."""
        return memory_storage.get_document(document_id)
    
    def get_documents(
        self, 
        *, 
        query: Optional[str] = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> List[MemoryDocument]:
        """Get documents with filtering and pagination."""
        return memory_storage.get_documents(
            query=query,
            include_deleted=include_deleted,
            page=page,
            page_size=page_size
        )
    
    def count_documents(
        self, 
        *, 
        query: Optional[str] = None,
        include_deleted: bool = False
    ) -> int:
        """Count documents with filtering."""
        return memory_storage.count_documents(
            query=query,
            include_deleted=include_deleted
        )
    
    def update_document(
        self, 
        document_id: str, 
        *, 
        title: Optional[str] = None,
        deleted: Optional[bool] = None
    ) -> Optional[MemoryDocument]:
        """Update a document's title and/or deleted status."""
        return memory_storage.update_document(
            document_id=document_id,
            title=title,
            deleted=deleted
        )
    
    def soft_delete_document(self, document_id: str) -> Optional[MemoryDocument]:
        """Soft delete a document by setting deleted_at timestamp."""
        return memory_storage.soft_delete_document(document_id)
    
    def add_document_update(
        self, 
        document_id: str, 
        op_id: str, 
        actor_id: str, 
        delta_b64: str
    ) -> int:
        """
        Add a document update with atomic sequence assignment.
        
        Args:
            document_id: ID of the document
            op_id: Unique operation ID for deduplication
            actor_id: ID of the actor making the update
            delta_b64: Base64 encoded delta data
            
        Returns:
            The assigned sequence number
            
        Raises:
            ValueError: If op_id already exists
        """
        return memory_storage.add_document_update(
            document_id=document_id,
            op_id=op_id,
            actor_id=actor_id,
            delta_b64=delta_b64
        )
    
    def get_document_updates_after_version(
        self, 
        document_id: str, 
        after_version: int
    ) -> List[MemoryDocumentUpdate]:
        """
        Get all document updates after a specific version.
        
        Args:
            document_id: ID of the document
            after_version: Version number to get updates after
            
        Returns:
            List of updates ordered by sequence number
        """
        return memory_storage.get_document_updates_after_version(
            document_id=document_id,
            after_version=after_version
        )
    
    def get_document_latest_sequence(self, document_id: str) -> int:
        """
        Get the latest sequence number for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Latest sequence number, or 0 if no updates exist
        """
        return memory_storage.get_document_latest_sequence(document_id)
    
    def add_document_snapshot(
        self,
        document_id: str,
        version: int,
        snapshot_b64: str
    ) -> MemoryDocumentSnapshot:
        """
        Add a document snapshot.
        
        Args:
            document_id: ID of the document
            version: Version number of the snapshot
            snapshot_b64: Base64 encoded snapshot data
            
        Returns:
            The created snapshot
            
        Raises:
            ValueError: If snapshot_b64 is invalid
        """
        return memory_storage.add_document_snapshot(
            document_id=document_id,
            version=version,
            snapshot_b64=snapshot_b64
        )
    
    def get_document_latest_snapshot(self, document_id: str) -> Optional[MemoryDocumentSnapshot]:
        """
        Get the latest snapshot for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            The latest snapshot, or None if no snapshots exist
        """
        return memory_storage.get_document_latest_snapshot(document_id)
