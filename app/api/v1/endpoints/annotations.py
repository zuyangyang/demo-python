from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import JSONResponse

from app.schemas.annotation import (
    AnnotationCreateRequest,
    AnnotationUpdateRequest,
    AnnotationResponse,
    AnnotationListResponse,
    AnnotationDeleteResponse,
    GroupAnnotationsRequest,
    UngroupAnnotationsRequest,
    GroupResponse,
)
from app.services.annotation_service import annotation_service

router = APIRouter()


@router.post("/rooms/{room_id}/annotations", response_model=AnnotationResponse)
async def create_annotation(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    request: AnnotationCreateRequest = ...,
    user_id: str = Query(..., description="User ID"),
) -> AnnotationResponse:
    """Create a new annotation in the specified room."""
    try:
        annotation, seq = await annotation_service.create_annotation(
            room_id, user_id, request
        )
        return AnnotationResponse(annotation=annotation, seq=seq)
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/rooms/{room_id}/annotations", response_model=AnnotationListResponse)
async def list_annotations(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    include_deleted: bool = Query(False, description="Include deleted annotations"),
) -> AnnotationListResponse:
    """List all annotations in the specified room."""
    try:
        annotations, seq = await annotation_service.get_annotations(
            room_id, include_deleted
        )
        return AnnotationListResponse(
            annotations=annotations,
            total=len(annotations),
            seq=seq
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/rooms/{room_id}/annotations/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    annotation_id: str = Path(..., min_length=1, description="Annotation ID"),
) -> AnnotationResponse:
    """Get a specific annotation by ID."""
    try:
        annotations, seq = await annotation_service.get_annotations(room_id)
        annotation = next((a for a in annotations if a.id == annotation_id), None)
        if not annotation:
            raise HTTPException(status_code=404, detail="Annotation not found")
        return AnnotationResponse(annotation=annotation, seq=seq)
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.patch("/rooms/{room_id}/annotations/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    annotation_id: str = Path(..., min_length=1, description="Annotation ID"),
    request: AnnotationUpdateRequest = ...,
    user_id: str = Query(..., description="User ID"),
) -> AnnotationResponse:
    """Update an existing annotation."""
    try:
        annotation, seq = await annotation_service.update_annotation(
            room_id, annotation_id, user_id, request
        )
        return AnnotationResponse(annotation=annotation, seq=seq)
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/rooms/{room_id}/annotations/{annotation_id}", response_model=AnnotationDeleteResponse)
async def delete_annotation(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    annotation_id: str = Path(..., min_length=1, description="Annotation ID"),
    user_id: str = Query(..., description="User ID"),
) -> AnnotationDeleteResponse:
    """Delete an annotation."""
    try:
        deleted_id, seq = await annotation_service.delete_annotation(
            room_id, annotation_id, user_id
        )
        return AnnotationDeleteResponse(deleted_id=deleted_id, seq=seq)
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/rooms/{room_id}/annotations/group", response_model=GroupResponse)
async def group_annotations(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    request: GroupAnnotationsRequest = ...,
    user_id: str = Query(..., description="User ID"),
) -> GroupResponse:
    """Group multiple annotations together."""
    try:
        group_id, annotation_ids, seq = await annotation_service.group_annotations(
            room_id, user_id, request
        )
        return GroupResponse(
            group_id=group_id,
            annotation_ids=annotation_ids,
            seq=seq
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/rooms/{room_id}/annotations/ungroup", response_model=GroupResponse)
async def ungroup_annotations(
    room_id: str = Path(..., min_length=1, description="Room ID"),
    request: UngroupAnnotationsRequest = ...,
    user_id: str = Query(..., description="User ID"),
) -> GroupResponse:
    """Ungroup annotations."""
    try:
        group_id, seq = await annotation_service.ungroup_annotations(
            room_id, user_id, request
        )
        return GroupResponse(
            group_id=group_id,
            annotation_ids=[],  # Empty for ungroup operation
            seq=seq
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
