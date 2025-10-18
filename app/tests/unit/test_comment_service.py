import pytest
import time
from unittest.mock import AsyncMock, patch

from app.services.comment_service import comment_service
from app.schemas.comment import (
    CommentCreateRequest,
    CommentUpdateRequest,
    CommentThreadCreateRequest,
    CommentThreadUpdateRequest,
    CommentAnchor,
    CommentStatus,
)


class TestCommentService:
    """Test cases for CommentService."""

    @pytest.fixture
    def mock_room_registry(self):
        """Mock room registry for testing."""
        with patch('app.services.comment_service.room_registry') as mock:
            mock.append_update = AsyncMock(return_value=1)
            mock.get_room = AsyncMock(return_value=AsyncMock(next_seq=2))
            yield mock

    @pytest.fixture
    def annotation_anchor(self):
        """Sample annotation anchor."""
        return CommentAnchor(annotation_id="annotation1")

    @pytest.fixture
    def coordinate_anchor(self):
        """Sample coordinate anchor."""
        return CommentAnchor(coordinate={"x": 100, "y": 200})

    @pytest.fixture
    def thread_create_request(self, annotation_anchor):
        """Sample thread create request."""
        return CommentThreadCreateRequest(
            anchor=annotation_anchor,
            initial_comment="This is a test comment"
        )

    @pytest.fixture
    def comment_create_request(self, coordinate_anchor):
        """Sample comment create request."""
        return CommentCreateRequest(
            content="This is a reply comment",
            anchor=coordinate_anchor,
            parent_id="parent_comment_id"
        )

    @pytest.mark.asyncio
    async def test_create_comment_thread_with_annotation_anchor(
        self, mock_room_registry, thread_create_request
    ):
        """Test creating a comment thread anchored to an annotation."""
        thread, seq = await comment_service.create_comment_thread(
            "room1", "user1", thread_create_request
        )
        
        assert thread.room_id == "room1"
        assert thread.anchor.annotation_id == "annotation1"
        assert thread.anchor.coordinate is None
        assert thread.status == CommentStatus.OPEN
        assert len(thread.comments) == 1
        assert thread.comments[0].content == "This is a test comment"
        assert thread.comments[0].author_id == "user1"
        assert thread.created_by == "user1"
        assert thread.visible is True
        assert seq == 1
        
        mock_room_registry.append_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_comment_thread_with_coordinate_anchor(
        self, mock_room_registry, coordinate_anchor
    ):
        """Test creating a comment thread anchored to coordinates."""
        request = CommentThreadCreateRequest(
            anchor=coordinate_anchor,
            initial_comment="Comment at coordinates"
        )
        
        thread, seq = await comment_service.create_comment_thread(
            "room1", "user1", request
        )
        
        assert thread.anchor.coordinate == {"x": 100, "y": 200}
        assert thread.anchor.annotation_id is None
        assert thread.comments[0].content == "Comment at coordinates"

    @pytest.mark.asyncio
    async def test_add_comment_to_thread(self, mock_room_registry, comment_create_request):
        """Test adding a comment to an existing thread."""
        comment, thread, seq = await comment_service.add_comment_to_thread(
            "room1", "thread1", "user1", comment_create_request
        )
        
        assert comment.content == "This is a reply comment"
        assert comment.author_id == "user1"
        assert comment.parent_id == "parent_comment_id"
        assert comment.thread_id == "thread1"
        assert seq == 1
        
        mock_room_registry.append_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_comment(self, mock_room_registry):
        """Test updating a comment."""
        update_request = CommentUpdateRequest(content="Updated comment content")
        
        comment, thread, seq = await comment_service.update_comment(
            "room1", "comment1", "user1", update_request
        )
        
        assert comment.content == "Updated comment content"
        assert comment.edited is True
        assert seq == 1
        
        mock_room_registry.append_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_comment_thread_status(self, mock_room_registry):
        """Test updating comment thread status."""
        update_request = CommentThreadUpdateRequest(status=CommentStatus.RESOLVED)
        
        thread, seq = await comment_service.update_comment_thread(
            "room1", "thread1", "user1", update_request
        )
        
        assert thread.status == CommentStatus.RESOLVED
        assert seq == 1
        
        mock_room_registry.append_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_comment_thread_visibility(self, mock_room_registry):
        """Test updating comment thread visibility."""
        update_request = CommentThreadUpdateRequest(visible=False)
        
        thread, seq = await comment_service.update_comment_thread(
            "room1", "thread1", "user1", update_request
        )
        
        assert thread.visible is False
        assert seq == 1

    @pytest.mark.asyncio
    async def test_resolve_comment_thread_sets_timestamps(self, mock_room_registry):
        """Test that resolving a thread sets resolution timestamps."""
        with patch('time.time', return_value=1234567890.0):
            update_request = CommentThreadUpdateRequest(status=CommentStatus.RESOLVED)
            
            thread, seq = await comment_service.update_comment_thread(
                "room1", "thread1", "user1", update_request
            )
            
            assert thread.resolved_at == 1234567890.0
            assert thread.resolved_by == "user1"

    @pytest.mark.asyncio
    async def test_reopen_comment_thread_clears_timestamps(self, mock_room_registry):
        """Test that reopening a thread clears resolution timestamps."""
        update_request = CommentThreadUpdateRequest(status=CommentStatus.OPEN)
        
        thread, seq = await comment_service.update_comment_thread(
            "room1", "thread1", "user1", update_request
        )
        
        assert thread.resolved_at is None
        assert thread.resolved_by is None

    @pytest.mark.asyncio
    async def test_delete_comment(self, mock_room_registry):
        """Test deleting a comment."""
        deleted_id, thread_id, seq = await comment_service.delete_comment(
            "room1", "comment1", "user1"
        )
        
        assert deleted_id == "comment1"
        assert thread_id == "placeholder"  # Mock value
        assert seq == 1
        
        mock_room_registry.append_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_comment_thread(self, mock_room_registry):
        """Test deleting a comment thread."""
        deleted_thread_id, seq = await comment_service.delete_comment_thread(
            "room1", "thread1", "user1"
        )
        
        assert deleted_thread_id == "thread1"
        assert seq == 1
        
        mock_room_registry.append_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_comment_threads(self, mock_room_registry):
        """Test getting comment threads for a room."""
        threads, seq = await comment_service.get_comment_threads("room1")
        
        assert isinstance(threads, list)
        assert seq == 1

    @pytest.mark.asyncio
    async def test_get_comment_threads_include_resolved(self, mock_room_registry):
        """Test getting comment threads with resolved filter."""
        threads, seq = await comment_service.get_comment_threads("room1", include_resolved=False)
        
        assert isinstance(threads, list)
        assert seq == 1

    @pytest.mark.asyncio
    async def test_get_comments_for_annotation(self, mock_room_registry):
        """Test getting comments for a specific annotation."""
        threads, seq = await comment_service.get_comments_for_annotation(
            "room1", "annotation1"
        )
        
        assert isinstance(threads, list)
        assert seq == 1

    @pytest.mark.asyncio
    async def test_create_comment_thread_room_not_found(self, mock_room_registry):
        """Test creating comment thread when room doesn't exist."""
        mock_room_registry.append_update.side_effect = KeyError("room not found")
        
        request = CommentThreadCreateRequest(
            anchor=CommentAnchor(coordinate={"x": 0, "y": 0}),
            initial_comment="Test"
        )
        
        with pytest.raises(KeyError, match="room not found"):
            await comment_service.create_comment_thread("nonexistent", "user1", request)

    @pytest.mark.asyncio
    async def test_comment_thread_timestamps(self, mock_room_registry, thread_create_request):
        """Test that comment threads have proper timestamps."""
        with patch('time.time', return_value=1234567890.0):
            thread, seq = await comment_service.create_comment_thread(
                "room1", "user1", thread_create_request
            )
            
            assert thread.created_at == 1234567890.0
            assert thread.updated_at == 1234567890.0
            assert thread.created_by == "user1"
            assert thread.updated_by == "user1"

    @pytest.mark.asyncio
    async def test_comment_timestamps(self, mock_room_registry, comment_create_request):
        """Test that comments have proper timestamps."""
        with patch('time.time', return_value=1234567890.0):
            comment, thread, seq = await comment_service.add_comment_to_thread(
                "room1", "thread1", "user1", comment_create_request
            )
            
            assert comment.created_at == 1234567890.0
            assert comment.updated_at == 1234567890.0
            assert comment.author_id == "user1"

    @pytest.mark.asyncio
    async def test_comment_edit_tracking(self, mock_room_registry):
        """Test that comment edits are tracked."""
        update_request = CommentUpdateRequest(content="Updated content")
        
        comment, thread, seq = await comment_service.update_comment(
            "room1", "comment1", "user1", update_request
        )
        
        assert comment.edited is True

    @pytest.mark.asyncio
    async def test_comment_thread_initial_comment(self, mock_room_registry, thread_create_request):
        """Test that initial comment is properly created with thread."""
        thread, seq = await comment_service.create_comment_thread(
            "room1", "user1", thread_create_request
        )
        
        assert len(thread.comments) == 1
        initial_comment = thread.comments[0]
        assert initial_comment.content == "This is a test comment"
        assert initial_comment.author_id == "user1"
        assert initial_comment.thread_id == thread.id
        assert initial_comment.parent_id is None

    @pytest.mark.asyncio
    async def test_comment_with_parent(self, mock_room_registry, comment_create_request):
        """Test creating a comment with a parent comment."""
        comment, thread, seq = await comment_service.add_comment_to_thread(
            "room1", "thread1", "user1", comment_create_request
        )
        
        assert comment.parent_id == "parent_comment_id"

    @pytest.mark.asyncio
    async def test_comment_thread_anchor_validation(self):
        """Test comment thread anchor validation."""
        # Test invalid coordinate
        with pytest.raises(ValueError, match="Coordinate must have x and y fields"):
            CommentAnchor(coordinate={"x": 100})  # Missing y
        
        with pytest.raises(ValueError, match="Coordinate x and y must be numbers"):
            CommentAnchor(coordinate={"x": "100", "y": 200})  # x is string
        
        # Test both annotation_id and coordinate provided
        with pytest.raises(ValueError, match="Cannot specify both annotation_id and coordinate"):
            CommentAnchor(annotation_id="ann1", coordinate={"x": 100, "y": 200})
        
        # Test neither annotation_id nor coordinate provided
        with pytest.raises(ValueError, match="Cannot specify both annotation_id and coordinate"):
            CommentAnchor()  # Neither provided

    @pytest.mark.asyncio
    async def test_comment_content_validation(self):
        """Test comment content validation."""
        # Test empty content
        with pytest.raises(ValueError, match="ensure this value has at least 1 characters"):
            CommentCreateRequest(
                content="",
                anchor=CommentAnchor(coordinate={"x": 0, "y": 0})
            )
        
        # Test valid content
        request = CommentCreateRequest(
            content="Valid comment",
            anchor=CommentAnchor(coordinate={"x": 0, "y": 0})
        )
        assert request.content == "Valid comment"
