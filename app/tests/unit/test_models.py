import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.document import Document, DocumentSnapshot, DocumentUpdate


class TestDocumentModels:
    """Test SQLAlchemy models for documents."""
    
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
    
    def test_document_table_creation(self, engine):
        """Test that document table is created with correct structure."""
        Base.metadata.create_all(bind=engine)
        
        with engine.connect() as conn:
            # Check that documents table exists
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='documents'
            """))
            assert result.fetchone() is not None
            
            # Check table structure
            result = conn.execute(text("PRAGMA table_info(documents)"))
            columns = {row[1]: row[2] for row in result.fetchall()}
            
            assert 'id' in columns
            assert 'title' in columns
            assert 'owner_id' in columns
            assert 'created_at' in columns
            assert 'updated_at' in columns
            assert 'deleted_at' in columns
    
    def test_document_snapshots_table_creation(self, engine):
        """Test that document_snapshots table is created with correct structure."""
        Base.metadata.create_all(bind=engine)
        
        with engine.connect() as conn:
            # Check that document_snapshots table exists
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='document_snapshots'
            """))
            assert result.fetchone() is not None
            
            # Check table structure
            result = conn.execute(text("PRAGMA table_info(document_snapshots)"))
            columns = {row[1]: row[2] for row in result.fetchall()}
            
            assert 'document_id' in columns
            assert 'version' in columns
            assert 'snapshot_blob' in columns
            assert 'created_at' in columns
            assert 'updated_at' in columns
    
    def test_document_updates_table_creation(self, engine):
        """Test that document_updates table is created with correct structure."""
        Base.metadata.create_all(bind=engine)
        
        with engine.connect() as conn:
            # Check that document_updates table exists
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='document_updates'
            """))
            assert result.fetchone() is not None
            
            # Check table structure
            result = conn.execute(text("PRAGMA table_info(document_updates)"))
            columns = {row[1]: row[2] for row in result.fetchall()}
            
            assert 'id' in columns
            assert 'document_id' in columns
            assert 'seq' in columns
            assert 'op_id' in columns
            assert 'actor_id' in columns
            assert 'delta_blob' in columns
            assert 'created_at' in columns
            assert 'updated_at' in columns
    
    def test_document_model_creation(self, session):
        """Test creating a document instance."""
        doc = Document(
            id="test-doc-123",
            title="Test Document",
            owner_id="user-123"
        )
        
        session.add(doc)
        session.commit()
        
        # Verify document was created
        retrieved_doc = session.query(Document).filter(Document.id == "test-doc-123").first()
        assert retrieved_doc is not None
        assert retrieved_doc.title == "Test Document"
        assert retrieved_doc.owner_id == "user-123"
        assert retrieved_doc.deleted_at is None
        assert retrieved_doc.created_at is not None
        assert retrieved_doc.updated_at is not None
    
    def test_document_snapshot_model_creation(self, session):
        """Test creating a document snapshot instance."""
        # First create a document
        doc = Document(id="test-doc-123", title="Test Document")
        session.add(doc)
        session.commit()
        
        # Create a snapshot
        snapshot = DocumentSnapshot(
            document_id="test-doc-123",
            version=1,
            snapshot_blob=b"test snapshot data"
        )
        
        session.add(snapshot)
        session.commit()
        
        # Verify snapshot was created
        retrieved_snapshot = session.query(DocumentSnapshot).filter(
            DocumentSnapshot.document_id == "test-doc-123"
        ).first()
        assert retrieved_snapshot is not None
        assert retrieved_snapshot.version == 1
        assert retrieved_snapshot.snapshot_blob == b"test snapshot data"
    
    def test_document_update_model_creation(self, session):
        """Test creating a document update instance."""
        # First create a document
        doc = Document(id="test-doc-123", title="Test Document")
        session.add(doc)
        session.commit()
        
        # Create an update
        update = DocumentUpdate(
            id="update-123",
            document_id="test-doc-123",
            seq=1,
            op_id="op-123",
            actor_id="user-123",
            delta_blob=b"test delta data"
        )
        
        session.add(update)
        session.commit()
        
        # Verify update was created
        retrieved_update = session.query(DocumentUpdate).filter(
            DocumentUpdate.id == "update-123"
        ).first()
        assert retrieved_update is not None
        assert retrieved_update.document_id == "test-doc-123"
        assert retrieved_update.seq == 1
        assert retrieved_update.op_id == "op-123"
        assert retrieved_update.actor_id == "user-123"
        assert retrieved_update.delta_blob == b"test delta data"
    
    def test_document_relationships(self, session):
        """Test that document relationships work correctly."""
        # Create a document
        doc = Document(id="test-doc-123", title="Test Document")
        session.add(doc)
        session.commit()
        
        # Create snapshots and updates
        snapshot = DocumentSnapshot(
            document_id="test-doc-123",
            version=1,
            snapshot_blob=b"snapshot data"
        )
        update = DocumentUpdate(
            id="update-123",
            document_id="test-doc-123",
            seq=1,
            op_id="op-123",
            actor_id="user-123",
            delta_blob=b"delta data"
        )
        
        session.add(snapshot)
        session.add(update)
        session.commit()
        
        # Test relationships
        retrieved_doc = session.query(Document).filter(Document.id == "test-doc-123").first()
        assert len(retrieved_doc.snapshots) == 1
        assert len(retrieved_doc.updates) == 1
        assert retrieved_doc.snapshots[0].version == 1
        assert retrieved_doc.updates[0].op_id == "op-123"
