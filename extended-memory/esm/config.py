"""ESM Configuration Management"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = Field(
        default="postgresql://esm_user:esm_password@localhost:5432/esm",
        description="PostgreSQL connection URL"
    )
    
    # Search
    typesense_url: str = Field(
        default="http://localhost:8108",
        description="Typesense server URL"
    )
    typesense_api_key: str = Field(
        default="esm_search_key",
        description="Typesense API key"
    )
    
    # AI Services
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for embeddings"
    )
    
    # Application
    secret_key: str = Field(
        default="change-this-super-secret-key-in-production",
        description="Secret key for JWT tokens"
    )
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Server
         


    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
        # Security
    allowed_origins: list[str] = Field(
        default=["http://localhost", "http://localhost:3000"],
        description="List of origins allowed by CORS"
    )
    allowed_hosts: list[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="List of hosts allowed by TrustedHostMiddleware"
    )

    
    # Memory Settings
    max_memory_size: int = Field(
        default=50000,
        description="Maximum memory content length"
    )
    default_importance: int = Field(
        default=5,
        description="Default memory importance (1-10)"
    )
    
    # Search Settings
    search_limit: int = Field(
        default=50,
        description="Default search result limit"
    )
    embedding_dimensions: int = Field(
        default=1536,
        description="OpenAI embedding dimensions"
    )
    
    class Config:
    


        env_file = ".env"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings():
    """Reload settings (for testing)"""
    global _settings
    _settings = None
    return get_settings()
