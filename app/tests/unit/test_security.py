import pytest
from datetime import timedelta
from app.core.security import verify_password, get_password_hash, create_access_token, verify_token

def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = get_password_hash(password)

    # Hash should be different from original password
    assert hashed != password

    # Verification should work
    assert verify_password(password, hashed) is True

    # Wrong password should fail
    assert verify_password("wrong_password", hashed) is False

def test_jwt_token_creation():
    """Test JWT token creation and verification."""
    data = {"sub": "test_user"}
    token = create_access_token(data)

    # Token should be a string
    assert isinstance(token, str)
    assert len(token) > 0

    # Verify token
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "test_user"
    assert "exp" in payload

def test_jwt_token_expiration():
    """Test JWT token expiration."""
    data = {"sub": "test_user"}
    expires_delta = timedelta(seconds=1)
    token = create_access_token(data, expires_delta)

    # Token should be valid immediately
    payload = verify_token(token)
    assert payload is not None

    # Wait for expiration
    import time
    time.sleep(2)

    # Token should be expired
    payload = verify_token(token)
    assert payload is None

def test_invalid_token():
    """Test verification of invalid tokens."""
    invalid_tokens = [
        "invalid.token.here",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
        "",
        "not_a_token_at_all"
    ]

    for token in invalid_tokens:
        payload = verify_token(token)
        assert payload is None
