"""WebSocket room management for real-time collaboration."""

import asyncio
import json
import time
from typing import Dict, List, Optional, Set
from uuid import uuid4

from fastapi import WebSocket

from app.schemas.websocket import (
    ErrorMessage,
    PresenceUpdateMessage,
    StateMessage,
    UserPresence,
)


class DocumentRoom:
    """Manages WebSocket connections for a single document."""
    
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.connections: Dict[str, WebSocket] = {}
        self.presence: Dict[str, UserPresence] = {}
        self.lock = asyncio.Lock()
    
    async def add_connection(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        display_name: str
    ) -> None:
        """Add a new connection to the room."""
        async with self.lock:
            # Store connection
            self.connections[user_id] = websocket
            
            # Create user presence
            presence = UserPresence(
                userId=user_id,
                displayName=display_name,
                connected_at=int(time.time())
            )
            self.presence[user_id] = presence
            
            # Notify other users about new presence
            await self._broadcast_presence_update(presence, exclude_user=user_id)
    
    async def remove_connection(self, user_id: str) -> None:
        """Remove a connection from the room."""
        async with self.lock:
            if user_id in self.connections:
                del self.connections[user_id]
            
            if user_id in self.presence:
                del self.presence[user_id]
                
                # Notify other users about presence removal
                await self._broadcast_presence_removal(user_id)
    
    async def update_presence(
        self, 
        user_id: str, 
        cursor: Optional[Dict] = None, 
        color: Optional[str] = None
    ) -> None:
        """Update user presence information."""
        async with self.lock:
            if user_id in self.presence:
                self.presence[user_id].cursor = cursor
                self.presence[user_id].color = color
                
                # Broadcast presence update to other users
                await self._broadcast_presence_update(self.presence[user_id], exclude_user=user_id)
    
    async def send_state(self, user_id: str, version: int, snapshot_b64: str) -> None:
        """Send initial state to a user."""
        if user_id in self.connections:
            message = StateMessage(
                type="state",
                version=version,
                snapshotB64=snapshot_b64
            )
            await self._send_to_user(user_id, message.model_dump())
    
    async def send_error(self, user_id: str, code: str, message: str) -> None:
        """Send error message to a user."""
        if user_id in self.connections:
            error_msg = ErrorMessage(
                type="error",
                code=code,
                message=message
            )
            await self._send_to_user(user_id, error_msg.model_dump())
    
    async def _broadcast_presence_update(
        self, 
        presence: UserPresence, 
        exclude_user: Optional[str] = None
    ) -> None:
        """Broadcast presence update to all users except the sender."""
        message = PresenceUpdateMessage(
            type="presence",
            userId=presence.userId,
            cursor=presence.cursor,
            color=presence.color
        )
        
        for user_id, websocket in self.connections.items():
            if user_id != exclude_user:
                await self._send_to_user(user_id, message.model_dump())
    
    async def _broadcast_presence_removal(self, user_id: str) -> None:
        """Broadcast presence removal to all users."""
        message = PresenceUpdateMessage(
            type="presence",
            userId=user_id,
            cursor=None,
            color=None
        )
        
        for target_user_id, websocket in self.connections.items():
            if target_user_id != user_id:
                await self._send_to_user(target_user_id, message.model_dump())
    
    async def _send_to_user(self, user_id: str, message: Dict) -> None:
        """Send message to a specific user."""
        if user_id in self.connections:
            try:
                await self.connections[user_id].send_text(json.dumps(message))
            except Exception:
                # Connection might be closed, remove it
                await self.remove_connection(user_id)
    
    def get_connected_users(self) -> List[UserPresence]:
        """Get list of connected users."""
        return list(self.presence.values())
    
    def is_empty(self) -> bool:
        """Check if room is empty."""
        return len(self.connections) == 0


class WebSocketManager:
    """Manages WebSocket rooms for all documents."""
    
    def __init__(self):
        self.rooms: Dict[str, DocumentRoom] = {}
        self.lock = asyncio.Lock()
    
    async def get_room(self, document_id: str) -> DocumentRoom:
        """Get or create a room for a document."""
        async with self.lock:
            if document_id not in self.rooms:
                self.rooms[document_id] = DocumentRoom(document_id)
            return self.rooms[document_id]
    
    async def remove_room(self, document_id: str) -> None:
        """Remove a room if it's empty."""
        async with self.lock:
            if document_id in self.rooms and self.rooms[document_id].is_empty():
                del self.rooms[document_id]
    
    async def cleanup_empty_rooms(self) -> None:
        """Clean up all empty rooms."""
        async with self.lock:
            empty_rooms = [
                doc_id for doc_id, room in self.rooms.items() 
                if room.is_empty()
            ]
            for doc_id in empty_rooms:
                del self.rooms[doc_id]


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
