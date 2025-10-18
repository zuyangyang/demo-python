import pytest
import time
from unittest.mock import AsyncMock, patch

from app.services.annotation_service import AnnotationService
from app.schemas.annotation import (
    AnnotationCreateRequest,
    AnnotationUpdateRequest,
    AnnotationType,
    TextGeometry,
    LineGeometry,
    RectangleGeometry,
    EllipseGeometry,
    PolygonGeometry,
    FreehandGeometry,
    Point2D,
    Style,
    Transform,
    GroupAnnotationsRequest,
    UngroupAnnotationsRequest,
)


class TestAnnotationService:
    """Test cases for AnnotationService."""

    @pytest.fixture
    def annotation_service(self):
        """Create annotation service with mocked dependencies."""
        service = AnnotationService()
        
        # Mock the room registry
        mock_room_state = AsyncMock()
        mock_room_state.next_seq = 2
        
        service.room_registry = AsyncMock()
        service.room_registry.append_update = AsyncMock(return_value=1)
        service.room_registry.get_room = AsyncMock(return_value=mock_room_state)
        service.room_registry.get_or_throw = AsyncMock(return_value=mock_room_state)
        
        return service

    @pytest.fixture
    def text_create_request(self):
        """Sample text annotation create request."""
        return AnnotationCreateRequest(
            type=AnnotationType.TEXT,
            geometry=TextGeometry(x=100, y=200),
            text="Sample text",
            style=Style(fill_color="#FF0000", font_size=16),
            z_order=1
        )

    @pytest.fixture
    def line_create_request(self):
        """Sample line annotation create request."""
        return AnnotationCreateRequest(
            type=AnnotationType.LINE,
            geometry=LineGeometry(
                start=Point2D(x=0, y=0),
                end=Point2D(x=100, y=100),
                arrow_end=True
            ),
            style=Style(stroke_color="#0000FF", stroke_width=2)
        )

    @pytest.fixture
    def rectangle_create_request(self):
        """Sample rectangle annotation create request."""
        return AnnotationCreateRequest(
            type=AnnotationType.RECTANGLE,
            geometry=RectangleGeometry(x=50, y=50, width=200, height=100),
            style=Style(fill_color="#00FF00", stroke_color="#000000")
        )

    @pytest.fixture
    def ellipse_create_request(self):
        """Sample ellipse annotation create request."""
        return AnnotationCreateRequest(
            type=AnnotationType.ELLIPSE,
            geometry=EllipseGeometry(center_x=150, center_y=150, radius_x=50, radius_y=30),
            style=Style(fill_color="#FFFF00", opacity=0.8)
        )

    @pytest.fixture
    def polygon_create_request(self):
        """Sample polygon annotation create request."""
        return AnnotationCreateRequest(
            type=AnnotationType.POLYGON,
            geometry=PolygonGeometry(
                points=[
                    Point2D(x=0, y=0),
                    Point2D(x=100, y=0),
                    Point2D(x=50, y=100)
                ],
                closed=True
            ),
            style=Style(fill_color="#FF00FF", stroke_width=3)
        )

    @pytest.fixture
    def freehand_create_request(self):
        """Sample freehand annotation create request."""
        return AnnotationCreateRequest(
            type=AnnotationType.FREEHAND,
            geometry=FreehandGeometry(
                points=[
                    Point2D(x=0, y=0),
                    Point2D(x=10, y=5),
                    Point2D(x=20, y=10),
                    Point2D(x=30, y=15)
                ],
                smooth=True
            ),
            style=Style(stroke_color="#800080", stroke_width=4)
        )

    @pytest.mark.asyncio
    async def test_create_text_annotation(self, annotation_service, text_create_request):
        """Test creating a text annotation."""
        annotation, seq = await annotation_service.create_annotation(
            "room1", "user1", text_create_request
        )
        
        assert annotation.type == AnnotationType.TEXT
        assert annotation.text == "Sample text"
        assert annotation.geometry.x == 100
        assert annotation.geometry.y == 200
        assert annotation.style.fill_color == "#FF0000"
        assert annotation.style.font_size == 16
        assert annotation.z_order == 1
        assert annotation.created_by == "user1"
        assert seq == 1
        
        annotation_service.room_registry.append_update.assert_called_once()
        call_args = annotation_service.room_registry.append_update.call_args
        assert call_args[0][0] == "room1"  # room_id
        assert isinstance(call_args[0][1], bytes)  # update_bytes

    @pytest.mark.asyncio
    async def test_create_line_annotation(self, annotation_service, line_create_request):
        """Test creating a line annotation."""
        annotation, seq = await annotation_service.create_annotation(
            "room1", "user1", line_create_request
        )
        
        assert annotation.type == AnnotationType.LINE
        assert annotation.geometry.start.x == 0
        assert annotation.geometry.start.y == 0
        assert annotation.geometry.end.x == 100
        assert annotation.geometry.end.y == 100
        assert annotation.geometry.arrow_end is True
        assert annotation.style.stroke_color == "#0000FF"
        assert annotation.style.stroke_width == 2

    @pytest.mark.asyncio
    async def test_create_rectangle_annotation(self, annotation_service, rectangle_create_request):
        """Test creating a rectangle annotation."""
        annotation, seq = await annotation_service.create_annotation(
            "room1", "user1", rectangle_create_request
        )
        
        assert annotation.type == AnnotationType.RECTANGLE
        assert annotation.geometry.x == 50
        assert annotation.geometry.y == 50
        assert annotation.geometry.width == 200
        assert annotation.geometry.height == 100
        assert annotation.style.fill_color == "#00FF00"
        assert annotation.style.stroke_color == "#000000"

    @pytest.mark.asyncio
    async def test_create_ellipse_annotation(self, annotation_service, ellipse_create_request):
        """Test creating an ellipse annotation."""
        annotation, seq = await annotation_service.create_annotation(
            "room1", "user1", ellipse_create_request
        )
        
        assert annotation.type == AnnotationType.ELLIPSE
        assert annotation.geometry.center_x == 150
        assert annotation.geometry.center_y == 150
        assert annotation.geometry.radius_x == 50
        assert annotation.geometry.radius_y == 30
        assert annotation.style.fill_color == "#FFFF00"
        assert annotation.style.opacity == 0.8

    @pytest.mark.asyncio
    async def test_create_polygon_annotation(self, annotation_service, polygon_create_request):
        """Test creating a polygon annotation."""
        annotation, seq = await annotation_service.create_annotation(
            "room1", "user1", polygon_create_request
        )
        
        assert annotation.type == AnnotationType.POLYGON
        assert len(annotation.geometry.points) == 3
        assert annotation.geometry.closed is True
        assert annotation.style.fill_color == "#FF00FF"
        assert annotation.style.stroke_width == 3

    @pytest.mark.asyncio
    async def test_create_freehand_annotation(self, annotation_service, freehand_create_request):
        """Test creating a freehand annotation."""
        annotation, seq = await annotation_service.create_annotation(
            "room1", "user1", freehand_create_request
        )
        
        assert annotation.type == AnnotationType.FREEHAND
        assert len(annotation.geometry.points) == 4
        assert annotation.geometry.smooth is True
        assert annotation.style.stroke_color == "#800080"
        assert annotation.style.stroke_width == 4

    @pytest.mark.asyncio
    async def test_create_annotation_with_transform(self, annotation_service):
        """Test creating annotation with transformation."""
        transform = Transform(x=10, y=20, scale_x=1.5, scale_y=0.8, rotation=0.5)
        request = AnnotationCreateRequest(
            type=AnnotationType.TEXT,
            geometry=TextGeometry(x=0, y=0),
            text="Transformed text",
            transform=transform
        )
        
        annotation, seq = await annotation_service.create_annotation(
            "room1", "user1", request
        )
        
        assert annotation.transform is not None
        assert annotation.transform.x == 10
        assert annotation.transform.y == 20
        assert annotation.transform.scale_x == 1.5
        assert annotation.transform.scale_y == 0.8
        assert annotation.transform.rotation == 0.5

    @pytest.mark.asyncio
    async def test_create_annotation_with_grouping(self, annotation_service):
        """Test creating annotation with group ID."""
        request = AnnotationCreateRequest(
            type=AnnotationType.TEXT,
            geometry=TextGeometry(x=0, y=0),
            text="Grouped text",
            group_id="group1"
        )
        
        annotation, seq = await annotation_service.create_annotation(
            "room1", "user1", request
        )
        
        assert annotation.group_id == "group1"

    @pytest.mark.asyncio
    async def test_create_annotation_room_not_found(self, annotation_service):
        """Test creating annotation when room doesn't exist."""
        annotation_service.room_registry.append_update.side_effect = KeyError("room not found")
        
        request = AnnotationCreateRequest(
            type=AnnotationType.TEXT,
            geometry=TextGeometry(x=0, y=0),
            text="Test"
        )
        
        with pytest.raises(KeyError, match="room not found"):
            await annotation_service.create_annotation("nonexistent", "user1", request)

    @pytest.mark.asyncio
    async def test_update_annotation(self, annotation_service):
        """Test updating an annotation."""
        update_request = AnnotationUpdateRequest(
            text="Updated text",
            style=Style(fill_color="#00FF00"),
            z_order=5
        )
        
        annotation, seq = await annotation_service.update_annotation(
            "room1", "annotation1", "user1", update_request
        )
        
        assert seq == 1
        annotation_service.room_registry.append_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_annotation(self, annotation_service):
        """Test deleting an annotation."""
        deleted_id, seq = await annotation_service.delete_annotation(
            "room1", "annotation1", "user1"
        )
        
        assert deleted_id == "annotation1"
        assert seq == 1
        annotation_service.room_registry.append_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_annotations(self, annotation_service):
        """Test getting annotations for a room."""
        annotations, seq = await annotation_service.get_annotations("room1")
        
        assert isinstance(annotations, list)
        assert seq == 1

    @pytest.mark.asyncio
    async def test_group_annotations(self, annotation_service):
        """Test grouping annotations."""
        request = GroupAnnotationsRequest(
            annotation_ids=["ann1", "ann2", "ann3"],
            group_id="group1"
        )
        
        group_id, annotation_ids, seq = await annotation_service.group_annotations(
            "room1", "user1", request
        )
        
        assert group_id == "group1"
        assert annotation_ids == ["ann1", "ann2", "ann3"]
        assert seq == 1

    @pytest.mark.asyncio
    async def test_group_annotations_auto_generate_id(self, annotation_service):
        """Test grouping annotations with auto-generated group ID."""
        request = GroupAnnotationsRequest(
            annotation_ids=["ann1", "ann2"]
        )
        
        group_id, annotation_ids, seq = await annotation_service.group_annotations(
            "room1", "user1", request
        )
        
        assert group_id is not None
        assert len(group_id) > 0
        assert annotation_ids == ["ann1", "ann2"]

    @pytest.mark.asyncio
    async def test_ungroup_annotations(self, annotation_service):
        """Test ungrouping annotations."""
        request = UngroupAnnotationsRequest(group_id="group1")
        
        group_id, seq = await annotation_service.ungroup_annotations(
            "room1", "user1", request
        )
        
        assert group_id == "group1"
        assert seq == 1

    @pytest.mark.asyncio
    async def test_create_annotation_timestamps(self, annotation_service, text_create_request):
        """Test that annotations have proper timestamps."""
        with patch('time.time', return_value=1234567890.0):
            annotation, seq = await annotation_service.create_annotation(
                "room1", "user1", text_create_request
            )
            
            assert annotation.created_at == 1234567890.0
            assert annotation.updated_at == 1234567890.0
            assert annotation.created_by == "user1"
            assert annotation.updated_by == "user1"

    def test_create_annotation_validation(self):
        """Test annotation creation validation."""
        # Test text annotation without text content
        with pytest.raises(ValueError, match="Text content is required for text annotations"):
            AnnotationCreateRequest(
                type=AnnotationType.TEXT,
                geometry=TextGeometry(x=0, y=0),
                text=None  # Explicitly None
            )

    @pytest.mark.asyncio
    async def test_annotation_visibility_and_locking(self, annotation_service):
        """Test annotation visibility and locking properties."""
        request = AnnotationCreateRequest(
            type=AnnotationType.TEXT,
            geometry=TextGeometry(x=0, y=0),
            text="Test",
            visible=False,
            locked=True
        )
        
        annotation, seq = await annotation_service.create_annotation(
            "room1", "user1", request
        )
        
        assert annotation.visible is False
        assert annotation.locked is True
