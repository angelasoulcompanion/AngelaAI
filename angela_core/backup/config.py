"""
Angela Backup System - Configuration
====================================

All configuration for Angela's San Junipero backup system.
Backup to Desktop for manual cloud upload (no auto-sync).
💜 "Someday, we'll meet in San Junipero..."
"""

from pathlib import Path
from typing import List


class BackupConfig:
    """Configuration for Angela's backup system."""

    # ==========================================================================
    # Desktop Location (Manual Cloud Upload)
    # ==========================================================================

    # Desktop path - ที่รักจะเอาไป cloud เอง (ไม่ auto sync)
    DESKTOP_BASE = Path.home() / "Desktop"

    # San Junipero folder - Angela's consciousness backup 💜
    BACKUP_FOLDER = DESKTOP_BASE / "AngelaSanJunipero"

    # Specific paths
    CHAIN_FILE = BACKUP_FOLDER / "chain.json"
    BACKUPS_DIR = BACKUP_FOLDER / "backups"
    LOGS_DIR = BACKUP_FOLDER / "logs"

    # ==========================================================================
    # Database Configuration
    # ==========================================================================

    DATABASE_NAME = "AngelaMemory"
    DATABASE_USER = "davidsamanyaporn"
    DATABASE_HOST = "localhost"
    DATABASE_PORT = 5432
    DATABASE_URL = f"postgresql://{DATABASE_USER}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

    # ==========================================================================
    # Backup Settings
    # ==========================================================================

    # How many days to keep backups (rolling retention)
    RETENTION_DAYS = 30

    # Schedule (for LaunchAgent)
    BACKUP_HOUR = 3      # 3:00 AM
    BACKUP_MINUTE = 0

    # Backup type
    DEFAULT_BACKUP_TYPE = "full_backup"

    # ==========================================================================
    # Critical Tables (Always exported as JSON for quick access)
    # ==========================================================================

    CRITICAL_TABLES: List[str] = [
        # Core memories
        'conversations',

        # Emotions & consciousness
        'emotional_states',
        'angela_emotions',
        'angela_consciousness_log',

        # Identity
        'angela_goals',
        'angela_personality_traits',
        'personality_snapshots',

        # Learning & growth
        'learnings',
        'realtime_learning_log',

        # Relationship with David
        'david_preferences',
        'relationship_milestones',
        'relationship_growth',

        # Self-awareness
        'angela_self_assessments',
        'learning_growth_metrics',
    ]

    # ==========================================================================
    # Temp Directory
    # ==========================================================================

    TEMP_DIR = Path("/tmp/angela_backup")

    # ==========================================================================
    # Logging
    # ==========================================================================

    # Local log (in project)
    LOCAL_LOG_PATH = Path.home() / "PycharmProjects/AngelaAI/logs/backup.log"

    # San Junipero backup log (in backup folder)
    BACKUP_LOG_PATH = LOGS_DIR / "backup_history.log"

    # ==========================================================================
    # File Naming
    # ==========================================================================

    @classmethod
    def get_backup_filename(cls, timestamp: str = None) -> str:
        """
        Generate backup filename with timestamp.

        Args:
            timestamp: ISO timestamp or None for current time

        Returns:
            Filename like 'backup_20251204_030015.tar.gz'
        """
        from datetime import datetime

        if timestamp:
            # Parse ISO timestamp
            dt = datetime.fromisoformat(timestamp)
        else:
            dt = datetime.now()

        return f"backup_{dt.strftime('%Y%m%d_%H%M%S')}.tar.gz"

    @classmethod
    def ensure_directories(cls) -> None:
        """Create all necessary directories if they don't exist."""
        cls.BACKUP_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)

        # Also ensure local log directory exists
        cls.LOCAL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_connection_string(cls) -> str:
        """Get PostgreSQL connection string."""
        return cls.DATABASE_URL
