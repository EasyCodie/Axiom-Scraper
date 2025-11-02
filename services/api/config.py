"""
Configuration module for FastAPI service.

Loads settings from environment variables or config file including:
- DuckDB database path
- Redis connection settings
- Moralis API key
- Supabase JWKS URL and settings
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """FastAPI service settings."""

    # Server
    host: str = Field(default="0.0.0.0", description="API server host")
    port: int = Field(default=8000, description="API server port")
    reload: bool = Field(default=False, description="Enable auto-reload for development")
    workers: int = Field(default=1, description="Number of worker processes")

    # Database
    database_path: str = Field(
        default="data/axiom.duckdb", description="Path to DuckDB database file"
    )

    # Redis Cache
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    cache_ttl_short: int = Field(default=300, description="Short cache TTL in seconds (5 min)")
    cache_ttl_medium: int = Field(default=600, description="Medium cache TTL in seconds (10 min)")
    cache_ttl_long: int = Field(default=900, description="Long cache TTL in seconds (15 min)")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_default: str = Field(default="100/minute", description="Default rate limit")
    rate_limit_search: str = Field(default="20/minute", description="Search endpoint rate limit")

    # Moralis API
    moralis_api_key: Optional[str] = Field(default=None, description="Moralis API key")
    moralis_base_url: str = Field(
        default="https://deep-index.moralis.io/api/v2.2", description="Moralis API base URL"
    )
    moralis_timeout: int = Field(default=10, description="Moralis API timeout in seconds")

    # Supabase Authentication
    supabase_url: Optional[str] = Field(default=None, description="Supabase project URL")
    supabase_jwks_url: Optional[str] = Field(
        default=None, description="Supabase JWKS URL for JWT verification"
    )
    supabase_jwt_secret: Optional[str] = Field(
        default=None, description="Supabase JWT secret (alternative to JWKS)"
    )
    jwt_algorithm: str = Field(default="RS256", description="JWT algorithm")
    jwt_audience: str = Field(default="authenticated", description="JWT audience")

    # CORS
    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"], description="Allowed CORS origins"
    )
    cors_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_methods: list[str] = Field(
        default_factory=lambda: ["*"], description="Allowed CORS methods"
    )
    cors_headers: list[str] = Field(
        default_factory=lambda: ["*"], description="Allowed CORS headers"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")

    # Chain
    default_chain: str = Field(default="sol", description="Default blockchain chain")

    class Config:
        env_file = ".env"
        env_prefix = "API_"
        case_sensitive = False


def get_settings() -> APISettings:
    """
    Get API settings instance.

    Returns:
        APISettings instance
    """
    return APISettings()


# Global settings instance
settings = get_settings()
