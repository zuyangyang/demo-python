from __future__ import annotations

from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class CommentStatus(str, Enum):
    """Comment thread status."""
    OPEN = "open"
    RESOLVED = "resolved"


class CommentAnchor(BaseModel):
    """Anchor point for comments - either annotation ID or coordinate."""
    annotation_id: Optional[str] = Field(None, description="ID of annotation being commented on")
    coordinate: Optional[dict] = Field(None, description="Coordinate point {x, y} for general comments")
    
    @field_validator('coordinate')
    @classmethod
    def validate_coordinate(cls, v):
        """Validate coordinate has x and y fields."""
        if v is not None:
            if not isinstance(v, dict) or 'x' not in v or 'y' not in v:
                raise ValueError('Coordinate must have x and y fields')
            if not isinstance(v['x'], (int, float)) or not isinstance(v['y'], (int, float)):
                raise ValueError('Coordinate x and y must be numbers')
        return v
    
    @model_validator(mode='after')
    def validate_anchor(self):
        """Ensure either annotation_id or coordinate is provided, but not both."""
        if self.annotation_id is not None and self.coordinate is not None:
            raise ValueError('Cannot specify both annotation_id and coordinate')
        if self.annotation_id is None and self.coordinate is None:
            raise ValueError('Must specify either annotation_id or coordinate')
        return self


class Comment(BaseModel):
    """Individual comment within a thread."""
    id: str = Field(description="Unique comment identifier")
    thread_id: str = Field(description="ID of the comment thread")
    content: str = Field(min_length=1, description="Comment text content")
    author_id: str = Field(description="User ID who wrote the comment")
    created_at: float = Field(description="Creation timestamp")
    updated_at: float = Field(description="Last update timestamp")
    edited: bool = Field(False, description="Whether comment has been edited")
    parent_id: Optional[str] = Field(None, description="Parent comment ID for nested replies")


class CommentThread(BaseModel):
    """Comment thread anchored to an annotation or coordinate."""
    id: str = Field(description="Unique thread identifier")
    room_id: str = Field(description="Room ID containing the thread")
    anchor: CommentAnchor = Field(description="Thread anchor point")
    status: CommentStatus = Field(CommentStatus.OPEN, description="Thread status")
    comments: List[Comment] = Field(default_factory=list, description="Comments in the thread")
    created_at: float = Field(description="Thread creation timestamp")
    created_by: str = Field(description="User ID who created the thread")
    updated_at: float = Field(description="Last update timestamp")
    updated_by: str = Field(description="User ID who last updated the thread")
    visible: bool = Field(True, description="Whether thread is visible")
    resolved_at: Optional[float] = Field(None, description="Resolution timestamp")
    resolved_by: Optional[str] = Field(None, description="User ID who resolved the thread")


class CommentCreateRequest(BaseModel):
    """Request model for creating comments."""
    content: str = Field(min_length=1, description="Comment text content")
    anchor: CommentAnchor = Field(description="Thread anchor point")
    parent_id: Optional[str] = Field(None, description="Parent comment ID for nested replies")
    thread_id: Optional[str] = Field(None, description="Existing thread ID (if adding to existing thread)")


class CommentUpdateRequest(BaseModel):
    """Request model for updating comments."""
    content: Optional[str] = Field(None, min_length=1, description="Updated comment text")


class CommentThreadCreateRequest(BaseModel):
    """Request model for creating comment threads."""
    anchor: CommentAnchor = Field(description="Thread anchor point")
    initial_comment: str = Field(min_length=1, description="Initial comment text")


class CommentThreadUpdateRequest(BaseModel):
    """Request model for updating comment threads."""
    status: Optional[CommentStatus] = Field(None, description="Updated thread status")
    visible: Optional[bool] = Field(None, description="Updated visibility")


class CommentResponse(BaseModel):
    """Response model for comment operations."""
    comment: Comment = Field(description="The comment data")
    thread: CommentThread = Field(description="The thread containing the comment")
    seq: int = Field(description="Sequence number of the CRDT update")


class CommentThreadResponse(BaseModel):
    """Response model for comment thread operations."""
    thread: CommentThread = Field(description="The thread data")
    seq: int = Field(description="Sequence number of the CRDT update")


class CommentListResponse(BaseModel):
    """Response model for listing comments."""
    threads: List[CommentThread] = Field(description="List of comment threads")
    total: int = Field(description="Total number of threads")
    seq: int = Field(description="Current sequence number")


class CommentThreadListResponse(BaseModel):
    """Response model for listing comment threads."""
    threads: List[CommentThread] = Field(description="List of comment threads")
    total: int = Field(description="Total number of threads")
    seq: int = Field(description="Current sequence number")


class CommentDeleteResponse(BaseModel):
    """Response model for comment deletion."""
    deleted_id: str = Field(description="ID of deleted comment")
    thread_id: str = Field(description="ID of the thread containing the comment")
    seq: int = Field(description="Sequence number of the CRDT update")


class CommentThreadDeleteResponse(BaseModel):
    """Response model for comment thread deletion."""
    deleted_thread_id: str = Field(description="ID of deleted thread")
    seq: int = Field(description="Sequence number of the CRDT update")


class CommentFilter(BaseModel):
    """Filter options for listing comments."""
    status: Optional[CommentStatus] = Field(None, description="Filter by thread status")
    annotation_id: Optional[str] = Field(None, description="Filter by annotation ID")
    author_id: Optional[str] = Field(None, description="Filter by comment author")
    include_resolved: bool = Field(True, description="Include resolved threads")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of threads to return")
    offset: int = Field(0, ge=0, description="Number of threads to skip")
