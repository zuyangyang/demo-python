from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class StorageMode(str, Enum):
    SQLITE = "sqlite"
    MEMORY = "memory"


class Settings(BaseSettings):
    app_name: str = "Demo Python API"
    debug: bool = False
    database_url: str = "memory://"  # Default to in-memory mode
    
    # Pydantic v2: use SettingsConfigDict instead of inner Config class
    model_config = SettingsConfigDict(env_file=".env")
    
    @property
    def storage_mode(self) -> StorageMode:
        """Determine storage mode based on database_url."""
        if self.database_url.startswith("memory://"):
            return StorageMode.MEMORY
        else:
            return StorageMode.SQLITE


settings = Settings()


