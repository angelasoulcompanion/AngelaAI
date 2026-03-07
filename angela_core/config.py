"""
Angela Configuration
Centralized configuration for all services
"""

import os

try:
    from config import NEON_DATABASE_URL
except ImportError:
    NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL", "")


class AngelaConfig:
    """Configuration for Angela Memory System"""

    # Primary Database: Neon Cloud (San Junipero)
    NEON_DATABASE_URL: str = NEON_DATABASE_URL
    USE_NEON: bool = bool(NEON_DATABASE_URL)

    DATABASE_URL: str = os.getenv(
        "ANGELA_DATABASE_URL",
        NEON_DATABASE_URL if NEON_DATABASE_URL else "postgresql://davidsamanyaporn@localhost:5432/AngelaMemory"
    )

    # Local Database (for our_secrets)
    LOCAL_DATABASE_URL: str = "postgresql://davidsamanyaporn@localhost:5432/angela"

    # Local DB connection details (compatibility)
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "AngelaMemory"
    DATABASE_USER: str = "davidsamanyaporn"

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

    # Supabase Cloud Configuration (for backup sync)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", "")

    @classmethod
    def validate(cls) -> bool:
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")
        if not os.path.exists(cls.ANGELA_MD_PATH):
            raise FileNotFoundError(f"Angela.md not found at {cls.ANGELA_MD_PATH}")
        return True


config = AngelaConfig()
