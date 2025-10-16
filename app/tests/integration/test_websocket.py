"""Integration tests for WebSocket functionality."""

import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.document import Document
from app.core.database import get_db
from app.schemas.websocket import StateMessage, PresenceUpdateMessage, ErrorMessage


class TestWebSocketIntegration:
    """Test WebSocket integration scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def test_document(self, clear_database):
        """Create a test document."""
        from app.core.database import get_db
        from app.models.document import Document
        
        db = next(get_db())
        try:
            document = Document(
                id="test-doc-123",
                title="Test Document",
                owner_id="test-user"
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            return document
        finally:
            db.close()
    
    def test_websocket_connection_success(self, client, test_document):
        """Test successful WebSocket connection to existing document."""
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket:
            # Should receive initial state message
            message = websocket.receive_text()
            data = json.loads(message)
            
            assert data["type"] == "state"
            assert data["version"] == 0
            assert data["snapshotB64"] == ""
            
            # Send a ping to keep connection alive and test message handling
            ping_message = {
                "type": "ping",
                "ts": 1234567890
            }
            websocket.send_text(json.dumps(ping_message))
            
            # Connection should close cleanly when context exits
    
    def test_websocket_connection_invalid_document(self, client):
        """Test WebSocket connection to non-existent document."""
        with pytest.raises(Exception):  # WebSocket connection should fail
            with client.websocket_connect("/api/v1/ws/documents/non-existent?userId=user1&displayName=User%201") as websocket:
                websocket.receive_text()
    
    def test_websocket_connection_missing_params(self, client):
        """Test WebSocket connection with missing parameters."""
        with pytest.raises(Exception):  # WebSocket connection should fail
            with client.websocket_connect("/api/v1/ws/documents/test-doc-123") as websocket:
                websocket.receive_text()
    
    def test_websocket_join_message(self, client, test_document):
        """Test sending join message."""
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket:
            # Receive initial state
            websocket.receive_text()
            
            # Send join message
            join_message = {
                "type": "join",
                "userId": "user1",
                "displayName": "User 1"
            }
            websocket.send_text(json.dumps(join_message))
            
            # Should not receive any response for join (already joined)
            # Just verify connection is still alive
            ping_message = {
                "type": "ping",
                "ts": 1234567890
            }
            websocket.send_text(json.dumps(ping_message))
    
    def test_websocket_presence_message(self, client, test_document):
        """Test sending presence message."""
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket:
            # Receive initial state
            websocket.receive_text()
            
            # Send presence message
            presence_message = {
                "type": "presence",
                "cursor": {"from": 0, "to": 5},
                "color": "#ff0000"
            }
            websocket.send_text(json.dumps(presence_message))
            
            # Should not receive any response for presence update
            # Just verify connection is still alive
            ping_message = {
                "type": "ping",
                "ts": 1234567890
            }
            websocket.send_text(json.dumps(ping_message))
    
    def test_websocket_ping_message(self, client, test_document):
        """Test sending ping message."""
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket:
            # Receive initial state
            websocket.receive_text()
            
            # Send ping message
            ping_message = {
                "type": "ping",
                "ts": 1234567890
            }
            websocket.send_text(json.dumps(ping_message))
            
            # Should not receive any response for ping
            # Just verify connection is still alive
            websocket.send_text(json.dumps(ping_message))
    
    def test_websocket_invalid_message_type(self, client, test_document):
        """Test sending invalid message type."""
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket:
            # Receive initial state
            websocket.receive_text()
            
            # Send invalid message
            invalid_message = {
                "type": "invalid_type",
                "data": "test"
            }
            websocket.send_text(json.dumps(invalid_message))
            
            # Should receive error message
            message = websocket.receive_text()
            data = json.loads(message)
            
            assert data["type"] == "error"
            assert data["code"] == "UNKNOWN_MESSAGE_TYPE"
            assert "Unknown message type: invalid_type" in data["message"]
    
    def test_websocket_invalid_json(self, client, test_document):
        """Test sending invalid JSON."""
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket:
            # Receive initial state
            websocket.receive_text()
            
            # Send invalid JSON
            websocket.send_text("invalid json")
            
            # Should receive error message
            message = websocket.receive_text()
            data = json.loads(message)
            
            assert data["type"] == "error"
            assert data["code"] == "INVALID_JSON"
            assert data["message"] == "Invalid JSON message"


class TestWebSocketMessageValidation:
    """Test WebSocket message validation."""
    
    def test_join_message_validation(self):
        """Test join message validation."""
        from app.schemas.websocket import JoinMessage
        
        # Valid join message
        valid_data = {
            "type": "join",
            "userId": "user123",
            "displayName": "Test User"
        }
        message = JoinMessage.model_validate(valid_data)
        assert message.type == "join"
        assert message.userId == "user123"
        assert message.displayName == "Test User"
    
    def test_presence_message_validation(self):
        """Test presence message validation."""
        from app.schemas.websocket import PresenceMessage
        
        # Valid presence message
        valid_data = {
            "type": "presence",
            "cursor": {"from": 0, "to": 5},
            "color": "#ff0000"
        }
        message = PresenceMessage.model_validate(valid_data)
        assert message.type == "presence"
        assert message.cursor == {"from": 0, "to": 5}
        assert message.color == "#ff0000"
    
    def test_ping_message_validation(self):
        """Test ping message validation."""
        from app.schemas.websocket import PingMessage
        
        # Valid ping message
        valid_data = {
            "type": "ping",
            "ts": 1234567890
        }
        message = PingMessage.model_validate(valid_data)
        assert message.type == "ping"
        assert message.ts == 1234567890
    
    def test_state_message_validation(self):
        """Test state message validation."""
        from app.schemas.websocket import StateMessage
        
        # Valid state message
        valid_data = {
            "type": "state",
            "version": 5,
            "snapshotB64": "base64data"
        }
        message = StateMessage.model_validate(valid_data)
        assert message.type == "state"
        assert message.version == 5
        assert message.snapshotB64 == "base64data"