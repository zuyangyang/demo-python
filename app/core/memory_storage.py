"""
In-memory storage implementation for documents, snapshots, and updates.
This module provides the same interface as SQLite repositories but stores data in memory.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid
import base64
import threading
from dataclasses import dataclass, field

from app.models.document import Document, DocumentSnapshot, DocumentUpdate
from app.schemas.document import DocumentCreate, DocumentUpdate as DocumentUpdateSchema


@dataclass
class MemoryDocument:
    """In-memory document representation."""
    id: str
    title: str
    owner_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


@dataclass
class MemoryDocumentSnapshot:
    """In-memory document snapshot representation."""
    document_id: str
    version: int
    snapshot_blob: bytes
    created_at: datetime


@dataclass
class MemoryDocumentUpdate:
    """In-memory document update representation."""
    id: str
    document_id: str
    seq: int
    op_id: str
    actor_id: str
    delta_blob: bytes
    created_at: datetime


class MemoryStorage:
    """Thread-safe in-memory storage for all document-related data."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._documents: Dict[str, MemoryDocument] = {}
        self._document_snapshots: Dict[str, List[MemoryDocumentSnapshot]] = {}
        self._document_updates: Dict[str, List[MemoryDocumentUpdate]] = {}
        self._op_ids: set = set()  # Track op_ids for deduplication
        self._sequence_counters: Dict[str, int] = {}  # Track sequence numbers per document
    
    def clear_all(self):
        """Clear all stored data. Used for testing."""
        with self._lock:
            self._documents.clear()
            self._document_snapshots.clear()
            self._document_updates.clear()
            self._op_ids.clear()
            self._sequence_counters.clear()
    
    # Document operations
    def create_document(self, title: str, owner_id: Optional[str] = None) -> MemoryDocument:
        """Create a new document."""
        with self._lock:
            document_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            document = MemoryDocument(
                id=document_id,
                title=title,
                owner_id=owner_id,
                created_at=now,
                updated_at=now
            )
            self._documents[document_id] = document
            self._document_snapshots[document_id] = []
            self._document_updates[document_id] = []
            self._sequence_counters[document_id] = 0
            return document
    
    def get_document(self, document_id: str) -> Optional[MemoryDocument]:
        """Get a document by ID."""
        with self._lock:
            return self._documents.get(document_id)
    
    def get_documents(
        self,
        query: Optional[str] = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> List[MemoryDocument]:
        """Get documents with filtering and pagination."""
        with self._lock:
            documents = list(self._documents.values())
            
            # Filter by query
            if query:
                documents = [d for d in documents if query.lower() in d.title.lower()]
            
            # Filter by deleted status
            if not include_deleted:
                documents = [d for d in documents if d.deleted_at is None]
            
            # Sort by updated_at descending
            documents.sort(key=lambda d: d.updated_at, reverse=True)
            
            # Paginate
            skip = (page - 1) * page_size
            return documents[skip:skip + page_size]
    
    def count_documents(
        self,
        query: Optional[str] = None,
        include_deleted: bool = False
    ) -> int:
        """Count documents with filtering."""
        with self._lock:
            documents = list(self._documents.values())
            
            # Filter by query
            if query:
                documents = [d for d in documents if query.lower() in d.title.lower()]
            
            # Filter by deleted status
            if not include_deleted:
                documents = [d for d in documents if d.deleted_at is None]
            
            return len(documents)
    
    def update_document(
        self,
        document_id: str,
        title: Optional[str] = None,
        deleted: Optional[bool] = None
    ) -> Optional[MemoryDocument]:
        """Update a document's title and/or deleted status."""
        with self._lock:
            document = self._documents.get(document_id)
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
            
            return document
    
    def soft_delete_document(self, document_id: str) -> Optional[MemoryDocument]:
        """Soft delete a document by setting deleted_at timestamp."""
        return self.update_document(document_id, deleted=True)
    
    # Document update operations
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
            ValueError: If op_id already exists or delta_b64 is invalid
        """
        with self._lock:
            # Check if op_id already exists
            if op_id in self._op_ids:
                raise ValueError(f"Operation ID {op_id} already exists")
            
            # Decode base64 delta
            try:
                delta_blob = base64.b64decode(delta_b64)
            except Exception as e:
                raise ValueError(f"Invalid base64 delta data: {e}")
            
            # Get next sequence number
            current_seq = self._sequence_counters.get(document_id, 0)
            next_seq = current_seq + 1
            
            # Create the update record
            update_id = str(uuid.uuid4())
            update = MemoryDocumentUpdate(
                id=update_id,
                document_id=document_id,
                seq=next_seq,
                op_id=op_id,
                actor_id=actor_id,
                delta_blob=delta_blob,
                created_at=datetime.now(timezone.utc)
            )
            
            # Store the update
            if document_id not in self._document_updates:
                self._document_updates[document_id] = []
            self._document_updates[document_id].append(update)
            
            # Update counters
            self._op_ids.add(op_id)
            self._sequence_counters[document_id] = next_seq
            
            return next_seq
    
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
        with self._lock:
            updates = self._document_updates.get(document_id, [])
            return [u for u in updates if u.seq > after_version]
    
    def get_document_latest_sequence(self, document_id: str) -> int:
        """
        Get the latest sequence number for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Latest sequence number, or 0 if no updates exist
        """
        with self._lock:
            return self._sequence_counters.get(document_id, 0)
    
    # Document snapshot operations
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
        with self._lock:
            # Decode base64 snapshot
            try:
                snapshot_blob = base64.b64decode(snapshot_b64)
            except Exception as e:
                raise ValueError(f"Invalid base64 snapshot data: {e}")
            
            snapshot = MemoryDocumentSnapshot(
                document_id=document_id,
                version=version,
                snapshot_blob=snapshot_blob,
                created_at=datetime.now(timezone.utc)
            )
            
            # Store the snapshot
            if document_id not in self._document_snapshots:
                self._document_snapshots[document_id] = []
            self._document_snapshots[document_id].append(snapshot)
            
            return snapshot
    
    def get_document_latest_snapshot(self, document_id: str) -> Optional[MemoryDocumentSnapshot]:
        """
        Get the latest snapshot for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            The latest snapshot, or None if no snapshots exist
        """
        with self._lock:
            snapshots = self._document_snapshots.get(document_id, [])
            if not snapshots:
                return None
            
            # Return the snapshot with the highest version
            return max(snapshots, key=lambda s: s.version)


# Global in-memory storage instance
memory_storage = MemoryStorage()
