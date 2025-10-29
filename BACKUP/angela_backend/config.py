"""
Angela Backend Configuration
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # API Settings
    app_name: str = "Angela Backend"
    app_version: str = "1.0.0"
    debug: bool = True

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS Settings
    allowed_origins: List[str] = ["*"]  # In production, specify exact origins

    # Database Settings
    database_url: str = "postgresql://davidsamanyaporn@localhost:5432/AngelaMemory"

    # Ollama Settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "angie:contextaware"
    ollama_reasoning_model: str = "qwen2.5:14b"

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/angela_backend.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
