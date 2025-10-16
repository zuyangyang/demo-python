"""
Unit tests for in-memory document repository.
"""

import pytest
import base64
from datetime import datetime, timezone

from app.repositories.memory_document_repository import MemoryDocumentRepository
from app.core.memory_storage import memory_storage


class TestMemoryDocumentRepository:
    """Test in-memory document repository operations."""
    
    def setup_method(self):
        """Set up fresh storage for each test."""
        memory_storage.clear_all()
        self.repository = MemoryDocumentRepository()
    
    def test_create_document(self):
        """Test document creation."""
        doc = self.repository.create_document(title="Test Document", owner_id="user123")
        
        assert doc.title == "Test Document"
        assert doc.owner_id == "user123"
        assert doc.deleted_at is None
        assert doc.id is not None
        assert doc.created_at is not None
        assert doc.updated_at is not None
    
    def test_get_document(self):
        """Test getting a document."""
        doc = self.repository.create_document(title="Test Document")
        
        # Get existing document
        retrieved = self.repository.get_document(doc.id)
        assert retrieved is not None
        assert retrieved.id == doc.id
        assert retrieved.title == "Test Document"
        
        # Get non-existing document
        assert self.repository.get_document("nonexistent") is None
    
    def test_get_documents_with_filtering(self):
        """Test document listing with filtering."""
        # Create test documents
        doc1 = self.repository.create_document(title="First Document")
        doc2 = self.repository.create_document(title="Second Document")
        doc3 = self.repository.create_document(title="Third Item")
        
        # Test without filters
        docs = self.repository.get_documents()
        assert len(docs) == 3
        
        # Test with query filter
        docs = self.repository.get_documents(query="Document")
        assert len(docs) == 2
        assert all("Document" in doc.title for doc in docs)
        
        # Test with deleted filter
        self.repository.update_document(doc2.id, deleted=True)
        docs = self.repository.get_documents(include_deleted=False)
        assert len(docs) == 2
        docs = self.repository.get_documents(include_deleted=True)
        assert len(docs) == 3
    
    def test_get_documents_with_pagination(self):
        """Test document listing with pagination."""
        # Create test documents
        for i in range(5):
            self.repository.create_document(title=f"Document {i}")
        
        # Test pagination
        docs = self.repository.get_documents(page=1, page_size=2)
        assert len(docs) == 2
        
        docs = self.repository.get_documents(page=2, page_size=2)
        assert len(docs) == 2
        
        docs = self.repository.get_documents(page=3, page_size=2)
        assert len(docs) == 1
    
    def test_count_documents(self):
        """Test document counting."""
        # Create test documents
        doc1 = self.repository.create_document(title="First Document")
        doc2 = self.repository.create_document(title="Second Document")
        
        # Test counting
        assert self.repository.count_documents() == 2
        assert self.repository.count_documents(query="First") == 1
        
        # Test with deleted documents
        self.repository.update_document(doc1.id, deleted=True)
        assert self.repository.count_documents(include_deleted=False) == 1
        assert self.repository.count_documents(include_deleted=True) == 2
    
    def test_update_document(self):
        """Test document updates."""
        doc = self.repository.create_document(title="Original Title")
        
        # Update title
        updated = self.repository.update_document(doc.id, title="New Title")
        assert updated.title == "New Title"
        assert updated.updated_at >= doc.updated_at
        
        # Update deleted status
        updated = self.repository.update_document(doc.id, deleted=True)
        assert updated.deleted_at is not None
        
        # Undelete
        updated = self.repository.update_document(doc.id, deleted=False)
        assert updated.deleted_at is None
        
        # Update non-existing document
        assert self.repository.update_document("nonexistent", title="New") is None
    
    def test_soft_delete_document(self):
        """Test soft deleting a document."""
        doc = self.repository.create_document(title="Test Document")
        
        deleted = self.repository.soft_delete_document(doc.id)
        assert deleted is not None
        assert deleted.deleted_at is not None
        
        # Delete non-existing document
        assert self.repository.soft_delete_document("nonexistent") is None
    
    def test_add_document_update(self):
        """Test adding document updates."""
        doc = self.repository.create_document(title="Test Document")
        delta_b64 = base64.b64encode(b"test delta").decode()
        
        # Add update
        seq = self.repository.add_document_update(
            document_id=doc.id,
            op_id="op1",
            actor_id="actor1",
            delta_b64=delta_b64
        )
        assert seq == 1
        
        # Add another update
        seq = self.repository.add_document_update(
            document_id=doc.id,
            op_id="op2",
            actor_id="actor2",
            delta_b64=delta_b64
        )
        assert seq == 2
        
        # Test duplicate op_id
        with pytest.raises(ValueError, match="Operation ID op1 already exists"):
            self.repository.add_document_update(
                document_id=doc.id,
                op_id="op1",
                actor_id="actor3",
                delta_b64=delta_b64
            )
        
        # Test invalid base64
        with pytest.raises(ValueError, match="Invalid base64 delta data"):
            self.repository.add_document_update(
                document_id=doc.id,
                op_id="op3",
                actor_id="actor3",
                delta_b64="invalid_base64"
            )
    
    def test_get_document_updates_after_version(self):
        """Test getting updates after a specific version."""
        doc = self.repository.create_document(title="Test Document")
        delta_b64 = base64.b64encode(b"test delta").decode()
        
        # Add updates
        self.repository.add_document_update(doc.id, "op1", "actor1", delta_b64)
        self.repository.add_document_update(doc.id, "op2", "actor2", delta_b64)
        self.repository.add_document_update(doc.id, "op3", "actor3", delta_b64)
        
        # Get updates after version 1
        updates = self.repository.get_document_updates_after_version(doc.id, 1)
        assert len(updates) == 2
        assert updates[0].seq == 2
        assert updates[1].seq == 3
        
        # Get updates after version 0
        updates = self.repository.get_document_updates_after_version(doc.id, 0)
        assert len(updates) == 3
        
        # Get updates after latest version
        updates = self.repository.get_document_updates_after_version(doc.id, 3)
        assert len(updates) == 0
    
    def test_get_document_latest_sequence(self):
        """Test getting latest sequence number."""
        doc = self.repository.create_document(title="Test Document")
        delta_b64 = base64.b64encode(b"test delta").decode()
        
        # No updates yet
        assert self.repository.get_document_latest_sequence(doc.id) == 0
        
        # Add updates
        self.repository.add_document_update(doc.id, "op1", "actor1", delta_b64)
        assert self.repository.get_document_latest_sequence(doc.id) == 1
        
        self.repository.add_document_update(doc.id, "op2", "actor2", delta_b64)
        assert self.repository.get_document_latest_sequence(doc.id) == 2
    
    def test_add_document_snapshot(self):
        """Test adding document snapshots."""
        doc = self.repository.create_document(title="Test Document")
        snapshot_b64 = base64.b64encode(b"test snapshot").decode()
        
        # Add snapshot
        snapshot = self.repository.add_document_snapshot(
            document_id=doc.id,
            version=5,
            snapshot_b64=snapshot_b64
        )
        assert snapshot.document_id == doc.id
        assert snapshot.version == 5
        assert snapshot.snapshot_blob == b"test snapshot"
        
        # Test invalid base64
        with pytest.raises(ValueError, match="Invalid base64 snapshot data"):
            self.repository.add_document_snapshot(
                document_id=doc.id,
                version=6,
                snapshot_b64="invalid_base64"
            )
    
    def test_get_document_latest_snapshot(self):
        """Test getting latest snapshot."""
        doc = self.repository.create_document(title="Test Document")
        snapshot_b64 = base64.b64encode(b"test snapshot").decode()
        
        # No snapshots yet
        assert self.repository.get_document_latest_snapshot(doc.id) is None
        
        # Add snapshots
        self.repository.add_document_snapshot(doc.id, 1, snapshot_b64)
        self.repository.add_document_snapshot(doc.id, 3, snapshot_b64)
        self.repository.add_document_snapshot(doc.id, 2, snapshot_b64)
        
        # Get latest (should be version 3)
        latest = self.repository.get_document_latest_snapshot(doc.id)
        assert latest is not None
        assert latest.version == 3
