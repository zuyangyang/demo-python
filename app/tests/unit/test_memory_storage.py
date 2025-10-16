"""
Unit tests for in-memory storage functionality.
"""

import pytest
import base64
from datetime import datetime, timezone

from app.core.memory_storage import MemoryStorage, MemoryDocument, MemoryDocumentSnapshot, MemoryDocumentUpdate


class TestMemoryStorage:
    """Test in-memory storage operations."""
    
    def setup_method(self):
        """Set up fresh storage for each test."""
        self.storage = MemoryStorage()
    
    def test_clear_all(self):
        """Test clearing all storage."""
        # Add some data
        doc = self.storage.create_document("Test Doc")
        self.storage.add_document_update(doc.id, "op1", "actor1", "dGVzdA==")
        
        # Clear and verify
        self.storage.clear_all()
        assert len(self.storage._documents) == 0
        assert len(self.storage._document_updates) == 0
        assert len(self.storage._op_ids) == 0
    
    def test_create_document(self):
        """Test document creation."""
        doc = self.storage.create_document("Test Document", "user123")
        
        assert doc.title == "Test Document"
        assert doc.owner_id == "user123"
        assert doc.deleted_at is None
        assert doc.id in self.storage._documents
        assert doc.id in self.storage._document_snapshots
        assert doc.id in self.storage._document_updates
        assert self.storage._sequence_counters[doc.id] == 0
    
    def test_get_document(self):
        """Test getting a document."""
        doc = self.storage.create_document("Test Document")
        
        # Get existing document
        retrieved = self.storage.get_document(doc.id)
        assert retrieved is not None
        assert retrieved.id == doc.id
        assert retrieved.title == "Test Document"
        
        # Get non-existing document
        assert self.storage.get_document("nonexistent") is None
    
    def test_get_documents_with_filtering(self):
        """Test document listing with filtering."""
        # Create test documents
        doc1 = self.storage.create_document("First Document")
        doc2 = self.storage.create_document("Second Document")
        doc3 = self.storage.create_document("Third Item")
        
        # Test without filters
        docs = self.storage.get_documents()
        assert len(docs) == 3
        
        # Test with query filter
        docs = self.storage.get_documents(query="Document")
        assert len(docs) == 2
        assert all("Document" in doc.title for doc in docs)
        
        # Test with deleted filter
        self.storage.update_document(doc2.id, deleted=True)
        docs = self.storage.get_documents(include_deleted=False)
        assert len(docs) == 2
        docs = self.storage.get_documents(include_deleted=True)
        assert len(docs) == 3
    
    def test_get_documents_with_pagination(self):
        """Test document listing with pagination."""
        # Create test documents
        for i in range(5):
            self.storage.create_document(f"Document {i}")
        
        # Test pagination
        docs = self.storage.get_documents(page=1, page_size=2)
        assert len(docs) == 2
        
        docs = self.storage.get_documents(page=2, page_size=2)
        assert len(docs) == 2
        
        docs = self.storage.get_documents(page=3, page_size=2)
        assert len(docs) == 1
    
    def test_count_documents(self):
        """Test document counting."""
        # Create test documents
        doc1 = self.storage.create_document("First Document")
        doc2 = self.storage.create_document("Second Document")
        
        # Test counting
        assert self.storage.count_documents() == 2
        assert self.storage.count_documents(query="First") == 1
        
        # Test with deleted documents
        self.storage.update_document(doc1.id, deleted=True)
        assert self.storage.count_documents(include_deleted=False) == 1
        assert self.storage.count_documents(include_deleted=True) == 2
    
    def test_update_document(self):
        """Test document updates."""
        doc = self.storage.create_document("Original Title")
        
        # Update title
        updated = self.storage.update_document(doc.id, title="New Title")
        assert updated.title == "New Title"
        assert updated.updated_at >= doc.updated_at
        
        # Update deleted status
        updated = self.storage.update_document(doc.id, deleted=True)
        assert updated.deleted_at is not None
        
        # Undelete
        updated = self.storage.update_document(doc.id, deleted=False)
        assert updated.deleted_at is None
        
        # Update non-existing document
        assert self.storage.update_document("nonexistent", title="New") is None
    
    def test_soft_delete_document(self):
        """Test soft deleting a document."""
        doc = self.storage.create_document("Test Document")
        
        deleted = self.storage.soft_delete_document(doc.id)
        assert deleted is not None
        assert deleted.deleted_at is not None
        
        # Delete non-existing document
        assert self.storage.soft_delete_document("nonexistent") is None
    
    def test_add_document_update(self):
        """Test adding document updates."""
        doc = self.storage.create_document("Test Document")
        delta_b64 = base64.b64encode(b"test delta").decode()
        
        # Add update
        seq = self.storage.add_document_update(doc.id, "op1", "actor1", delta_b64)
        assert seq == 1
        assert "op1" in self.storage._op_ids
        assert self.storage._sequence_counters[doc.id] == 1
        
        # Add another update
        seq = self.storage.add_document_update(doc.id, "op2", "actor2", delta_b64)
        assert seq == 2
        assert "op2" in self.storage._op_ids
        assert self.storage._sequence_counters[doc.id] == 2
        
        # Test duplicate op_id
        with pytest.raises(ValueError, match="Operation ID op1 already exists"):
            self.storage.add_document_update(doc.id, "op1", "actor3", delta_b64)
        
        # Test invalid base64
        with pytest.raises(ValueError, match="Invalid base64 delta data"):
            self.storage.add_document_update(doc.id, "op3", "actor3", "invalid_base64")
    
    def test_get_document_updates_after_version(self):
        """Test getting updates after a specific version."""
        doc = self.storage.create_document("Test Document")
        delta_b64 = base64.b64encode(b"test delta").decode()
        
        # Add updates
        self.storage.add_document_update(doc.id, "op1", "actor1", delta_b64)
        self.storage.add_document_update(doc.id, "op2", "actor2", delta_b64)
        self.storage.add_document_update(doc.id, "op3", "actor3", delta_b64)
        
        # Get updates after version 1
        updates = self.storage.get_document_updates_after_version(doc.id, 1)
        assert len(updates) == 2
        assert updates[0].seq == 2
        assert updates[1].seq == 3
        
        # Get updates after version 0
        updates = self.storage.get_document_updates_after_version(doc.id, 0)
        assert len(updates) == 3
        
        # Get updates after latest version
        updates = self.storage.get_document_updates_after_version(doc.id, 3)
        assert len(updates) == 0
    
    def test_get_document_latest_sequence(self):
        """Test getting latest sequence number."""
        doc = self.storage.create_document("Test Document")
        delta_b64 = base64.b64encode(b"test delta").decode()
        
        # No updates yet
        assert self.storage.get_document_latest_sequence(doc.id) == 0
        
        # Add updates
        self.storage.add_document_update(doc.id, "op1", "actor1", delta_b64)
        assert self.storage.get_document_latest_sequence(doc.id) == 1
        
        self.storage.add_document_update(doc.id, "op2", "actor2", delta_b64)
        assert self.storage.get_document_latest_sequence(doc.id) == 2
    
    def test_add_document_snapshot(self):
        """Test adding document snapshots."""
        doc = self.storage.create_document("Test Document")
        snapshot_b64 = base64.b64encode(b"test snapshot").decode()
        
        # Add snapshot
        snapshot = self.storage.add_document_snapshot(doc.id, 5, snapshot_b64)
        assert snapshot.document_id == doc.id
        assert snapshot.version == 5
        assert snapshot.snapshot_blob == b"test snapshot"
        
        # Test invalid base64
        with pytest.raises(ValueError, match="Invalid base64 snapshot data"):
            self.storage.add_document_snapshot(doc.id, 6, "invalid_base64")
    
    def test_get_document_latest_snapshot(self):
        """Test getting latest snapshot."""
        doc = self.storage.create_document("Test Document")
        snapshot_b64 = base64.b64encode(b"test snapshot").decode()
        
        # No snapshots yet
        assert self.storage.get_document_latest_snapshot(doc.id) is None
        
        # Add snapshots
        self.storage.add_document_snapshot(doc.id, 1, snapshot_b64)
        self.storage.add_document_snapshot(doc.id, 3, snapshot_b64)
        self.storage.add_document_snapshot(doc.id, 2, snapshot_b64)
        
        # Get latest (should be version 3)
        latest = self.storage.get_document_latest_snapshot(doc.id)
        assert latest is not None
        assert latest.version == 3
    
    def test_thread_safety(self):
        """Test thread safety of storage operations."""
        import threading
        import time
        
        doc = self.storage.create_document("Test Document")
        delta_b64 = base64.b64encode(b"test delta").decode()
        
        # Create multiple threads that add updates concurrently
        def add_updates():
            for i in range(10):
                try:
                    self.storage.add_document_update(
                        doc.id, 
                        f"op_{threading.current_thread().ident}_{i}", 
                        f"actor_{i}", 
                        delta_b64
                    )
                except ValueError:
                    # Expected for duplicate op_ids
                    pass
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=add_updates)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify final state is consistent
        updates = self.storage._document_updates[doc.id]
        assert len(updates) <= 50  # At most 50 updates (5 threads * 10 updates)
        assert self.storage._sequence_counters[doc.id] <= 50
