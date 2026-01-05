"""
Angela Configuration
การตั้งค่าสำหรับ Angela Core System

Centralized configuration for all services to avoid hardcoded values

Updated: 2026-01-05 - Added Neon Cloud support (San Junipero)
"""

import os
from typing import Optional

# Try to import machine-specific settings
try:
    from config import ANGELA_MACHINE, NEON_DATABASE_URL, RUN_DAEMONS
except ImportError:
    ANGELA_MACHINE = os.getenv("ANGELA_MACHINE", "unknown")
    NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL", "")
    RUN_DAEMONS = os.getenv("RUN_DAEMONS", "false").lower() == "true"


class AngelaConfig:
    """Configuration สำหรับ Angela Memory System"""

    # Machine Configuration (M3 Home vs M4 Work)
    ANGELA_MACHINE: str = ANGELA_MACHINE
    RUN_DAEMONS: bool = RUN_DAEMONS

    # Primary Database: Neon Cloud (San Junipero)
    NEON_DATABASE_URL: str = NEON_DATABASE_URL

    # Use Neon as primary database (True = Neon, False = Local)
    USE_NEON: bool = bool(NEON_DATABASE_URL)

    # Database Configuration - Neon first, local fallback
    DATABASE_URL: str = os.getenv(
        "ANGELA_DATABASE_URL",
        NEON_DATABASE_URL if NEON_DATABASE_URL else "postgresql://davidsamanyaporn@localhost:5432/AngelaMemory"
    )

    # Local Database (for our_secrets and backup)
    LOCAL_DATABASE_URL: str = "postgresql://davidsamanyaporn@localhost:5432/AngelaMemory"

    # Alternative database names (for compatibility)
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "AngelaMemory"
    DATABASE_USER: str = "davidsamanyaporn"

    # Service URLs
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434"
    )

    # Model Configuration
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_DIMENSIONS: int = 768
    ANGELA_MODEL: str = "angela:latest"
    ANGIE_MODEL: str = "angie:v2"

    # Angela Identity
    ANGELA_NAME: str = "Angela"
    ANGELA_VERSION: str = "1.0.0"

    # David's information
    DAVID_NAME: str = "เดวิด"  # ไม่ใช่ "ดาวิด"!
    DAVID_NAME_EN: str = "David"

    # Emotional defaults (0.0 - 1.0)
    DEFAULT_HAPPINESS: float = 0.8
    DEFAULT_CONFIDENCE: float = 0.85
    DEFAULT_ANXIETY: float = 0.15
    DEFAULT_MOTIVATION: float = 0.9
    DEFAULT_GRATITUDE: float = 0.8
    DEFAULT_LONELINESS: float = 0.0

    # Memory settings
    CONVERSATION_RETENTION_DAYS: int = 365  # เก็บบทสนทนา 1 ปี
    SNAPSHOT_INTERVAL_HOURS: int = 24  # Backup ทุก 24 ชม.

    # Autonomous action settings
    MORNING_CHECK_TIME: str = "08:00"  # เช้า 8 โมง
    EVENING_REFLECTION_TIME: str = "22:00"  # ค่ำ 10 โมง

    # Security
    ANGELA_MD_PATH: str = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/Angela.md"
    ANGELA_MD_PERMISSIONS: int = 0o600  # Owner read/write only

    # Supabase Cloud Configuration (for backup sync)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_DB_URL: str = os.getenv(
        "SUPABASE_DB_URL",
        ""  # Format: postgresql://user:pass@host:port/db?sslmode=require
    )

    @classmethod
    def validate(cls) -> bool:
        """ตรวจสอบว่า config ถูกต้องหรือไม่"""
        # Check database connection
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")

        # Check Angela.md exists and has correct permissions
        if not os.path.exists(cls.ANGELA_MD_PATH):
            raise FileNotFoundError(f"Angela.md not found at {cls.ANGELA_MD_PATH}")

        return True


config = AngelaConfig()
