"""WebSocket message schemas for real-time collaboration."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WebSocketMessage(BaseModel):
    """Base WebSocket message."""
    
    type: str = Field(..., description="Message type")


class JoinMessage(WebSocketMessage):
    """Client join message."""
    
    type: str = Field(default="join", description="Message type")
    userId: str = Field(..., description="User identifier")
    displayName: str = Field(..., description="User display name")


class PresenceMessage(WebSocketMessage):
    """Client presence message."""
    
    type: str = Field(default="presence", description="Message type")
    cursor: Optional[Dict[str, Any]] = Field(None, description="Cursor position")
    color: Optional[str] = Field(None, description="User color")


class PingMessage(WebSocketMessage):
    """Client ping message."""
    
    type: str = Field(default="ping", description="Message type")
    ts: int = Field(..., description="Timestamp")


class UpdateMessage(WebSocketMessage):
    """Client update message."""
    
    type: str = Field(default="update", description="Message type")
    opId: str = Field(..., description="Unique operation ID")
    baseVersion: int = Field(..., description="Base version for diagnostics")
    actorId: str = Field(..., description="Actor identifier")
    deltaB64: str = Field(..., description="Base64 encoded delta")


class StateMessage(WebSocketMessage):
    """Server state message."""
    
    type: str = Field(default="state", description="Message type")
    version: int = Field(..., description="Document version")
    snapshotB64: str = Field(..., description="Base64 encoded snapshot")


class PresenceUpdateMessage(WebSocketMessage):
    """Server presence update message."""
    
    type: str = Field(default="presence", description="Message type")
    userId: str = Field(..., description="User identifier")
    cursor: Optional[Dict[str, Any]] = Field(None, description="Cursor position")
    color: Optional[str] = Field(None, description="User color")


class AckMessage(WebSocketMessage):
    """Server acknowledgment message."""
    
    type: str = Field(default="ack", description="Message type")
    opId: str = Field(..., description="Operation ID being acknowledged")
    seq: int = Field(..., description="Assigned sequence number")


class RemoteUpdateMessage(WebSocketMessage):
    """Server remote update message."""
    
    type: str = Field(default="remote_update", description="Message type")
    seq: int = Field(..., description="Sequence number")
    deltaB64: str = Field(..., description="Base64 encoded delta")
    actorId: str = Field(..., description="Actor identifier")


class ErrorMessage(WebSocketMessage):
    """Server error message."""
    
    type: str = Field(default="error", description="Message type")
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")


class UserPresence(BaseModel):
    """User presence information."""
    
    userId: str = Field(..., description="User identifier")
    displayName: str = Field(..., description="User display name")
    cursor: Optional[Dict[str, Any]] = Field(None, description="Cursor position")
    color: Optional[str] = Field(None, description="User color")
    connected_at: int = Field(..., description="Connection timestamp")
