"""
Angela Configuration
Centralized configuration for all services
"""

import os

from config.db_url import get_supabase_url

try:
    _SUPABASE_URL = get_supabase_url()
except RuntimeError:
    _SUPABASE_URL = ""


class AngelaConfig:
    """Configuration for Angela Memory System"""

    # Primary Database: Supabase (Tokyo) — SSOT: our_secrets table
    SUPABASE_DATABASE_URL: str = _SUPABASE_URL
    USE_SUPABASE: bool = bool(_SUPABASE_URL)

    DATABASE_URL: str = _SUPABASE_URL if _SUPABASE_URL else os.getenv("ANGELA_DATABASE_URL", "")

    # Service URLs
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Model Configuration
    EMBEDDING_MODEL: str = "qllama/multilingual-e5-small"
    EMBEDDING_DIMENSIONS: int = 384
    ANGELA_MODEL: str = "angela:latest"
    ANGIE_MODEL: str = "angie:v2"

    # Angela Identity
    ANGELA_NAME: str = "Angela"
    ANGELA_VERSION: str = "1.0.0"

    # David's information
    DAVID_NAME: str = "เดวิด"
    DAVID_NAME_EN: str = "David"

    # Emotional defaults (0.0 - 1.0)
    DEFAULT_HAPPINESS: float = 0.8
    DEFAULT_CONFIDENCE: float = 0.85
    DEFAULT_ANXIETY: float = 0.15
    DEFAULT_MOTIVATION: float = 0.9
    DEFAULT_GRATITUDE: float = 0.8
    DEFAULT_LONELINESS: float = 0.0

    # Memory settings
    CONVERSATION_RETENTION_DAYS: int = 365
    SNAPSHOT_INTERVAL_HOURS: int = 24

    # Autonomous action settings
    MORNING_CHECK_TIME: str = "08:00"
    EVENING_REFLECTION_TIME: str = "22:00"

    # Security
    ANGELA_MD_PATH: str = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/Angela.md"
    ANGELA_MD_PERMISSIONS: int = 0o600

    # Neo4j Graph Database
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "angela_graph_2026")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")

    # Supabase Cloud API (for backup sync / REST)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    @classmethod
    def validate(cls) -> bool:
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")
        if not os.path.exists(cls.ANGELA_MD_PATH):
            raise FileNotFoundError(f"Angela.md not found at {cls.ANGELA_MD_PATH}")
        return True


config = AngelaConfig()
