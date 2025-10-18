import pytest
from fastapi import status
from app.core.exceptions import (
    APIException,
    NotFoundException,
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException
)

def test_api_exception():
    """Test base API exception."""
    exc = APIException("Test message", status.HTTP_400_BAD_REQUEST, {"key": "value"})

    assert exc.message == "Test message"
    assert exc.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.details == {"key": "value"}
    assert str(exc) == "Test message"

def test_not_found_exception():
    """Test not found exception."""
    exc = NotFoundException("User not found")

    assert exc.message == "User not found"
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.details == {}

def test_bad_request_exception():
    """Test bad request exception."""
    exc = BadRequestException("Invalid data", {"field": "email"})

    assert exc.message == "Invalid data"
    assert exc.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.details == {"field": "email"}

def test_unauthorized_exception():
    """Test unauthorized exception."""
    exc = UnauthorizedException("Invalid credentials")

    assert exc.message == "Invalid credentials"
    assert exc.status_code == status.HTTP_401_UNAUTHORIZED

def test_forbidden_exception():
    """Test forbidden exception."""
    exc = ForbiddenException("Access denied")

    assert exc.message == "Access denied"
    assert exc.status_code == status.HTTP_403_FORBIDDEN

def test_conflict_exception():
    """Test conflict exception."""
    exc = ConflictException("Resource already exists")

    assert exc.message == "Resource already exists"
    assert exc.status_code == status.HTTP_409_CONFLICT
