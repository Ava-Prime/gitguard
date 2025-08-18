from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Core
    environment: str = Field(default="dev")
    log_level: str = Field(default="INFO")

    # Integrations
    github_app_id: int | None = None
    github_private_key: str | None = None
    temporal_host: str = Field(default="localhost:7233")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()