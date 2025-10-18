from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator


class AnnotationType(str, Enum):
    """Supported annotation types."""
    TEXT = "text"
    LINE = "line"
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    POLYGON = "polygon"
    FREEHAND = "freehand"


class TextAlignment(str, Enum):
    """Text alignment options."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class Style(BaseModel):
    """Common styling properties for annotations."""
    fill_color: Optional[str] = Field(None, description="Fill color in hex format (#RRGGBB)")
    stroke_color: Optional[str] = Field(None, description="Stroke color in hex format (#RRGGBB)")
    stroke_width: Optional[float] = Field(None, ge=0, description="Stroke width in pixels")
    opacity: Optional[float] = Field(None, ge=0, le=1, description="Opacity (0-1)")
    font_family: Optional[str] = Field(None, description="Font family name")
    font_size: Optional[float] = Field(None, ge=0, description="Font size in pixels")
    font_weight: Optional[str] = Field(None, description="Font weight (normal, bold, etc.)")
    text_align: Optional[TextAlignment] = Field(None, description="Text alignment")


class Transform(BaseModel):
    """2D transformation properties."""
    x: float = Field(0, description="X translation in pixels")
    y: float = Field(0, description="Y translation in pixels")
    scale_x: float = Field(1, description="X scale factor")
    scale_y: float = Field(1, description="Y scale factor")
    rotation: float = Field(0, description="Rotation in radians")
    skew_x: float = Field(0, description="X skew in radians")
    skew_y: float = Field(0, description="Y skew in radians")


class Point2D(BaseModel):
    """2D point with x, y coordinates."""
    x: float = Field(description="X coordinate in pixels")
    y: float = Field(description="Y coordinate in pixels")


class RectangleGeometry(BaseModel):
    """Rectangle annotation geometry."""
    x: float = Field(description="Top-left X coordinate")
    y: float = Field(description="Top-left Y coordinate")
    width: float = Field(gt=0, description="Rectangle width")
    height: float = Field(gt=0, description="Rectangle height")


class EllipseGeometry(BaseModel):
    """Ellipse annotation geometry."""
    center_x: float = Field(description="Center X coordinate")
    center_y: float = Field(description="Center Y coordinate")
    radius_x: float = Field(gt=0, description="Horizontal radius")
    radius_y: float = Field(gt=0, description="Vertical radius")


class LineGeometry(BaseModel):
    """Line annotation geometry."""
    start: Point2D = Field(description="Start point")
    end: Point2D = Field(description="End point")
    arrow_start: bool = Field(False, description="Show arrow at start")
    arrow_end: bool = Field(True, description="Show arrow at end")


class PolygonGeometry(BaseModel):
    """Polygon annotation geometry."""
    points: List[Point2D] = Field(min_length=3, description="Polygon vertices")
    closed: bool = Field(True, description="Whether polygon is closed")


class FreehandGeometry(BaseModel):
    """Freehand path annotation geometry."""
    points: List[Point2D] = Field(min_length=2, description="Path points")
    smooth: bool = Field(True, description="Apply smoothing to path")


class TextGeometry(BaseModel):
    """Text annotation geometry."""
    x: float = Field(description="Text position X")
    y: float = Field(description="Text position Y")
    width: Optional[float] = Field(None, gt=0, description="Text box width (optional)")
    height: Optional[float] = Field(None, gt=0, description="Text box height (optional)")


class BaseAnnotation(BaseModel):
    """Base annotation model with common properties."""
    id: str = Field(description="Unique annotation identifier")
    type: AnnotationType = Field(description="Annotation type")
    z_order: int = Field(0, description="Z-order for layering (higher = on top)")
    style: Optional[Style] = Field(None, description="Styling properties")
    transform: Optional[Transform] = Field(None, description="Transformation properties")
    created_at: float = Field(description="Creation timestamp")
    created_by: str = Field(description="User ID who created the annotation")
    updated_at: float = Field(description="Last update timestamp")
    updated_by: str = Field(description="User ID who last updated the annotation")
    group_id: Optional[str] = Field(None, description="Group ID for grouping annotations")
    visible: bool = Field(True, description="Whether annotation is visible")
    locked: bool = Field(False, description="Whether annotation is locked from editing")


class TextAnnotation(BaseAnnotation):
    """Text annotation with text content and geometry."""
    type: Literal[AnnotationType.TEXT] = AnnotationType.TEXT
    geometry: TextGeometry = Field(description="Text geometry")
    text: str = Field(description="Text content")


class LineAnnotation(BaseAnnotation):
    """Line annotation with start/end points and optional arrows."""
    type: Literal[AnnotationType.LINE] = AnnotationType.LINE
    geometry: LineGeometry = Field(description="Line geometry")


class RectangleAnnotation(BaseAnnotation):
    """Rectangle annotation with position and dimensions."""
    type: Literal[AnnotationType.RECTANGLE] = AnnotationType.RECTANGLE
    geometry: RectangleGeometry = Field(description="Rectangle geometry")


class EllipseAnnotation(BaseAnnotation):
    """Ellipse annotation with center and radii."""
    type: Literal[AnnotationType.ELLIPSE] = AnnotationType.ELLIPSE
    geometry: EllipseGeometry = Field(description="Ellipse geometry")


class PolygonAnnotation(BaseAnnotation):
    """Polygon annotation with vertices."""
    type: Literal[AnnotationType.POLYGON] = AnnotationType.POLYGON
    geometry: PolygonGeometry = Field(description="Polygon geometry")


class FreehandAnnotation(BaseAnnotation):
    """Freehand path annotation with points."""
    type: Literal[AnnotationType.FREEHAND] = AnnotationType.FREEHAND
    geometry: FreehandGeometry = Field(description="Freehand geometry")


# Union type for all annotation types
Annotation = Union[
    TextAnnotation,
    LineAnnotation,
    RectangleAnnotation,
    EllipseAnnotation,
    PolygonAnnotation,
    FreehandAnnotation,
]


class AnnotationCreateRequest(BaseModel):
    """Request model for creating annotations."""
    type: AnnotationType = Field(description="Annotation type")
    geometry: Union[
        TextGeometry,
        LineGeometry,
        RectangleGeometry,
        EllipseGeometry,
        PolygonGeometry,
        FreehandGeometry,
    ] = Field(description="Annotation geometry")
    text: Optional[str] = Field(None, description="Text content (for text annotations)")
    style: Optional[Style] = Field(None, description="Styling properties")
    transform: Optional[Transform] = Field(None, description="Transformation properties")
    z_order: int = Field(0, description="Z-order for layering")
    group_id: Optional[str] = Field(None, description="Group ID for grouping")
    visible: bool = Field(True, description="Whether annotation is visible")
    locked: bool = Field(False, description="Whether annotation is locked")

    @field_validator('text')
    @classmethod
    def validate_text_for_text_type(cls, v, info):
        """Ensure text content is provided for text annotations."""
        if hasattr(info, 'data') and info.data.get('type') == AnnotationType.TEXT and not v:
            raise ValueError('Text content is required for text annotations')
        return v


class AnnotationUpdateRequest(BaseModel):
    """Request model for updating annotations."""
    geometry: Optional[Union[
        TextGeometry,
        LineGeometry,
        RectangleGeometry,
        EllipseGeometry,
        PolygonGeometry,
        FreehandGeometry,
    ]] = Field(None, description="Updated geometry")
    text: Optional[str] = Field(None, description="Updated text content")
    style: Optional[Style] = Field(None, description="Updated styling")
    transform: Optional[Transform] = Field(None, description="Updated transformation")
    z_order: Optional[int] = Field(None, description="Updated z-order")
    group_id: Optional[str] = Field(None, description="Updated group ID")
    visible: Optional[bool] = Field(None, description="Updated visibility")
    locked: Optional[bool] = Field(None, description="Updated lock status")


class AnnotationResponse(BaseModel):
    """Response model for annotation operations."""
    annotation: Annotation = Field(description="The annotation data")
    seq: int = Field(description="Sequence number of the CRDT update")


class AnnotationListResponse(BaseModel):
    """Response model for listing annotations."""
    annotations: List[Annotation] = Field(description="List of annotations")
    total: int = Field(description="Total number of annotations")
    seq: int = Field(description="Current sequence number")


class AnnotationDeleteResponse(BaseModel):
    """Response model for annotation deletion."""
    deleted_id: str = Field(description="ID of deleted annotation")
    seq: int = Field(description="Sequence number of the CRDT update")


class GroupAnnotationsRequest(BaseModel):
    """Request model for grouping annotations."""
    annotation_ids: List[str] = Field(min_length=2, description="IDs of annotations to group")
    group_id: Optional[str] = Field(None, description="Group ID (auto-generated if not provided)")


class UngroupAnnotationsRequest(BaseModel):
    """Request model for ungrouping annotations."""
    group_id: str = Field(description="Group ID to ungroup")


class GroupResponse(BaseModel):
    """Response model for grouping operations."""
    group_id: str = Field(description="Group ID")
    annotation_ids: List[str] = Field(description="IDs of grouped annotations")
    seq: int = Field(description="Sequence number of the CRDT update")
