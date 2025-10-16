import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.document import Document
from app.core.database import get_db


client = TestClient(app)


class TestDocumentCRUD:
    """Test document CRUD operations."""
    
    def test_create_document_success(self):
        """Test creating a document successfully."""
        response = client.post(
            "/api/v1/documents/",
            json={"title": "Test Document"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Document"
        assert data["deleted_at"] is None
        assert data["owner_id"] is None
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_document_invalid_title_empty(self):
        """Test creating a document with empty title fails."""
        response = client.post(
            "/api/v1/documents/",
            json={"title": ""}
        )
        
        assert response.status_code == 422
        assert "String should have at least 1 character" in str(response.json())
    
    def test_create_document_invalid_title_whitespace(self):
        """Test creating a document with whitespace-only title fails."""
        response = client.post(
            "/api/v1/documents/",
            json={"title": "   "}
        )
        
        assert response.status_code == 422
        assert "Title cannot be empty or whitespace only" in str(response.json())
    
    def test_create_document_invalid_title_too_long(self):
        """Test creating a document with title too long fails."""
        long_title = "a" * 257  # 257 characters, max is 256
        response = client.post(
            "/api/v1/documents/",
            json={"title": long_title}
        )
        
        assert response.status_code == 422
        assert "String should have at most 256 characters" in str(response.json())
    
    def test_get_document_success(self):
        """Test getting a document successfully."""
        # First create a document
        create_response = client.post(
            "/api/v1/documents/",
            json={"title": "Test Document for Get"}
        )
        assert create_response.status_code == 201
        document_id = create_response.json()["id"]
        
        # Then get it
        response = client.get(f"/api/v1/documents/{document_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == document_id
        assert data["title"] == "Test Document for Get"
        assert data["deleted_at"] is None
    
    def test_get_document_not_found(self):
        """Test getting a non-existent document returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/documents/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_document_title_success(self):
        """Test updating a document's title successfully."""
        # First create a document
        create_response = client.post(
            "/api/v1/documents/",
            json={"title": "Original Title"}
        )
        assert create_response.status_code == 201
        document_id = create_response.json()["id"]
        
        # Then update it
        response = client.patch(
            f"/api/v1/documents/{document_id}",
            json={"title": "Updated Title"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == document_id
        assert data["title"] == "Updated Title"
        assert data["deleted_at"] is None
    
    def test_update_document_soft_delete_success(self):
        """Test soft deleting a document successfully."""
        # First create a document
        create_response = client.post(
            "/api/v1/documents/",
            json={"title": "Document to Delete"}
        )
        assert create_response.status_code == 201
        document_id = create_response.json()["id"]
        
        # Then soft delete it
        response = client.patch(
            f"/api/v1/documents/{document_id}",
            json={"deleted": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == document_id
        assert data["deleted_at"] is not None
    
    def test_update_document_undelete_success(self):
        """Test un-deleting a document successfully."""
        # First create and delete a document
        create_response = client.post(
            "/api/v1/documents/",
            json={"title": "Document to Undelete"}
        )
        assert create_response.status_code == 201
        document_id = create_response.json()["id"]
        
        # Soft delete it
        delete_response = client.patch(
            f"/api/v1/documents/{document_id}",
            json={"deleted": True}
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted_at"] is not None
        
        # Then undelete it
        response = client.patch(
            f"/api/v1/documents/{document_id}",
            json={"deleted": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == document_id
        assert data["deleted_at"] is None
    
    def test_update_document_invalid_title(self):
        """Test updating a document with invalid title fails."""
        # First create a document
        create_response = client.post(
            "/api/v1/documents/",
            json={"title": "Original Title"}
        )
        assert create_response.status_code == 201
        document_id = create_response.json()["id"]
        
        # Then try to update with invalid title
        response = client.patch(
            f"/api/v1/documents/{document_id}",
            json={"title": ""}
        )
        
        assert response.status_code == 422
        assert "String should have at least 1 character" in str(response.json())
    
    def test_update_document_not_found(self):
        """Test updating a non-existent document returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.patch(
            f"/api/v1/documents/{fake_id}",
            json={"title": "Updated Title"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_delete_document_success(self):
        """Test soft deleting a document successfully."""
        # First create a document
        create_response = client.post(
            "/api/v1/documents/",
            json={"title": "Document to Delete"}
        )
        assert create_response.status_code == 201
        document_id = create_response.json()["id"]
        
        # Then delete it
        response = client.delete(f"/api/v1/documents/{document_id}")
        
        assert response.status_code == 204
        
        # Verify it's soft deleted by getting it
        get_response = client.get(f"/api/v1/documents/{document_id}")
        assert get_response.status_code == 200
        assert get_response.json()["deleted_at"] is not None
    
    def test_delete_document_not_found(self):
        """Test deleting a non-existent document returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/api/v1/documents/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_list_documents_empty(self):
        """Test listing documents when none exist."""
        response = client.get("/api/v1/documents/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total"] == 0
    
    def test_list_documents_with_data(self):
        """Test listing documents with data."""
        # Create some documents
        doc1_response = client.post("/api/v1/documents/", json={"title": "Document 1"})
        doc2_response = client.post("/api/v1/documents/", json={"title": "Document 2"})
        doc3_response = client.post("/api/v1/documents/", json={"title": "Another Document"})
        
        assert doc1_response.status_code == 201
        assert doc2_response.status_code == 201
        assert doc3_response.status_code == 201
        
        # List all documents
        response = client.get("/api/v1/documents/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 20
        
        # Check that documents are ordered by updated_at desc
        titles = [item["title"] for item in data["items"]]
        assert "Another Document" in titles
        assert "Document 1" in titles
        assert "Document 2" in titles
    
    def test_list_documents_with_query(self):
        """Test listing documents with search query."""
        # Create documents with different titles
        client.post("/api/v1/documents/", json={"title": "Python Tutorial"})
        client.post("/api/v1/documents/", json={"title": "JavaScript Guide"})
        client.post("/api/v1/documents/", json={"title": "Python Best Practices"})
        
        # Search for Python documents
        response = client.get("/api/v1/documents/?query=Python")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        
        titles = [item["title"] for item in data["items"]]
        assert "Python Tutorial" in titles
        assert "Python Best Practices" in titles
        assert "JavaScript Guide" not in titles
    
    def test_list_documents_with_pagination(self):
        """Test listing documents with pagination."""
        # Create 5 documents
        for i in range(5):
            client.post("/api/v1/documents/", json={"title": f"Document {i+1}"})
        
        # Get first page
        response = client.get("/api/v1/documents/?page=1&page_size=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 5
        
        # Get second page
        response = client.get("/api/v1/documents/?page=2&page_size=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2
        assert data["page_size"] == 2
        assert data["total"] == 5
    
    def test_list_documents_include_deleted(self):
        """Test listing documents including soft-deleted ones."""
        # Create and delete a document
        create_response = client.post("/api/v1/documents/", json={"title": "Document to Delete"})
        document_id = create_response.json()["id"]
        client.delete(f"/api/v1/documents/{document_id}")
        
        # Create another document
        client.post("/api/v1/documents/", json={"title": "Active Document"})
        
        # List without deleted documents
        response = client.get("/api/v1/documents/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Active Document"
        
        # List with deleted documents
        response = client.get("/api/v1/documents/?include_deleted=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        titles = [item["title"] for item in data["items"]]
        assert "Active Document" in titles
        assert "Document to Delete" in titles
    
    def test_list_documents_invalid_pagination(self):
        """Test listing documents with invalid pagination parameters."""
        # Test negative page
        response = client.get("/api/v1/documents/?page=0")
        assert response.status_code == 422
        
        # Test page size too large
        response = client.get("/api/v1/documents/?page_size=101")
        assert response.status_code == 422
        
        # Test negative page size
        response = client.get("/api/v1/documents/?page_size=0")
        assert response.status_code == 422


class TestDocumentCRUDIntegration:
    """Integration tests for complete document lifecycle."""
    
    def test_complete_document_lifecycle(self):
        """Test complete document lifecycle: create -> get -> list -> update -> delete -> list."""
        # 1. Create a document
        create_response = client.post("/api/v1/documents/", json={"title": "Lifecycle Test Document"})
        assert create_response.status_code == 201
        document_id = create_response.json()["id"]
        
        # 2. Get the document
        get_response = client.get(f"/api/v1/documents/{document_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "Lifecycle Test Document"
        assert get_response.json()["deleted_at"] is None
        
        # 3. List documents (should contain our document)
        list_response = client.get("/api/v1/documents/")
        assert list_response.status_code == 200
        assert list_response.json()["total"] >= 1
        document_titles = [doc["title"] for doc in list_response.json()["items"]]
        assert "Lifecycle Test Document" in document_titles
        
        # 4. Update the document title
        update_response = client.patch(
            f"/api/v1/documents/{document_id}",
            json={"title": "Updated Lifecycle Test Document"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated Lifecycle Test Document"
        
        # 5. Soft delete the document
        delete_response = client.delete(f"/api/v1/documents/{document_id}")
        assert delete_response.status_code == 204
        
        # 6. List documents without deleted (should not contain our document)
        list_response = client.get("/api/v1/documents/")
        assert list_response.status_code == 200
        document_titles = [doc["title"] for doc in list_response.json()["items"]]
        assert "Updated Lifecycle Test Document" not in document_titles
        
        # 7. List documents with deleted (should contain our document)
        list_response = client.get("/api/v1/documents/?include_deleted=true")
        assert list_response.status_code == 200
        document_titles = [doc["title"] for doc in list_response.json()["items"]]
        assert "Updated Lifecycle Test Document" in document_titles
        
        # 8. Verify the document is soft deleted
        get_response = client.get(f"/api/v1/documents/{document_id}")
        assert get_response.status_code == 200
        assert get_response.json()["deleted_at"] is not None
