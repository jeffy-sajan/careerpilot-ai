"""
Application configuration.
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    APP_NAME: str = "CareerPilot AI"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/careerpilot"

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"

    # JWT Authentication
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7" # Default dev key
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


settings = Settings()
