"""
Integration tests for memory mode functionality.
"""

import pytest
import json
import base64
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.memory_storage import memory_storage


class TestMemoryModeIntegration:
    """Test memory mode integration with REST API and WebSocket."""
    
    def setup_method(self):
        """Set up fresh storage for each test."""
        memory_storage.clear_all()
        # Ensure we're in memory mode
        assert settings.storage_mode.value == "memory"
    
    def test_health_endpoint_memory_mode(self):
        """Test health endpoint works in memory mode."""
        client = TestClient(app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_document_crud_memory_mode(self):
        """Test complete document CRUD operations in memory mode."""
        client = TestClient(app)
        
        # Create document
        response = client.post("/api/v1/documents", json={"title": "Test Document"})
        assert response.status_code == 201
        data = response.json()
        document_id = data["id"]
        assert data["title"] == "Test Document"
        assert data["deleted_at"] is None
        
        # Get document
        response = client.get(f"/api/v1/documents/{document_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == document_id
        assert data["title"] == "Test Document"
        
        # Update document
        response = client.patch(
            f"/api/v1/documents/{document_id}",
            json={"title": "Updated Document"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Document"
        
        # List documents
        response = client.get("/api/v1/documents")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Updated Document"
        
        # Soft delete document
        response = client.delete(f"/api/v1/documents/{document_id}")
        assert response.status_code == 204
        
        # List documents (should exclude deleted by default)
        response = client.get("/api/v1/documents")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        
        # List documents including deleted
        response = client.get("/api/v1/documents?include_deleted=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["deleted_at"] is not None
    
    def test_document_listing_with_filters_memory_mode(self):
        """Test document listing with various filters in memory mode."""
        client = TestClient(app)
        
        # Create test documents
        client.post("/api/v1/documents", json={"title": "First Document"})
        client.post("/api/v1/documents", json={"title": "Second Document"})
        client.post("/api/v1/documents", json={"title": "Third Item"})
        
        # Test query filter
        response = client.get("/api/v1/documents?query=Document")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert all("Document" in item["title"] for item in data["items"])
        
        # Test pagination
        response = client.get("/api/v1/documents?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 3
    
    def test_websocket_join_memory_mode(self):
        """Test WebSocket join functionality in memory mode."""
        client = TestClient(app)
        
        # Create a document first
        response = client.post("/api/v1/documents", json={"title": "Test Document"})
        document_id = response.json()["id"]
        
        # Test WebSocket connection
        with client.websocket_connect(f"/api/v1/ws/documents/{document_id}?userId=user1&displayName=User1") as websocket:
            # Should receive initial state
            data = websocket.receive_json()
            assert data["type"] == "state"
            assert data["version"] == 0
            assert data["snapshotB64"] == ""
    
    def test_websocket_update_flow_memory_mode(self):
        """Test WebSocket update flow in memory mode."""
        client = TestClient(app)
        
        # Create a document first
        response = client.post("/api/v1/documents", json={"title": "Test Document"})
        document_id = response.json()["id"]
        
        # Test WebSocket update flow
        with client.websocket_connect(f"/api/v1/ws/documents/{document_id}?userId=user1&displayName=User1") as websocket1:
            with client.websocket_connect(f"/api/v1/ws/documents/{document_id}?userId=user2&displayName=User2") as websocket2:
                # Both should receive initial state
                data1 = websocket1.receive_json()
                data2 = websocket2.receive_json()
                assert data1["type"] == "state"
                assert data2["type"] == "state"
                
                # When user2 joins, user1 may receive a presence update
                # Consume any presence messages
                import time
                time.sleep(0.1)  # Give presence messages time to arrive
                
                # Send update from user1
                delta_b64 = base64.b64encode(b"test delta").decode()
                update_msg = {
                    "type": "update",
                    "opId": "op1",
                    "baseVersion": 0,
                    "actorId": "user1",
                    "deltaB64": delta_b64
                }
                websocket1.send_text(json.dumps(update_msg))
                
                # User1 should receive ack (or presence first, then ack)
                ack_data = websocket1.receive_json()
                while ack_data.get("type") == "presence":
                    ack_data = websocket1.receive_json()
                assert ack_data["type"] == "ack"
                assert ack_data["opId"] == "op1"
                assert ack_data["seq"] == 1
                
                # User2 should receive remote update
                remote_update_data = websocket2.receive_json()
                assert remote_update_data["type"] == "remote_update"
                assert remote_update_data["seq"] == 1
                assert remote_update_data["deltaB64"] == delta_b64
                assert remote_update_data["actorId"] == "user1"
    
    def test_websocket_presence_memory_mode(self):
        """Test WebSocket presence functionality in memory mode."""
        client = TestClient(app)
        
        # Create a document first
        response = client.post("/api/v1/documents", json={"title": "Test Document"})
        document_id = response.json()["id"]
        
        # Test WebSocket presence
        with client.websocket_connect(f"/api/v1/ws/documents/{document_id}?userId=user1&displayName=User1") as websocket1:
            with client.websocket_connect(f"/api/v1/ws/documents/{document_id}?userId=user2&displayName=User2") as websocket2:
                # Both should receive initial state
                websocket1.receive_json()
                websocket2.receive_json()
                
                # Send presence update from user1
                presence_msg = {
                    "type": "presence",
                    "cursor": {"from": 0, "to": 5},
                    "color": "#ff0000"
                }
                websocket1.send_text(json.dumps(presence_msg))
                
                # User2 should receive presence update
                presence_data = websocket2.receive_json()
                assert presence_data["type"] == "presence"
                assert presence_data["userId"] == "user1"
                assert presence_data["cursor"] == {"from": 0, "to": 5}
    
    def test_websocket_ping_memory_mode(self):
        """Test WebSocket ping functionality in memory mode."""
        client = TestClient(app)
        
        # Create a document first
        response = client.post("/api/v1/documents", json={"title": "Test Document"})
        document_id = response.json()["id"]
        
        # Test WebSocket ping
        with client.websocket_connect(f"/api/v1/ws/documents/{document_id}?userId=user1&displayName=User1") as websocket:
            # Receive initial state
            websocket.receive_json()
            
            # Send ping
            ping_msg = {
                "type": "ping",
                "ts": 1234567890
            }
            websocket.send_text(json.dumps(ping_msg))
            
            # Should not receive any response for ping (it's just logged)
            # This test mainly ensures ping doesn't cause errors
    
    def test_websocket_error_handling_memory_mode(self):
        """Test WebSocket error handling in memory mode."""
        client = TestClient(app)
        
        # Create a document first
        response = client.post("/api/v1/documents", json={"title": "Test Document"})
        document_id = response.json()["id"]
        
        # Test WebSocket error handling
        with client.websocket_connect(f"/api/v1/ws/documents/{document_id}?userId=user1&displayName=User1") as websocket:
            # Receive initial state
            websocket.receive_json()
            
            # Send invalid update (duplicate op_id)
            delta_b64 = base64.b64encode(b"test delta").decode()
            update_msg = {
                "type": "update",
                "opId": "op1",
                "baseVersion": 0,
                "actorId": "user1",
                "deltaB64": delta_b64
            }
            websocket.send_text(json.dumps(update_msg))
            
            # Should receive ack
            ack_data = websocket.receive_json()
            assert ack_data["type"] == "ack"
            
            # Send same update again (should fail)
            websocket.send_text(json.dumps(update_msg))
            
            # Should receive error
            error_data = websocket.receive_json()
            assert error_data["type"] == "error"
            assert error_data["code"] == "INVALID_UPDATE"
    
    def test_websocket_nonexistent_document_memory_mode(self):
        """Test WebSocket connection to non-existent document in memory mode."""
        client = TestClient(app)
        
        # Try to connect to non-existent document
        with pytest.raises(Exception):  # WebSocket should close with error
            with client.websocket_connect("/api/v1/ws/documents/nonexistent?userId=user1&displayName=User1") as websocket:
                websocket.receive_json()
    
    def test_memory_storage_persistence_across_requests(self):
        """Test that memory storage persists data across multiple requests."""
        client = TestClient(app)
        
        # Create document in first request
        response = client.post("/api/v1/documents", json={"title": "Persistent Document"})
        document_id = response.json()["id"]
        
        # Verify document exists in second request
        response = client.get(f"/api/v1/documents/{document_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Persistent Document"
        
        # Verify document appears in list
        response = client.get("/api/v1/documents")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        assert response.json()["items"][0]["title"] == "Persistent Document"
    
    def test_memory_storage_isolation_between_tests(self):
        """Test that memory storage is properly isolated between tests."""
        client = TestClient(app)
        
        # This test should start with empty storage
        response = client.get("/api/v1/documents")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 0
        
        # Create a document
        response = client.post("/api/v1/documents", json={"title": "Isolated Document"})
        assert response.status_code == 201
        
        # Verify it exists
        response = client.get("/api/v1/documents")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
