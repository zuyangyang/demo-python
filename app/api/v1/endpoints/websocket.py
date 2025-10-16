"""WebSocket endpoints for real-time collaboration."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import DocumentNotFoundError
from app.core.websocket import websocket_manager
from app.repositories.document_repository import DocumentRepository
from app.schemas.websocket import (
    JoinMessage,
    PingMessage,
    PresenceMessage,
    UpdateMessage,
    AckMessage,
    RemoteUpdateMessage,
)
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/documents/{document_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    document_id: str,
    userId: str = Query(..., description="User identifier"),
    displayName: str = Query(..., description="User display name"),
):
    """WebSocket endpoint for document collaboration."""
    # Accept the WebSocket connection
    await websocket.accept()
    
    # Get database session
    db = next(get_db())
    try:
        # Get document service
        repository = DocumentRepository()
        document_service = DocumentService(repository)
        
        # Verify document exists
        try:
            document = document_service.get_document(db, document_id=document_id)
        except DocumentNotFoundError:
            await websocket.close(code=1008, reason="Document not found")
            return
        
        # Get or create room for this document
        room = await websocket_manager.get_room(document_id)
        
        # Add connection to room
        await room.add_connection(websocket, userId, displayName)
        
        # Send initial state (empty for now, will be implemented in step 5)
        await room.send_state(userId, version=0, snapshot_b64="")
        
        logger.info(f"User {userId} connected to document {document_id}")
        
        # Handle messages
        try:
            while True:
                try:
                    # Receive message
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    message_type = message_data.get("type")
                    
                    if message_type == "join":
                        # User already joined, just acknowledge
                        join_msg = JoinMessage.model_validate(message_data)
                        logger.debug(f"User {join_msg.userId} joined document {document_id}")
                    
                    elif message_type == "presence":
                        # Update user presence
                        presence_msg = PresenceMessage.model_validate(message_data)
                        await room.update_presence(
                            userId, 
                            cursor=presence_msg.cursor,
                            color=presence_msg.color
                        )
                        logger.debug(f"User {userId} updated presence in document {document_id}")
                    
                    elif message_type == "ping":
                        # Handle ping (keepalive)
                        ping_msg = PingMessage.model_validate(message_data)
                        logger.debug(f"User {userId} pinged document {document_id} at {ping_msg.ts}")
                    
                    elif message_type == "update":
                        # Handle document update
                        try:
                            update_msg = UpdateMessage.model_validate(message_data)
                            
                            # Add update to database with atomic sequence assignment
                            try:
                                seq = repository.add_document_update(
                                    db,
                                    document_id=document_id,
                                    op_id=update_msg.opId,
                                    actor_id=update_msg.actorId,
                                    delta_b64=update_msg.deltaB64
                                )
                                
                                # Send ack to the sender
                                ack_msg = AckMessage(opId=update_msg.opId, seq=seq)
                                await room.send_to_user(userId, ack_msg.model_dump())
                                
                                # Broadcast remote update to all other users in the room
                                remote_update_msg = RemoteUpdateMessage(
                                    seq=seq,
                                    deltaB64=update_msg.deltaB64,
                                    actorId=update_msg.actorId
                                )
                                await room.broadcast_except_user(
                                    userId, 
                                    remote_update_msg.model_dump()
                                )
                                
                                logger.info(f"Processed update {update_msg.opId} with seq {seq} from user {userId}")
                                
                            except ValueError as e:
                                # Invalid base64 or other validation error
                                await room.send_error(
                                    userId,
                                    "INVALID_UPDATE",
                                    str(e)
                                )
                                logger.warning(f"Invalid update from user {userId}: {e}")
                            
                            except Exception as e:
                                # Database error (e.g., duplicate op_id)
                                await room.send_error(
                                    userId,
                                    "UPDATE_FAILED",
                                    "Failed to process update"
                                )
                                logger.error(f"Failed to process update from user {userId}: {e}")
                        
                        except Exception as e:
                            # Message validation error
                            await room.send_error(
                                userId,
                                "INVALID_MESSAGE",
                                f"Invalid update message: {e}"
                            )
                            logger.warning(f"Invalid update message from user {userId}: {e}")
                    
                    else:
                        # Unknown message type
                        await room.send_error(
                            userId, 
                            "UNKNOWN_MESSAGE_TYPE", 
                            f"Unknown message type: {message_type}"
                        )
                        logger.warning(f"Unknown message type {message_type} from user {userId}")
                
                except json.JSONDecodeError:
                    await room.send_error(
                        userId, 
                        "INVALID_JSON", 
                        "Invalid JSON message"
                    )
                    logger.warning(f"Invalid JSON from user {userId} in document {document_id}")
                
                except Exception as e:
                    logger.error(f"Error processing message from user {userId}: {e}")
                    await room.send_error(
                        userId, 
                        "PROCESSING_ERROR", 
                        "Error processing message"
                    )
        except WebSocketDisconnect:
            logger.info(f"User {userId} disconnected from document {document_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {userId} in document {document_id}: {e}")
    
    finally:
        # Clean up connection
        try:
            room = await websocket_manager.get_room(document_id)
            await room.remove_connection(userId)
            await websocket_manager.remove_room(document_id)
        except Exception as e:
            logger.error(f"Error cleaning up connection for user {userId}: {e}")
        finally:
            # Close database session
            db.close()
