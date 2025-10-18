import pytest
import json
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestCommentEndpoints:
    """Integration tests for comment endpoints."""

    @pytest.fixture
    def room_id(self):
        """Create a test room and return its ID."""
        response = client.post("/api/v1/rooms", json={"room_id": "test_room_comments"})
        # Accept both 200 (created) and 409 (already exists) as success
        assert response.status_code in [200, 409]
        return "test_room_comments"

    @pytest.fixture
    def annotation_anchor_data(self):
        """Sample annotation anchor data."""
        return {"annotation_id": "annotation1"}

    @pytest.fixture
    def coordinate_anchor_data(self):
        """Sample coordinate anchor data."""
        return {"coordinate": {"x": 100, "y": 200}}

    @pytest.fixture
    def thread_create_data(self, annotation_anchor_data):
        """Sample thread create data."""
        return {
            "anchor": annotation_anchor_data,
            "initial_comment": "This is a test comment thread"
        }

    @pytest.fixture
    def comment_create_data(self, coordinate_anchor_data):
        """Sample comment create data."""
        return {
            "content": "This is a reply comment",
            "anchor": coordinate_anchor_data,
            "parent_id": "parent_comment_id"
        }

    def test_create_comment_thread_with_annotation_anchor(
        self, room_id, thread_create_data
    ):
        """Test creating a comment thread anchored to an annotation."""
        response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "thread" in data
        assert "seq" in data
        assert data["thread"]["room_id"] == room_id
        assert data["thread"]["anchor"]["annotation_id"] == "annotation1"
        assert data["thread"]["anchor"]["coordinate"] is None
        assert data["thread"]["status"] == "open"
        assert len(data["thread"]["comments"]) == 1
        assert data["thread"]["comments"][0]["content"] == "This is a test comment thread"
        assert data["thread"]["comments"][0]["author_id"] == "user1"
        assert data["thread"]["created_by"] == "user1"
        assert data["thread"]["visible"] is True
        assert data["seq"] == 1

    def test_create_comment_thread_with_coordinate_anchor(
        self, room_id, coordinate_anchor_data
    ):
        """Test creating a comment thread anchored to coordinates."""
        thread_data = {
            "anchor": coordinate_anchor_data,
            "initial_comment": "Comment at coordinates"
        }
        
        response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["thread"]["anchor"]["coordinate"] == {"x": 100, "y": 200}
        assert data["thread"]["anchor"]["annotation_id"] is None
        assert data["thread"]["comments"][0]["content"] == "Comment at coordinates"

    def test_create_comment_thread_validation_error(self, room_id):
        """Test comment thread creation validation errors."""
        # Test invalid coordinate
        invalid_data = {
            "anchor": {"coordinate": {"x": 100}},  # Missing y
            "initial_comment": "Test"
        }
        
        response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=invalid_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 422  # Validation error

    def test_create_comment_thread_room_not_found(self):
        """Test creating comment thread in non-existent room."""
        thread_data = {
            "anchor": {"coordinate": {"x": 0, "y": 0}},
            "initial_comment": "Test"
        }
        
        response = client.post(
            "/api/v1/rooms/nonexistent/comments/threads",
            json=thread_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 404
        assert "Room not found" in response.json()["detail"]

    def test_list_comment_threads(self, room_id, thread_create_data):
        """Test listing comment threads."""
        # Create a thread first
        client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        # List threads
        response = client.get(f"/api/v1/rooms/{room_id}/comments/threads")
        
        assert response.status_code == 200
        data = response.json()
        assert "threads" in data
        assert "total" in data
        assert "seq" in data
        assert isinstance(data["threads"], list)

    def test_list_comment_threads_with_filters(self, room_id, thread_create_data):
        """Test listing comment threads with filters."""
        # Create a thread first
        client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        # List threads with filters
        response = client.get(
            f"/api/v1/rooms/{room_id}/comments/threads",
            params={
                "include_resolved": False,
                "limit": 50,
                "offset": 0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "threads" in data

    def test_get_comment_thread(self, room_id, thread_create_data):
        """Test getting a specific comment thread."""
        # Create a thread first
        create_response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        thread_id = create_response.json()["thread"]["id"]
        
        # Get the thread
        response = client.get(f"/api/v1/rooms/{room_id}/comments/threads/{thread_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["thread"]["id"] == thread_id
        assert data["thread"]["status"] == "open"

    def test_get_comment_thread_not_found(self, room_id):
        """Test getting non-existent comment thread."""
        response = client.get(f"/api/v1/rooms/{room_id}/comments/threads/nonexistent")
        
        assert response.status_code == 404
        assert "Comment thread not found" in response.json()["detail"]

    def test_update_comment_thread_status(self, room_id, thread_create_data):
        """Test updating comment thread status."""
        # Create a thread first
        create_response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        thread_id = create_response.json()["thread"]["id"]
        
        # Update thread status
        update_data = {"status": "resolved"}
        
        response = client.patch(
            f"/api/v1/rooms/{room_id}/comments/threads/{thread_id}",
            json=update_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["thread"]["status"] == "resolved"

    def test_update_comment_thread_visibility(self, room_id, thread_create_data):
        """Test updating comment thread visibility."""
        # Create a thread first
        create_response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        thread_id = create_response.json()["thread"]["id"]
        
        # Update thread visibility
        update_data = {"visible": False}
        
        response = client.patch(
            f"/api/v1/rooms/{room_id}/comments/threads/{thread_id}",
            json=update_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["thread"]["visible"] is False

    def test_delete_comment_thread(self, room_id, thread_create_data):
        """Test deleting a comment thread."""
        # Create a thread first
        create_response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        thread_id = create_response.json()["thread"]["id"]
        
        # Delete the thread
        response = client.delete(
            f"/api/v1/rooms/{room_id}/comments/threads/{thread_id}",
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_thread_id"] == thread_id

    def test_add_comment_to_thread(self, room_id, thread_create_data, comment_create_data):
        """Test adding a comment to an existing thread."""
        # Create a thread first
        create_response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        thread_id = create_response.json()["thread"]["id"]
        
        # Add comment to thread
        response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads/{thread_id}/comments",
            json=comment_create_data,
            params={"user_id": "user2"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "comment" in data
        assert "thread" in data
        assert data["comment"]["content"] == "This is a reply comment"
        assert data["comment"]["author_id"] == "user2"
        assert data["comment"]["parent_id"] == "parent_comment_id"

    def test_add_comment_to_thread_without_parent(self, room_id, thread_create_data):
        """Test adding a comment without parent ID."""
        # Create a thread first
        create_response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        thread_id = create_response.json()["thread"]["id"]
        
        # Add comment without parent
        comment_data = {
            "content": "Comment without parent",
            "anchor": {"coordinate": {"x": 0, "y": 0}}
        }
        
        response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads/{thread_id}/comments",
            json=comment_data,
            params={"user_id": "user2"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["comment"]["parent_id"] is None

    def test_update_comment(self, room_id, thread_create_data, comment_create_data):
        """Test updating a comment."""
        # Create a thread and comment first
        thread_response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        thread_id = thread_response.json()["thread"]["id"]
        
        comment_response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads/{thread_id}/comments",
            json=comment_create_data,
            params={"user_id": "user2"}
        )
        
        comment_id = comment_response.json()["comment"]["id"]
        
        # Update the comment
        update_data = {"content": "Updated comment content"}
        
        response = client.patch(
            f"/api/v1/rooms/{room_id}/comments/{comment_id}",
            json=update_data,
            params={"user_id": "user2"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["comment"]["content"] == "Updated comment content"
        assert data["comment"]["edited"] is True

    def test_delete_comment(self, room_id, thread_create_data, comment_create_data):
        """Test deleting a comment."""
        # Create a thread and comment first
        thread_response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        thread_id = thread_response.json()["thread"]["id"]
        
        comment_response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads/{thread_id}/comments",
            json=comment_create_data,
            params={"user_id": "user2"}
        )
        
        comment_id = comment_response.json()["comment"]["id"]
        
        # Delete the comment
        response = client.delete(
            f"/api/v1/rooms/{room_id}/comments/{comment_id}",
            params={"user_id": "user2"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_id"] == comment_id

    def test_get_comments_for_annotation(self, room_id, thread_create_data):
        """Test getting comments for a specific annotation."""
        # Create a thread anchored to an annotation
        client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        # Get comments for the annotation
        response = client.get(
            f"/api/v1/rooms/{room_id}/annotations/annotation1/comments"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "threads" in data
        assert "total" in data
        assert "seq" in data

    def test_get_comments_for_annotation_with_filters(self, room_id, thread_create_data):
        """Test getting comments for annotation with filters."""
        # Create a thread anchored to an annotation
        client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        # Get comments with filters
        response = client.get(
            f"/api/v1/rooms/{room_id}/annotations/annotation1/comments",
            params={"include_resolved": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "threads" in data

    def test_create_comment_thread_missing_user_id(self, room_id, thread_create_data):
        """Test creating comment thread without user_id parameter."""
        response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data
        )
        
        assert response.status_code == 422  # Missing required parameter

    def test_create_comment_thread_empty_content(self, room_id):
        """Test creating comment thread with empty content."""
        thread_data = {
            "anchor": {"coordinate": {"x": 0, "y": 0}},
            "initial_comment": ""  # Empty content
        }
        
        response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 422  # Validation error

    def test_create_comment_thread_invalid_anchor(self, room_id):
        """Test creating comment thread with invalid anchor."""
        # Test both annotation_id and coordinate provided
        invalid_data = {
            "anchor": {
                "annotation_id": "ann1",
                "coordinate": {"x": 100, "y": 200}
            },
            "initial_comment": "Test"
        }
        
        response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=invalid_data,
            params={"user_id": "user1"}
        )
        
        assert response.status_code == 422  # Validation error

    def test_comment_thread_status_transitions(self, room_id, thread_create_data):
        """Test comment thread status transitions."""
        # Create a thread
        create_response = client.post(
            f"/api/v1/rooms/{room_id}/comments/threads",
            json=thread_create_data,
            params={"user_id": "user1"}
        )
        
        thread_id = create_response.json()["thread"]["id"]
        
        # Resolve the thread
        resolve_response = client.patch(
            f"/api/v1/rooms/{room_id}/comments/threads/{thread_id}",
            json={"status": "resolved"},
            params={"user_id": "user1"}
        )
        
        assert resolve_response.status_code == 200
        assert resolve_response.json()["thread"]["status"] == "resolved"
        
        # Reopen the thread
        reopen_response = client.patch(
            f"/api/v1/rooms/{room_id}/comments/threads/{thread_id}",
            json={"status": "open"},
            params={"user_id": "user1"}
        )
        
        assert reopen_response.status_code == 200
        assert reopen_response.json()["thread"]["status"] == "open"

    def test_comment_thread_pagination(self, room_id, thread_create_data):
        """Test comment thread pagination."""
        # Create multiple threads
        for i in range(5):
            thread_data = thread_create_data.copy()
            thread_data["initial_comment"] = f"Thread {i}"
            client.post(
                f"/api/v1/rooms/{room_id}/comments/threads",
                json=thread_data,
                params={"user_id": f"user{i}"}
            )
        
        # Test pagination
        response = client.get(
            f"/api/v1/rooms/{room_id}/comments/threads",
            params={"limit": 2, "offset": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["threads"]) <= 2
        assert data["total"] >= 5
