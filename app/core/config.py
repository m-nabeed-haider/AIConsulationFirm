"""Application configuration.

This module defines a single, typed source of truth for all
environment-driven configuration values. It uses Pydantic settings to
validate and parse environment variables, falling back to sensible
defaults where appropriate.

No other module should read from ``os.environ`` directly. Instead,
consumers should call :func:`get_settings` to obtain a cached,
validated :class:`Settings` instance.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables.

    Attributes:
        app_name: Human-readable name of the application.
        app_env: Deployment environment identifier (e.g. "local",
            "development", "production").
        log_level: Minimum severity level for log messages.
        ollama_host: Base URL of the local Ollama server. Reserved for
            future modules; unused in Module 0.
        default_model: Name of the default LLM to use. Reserved for
            future modules; unused in Module 0.
        database_url: Connection string for the application database.
            Reserved for future modules; unused in Module 0.
        vector_db_path: Filesystem path for the vector database.
            Reserved for future modules; unused in Module 0.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="AI Consulting Firm")
    app_env: str = Field(default="local")
    log_level: str = Field(default="INFO")

    ollama_host: str = Field(default="http://localhost:11434")
    default_model: str = Field(default="")

    database_url: str = Field(default="")
    vector_db_path: str = Field(default="")


@lru_cache
def get_settings() -> Settings:
    """Return a cached, validated :class:`Settings` instance.

    The result is cached so the environment is parsed only once per
    process, while still allowing every module to import and call
    this function cheaply.

    Returns:
        Settings: The application-wide configuration object.
    """
    return Settings()
