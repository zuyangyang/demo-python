"""Unit tests for document update repository methods."""

import base64
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.document import Document, DocumentUpdate
from app.repositories.document_repository import DocumentRepository


class TestDocumentUpdateRepository:
    """Test document update repository methods."""
    
    @pytest.fixture
    def engine(self):
        """Create an in-memory SQLite engine for testing."""
        return create_engine(
            "sqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    
    @pytest.fixture
    def session(self, engine):
        """Create a database session for testing."""
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    @pytest.fixture
    def repository(self):
        """Create a document repository instance."""
        return DocumentRepository()
    
    @pytest.fixture
    def test_document(self, session):
        """Create a test document."""
        doc = Document(
            id="test-doc-123",
            title="Test Document",
            owner_id="user-123"
        )
        session.add(doc)
        session.commit()
        return doc
    
    def test_add_document_update_success(self, repository, session, test_document):
        """Test successfully adding a document update."""
        # Prepare test data
        op_id = "op-123"
        actor_id = "user-456"
        delta_data = b"test delta data"
        delta_b64 = base64.b64encode(delta_data).decode('utf-8')
        
        # Add update
        seq = repository.add_document_update(
            session,
            document_id=test_document.id,
            op_id=op_id,
            actor_id=actor_id,
            delta_b64=delta_b64
        )
        
        # Verify sequence number
        assert seq == 1
        
        # Verify update was persisted
        update = session.query(DocumentUpdate).filter(
            DocumentUpdate.op_id == op_id
        ).first()
        
        assert update is not None
        assert update.document_id == test_document.id
        assert update.seq == 1
        assert update.op_id == op_id
        assert update.actor_id == actor_id
        assert update.delta_blob == delta_data
    
    def test_add_document_update_duplicate_op_id(self, repository, session, test_document):
        """Test that duplicate op_id raises IntegrityError."""
        # Prepare test data
        op_id = "op-123"
        actor_id = "user-456"
        delta_b64 = base64.b64encode(b"test delta data").decode('utf-8')
        
        # Add first update
        repository.add_document_update(
            session,
            document_id=test_document.id,
            op_id=op_id,
            actor_id=actor_id,
            delta_b64=delta_b64
        )
        
        # Try to add update with same op_id
        with pytest.raises(IntegrityError):
            repository.add_document_update(
                session,
                document_id=test_document.id,
                op_id=op_id,  # Same op_id
                actor_id="user-789",
                delta_b64=base64.b64encode(b"different delta").decode('utf-8')
            )
    
    def test_add_document_update_sequence_monotonicity(self, repository, session, test_document):
        """Test that sequence numbers are strictly increasing."""
        # Add multiple updates
        sequences = []
        for i in range(5):
            op_id = f"op-{i}"
            actor_id = f"user-{i}"
            delta_b64 = base64.b64encode(f"delta-{i}".encode()).decode('utf-8')
            
            seq = repository.add_document_update(
                session,
                document_id=test_document.id,
                op_id=op_id,
                actor_id=actor_id,
                delta_b64=delta_b64
            )
            sequences.append(seq)
        
        # Verify sequences are monotonic
        assert sequences == [1, 2, 3, 4, 5]
        
        # Verify all updates were persisted
        updates = session.query(DocumentUpdate).filter(
            DocumentUpdate.document_id == test_document.id
        ).order_by(DocumentUpdate.seq).all()
        
        assert len(updates) == 5
        for i, update in enumerate(updates, 1):
            assert update.seq == i
    
    def test_add_document_update_invalid_base64(self, repository, session, test_document):
        """Test that invalid base64 data raises ValueError."""
        with pytest.raises(ValueError, match="Invalid base64 delta data"):
            repository.add_document_update(
                session,
                document_id=test_document.id,
                op_id="op-123",
                actor_id="user-456",
                delta_b64="invalid-base64-data!"
            )
    
    def test_get_document_updates_after_version(self, repository, session, test_document):
        """Test getting updates after a specific version."""
        # Add updates with different sequences
        for i in range(1, 6):
            op_id = f"op-{i}"
            actor_id = f"user-{i}"
            delta_b64 = base64.b64encode(f"delta-{i}".encode()).decode('utf-8')
            
            repository.add_document_update(
                session,
                document_id=test_document.id,
                op_id=op_id,
                actor_id=actor_id,
                delta_b64=delta_b64
            )
        
        # Get updates after version 2
        updates = repository.get_document_updates_after_version(
            session,
            document_id=test_document.id,
            after_version=2
        )
        
        # Should get updates with seq 3, 4, 5
        assert len(updates) == 3
        assert [update.seq for update in updates] == [3, 4, 5]
        assert [update.op_id for update in updates] == ["op-3", "op-4", "op-5"]
    
    def test_get_document_updates_after_version_empty(self, repository, session, test_document):
        """Test getting updates after version when no updates exist."""
        updates = repository.get_document_updates_after_version(
            session,
            document_id=test_document.id,
            after_version=0
        )
        
        assert len(updates) == 0
    
    def test_get_document_updates_after_version_nonexistent_document(self, repository, session):
        """Test getting updates for non-existent document."""
        updates = repository.get_document_updates_after_version(
            session,
            document_id="nonexistent-doc",
            after_version=0
        )
        
        assert len(updates) == 0
    
    def test_get_document_latest_sequence(self, repository, session, test_document):
        """Test getting the latest sequence number for a document."""
        # Initially should be 0
        latest_seq = repository.get_document_latest_sequence(
            session,
            document_id=test_document.id
        )
        assert latest_seq == 0
        
        # Add some updates
        for i in range(1, 4):
            op_id = f"op-{i}"
            actor_id = f"user-{i}"
            delta_b64 = base64.b64encode(f"delta-{i}".encode()).decode('utf-8')
            
            repository.add_document_update(
                session,
                document_id=test_document.id,
                op_id=op_id,
                actor_id=actor_id,
                delta_b64=delta_b64
            )
        
        # Latest sequence should be 3
        latest_seq = repository.get_document_latest_sequence(
            session,
            document_id=test_document.id
        )
        assert latest_seq == 3
    
    def test_get_document_latest_sequence_nonexistent_document(self, repository, session):
        """Test getting latest sequence for non-existent document."""
        latest_seq = repository.get_document_latest_sequence(
            session,
            document_id="nonexistent-doc"
        )
        assert latest_seq == 0
    
    def test_sequence_assignment_atomic(self, repository, session, test_document):
        """Test that sequence assignment is atomic."""
        # This test simulates concurrent access by using the same session
        # In a real scenario, this would be tested with actual concurrency
        
        # Add first update
        seq1 = repository.add_document_update(
            session,
            document_id=test_document.id,
            op_id="op-1",
            actor_id="user-1",
            delta_b64=base64.b64encode(b"delta-1").decode('utf-8')
        )
        
        # Add second update
        seq2 = repository.add_document_update(
            session,
            document_id=test_document.id,
            op_id="op-2",
            actor_id="user-2",
            delta_b64=base64.b64encode(b"delta-2").decode('utf-8')
        )
        
        # Verify sequences are unique and monotonic
        assert seq1 == 1
        assert seq2 == 2
        assert seq1 < seq2
        
        # Verify both updates exist
        updates = session.query(DocumentUpdate).filter(
            DocumentUpdate.document_id == test_document.id
        ).order_by(DocumentUpdate.seq).all()
        
        assert len(updates) == 2
        assert updates[0].seq == 1
        assert updates[1].seq == 2
    
    def test_update_with_large_delta(self, repository, session, test_document):
        """Test adding update with large delta data."""
        # Create large delta data
        large_delta = b"x" * 10000  # 10KB of data
        delta_b64 = base64.b64encode(large_delta).decode('utf-8')
        
        # Add update
        seq = repository.add_document_update(
            session,
            document_id=test_document.id,
            op_id="op-large",
            actor_id="user-large",
            delta_b64=delta_b64
        )
        
        # Verify update was persisted correctly
        update = session.query(DocumentUpdate).filter(
            DocumentUpdate.op_id == "op-large"
        ).first()
        
        assert update is not None
        assert update.delta_blob == large_delta
        assert len(update.delta_blob) == 10000
