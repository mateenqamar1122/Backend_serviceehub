"""
Core settings and configuration for ServiceHub application.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "ServiceHub"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    api_version: str = "v1"
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/servicehub"
    supabase_url: str
    supabase_key: str
    supabase_service_key: str

    # JWT & Supabase Auth
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    supabase_jwt_secret: str = ""  # Supabase JWT secret for token verification
    supabase_anon_key: str = ""  # Supabase anonymous key

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    # Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = "servicehub-uploads"
    aws_region: str = "us-east-1"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

