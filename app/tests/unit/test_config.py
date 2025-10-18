import pytest
import os
from app.core.config import settings

def test_default_settings():
    """Test default settings values."""
    assert settings.app_name == "Multi-User Task Assignment System"
    assert settings.debug is False
    assert settings.version == "1.0.0"
    assert settings.database_url == "sqlite:///./task_assignment.db"
    assert settings.secret_key == "your-secret-key-change-in-production"
    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30
    assert settings.allowed_origins == ["http://localhost:3000", "http://localhost:8080"]
    assert settings.log_level == "INFO"

def test_settings_from_env():
    """Test settings loading from environment variables."""
    # Set environment variables
    os.environ["APP_NAME"] = "Test App"
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"

    # Reload settings
    from app.core.config import Settings
    test_settings = Settings()

    assert test_settings.app_name == "Test App"
    assert test_settings.debug is True
    assert test_settings.log_level == "DEBUG"

    # Cleanup
    del os.environ["APP_NAME"]
    del os.environ["DEBUG"]
    del os.environ["LOG_LEVEL"]
