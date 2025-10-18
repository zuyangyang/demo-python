from __future__ import annotations

import json
import time
import uuid
from typing import Dict, List, Optional, Tuple

from app.schemas.comment import (
    Comment,
    CommentThread,
    CommentCreateRequest,
    CommentUpdateRequest,
    CommentThreadCreateRequest,
    CommentThreadUpdateRequest,
    CommentStatus,
    CommentAnchor,
)
from app.services.room_registry import room_registry


class CommentService:
    """Service for managing comments and comment threads via CRDT operations."""

    def __init__(self):
        self.room_registry = room_registry

    async def create_comment_thread(
        self,
        room_id: str,
        user_id: str,
        request: CommentThreadCreateRequest
    ) -> tuple[CommentThread, int]:
        """Create a new comment thread with initial comment."""
        thread_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())
        current_time = time.time()
        
        # Create initial comment
        comment = Comment(
            id=comment_id,
            thread_id=thread_id,
            content=request.initial_comment,
            author_id=user_id,
            created_at=current_time,
            updated_at=current_time,
            edited=False
        )
        
        # Create thread
        thread = CommentThread(
            id=thread_id,
            room_id=room_id,
            anchor=request.anchor,
            status=CommentStatus.OPEN,
            comments=[comment],
            created_at=current_time,
            created_by=user_id,
            updated_at=current_time,
            updated_by=user_id,
            visible=True
        )
        
        # Store in CRDT
        crdt_update = {
            "type": "comment_thread_create",
            "thread": thread.model_dump()
        }
        
        update_bytes = json.dumps(crdt_update).encode('utf-8')
        seq = await self.room_registry.append_update(room_id, update_bytes)
        
        return thread, seq

    async def add_comment_to_thread(
        self,
        room_id: str,
        thread_id: str,
        user_id: str,
        request: CommentCreateRequest
    ) -> tuple[Comment, CommentThread, int]:
        """Add a comment to an existing thread."""
        comment_id = str(uuid.uuid4())
        current_time = time.time()
        
        # Create comment
        comment = Comment(
            id=comment_id,
            thread_id=thread_id,
            content=request.content,
            author_id=user_id,
            created_at=current_time,
            updated_at=current_time,
            edited=False,
            parent_id=request.parent_id
        )
        
        # Store in CRDT
        crdt_update = {
            "type": "comment_add",
            "thread_id": thread_id,
            "comment": comment.model_dump()
        }
        
        update_bytes = json.dumps(crdt_update).encode('utf-8')
        seq = await self.room_registry.append_update(room_id, update_bytes)
        
        # In a real implementation, we'd reconstruct the thread from CRDT state
        # For now, return a placeholder thread
        thread = self._create_placeholder_thread(thread_id, room_id, user_id, current_time)
        
        return comment, thread, seq

    async def update_comment(
        self,
        room_id: str,
        comment_id: str,
        user_id: str,
        request: CommentUpdateRequest
    ) -> tuple[Comment, CommentThread, int]:
        """Update an existing comment."""
        current_time = time.time()
        
        # Create update data
        update_data = request.model_dump(exclude_unset=True)
        update_data["updated_at"] = current_time
        update_data["edited"] = True
        
        # Store in CRDT
        crdt_update = {
            "type": "comment_update",
            "comment_id": comment_id,
            "updates": update_data,
            "updated_by": user_id
        }
        
        update_bytes = json.dumps(crdt_update).encode('utf-8')
        seq = await self.room_registry.append_update(room_id, update_bytes)
        
        # In a real implementation, we'd reconstruct the comment and thread from CRDT state
        comment = self._create_placeholder_comment(comment_id, user_id, current_time)
        thread = self._create_placeholder_thread("placeholder", room_id, user_id, current_time)
        
        return comment, thread, seq

    async def update_comment_thread(
        self,
        room_id: str,
        thread_id: str,
        user_id: str,
        request: CommentThreadUpdateRequest
    ) -> tuple[CommentThread, int]:
        """Update a comment thread (status, visibility, etc.)."""
        current_time = time.time()
        
        # Create update data
        update_data = request.model_dump(exclude_unset=True)
        update_data["updated_at"] = current_time
        update_data["updated_by"] = user_id
        
        # Handle status changes
        if "status" in update_data:
            if update_data["status"] == CommentStatus.RESOLVED:
                update_data["resolved_at"] = current_time
                update_data["resolved_by"] = user_id
            elif update_data["status"] == CommentStatus.OPEN:
                update_data["resolved_at"] = None
                update_data["resolved_by"] = None
        
        # Store in CRDT
        crdt_update = {
            "type": "comment_thread_update",
            "thread_id": thread_id,
            "updates": update_data
        }
        
        update_bytes = json.dumps(crdt_update).encode('utf-8')
        seq = await self.room_registry.append_update(room_id, update_bytes)
        
        # In a real implementation, we'd reconstruct the thread from CRDT state
        thread = self._create_placeholder_thread(thread_id, room_id, user_id, current_time)
        
        return thread, seq

    async def delete_comment(
        self,
        room_id: str,
        comment_id: str,
        user_id: str
    ) -> tuple[str, str, int]:
        """Delete a comment."""
        current_time = time.time()
        
        # Store in CRDT
        crdt_update = {
            "type": "comment_delete",
            "comment_id": comment_id,
            "deleted_by": user_id,
            "deleted_at": current_time
        }
        
        update_bytes = json.dumps(crdt_update).encode('utf-8')
        seq = await self.room_registry.append_update(room_id, update_bytes)
        
        # In a real implementation, we'd get the thread_id from CRDT state
        thread_id = "placeholder"
        
        return comment_id, thread_id, seq

    async def delete_comment_thread(
        self,
        room_id: str,
        thread_id: str,
        user_id: str
    ) -> tuple[str, int]:
        """Delete an entire comment thread."""
        current_time = time.time()
        
        # Store in CRDT
        crdt_update = {
            "type": "comment_thread_delete",
            "thread_id": thread_id,
            "deleted_by": user_id,
            "deleted_at": current_time
        }
        
        update_bytes = json.dumps(crdt_update).encode('utf-8')
        seq = await self.room_registry.append_update(room_id, update_bytes)
        
        return thread_id, seq

    async def get_comment_threads(
        self,
        room_id: str,
        include_resolved: bool = True
    ) -> tuple[List[CommentThread], int]:
        """Get all comment threads for a room from CRDT state."""
        # In a real implementation, this would reconstruct threads from CRDT state
        room_state = await self.room_registry.get_room(room_id)
        if not room_state:
            return [], 0
        
        # Get current sequence number
        current_seq = room_state.next_seq - 1 if room_state.next_seq > 1 else 0
        
        # In a real implementation, we'd parse the event log to reconstruct threads
        threads = []
        
        return threads, current_seq

    async def get_comments_for_annotation(
        self,
        room_id: str,
        annotation_id: str
    ) -> tuple[List[CommentThread], int]:
        """Get all comment threads anchored to a specific annotation."""
        # In a real implementation, this would filter threads by annotation_id
        threads, seq = await self.get_comment_threads(room_id)
        
        # Filter by annotation_id
        filtered_threads = [
            thread for thread in threads
            if thread.anchor.annotation_id == annotation_id
        ]
        
        return filtered_threads, seq

    def _create_placeholder_comment(
        self,
        comment_id: str,
        user_id: str,
        current_time: float
    ) -> Comment:
        """Create a placeholder comment for testing."""
        return Comment(
            id=comment_id,
            thread_id="placeholder",
            content="Placeholder comment",
            author_id=user_id,
            created_at=current_time,
            updated_at=current_time,
            edited=False
        )

    def _create_placeholder_thread(
        self,
        thread_id: str,
        room_id: str,
        user_id: str,
        current_time: float
    ) -> CommentThread:
        """Create a placeholder thread for testing."""
        return CommentThread(
            id=thread_id,
            room_id=room_id,
            anchor=CommentAnchor(coordinate={"x": 0, "y": 0}),
            status=CommentStatus.OPEN,
            comments=[],
            created_at=current_time,
            created_by=user_id,
            updated_at=current_time,
            updated_by=user_id,
            visible=True
        )


# Singleton service instance
comment_service = CommentService()
