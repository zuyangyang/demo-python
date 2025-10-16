"""Integration tests for WebSocket functionality."""

import json
import base64
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.document import Document
from app.core.database import get_db
from app.schemas.websocket import StateMessage, PresenceUpdateMessage, ErrorMessage, UpdateMessage, AckMessage, RemoteUpdateMessage


class TestWebSocketIntegration:
    """Test WebSocket integration scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def test_document(self, clear_database):
        """Create a test document."""
        from app.core.storage_factory import get_document_repository
        from app.core.database import get_db
        
        db = next(get_db())
        repository = get_document_repository(db)
        document = repository.create_document(title="Test Document", owner_id="test-user")
        return document
    
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


class TestWebSocketUpdateIntegration:
    """Test WebSocket update functionality integration."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def test_document(self, clear_database):
        """Create a test document."""
        from app.core.storage_factory import get_document_repository
        from app.core.database import get_db
        import uuid
        
        db = next(get_db())
        repository = get_document_repository(db)
        document = repository.create_document(title="Test Document", owner_id="test-user")
        return document
    
    def test_single_client_update_flow(self, client, test_document):
        """Test single client sending update and receiving ack."""
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket:
            # Receive initial state
            websocket.receive_text()
            
            # Send update message
            delta_data = b"test delta data"
            delta_b64 = base64.b64encode(delta_data).decode('utf-8')
            
            update_message = {
                "type": "update",
                "opId": "op-123",
                "baseVersion": 0,
                "actorId": "user1",
                "deltaB64": delta_b64
            }
            websocket.send_text(json.dumps(update_message))
            
            # Should receive ack message
            message = websocket.receive_text()
            data = json.loads(message)
            
            assert data["type"] == "ack"
            assert data["opId"] == "op-123"
            assert data["seq"] == 1
    
    def test_two_clients_update_broadcast(self, client, test_document):
        """Test two clients where one sends update and other receives remote_update."""
        # Connect first client
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket1:
            # Connect second client
            with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user2&displayName=User%202") as websocket2:
                # Both clients receive initial state
                websocket1.receive_text()
                websocket2.receive_text()
                
                # User1 may receive presence update for user2 joining
                # Skip any presence messages
                while True:
                    try:
                        message = websocket1.receive_text(timeout=0.1)
                        data = json.loads(message)
                        if data["type"] != "presence":
                            break
                    except:
                        break
                
                # User1 sends update
                delta_data = b"test delta from user1"
                delta_b64 = base64.b64encode(delta_data).decode('utf-8')
                
                update_message = {
                    "type": "update",
                    "opId": "op-user1-1",
                    "baseVersion": 0,
                    "actorId": "user1",
                    "deltaB64": delta_b64
                }
                websocket1.send_text(json.dumps(update_message))
                
                # User1 should receive ack (skip any presence messages)
                while True:
                    ack_message = websocket1.receive_text()
                    ack_data = json.loads(ack_message)
                    if ack_data["type"] == "ack":
                        break
                
                assert ack_data["opId"] == "op-user1-1"
                assert ack_data["seq"] == 1
                
                # User2 should receive remote_update
                remote_message = websocket2.receive_text()
                remote_data = json.loads(remote_message)
                assert remote_data["type"] == "remote_update"
                assert remote_data["seq"] == 1
                assert remote_data["actorId"] == "user1"
                assert remote_data["deltaB64"] == delta_b64
    
    def test_multiple_updates_sequence_order(self, client, test_document):
        """Test multiple updates maintain correct sequence order."""
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket1:
            with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user2&displayName=User%202") as websocket2:
                # Both clients receive initial state
                websocket1.receive_text()
                websocket2.receive_text()
                
                # Skip any presence messages from user2 joining
                while True:
                    try:
                        message = websocket1.receive_text(timeout=0.1)
                        data = json.loads(message)
                        if data["type"] != "presence":
                            break
                    except:
                        break
                
                # Send multiple updates from user1
                for i in range(3):
                    delta_data = f"delta-{i}".encode()
                    delta_b64 = base64.b64encode(delta_data).decode('utf-8')
                    
                    update_message = {
                        "type": "update",
                        "opId": f"op-user1-{i}",
                        "baseVersion": 0,
                        "actorId": "user1",
                        "deltaB64": delta_b64
                    }
                    websocket1.send_text(json.dumps(update_message))
                    
                    # User1 receives ack (skip any presence messages)
                    while True:
                        ack_message = websocket1.receive_text()
                        ack_data = json.loads(ack_message)
                        if ack_data["type"] == "ack":
                            break
                    assert ack_data["seq"] == i + 1
                    
                    # User2 receives remote_update
                    remote_message = websocket2.receive_text()
                    remote_data = json.loads(remote_message)
                    assert remote_data["type"] == "remote_update"
                    assert remote_data["seq"] == i + 1
                    assert remote_data["actorId"] == "user1"
    
    def test_invalid_update_message_format(self, client, test_document):
        """Test sending invalid update message format."""
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket:
            # Receive initial state
            websocket.receive_text()
            
            # Send invalid update message (missing required fields)
            invalid_message = {
                "type": "update",
                "opId": "op-123"
                # Missing baseVersion, actorId, deltaB64
            }
            websocket.send_text(json.dumps(invalid_message))
            
            # Should receive error message
            message = websocket.receive_text()
            data = json.loads(message)
            
            assert data["type"] == "error"
            assert data["code"] == "INVALID_MESSAGE"
            assert "Invalid update message" in data["message"]
    
    def test_invalid_base64_delta(self, client, test_document):
        """Test sending update with invalid base64 delta."""
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket:
            # Receive initial state
            websocket.receive_text()
            
            # Send update with invalid base64
            update_message = {
                "type": "update",
                "opId": "op-123",
                "baseVersion": 0,
                "actorId": "user1",
                "deltaB64": "invalid-base64-data!"
            }
            websocket.send_text(json.dumps(update_message))
            
            # Should receive error message
            message = websocket.receive_text()
            data = json.loads(message)
            
            assert data["type"] == "error"
            assert data["code"] == "INVALID_UPDATE"
            assert "Invalid base64 delta data" in data["message"]
    
    def test_duplicate_op_id_handling(self, client, test_document):
        """Test handling of duplicate operation IDs."""
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket:
            # Receive initial state
            websocket.receive_text()
            
            # Send first update
            delta_data = b"first delta"
            delta_b64 = base64.b64encode(delta_data).decode('utf-8')
            
            update_message = {
                "type": "update",
                "opId": "op-123",
                "baseVersion": 0,
                "actorId": "user1",
                "deltaB64": delta_b64
            }
            websocket.send_text(json.dumps(update_message))
            
            # Should receive ack
            ack_message = websocket.receive_text()
            ack_data = json.loads(ack_message)
            assert ack_data["type"] == "ack"
            assert ack_data["seq"] == 1
            
            # Send second update with same opId
            delta_data2 = b"second delta"
            delta_b64_2 = base64.b64encode(delta_data2).decode('utf-8')
            
            update_message2 = {
                "type": "update",
                "opId": "op-123",  # Same opId
                "baseVersion": 0,
                "actorId": "user1",
                "deltaB64": delta_b64_2
            }
            websocket.send_text(json.dumps(update_message2))
            
            # Should receive error message
            error_message = websocket.receive_text()
            error_data = json.loads(error_message)
            assert error_data["type"] == "error"
            assert error_data["code"] == "INVALID_UPDATE"
    
    def test_large_delta_payload(self, client, test_document):
        """Test handling of large delta payload."""
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket:
            # Receive initial state
            websocket.receive_text()
            
            # Create large delta data (10KB)
            large_delta = b"x" * 10000
            delta_b64 = base64.b64encode(large_delta).decode('utf-8')
            
            update_message = {
                "type": "update",
                "opId": "op-large",
                "baseVersion": 0,
                "actorId": "user1",
                "deltaB64": delta_b64
            }
            websocket.send_text(json.dumps(update_message))
            
            # Should receive ack
            ack_message = websocket.receive_text()
            ack_data = json.loads(ack_message)
            assert ack_data["type"] == "ack"
            assert ack_data["opId"] == "op-large"
            assert ack_data["seq"] == 1
    
    def test_concurrent_updates_from_multiple_clients(self, client, test_document):
        """Test concurrent updates from multiple clients."""
        # Use a simpler approach to avoid race conditions
        with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user1&displayName=User%201") as websocket1:
            with client.websocket_connect(f"/api/v1/ws/documents/{test_document.id}?userId=user2&displayName=User%202") as websocket2:
                # All clients receive initial state
                websocket1.receive_text()
                websocket2.receive_text()
                
                # Consume any presence messages from user2 joining
                import time
                time.sleep(0.1)  # Give time for presence messages
                
                # Send update from user1
                delta_data = "delta-from-user1".encode()
                delta_b64 = base64.b64encode(delta_data).decode('utf-8')
                
                update_message1 = {
                    "type": "update",
                    "opId": "op-user1-1",
                    "baseVersion": 0,
                    "actorId": "user1",
                    "deltaB64": delta_b64
                }
                websocket1.send_text(json.dumps(update_message1))
                
                # User1 should receive ack (or presence first, then ack)
                ack_data = websocket1.receive_json()
                while ack_data.get("type") == "presence":
                    ack_data = websocket1.receive_json()
                assert ack_data["type"] == "ack"
                assert ack_data["opId"] == "op-user1-1"
                assert ack_data["seq"] == 1
                
                # User2 should receive remote update
                remote_update_data = websocket2.receive_json()
                assert remote_update_data["type"] == "remote_update"
                assert remote_update_data["seq"] == 1
                assert remote_update_data["actorId"] == "user1"
                
                # Send update from user2
                delta_data2 = "delta-from-user2".encode()
                delta_b64_2 = base64.b64encode(delta_data2).decode('utf-8')
                
                update_message2 = {
                    "type": "update",
                    "opId": "op-user2-1",
                    "baseVersion": 0,
                    "actorId": "user2",
                    "deltaB64": delta_b64_2
                }
                websocket2.send_text(json.dumps(update_message2))
                
                # User2 should receive ack
                ack_data2 = websocket2.receive_json()
                assert ack_data2["type"] == "ack"
                assert ack_data2["opId"] == "op-user2-1"
                assert ack_data2["seq"] == 2
                
                # User1 should receive remote update
                remote_update_data2 = websocket1.receive_json()
                assert remote_update_data2["type"] == "remote_update"
                assert remote_update_data2["seq"] == 2
                assert remote_update_data2["actorId"] == "user2"


