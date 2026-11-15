
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API keys for external services
    openai_api_key: str = ""
    gemini_api_key: str = ""

    # Models for external services
    openai_model: str = "gpt-5.4-nano"
    gemini_model: str = "gemini-2.5-flash"

    # PostgreSQL connection
    database_url: str

    # Pydantic model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

# Cached settings instance for the application
@lru_cache
def get_settings() -> Settings:
    return Settings()
