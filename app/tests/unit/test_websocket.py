"""Unit tests for WebSocket components."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.websocket import DocumentRoom, WebSocketManager
from app.schemas.websocket import UserPresence


class TestDocumentRoom:
    """Test DocumentRoom functionality."""
    
    @pytest.fixture
    def room(self):
        """Create a test room."""
        return DocumentRoom("test-doc-123")
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        websocket = AsyncMock()
        websocket.send_text = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_add_connection(self, room, mock_websocket):
        """Test adding a connection to the room."""
        await room.add_connection(mock_websocket, "user1", "User 1")
        
        assert "user1" in room.connections
        assert "user1" in room.presence
        assert room.connections["user1"] == mock_websocket
        assert room.presence["user1"].userId == "user1"
        assert room.presence["user1"].displayName == "User 1"
    
    @pytest.mark.asyncio
    async def test_remove_connection(self, room, mock_websocket):
        """Test removing a connection from the room."""
        await room.add_connection(mock_websocket, "user1", "User 1")
        await room.remove_connection("user1")
        
        assert "user1" not in room.connections
        assert "user1" not in room.presence
    
    @pytest.mark.asyncio
    async def test_update_presence(self, room, mock_websocket):
        """Test updating user presence."""
        await room.add_connection(mock_websocket, "user1", "User 1")
        
        await room.update_presence("user1", cursor={"from": 0, "to": 5}, color="#ff0000")
        
        assert room.presence["user1"].cursor == {"from": 0, "to": 5}
        assert room.presence["user1"].color == "#ff0000"
    
    @pytest.mark.asyncio
    async def test_send_state(self, room, mock_websocket):
        """Test sending state to a user."""
        await room.add_connection(mock_websocket, "user1", "User 1")
        
        await room.send_state("user1", version=5, snapshot_b64="testdata")
        
        # Verify send_text was called with state message
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        data = json.loads(call_args)
        
        assert data["type"] == "state"
        assert data["version"] == 5
        assert data["snapshotB64"] == "testdata"
    
    @pytest.mark.asyncio
    async def test_send_error(self, room, mock_websocket):
        """Test sending error to a user."""
        await room.add_connection(mock_websocket, "user1", "User 1")
        
        await room.send_error("user1", "TEST_ERROR", "Test error message")
        
        # Verify send_text was called with error message
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        data = json.loads(call_args)
        
        assert data["type"] == "error"
        assert data["code"] == "TEST_ERROR"
        assert data["message"] == "Test error message"
    
    @pytest.mark.asyncio
    async def test_broadcast_presence_update(self, room):
        """Test broadcasting presence updates."""
        # Add two connections
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        
        await room.add_connection(ws1, "user1", "User 1")
        await room.add_connection(ws2, "user2", "User 2")
        
        # Clear the calls from the join process
        ws1.send_text.reset_mock()
        ws2.send_text.reset_mock()
        
        # Update presence for user1
        await room.update_presence("user1", cursor={"from": 0, "to": 5}, color="#ff0000")
        
        # user2 should receive presence update
        ws2.send_text.assert_called_once()
        call_args = ws2.send_text.call_args[0][0]
        data = json.loads(call_args)
        
        assert data["type"] == "presence"
        assert data["userId"] == "user1"
        assert data["cursor"] == {"from": 0, "to": 5}
        assert data["color"] == "#ff0000"
        
        # user1 should not receive their own update
        ws1.send_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_broadcast_presence_removal(self, room):
        """Test broadcasting presence removal."""
        # Add two connections
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        
        await room.add_connection(ws1, "user1", "User 1")
        await room.add_connection(ws2, "user2", "User 2")
        
        # Remove user1
        await room.remove_connection("user1")
        
        # user2 should receive presence removal
        ws2.send_text.assert_called_once()
        call_args = ws2.send_text.call_args[0][0]
        data = json.loads(call_args)
        
        assert data["type"] == "presence"
        assert data["userId"] == "user1"
        assert data["cursor"] is None
        assert data["color"] is None
    
    @pytest.mark.asyncio
    async def test_get_connected_users(self, room, mock_websocket):
        """Test getting connected users."""
        await room.add_connection(mock_websocket, "user1", "User 1")
        
        users = room.get_connected_users()
        
        assert len(users) == 1
        assert users[0].userId == "user1"
        assert users[0].displayName == "User 1"
    
    def test_is_empty(self, room):
        """Test checking if room is empty."""
        assert room.is_empty() is True
        
        # Add a connection
        room.connections["user1"] = AsyncMock()
        assert room.is_empty() is False


class TestWebSocketManager:
    """Test WebSocketManager functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create a test manager."""
        return WebSocketManager()
    
    @pytest.mark.asyncio
    async def test_get_room_creates_new(self, manager):
        """Test getting a room creates it if it doesn't exist."""
        room = await manager.get_room("doc-123")
        
        assert isinstance(room, DocumentRoom)
        assert room.document_id == "doc-123"
        assert "doc-123" in manager.rooms
    
    @pytest.mark.asyncio
    async def test_get_room_returns_existing(self, manager):
        """Test getting a room returns existing one."""
        room1 = await manager.get_room("doc-123")
        room2 = await manager.get_room("doc-123")
        
        assert room1 is room2
    
    @pytest.mark.asyncio
    async def test_remove_room_when_empty(self, manager):
        """Test removing empty room."""
        room = await manager.get_room("doc-123")
        assert "doc-123" in manager.rooms
        
        await manager.remove_room("doc-123")
        assert "doc-123" not in manager.rooms
    
    @pytest.mark.asyncio
    async def test_remove_room_when_not_empty(self, manager):
        """Test removing non-empty room does nothing."""
        room = await manager.get_room("doc-123")
        room.connections["user1"] = AsyncMock()  # Make room non-empty
        
        await manager.remove_room("doc-123")
        assert "doc-123" in manager.rooms  # Should still exist
    
    @pytest.mark.asyncio
    async def test_cleanup_empty_rooms(self, manager):
        """Test cleaning up empty rooms."""
        # Create rooms
        room1 = await manager.get_room("doc-1")
        room2 = await manager.get_room("doc-2")
        room3 = await manager.get_room("doc-3")
        
        # Make room2 non-empty
        room2.connections["user1"] = AsyncMock()
        
        # Cleanup should remove empty rooms
        await manager.cleanup_empty_rooms()
        
        assert "doc-1" not in manager.rooms
        assert "doc-2" in manager.rooms  # Non-empty, should remain
        assert "doc-3" not in manager.rooms


class TestUserPresence:
    """Test UserPresence model."""
    
    def test_user_presence_creation(self):
        """Test creating UserPresence instance."""
        presence = UserPresence(
            userId="user123",
            displayName="Test User",
            cursor={"from": 0, "to": 5},
            color="#ff0000",
            connected_at=1234567890
        )
        
        assert presence.userId == "user123"
        assert presence.displayName == "Test User"
        assert presence.cursor == {"from": 0, "to": 5}
        assert presence.color == "#ff0000"
        assert presence.connected_at == 1234567890
    
    def test_user_presence_optional_fields(self):
        """Test UserPresence with optional fields."""
        presence = UserPresence(
            userId="user123",
            displayName="Test User",
            connected_at=1234567890
        )
        
        assert presence.userId == "user123"
        assert presence.displayName == "Test User"
        assert presence.cursor is None
        assert presence.color is None
        assert presence.connected_at == 1234567890