class TestWebSocketUpdateMessageValidation:
    """Test WebSocket update message validation."""
    
    def test_update_message_validation(self):
        """Test update message validation."""
        # Valid update message
        valid_data = {
            "type": "update",
            "opId": "op-123",
            "baseVersion": 0,
            "actorId": "user1",
            "deltaB64": "dGVzdCBkZWx0YQ=="  # "test delta" in base64
        }
        message = UpdateMessage.model_validate(valid_data)
        assert message.type == "update"
        assert message.opId == "op-123"
        assert message.baseVersion == 0
        assert message.actorId == "user1"
        assert message.deltaB64 == "dGVzdCBkZWx0YQ=="
    
    def test_ack_message_validation(self):
        """Test ack message validation."""
        # Valid ack message
        valid_data = {
            "type": "ack",
            "opId": "op-123",
            "seq": 1
        }
        message = AckMessage.model_validate(valid_data)
        assert message.type == "ack"
        assert message.opId == "op-123"
        assert message.seq == 1
    
    def test_remote_update_message_validation(self):
        """Test remote update message validation."""
        # Valid remote update message
        valid_data = {
            "type": "remote_update",
            "seq": 1,
            "deltaB64": "dGVzdCBkZWx0YQ==",
            "actorId": "user1"
        }
        message = RemoteUpdateMessage.model_validate(valid_data)
        assert message.type == "remote_update"
        assert message.seq == 1
        assert message.deltaB64 == "dGVzdCBkZWx0YQ=="
        assert message.actorId == "user1"