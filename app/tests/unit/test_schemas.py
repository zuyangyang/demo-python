import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentOut,
    DocumentListResponse
)


class TestDocumentSchemas:
    """Test Pydantic schemas for document operations."""
    
    def test_document_create_valid(self):
        """Test creating a valid DocumentCreate instance."""
        doc_create = DocumentCreate(title="Test Document")
        assert doc_create.title == "Test Document"
    
    def test_document_create_title_too_long(self):
        """Test DocumentCreate with title exceeding 256 characters."""
        long_title = "a" * 257
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(title=long_title)
        
        assert "at most 256 characters" in str(exc_info.value)
    
    def test_document_create_title_empty(self):
        """Test DocumentCreate with empty title."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(title="")
        
        assert "at least 1 character" in str(exc_info.value)
    
    def test_document_create_title_whitespace_only(self):
        """Test DocumentCreate with whitespace-only title."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(title="   ")
        
        assert "Title cannot be empty or whitespace only" in str(exc_info.value)
    
    def test_document_update_valid(self):
        """Test creating a valid DocumentUpdate instance."""
        doc_update = DocumentUpdate(title="Updated Title", deleted=True)
        assert doc_update.title == "Updated Title"
        assert doc_update.deleted is True
    
    def test_document_update_partial(self):
        """Test DocumentUpdate with only some fields."""
        doc_update = DocumentUpdate(title="New Title")
        assert doc_update.title == "New Title"
        assert doc_update.deleted is None
    
    def test_document_update_empty_title(self):
        """Test DocumentUpdate with empty title."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentUpdate(title="")
        
        assert "at least 1 character" in str(exc_info.value)
    
    def test_document_update_whitespace_title(self):
        """Test DocumentUpdate with whitespace-only title."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentUpdate(title="   ")
        
        assert "Title cannot be empty" in str(exc_info.value)
    
    def test_document_update_title_too_long(self):
        """Test DocumentUpdate with title exceeding 256 characters."""
        long_title = "a" * 257
        with pytest.raises(ValidationError) as exc_info:
            DocumentUpdate(title=long_title)
        
        assert "at most 256 characters" in str(exc_info.value)
    
    def test_document_update_none_title(self):
        """Test DocumentUpdate with None title (should be valid)."""
        doc_update = DocumentUpdate(title=None)
        assert doc_update.title is None
    
    def test_document_out_valid(self):
        """Test creating a valid DocumentOut instance."""
        now = datetime.now()
        doc_out = DocumentOut(
            id="test-doc-123",
            title="Test Document",
            created_at=now,
            updated_at=now,
            deleted_at=None,
            owner_id="user-123"
        )
        
        assert doc_out.id == "test-doc-123"
        assert doc_out.title == "Test Document"
        assert doc_out.created_at == now
        assert doc_out.updated_at == now
        assert doc_out.deleted_at is None
        assert doc_out.owner_id == "user-123"
    
    def test_document_out_with_deleted(self):
        """Test DocumentOut with deleted document."""
        now = datetime.now()
        deleted_at = datetime.now()
        
        doc_out = DocumentOut(
            id="test-doc-123",
            title="Deleted Document",
            created_at=now,
            updated_at=now,
            deleted_at=deleted_at,
            owner_id=None
        )
        
        assert doc_out.deleted_at == deleted_at
        assert doc_out.owner_id is None
    
    def test_document_out_from_attributes(self):
        """Test DocumentOut can be created from SQLAlchemy attributes."""
        # This tests the from_attributes = True configuration
        class MockDocument:
            def __init__(self):
                self.id = "test-doc-123"
                self.title = "Test Document"
                self.created_at = datetime.now()
                self.updated_at = datetime.now()
                self.deleted_at = None
                self.owner_id = "user-123"
        
        mock_doc = MockDocument()
        doc_out = DocumentOut.model_validate(mock_doc)
        
        assert doc_out.id == "test-doc-123"
        assert doc_out.title == "Test Document"
    
    def test_document_list_response_valid(self):
        """Test creating a valid DocumentListResponse instance."""
        now = datetime.now()
        documents = [
            DocumentOut(
                id="doc-1",
                title="Document 1",
                created_at=now,
                updated_at=now,
                deleted_at=None,
                owner_id="user-1"
            ),
            DocumentOut(
                id="doc-2",
                title="Document 2",
                created_at=now,
                updated_at=now,
                deleted_at=None,
                owner_id="user-2"
            )
        ]
        
        response = DocumentListResponse(
            items=documents,
            page=1,
            page_size=10,
            total=2
        )
        
        assert len(response.items) == 2
        assert response.page == 1
        assert response.page_size == 10
        assert response.total == 2
        assert response.items[0].title == "Document 1"
        assert response.items[1].title == "Document 2"
    
    def test_document_list_response_empty(self):
        """Test DocumentListResponse with empty items list."""
        response = DocumentListResponse(
            items=[],
            page=1,
            page_size=10,
            total=0
        )
        
        assert len(response.items) == 0
        assert response.total == 0
