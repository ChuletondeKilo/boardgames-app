"""
Database Configuration using Pydantic Settings

This module handles all database-related configuration, loading from environment variables.
"""

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """
    Database configuration loaded from environment variables.
    
    Pydantic Settings automatically:
    1. Loads values from environment variables
    2. Validates types (e.g., ensures url is a valid PostgreSQL URL)
    3. Uses .env file if present
    
    Environment variables expected:
    - DATABASE_URL: Full PostgreSQL connection string
      Format: postgresql+asyncpg://user:password@host:port/dbname
    """
    
    # Configuration for pydantic-settings
    # env_file: Automatically load from .env file in the backend directory
    # case_sensitive: Environment variable names must match exactly
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # PostgreSQL connection URL
    # The validation_alias allows both "DATABASE_URL" and "database_url" to work
    # Default is set for local development (you'll override this with your cloud DB)
    url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/boardgames",
        validation_alias="DATABASE_URL",
        description="PostgreSQL database URL with asyncpg driver"
    )

    # Optional: Connection pool settings for production
    pool_size: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of connections to maintain in the pool"
    )
    
    max_overflow: int = Field(
        default=10,
        ge=0,
        le=50,
        description="Max connections that can be created beyond pool_size"
    )

    pool_timeout: int = Field(
        default=30,
        ge=0,
        le=60,
        description="Wait 30s for available connection"
    )
    
    pool_pre_ping: bool = Field(
        default=True,
        description="Test connection before using"
    )
    
    # Echo SQL queries to console (useful for debugging)
    echo: bool = Field(
        default=False,
        description="Log all SQL queries to console"
    )


# Create a single instance to be imported throughout the app
# This is instantiated once when the module is imported
settings = DatabaseSettings()
