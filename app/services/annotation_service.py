from __future__ import annotations

import json
import time
import uuid
from typing import Dict, List, Optional, Union

from app.schemas.annotation import (
    Annotation,
    AnnotationCreateRequest,
    AnnotationUpdateRequest,
    AnnotationType,
    TextAnnotation,
    LineAnnotation,
    RectangleAnnotation,
    EllipseAnnotation,
    PolygonAnnotation,
    FreehandAnnotation,
    GroupAnnotationsRequest,
    UngroupAnnotationsRequest,
)
from app.services.room_registry import room_registry


class AnnotationService:
    """Service for managing annotations via CRDT operations."""

    def __init__(self):
        self.room_registry = room_registry

    async def create_annotation(
        self, 
        room_id: str, 
        user_id: str, 
        request: AnnotationCreateRequest
    ) -> tuple[Annotation, int]:
        """Create a new annotation and return it with sequence number."""
        # Generate unique ID
        annotation_id = str(uuid.uuid4())
        current_time = time.time()
        
        # Create annotation based on type
        annotation = self._create_annotation_from_request(
            annotation_id, user_id, current_time, request
        )
        
        # Serialize to JSON for CRDT storage
        annotation_data = annotation.model_dump()
        crdt_update = {
            "type": "annotation_create",
            "annotation": annotation_data
        }
        
        # Store in CRDT
        update_bytes = json.dumps(crdt_update).encode('utf-8')
        seq = await self.room_registry.append_update(room_id, update_bytes)
        
        return annotation, seq

    async def update_annotation(
        self,
        room_id: str,
        annotation_id: str,
        user_id: str,
        request: AnnotationUpdateRequest
    ) -> tuple[Annotation, int]:
        """Update an existing annotation and return it with sequence number."""
        current_time = time.time()
        
        # Get current annotation state (in a real implementation, this would be from CRDT)
        # For now, we'll create a partial update
        update_data = request.model_dump(exclude_unset=True)
        update_data["updated_at"] = current_time
        update_data["updated_by"] = user_id
        
        crdt_update = {
            "type": "annotation_update",
            "annotation_id": annotation_id,
            "updates": update_data
        }
        
        # Store in CRDT
        update_bytes = json.dumps(crdt_update).encode('utf-8')
        seq = await self.room_registry.append_update(room_id, update_bytes)
        
        # In a real implementation, we'd reconstruct the full annotation from CRDT state
        # For now, return a placeholder
        annotation = self._create_placeholder_annotation(annotation_id, user_id, current_time)
        
        return annotation, seq

    async def delete_annotation(
        self,
        room_id: str,
        annotation_id: str,
        user_id: str
    ) -> tuple[str, int]:
        """Delete an annotation and return its ID with sequence number."""
        crdt_update = {
            "type": "annotation_delete",
            "annotation_id": annotation_id,
            "deleted_by": user_id,
            "deleted_at": time.time()
        }
        
        # Store in CRDT
        update_bytes = json.dumps(crdt_update).encode('utf-8')
        seq = await self.room_registry.append_update(room_id, update_bytes)
        
        return annotation_id, seq

    async def get_annotations(
        self,
        room_id: str,
        include_deleted: bool = False
    ) -> tuple[List[Annotation], int]:
        """Get all annotations for a room from CRDT state."""
        # In a real implementation, this would reconstruct annotations from CRDT state
        # For now, return empty list
        room_state = await self.room_registry.get_room(room_id)
        if not room_state:
            return [], 0
        
        # Get current sequence number
        current_seq = room_state.next_seq - 1 if room_state.next_seq > 1 else 0
        
        # In a real implementation, we'd parse the event log to reconstruct annotations
        annotations = []
        
        return annotations, current_seq

    async def group_annotations(
        self,
        room_id: str,
        user_id: str,
        request: GroupAnnotationsRequest
    ) -> tuple[str, List[str], int]:
        """Group multiple annotations together."""
        group_id = request.group_id or str(uuid.uuid4())
        current_time = time.time()
        
        crdt_update = {
            "type": "annotation_group",
            "group_id": group_id,
            "annotation_ids": request.annotation_ids,
            "grouped_by": user_id,
            "grouped_at": current_time
        }
        
        # Store in CRDT
        update_bytes = json.dumps(crdt_update).encode('utf-8')
        seq = await self.room_registry.append_update(room_id, update_bytes)
        
        return group_id, request.annotation_ids, seq

    async def ungroup_annotations(
        self,
        room_id: str,
        user_id: str,
        request: UngroupAnnotationsRequest
    ) -> tuple[str, int]:
        """Ungroup annotations."""
        current_time = time.time()
        
        crdt_update = {
            "type": "annotation_ungroup",
            "group_id": request.group_id,
            "ungrouped_by": user_id,
            "ungrouped_at": current_time
        }
        
        # Store in CRDT
        update_bytes = json.dumps(crdt_update).encode('utf-8')
        seq = await self.room_registry.append_update(room_id, update_bytes)
        
        return request.group_id, seq

    def _create_annotation_from_request(
        self,
        annotation_id: str,
        user_id: str,
        current_time: float,
        request: AnnotationCreateRequest
    ) -> Annotation:
        """Create an annotation object from a create request."""
        base_data = {
            "id": annotation_id,
            "type": request.type,
            "z_order": request.z_order,
            "style": request.style,
            "transform": request.transform,
            "created_at": current_time,
            "created_by": user_id,
            "updated_at": current_time,
            "updated_by": user_id,
            "group_id": request.group_id,
            "visible": request.visible,
            "locked": request.locked,
        }
        
        if request.type == AnnotationType.TEXT:
            return TextAnnotation(
                **base_data,
                geometry=request.geometry,
                text=request.text or ""
            )
        elif request.type == AnnotationType.LINE:
            return LineAnnotation(
                **base_data,
                geometry=request.geometry
            )
        elif request.type == AnnotationType.RECTANGLE:
            return RectangleAnnotation(
                **base_data,
                geometry=request.geometry
            )
        elif request.type == AnnotationType.ELLIPSE:
            return EllipseAnnotation(
                **base_data,
                geometry=request.geometry
            )
        elif request.type == AnnotationType.POLYGON:
            return PolygonAnnotation(
                **base_data,
                geometry=request.geometry
            )
        elif request.type == AnnotationType.FREEHAND:
            return FreehandAnnotation(
                **base_data,
                geometry=request.geometry
            )
        else:
            raise ValueError(f"Unsupported annotation type: {request.type}")

    def _create_placeholder_annotation(
        self,
        annotation_id: str,
        user_id: str,
        current_time: float
    ) -> Annotation:
        """Create a placeholder annotation for testing."""
        from app.schemas.annotation import TextGeometry, TextAnnotation
        
        return TextAnnotation(
            id=annotation_id,
            type=AnnotationType.TEXT,
            geometry=TextGeometry(x=0, y=0),
            text="Placeholder",
            z_order=0,
            created_at=current_time,
            created_by=user_id,
            updated_at=current_time,
            updated_by=user_id,
            visible=True,
            locked=False
        )


# Singleton service instance
annotation_service = AnnotationService()
