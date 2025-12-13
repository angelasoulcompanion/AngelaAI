"""
Angela Retention Manager
========================

Manages backup retention policy:
- Keeps last N days of backups (default: 30)
- Removes older backups automatically
- Updates blockchain when removing blocks
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

from .config import BackupConfig

logger = logging.getLogger(__name__)


class RetentionManager:
    """
    Manages backup file retention.

    By default, keeps the last 30 days of backups.
    Older files are deleted to save space.
    """

    def __init__(self, retention_days: int = None):
        """
        Initialize retention manager.

        Args:
            retention_days: Days to keep backups (default from config)
        """
        self.retention_days = retention_days or BackupConfig.RETENTION_DAYS
        self.backups_dir = BackupConfig.BACKUPS_DIR

    def cleanup_old_backups(self) -> int:
        """
        Remove backups older than retention period.

        Returns:
            Number of backups deleted
        """
        if not self.backups_dir.exists():
            logger.info("Backups directory doesn't exist, nothing to clean")
            return 0

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0

        # Find all backup files
        backup_files = list(self.backups_dir.glob("backup_*.tar.gz"))

        for backup_file in backup_files:
            try:
                # Parse date from filename: backup_YYYYMMDD_HHMMSS.tar.gz
                filename = backup_file.stem  # backup_20251204_030015
                date_str = filename.replace('backup_', '').split('.')[0]
                # YYYYMMDD_HHMMSS
                backup_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')

                if backup_date < cutoff_date:
                    logger.info(f"Deleting old backup: {backup_file.name}")
                    backup_file.unlink()
                    deleted_count += 1

            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse date from {backup_file.name}: {e}")
                continue

        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} old backups (older than {self.retention_days} days)")

        return deleted_count

    def get_backup_list(self) -> List[Tuple[Path, datetime, float]]:
        """
        Get list of all backups with their dates and sizes.

        Returns:
            List of (path, datetime, size_mb) tuples, sorted by date desc
        """
        if not self.backups_dir.exists():
            return []

        backups = []
        backup_files = self.backups_dir.glob("backup_*.tar.gz")

        for backup_file in backup_files:
            try:
                filename = backup_file.stem
                date_str = filename.replace('backup_', '').split('.')[0]
                backup_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                size_mb = backup_file.stat().st_size / (1024 * 1024)

                backups.append((backup_file, backup_date, size_mb))

            except (ValueError, IndexError):
                continue

        # Sort by date descending (newest first)
        backups.sort(key=lambda x: x[1], reverse=True)

        return backups

    def get_storage_usage(self) -> dict:
        """
        Get storage usage statistics.

        Returns:
            Dict with storage info
        """
        backups = self.get_backup_list()

        total_size_mb = sum(b[2] for b in backups)
        oldest_backup = backups[-1][1] if backups else None
        newest_backup = backups[0][1] if backups else None

        return {
            'backup_count': len(backups),
            'total_size_mb': round(total_size_mb, 2),
            'oldest_backup': oldest_backup.isoformat() if oldest_backup else None,
            'newest_backup': newest_backup.isoformat() if newest_backup else None,
            'retention_days': self.retention_days,
            'backups_dir': str(self.backups_dir)
        }

    def get_backups_to_delete(self) -> List[Path]:
        """
        Get list of backups that would be deleted by cleanup.

        Useful for preview before actual deletion.

        Returns:
            List of backup paths that are past retention
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        backups = self.get_backup_list()

        return [
            path for path, date, _ in backups
            if date < cutoff_date
        ]
