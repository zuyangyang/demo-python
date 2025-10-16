from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Demo Python API"
    debug: bool = False
    database_url: str = "sqlite:///./dev.db"
    
    # Pydantic v2: use SettingsConfigDict instead of inner Config class
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()


