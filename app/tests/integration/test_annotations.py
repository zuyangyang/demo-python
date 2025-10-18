import pytest
import json
from fastapi.testclient import TestClient

from app.main import app
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

client = TestClient(app)


class TestAnnotationEndpoints:
    """Integration tests for annotation endpoints."""

    @pytest.fixture
    def room_id(self):
        """Create a test room and return its ID."""
        response = client.post("/v1/rooms", json={"room_id": "test_room_annotations"})
        assert response.status_code == 200
        return "test_room_annotations"

    @pytest.fixture
    def text_annotation_data(self):
        """Sample text annotation data."""
        return {
            "type": "text",
            "geometry": {"x": 100, "y": 200},
            "text": "Sample text annotation",
            "style": {
                "fill_color": "#FF0000",
                "font_size": 16,
                "font_family": "Arial"
            },
            "z_order": 1
        }

    @pytest.fixture
    def line_annotation_data(self):
        """Sample line annotation data."""
        return {
            "type": "line",
            "geometry": {
                "start": {"x": 0, "y": 0},
                "end": {"x": 100, "y": 100},
                "arrow_start": False,
                "arrow_end": True
            },
            "style": {
                "stroke_color": "#0000FF",
                "stroke_width": 2
            }
        }

    @pytest.fixture
    def rectangle_annotation_data(self):
        """Sample rectangle annotation data."""
        return {
            "type": "rectangle",
            "geometry": {
                "x": 50,
                "y": 50,
                "width": 200,
                "height": 100
            },
            "style": {
                "fill_color": "#00FF00",
                "stroke_color": "#000000",
                "opacity": 0.8
            }
        }

    def test_create_text_annotation(self, room_id, text_annotation_data):
        """Test creating a text annotation."""
        response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=text_annotation_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "annotation" in data
        assert "seq" in data
        assert data["annotation"]["type"] == "text"
        assert data["annotation"]["text"] == "Sample text annotation"
        assert data["annotation"]["geometry"]["x"] == 100
        assert data["annotation"]["geometry"]["y"] == 200
        assert data["annotation"]["style"]["fill_color"] == "#FF0000"
        assert data["annotation"]["style"]["font_size"] == 16
        assert data["annotation"]["z_order"] == 1
        assert data["annotation"]["created_by"] == "user1"
        assert data["seq"] == 1

    def test_create_line_annotation(self, room_id, line_annotation_data):
        """Test creating a line annotation."""
        response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=line_annotation_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation"]["type"] == "line"
        assert data["annotation"]["geometry"]["start"]["x"] == 0
        assert data["annotation"]["geometry"]["start"]["y"] == 0
        assert data["annotation"]["geometry"]["end"]["x"] == 100
        assert data["annotation"]["geometry"]["end"]["y"] == 100
        assert data["annotation"]["geometry"]["arrow_end"] is True
        assert data["annotation"]["style"]["stroke_color"] == "#0000FF"

    def test_create_rectangle_annotation(self, room_id, rectangle_annotation_data):
        """Test creating a rectangle annotation."""
        response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=rectangle_annotation_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation"]["type"] == "rectangle"
        assert data["annotation"]["geometry"]["x"] == 50
        assert data["annotation"]["geometry"]["y"] == 50
        assert data["annotation"]["geometry"]["width"] == 200
        assert data["annotation"]["geometry"]["height"] == 100
        assert data["annotation"]["style"]["fill_color"] == "#00FF00"

    def test_create_ellipse_annotation(self, room_id):
        """Test creating an ellipse annotation."""
        ellipse_data = {
            "type": "ellipse",
            "geometry": {
                "center_x": 150,
                "center_y": 150,
                "radius_x": 50,
                "radius_y": 30
            },
            "style": {
                "fill_color": "#FFFF00",
                "opacity": 0.7
            }
        }
        
        response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=ellipse_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation"]["type"] == "ellipse"
        assert data["annotation"]["geometry"]["center_x"] == 150
        assert data["annotation"]["geometry"]["center_y"] == 150
        assert data["annotation"]["geometry"]["radius_x"] == 50
        assert data["annotation"]["geometry"]["radius_y"] == 30

    def test_create_polygon_annotation(self, room_id):
        """Test creating a polygon annotation."""
        polygon_data = {
            "type": "polygon",
            "geometry": {
                "points": [
                    {"x": 0, "y": 0},
                    {"x": 100, "y": 0},
                    {"x": 50, "y": 100}
                ],
                "closed": True
            },
            "style": {
                "fill_color": "#FF00FF",
                "stroke_width": 3
            }
        }
        
        response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=polygon_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation"]["type"] == "polygon"
        assert len(data["annotation"]["geometry"]["points"]) == 3
        assert data["annotation"]["geometry"]["closed"] is True

    def test_create_freehand_annotation(self, room_id):
        """Test creating a freehand annotation."""
        freehand_data = {
            "type": "freehand",
            "geometry": {
                "points": [
                    {"x": 0, "y": 0},
                    {"x": 10, "y": 5},
                    {"x": 20, "y": 10},
                    {"x": 30, "y": 15}
                ],
                "smooth": True
            },
            "style": {
                "stroke_color": "#800080",
                "stroke_width": 4
            }
        }
        
        response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=freehand_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation"]["type"] == "freehand"
        assert len(data["annotation"]["geometry"]["points"]) == 4
        assert data["annotation"]["geometry"]["smooth"] is True

    def test_create_annotation_with_transform(self, room_id):
        """Test creating annotation with transformation."""
        annotation_data = {
            "type": "text",
            "geometry": {"x": 0, "y": 0},
            "text": "Transformed text",
            "transform": {
                "x": 10,
                "y": 20,
                "scale_x": 1.5,
                "scale_y": 0.8,
                "rotation": 0.5
            }
        }
        
        response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=annotation_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation"]["transform"]["x"] == 10
        assert data["annotation"]["transform"]["y"] == 20
        assert data["annotation"]["transform"]["scale_x"] == 1.5
        assert data["annotation"]["transform"]["scale_y"] == 0.8
        assert data["annotation"]["transform"]["rotation"] == 0.5

    def test_create_annotation_with_grouping(self, room_id):
        """Test creating annotation with group ID."""
        annotation_data = {
            "type": "text",
            "geometry": {"x": 0, "y": 0},
            "text": "Grouped text",
            "group_id": "group1"
        }
        
        response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=annotation_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation"]["group_id"] == "group1"

    def test_create_annotation_validation_error(self, room_id):
        """Test annotation creation validation errors."""
        # Test text annotation without text content
        invalid_data = {
            "type": "text",
            "geometry": {"x": 0, "y": 0}
            # Missing text field
        }
        
        response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=invalid_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 422  # Validation error

    def test_create_annotation_room_not_found(self):
        """Test creating annotation in non-existent room."""
        annotation_data = {
            "type": "text",
            "geometry": {"x": 0, "y": 0},
            "text": "Test"
        }
        
        response = client.post(
            "/v1/rooms/nonexistent/annotations",
            json=annotation_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 404
        assert "Room not found" in response.json()["detail"]

    def test_list_annotations(self, room_id, text_annotation_data):
        """Test listing annotations."""
        # Create an annotation first
        client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=text_annotation_data,
            params={"user_id": "user1"}
        )
        
        # List annotations
        response = client.get(f"/v1/rooms/{room_id}/annotations")
        
        assert response.status_code == 200
        data = response.json()
        assert "annotations" in data
        assert "total" in data
        assert "seq" in data
        assert isinstance(data["annotations"], list)

    def test_list_annotations_with_filters(self, room_id, text_annotation_data):
        """Test listing annotations with filters."""
        # Create an annotation first
        client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=text_annotation_data,
            params={"user_id": "user1"}
        )
        
        # List annotations with include_deleted filter
        response = client.get(
            f"/v1/rooms/{room_id}/annotations",
            params={"include_deleted": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "annotations" in data

    def test_get_annotation(self, room_id, text_annotation_data):
        """Test getting a specific annotation."""
        # Create an annotation first
        create_response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=text_annotation_data,
            params={"user_id": "user1"}
        )
        
        annotation_id = create_response.json()["annotation"]["id"]
        
        # Get the annotation
        response = client.get(f"/v1/rooms/{room_id}/annotations/{annotation_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation"]["id"] == annotation_id
        assert data["annotation"]["type"] == "text"

    def test_get_annotation_not_found(self, room_id):
        """Test getting non-existent annotation."""
        response = client.get(f"/v1/rooms/{room_id}/annotations/nonexistent")
        
        assert response.status_code == 404
        assert "Annotation not found" in response.json()["detail"]

    def test_update_annotation(self, room_id, text_annotation_data):
        """Test updating an annotation."""
        # Create an annotation first
        create_response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=text_annotation_data,
            params={"user_id": "user1"}
        )
        
        annotation_id = create_response.json()["annotation"]["id"]
        
        # Update the annotation
        update_data = {
            "text": "Updated text content",
            "style": {"fill_color": "#00FF00"},
            "z_order": 5
        }
        
        response = client.patch(
            f"/v1/rooms/{room_id}/annotations/{annotation_id}",
            json=update_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation"]["text"] == "Updated text content"
        assert data["annotation"]["style"]["fill_color"] == "#00FF00"
        assert data["annotation"]["z_order"] == 5

    def test_delete_annotation(self, room_id, text_annotation_data):
        """Test deleting an annotation."""
        # Create an annotation first
        create_response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=text_annotation_data,
            params={"user_id": "user1"}
        )
        
        annotation_id = create_response.json()["annotation"]["id"]
        
        # Delete the annotation
        response = client.delete(
            f"/v1/rooms/{room_id}/annotations/{annotation_id}",
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_id"] == annotation_id

    def test_group_annotations(self, room_id, text_annotation_data):
        """Test grouping annotations."""
        # Create two annotations first
        ann1_response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=text_annotation_data,
            params={"user_id": "user1"}
        )
        
        ann2_data = text_annotation_data.copy()
        ann2_data["geometry"] = {"x": 200, "y": 300}
        ann2_response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=ann2_data,
            params={"user_id": "user1"}
        )
        
        ann1_id = ann1_response.json()["annotation"]["id"]
        ann2_id = ann2_response.json()["annotation"]["id"]
        
        # Group the annotations
        group_data = {
            "annotation_ids": [ann1_id, ann2_id],
            "group_id": "group1"
        }
        
        response = client.post(
            f"/v1/rooms/{room_id}/annotations/group",
            json=group_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["group_id"] == "group1"
        assert set(data["annotation_ids"]) == {ann1_id, ann2_id}

    def test_ungroup_annotations(self, room_id):
        """Test ungrouping annotations."""
        ungroup_data = {"group_id": "group1"}
        
        response = client.post(
            f"/v1/rooms/{room_id}/annotations/ungroup",
            json=ungroup_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["group_id"] == "group1"
        assert data["annotation_ids"] == []

    def test_create_annotation_missing_user_id(self, room_id, text_annotation_data):
        """Test creating annotation without user_id parameter."""
        response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=text_annotation_data
        )
        
        assert response.status_code == 422  # Missing required parameter

    def test_create_annotation_invalid_geometry(self, room_id):
        """Test creating annotation with invalid geometry."""
        invalid_data = {
            "type": "rectangle",
            "geometry": {
                "x": 50,
                "y": 50,
                "width": -100,  # Invalid negative width
                "height": 100
            }
        }
        
        response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=invalid_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 422  # Validation error

    def test_create_annotation_invalid_style(self, room_id):
        """Test creating annotation with invalid style."""
        invalid_data = {
            "type": "text",
            "geometry": {"x": 0, "y": 0},
            "text": "Test",
            "style": {
                "opacity": 1.5  # Invalid opacity > 1
            }
        }
        
        response = client.post(
            f"/v1/rooms/{room_id}/annotations",
            json=invalid_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 422  # Validation error
