from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import JSONResponse

from app.schemas.comment import (
    CommentCreateRequest,
    CommentUpdateRequest,
    CommentThreadCreateRequest,
    CommentThreadUpdateRequest,
    CommentResponse,
    CommentThreadResponse,
    CommentListResponse,
    CommentThreadListResponse,
    CommentDeleteResponse,
    CommentThreadDeleteResponse,
    CommentFilter,
)
from app.services.comment_service import comment_service

router = APIRouter()


@router.post("/rooms/{room_id}/comments/threads", response_model=CommentThreadResponse)
async def create_comment_thread(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    request: CommentThreadCreateRequest = ...,
    user_id: str = Query(..., description="User ID"),
) -> CommentThreadResponse:
    """Create a new comment thread in the specified room."""
    try:
        thread, seq = await comment_service.create_comment_thread(
            room_id, user_id, request
        )
        return CommentThreadResponse(thread=thread, seq=seq)
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/rooms/{room_id}/comments/threads", response_model=CommentThreadListResponse)
async def list_comment_threads(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    include_resolved: bool = Query(True, description="Include resolved threads"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of threads to return"),
    offset: int = Query(0, ge=0, description="Number of threads to skip"),
) -> CommentThreadListResponse:
    """List all comment threads in the specified room."""
    try:
        threads, seq = await comment_service.get_comment_threads(
            room_id, include_resolved
        )
        
        # Apply pagination
        total = len(threads)
        paginated_threads = threads[offset:offset + limit]
        
        return CommentThreadListResponse(
            threads=paginated_threads,
            total=total,
            seq=seq
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/rooms/{room_id}/comments/threads/{thread_id}", response_model=CommentThreadResponse)
async def get_comment_thread(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    thread_id: str = Path(..., min_length=1, description="Thread ID"),
) -> CommentThreadResponse:
    """Get a specific comment thread by ID."""
    try:
        threads, seq = await comment_service.get_comment_threads(room_id)
        thread = next((t for t in threads if t.id == thread_id), None)
        if not thread:
            raise HTTPException(status_code=404, detail="Comment thread not found")
        return CommentThreadResponse(thread=thread, seq=seq)
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.patch("/rooms/{room_id}/comments/threads/{thread_id}", response_model=CommentThreadResponse)
async def update_comment_thread(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    thread_id: str = Path(..., min_length=1, description="Thread ID"),
    request: CommentThreadUpdateRequest = ...,
    user_id: str = Query(..., description="User ID"),
) -> CommentThreadResponse:
    """Update a comment thread (status, visibility, etc.)."""
    try:
        thread, seq = await comment_service.update_comment_thread(
            room_id, thread_id, user_id, request
        )
        return CommentThreadResponse(thread=thread, seq=seq)
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/rooms/{room_id}/comments/threads/{thread_id}", response_model=CommentThreadDeleteResponse)
async def delete_comment_thread(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    thread_id: str = Path(..., min_length=1, description="Thread ID"),
    user_id: str = Query(..., description="User ID"),
) -> CommentThreadDeleteResponse:
    """Delete a comment thread and all its comments."""
    try:
        deleted_thread_id, seq = await comment_service.delete_comment_thread(
            room_id, thread_id, user_id
        )
        return CommentThreadDeleteResponse(deleted_thread_id=deleted_thread_id, seq=seq)
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/rooms/{room_id}/comments/threads/{thread_id}/comments", response_model=CommentResponse)
async def add_comment_to_thread(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    thread_id: str = Path(..., min_length=1, description="Thread ID"),
    request: CommentCreateRequest = ...,
    user_id: str = Query(..., description="User ID"),
) -> CommentResponse:
    """Add a comment to an existing thread."""
    try:
        comment, thread, seq = await comment_service.add_comment_to_thread(
            room_id, thread_id, user_id, request
        )
        return CommentResponse(comment=comment, thread=thread, seq=seq)
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.patch("/rooms/{room_id}/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    comment_id: str = Path(..., min_length=1, description="Comment ID"),
    request: CommentUpdateRequest = ...,
    user_id: str = Query(..., description="User ID"),
) -> CommentResponse:
    """Update an existing comment."""
    try:
        comment, thread, seq = await comment_service.update_comment(
            room_id, comment_id, user_id, request
        )
        return CommentResponse(comment=comment, thread=thread, seq=seq)
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/rooms/{room_id}/comments/{comment_id}", response_model=CommentDeleteResponse)
async def delete_comment(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    comment_id: str = Path(..., min_length=1, description="Comment ID"),
    user_id: str = Query(..., description="User ID"),
) -> CommentDeleteResponse:
    """Delete a comment."""
    try:
        deleted_comment_id, thread_id, seq = await comment_service.delete_comment(
            room_id, comment_id, user_id
        )
        return CommentDeleteResponse(
            deleted_id=deleted_comment_id,
            thread_id=thread_id,
            seq=seq
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/rooms/{room_id}/annotations/{annotation_id}/comments", response_model=CommentThreadListResponse)
async def get_comments_for_annotation(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    annotation_id: str = Path(..., min_length=1, description="Annotation ID"),
    include_resolved: bool = Query(True, description="Include resolved threads"),
) -> CommentThreadListResponse:
    """Get all comment threads anchored to a specific annotation."""
    try:
        threads, seq = await comment_service.get_comments_for_annotation(
            room_id, annotation_id
        )
        
        # Filter by resolved status if needed
        if not include_resolved:
            from app.schemas.comment import CommentStatus
            threads = [t for t in threads if t.status == CommentStatus.OPEN]
        
        return CommentThreadListResponse(
            threads=threads,
            total=len(threads),
            seq=seq
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
