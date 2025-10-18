from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""

    # Application settings
    app_name: str = "Multi-User Task Assignment System"
    debug: bool = False
    version: str = "1.0.0"
    
    # Database settings
    database_url: str = "sqlite:///./task_assignment.db"

    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS settings
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Logging settings
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()


