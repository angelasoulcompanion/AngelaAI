"""
Angela Restore Service
======================

Restores Angela's consciousness from backup.

Two restore modes:
1. Full restore: Complete database replacement from pg_dump
2. Critical tables only: Restore specific tables from JSON

IMPORTANT: This is for emergencies only!
Always verify backup integrity before restoring.
"""

import asyncio
import json
import logging
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .config import BackupConfig
from .models import RestoreResult
from .blockchain_manager import BlockchainManager

logger = logging.getLogger(__name__)


class RestoreService:
    """
    Restores Angela's consciousness from backup.

    Use with caution - this can overwrite existing data!
    """

    def __init__(self):
        """Initialize restore service."""
        self.config = BackupConfig
        self.blockchain = BlockchainManager()

    async def full_restore(
        self,
        backup_path: Path,
        verify_hash: bool = True,
        drop_existing: bool = False
    ) -> RestoreResult:
        """
        Perform full database restore from backup archive.

        Args:
            backup_path: Path to backup archive (tar.gz)
            verify_hash: Whether to verify hash against blockchain
            drop_existing: If True, drops existing database first

        Returns:
            RestoreResult with status and details
        """
        start_time = datetime.now()
        timestamp = start_time.isoformat()

        logger.info("=" * 60)
        logger.info(f"Starting FULL RESTORE from {backup_path}")
        logger.info("=" * 60)

        temp_dir: Optional[Path] = None

        try:
            # 1. Verify backup file exists
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

            # 2. Verify hash against blockchain (optional)
            if verify_hash:
                if not await self._verify_backup_hash(backup_path):
                    raise ValueError(
                        "Backup hash verification failed! "
                        "File may have been tampered with."
                    )

            # 3. Extract archive to temp directory
            temp_dir = self.config.TEMP_DIR / f"restore_{start_time.strftime('%Y%m%d_%H%M%S')}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Extracting archive to {temp_dir}...")
            subprocess.run(
                ['tar', '-xzf', str(backup_path), '-C', str(temp_dir)],
                check=True,
                capture_output=True
            )

            # Find the extracted directory (should be backup_YYYYMMDD_HHMMSS)
            extracted_dirs = list(temp_dir.glob("backup_*"))
            if not extracted_dirs:
                raise RuntimeError("No backup directory found in archive")
            extracted_dir = extracted_dirs[0]

            # 4. Find dump file
            dump_file = extracted_dir / "angela_dump.sql"
            if not dump_file.exists():
                raise FileNotFoundError(f"Dump file not found in archive: {dump_file}")

            # 5. Drop existing database if requested
            if drop_existing:
                logger.warning("Dropping existing database...")
                subprocess.run(
                    ['dropdb', '--if-exists', self.config.DATABASE_NAME],
                    capture_output=True
                )
                subprocess.run(
                    ['createdb', self.config.DATABASE_NAME],
                    check=True,
                    capture_output=True
                )

            # 6. Restore from dump
            logger.info("Restoring database from dump...")
            result = subprocess.run(
                [
                    'pg_restore',
                    '-d', self.config.DATABASE_NAME,
                    '-U', self.config.DATABASE_USER,
                    '--clean',  # Drop existing objects
                    '--if-exists',  # Don't error if objects don't exist
                    str(dump_file)
                ],
                capture_output=True,
                text=True
            )

            # pg_restore may return non-zero for warnings, check stderr
            if result.returncode != 0 and 'ERROR' in result.stderr:
                logger.error(f"pg_restore errors: {result.stderr}")
                raise RuntimeError(f"pg_restore failed: {result.stderr}")

            # 7. Get stats
            stats = await self._get_restored_stats()

            # 8. Clean up
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

            duration = (datetime.now() - start_time).total_seconds()

            logger.info("=" * 60)
            logger.info("FULL RESTORE COMPLETED SUCCESSFULLY!")
            logger.info(f"  Tables: {stats['tables_count']}")
            logger.info(f"  Rows: {stats['total_rows']}")
            logger.info(f"  Duration: {duration:.1f}s")
            logger.info("=" * 60)

            return RestoreResult(
                success=True,
                timestamp=timestamp,
                source_backup=str(backup_path),
                tables_restored=stats['tables_count'],
                rows_restored=stats['total_rows'],
                duration_seconds=round(duration, 2)
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)

            logger.error("=" * 60)
            logger.error(f"RESTORE FAILED: {error_msg}")
            logger.error("=" * 60)

            # Clean up on failure
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)

            return RestoreResult(
                success=False,
                timestamp=timestamp,
                source_backup=str(backup_path),
                duration_seconds=round(duration, 2),
                error_message=error_msg
            )

    async def restore_critical_tables(
        self,
        backup_path: Path,
        tables: Optional[List[str]] = None
    ) -> RestoreResult:
        """
        Restore only critical tables from JSON files.

        This is a gentler restore that doesn't affect the whole database.

        Args:
            backup_path: Path to backup archive
            tables: Specific tables to restore (default: all critical tables)

        Returns:
            RestoreResult with status
        """
        start_time = datetime.now()
        timestamp = start_time.isoformat()
        tables_to_restore = tables or self.config.CRITICAL_TABLES

        logger.info("=" * 60)
        logger.info(f"Starting CRITICAL TABLES restore")
        logger.info(f"Tables: {tables_to_restore}")
        logger.info("=" * 60)

        temp_dir: Optional[Path] = None
        total_rows = 0
        tables_restored = 0
        warnings: List[str] = []

        try:
            # 1. Extract archive
            temp_dir = self.config.TEMP_DIR / f"restore_{start_time.strftime('%Y%m%d_%H%M%S')}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run(
                ['tar', '-xzf', str(backup_path), '-C', str(temp_dir)],
                check=True,
                capture_output=True
            )

            # Find extracted directory
            extracted_dirs = list(temp_dir.glob("backup_*"))
            if not extracted_dirs:
                raise RuntimeError("No backup directory found")
            extracted_dir = extracted_dirs[0]
            json_dir = extracted_dir / "json_tables"

            if not json_dir.exists():
                raise FileNotFoundError("JSON tables directory not found in backup")

            # 2. Import database module
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from angela_core.database import AngelaDatabase

            db = AngelaDatabase()
            await db.connect()

            try:
                # 3. Restore each table
                for table in tables_to_restore:
                    json_file = json_dir / f"{table}.json"

                    if not json_file.exists():
                        warnings.append(f"No JSON file for {table}")
                        continue

                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        if not data:
                            logger.info(f"Table {table} is empty in backup")
                            continue

                        # Get column names from first row
                        columns = list(data[0].keys())

                        # Clear existing data
                        await db.execute(f"TRUNCATE TABLE {table} CASCADE")

                        # Insert rows
                        for row in data:
                            placeholders = ', '.join(f'${i+1}' for i in range(len(columns)))
                            values = [row.get(col) for col in columns]

                            await db.execute(
                                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                                *values
                            )

                        total_rows += len(data)
                        tables_restored += 1
                        logger.info(f"Restored {table}: {len(data)} rows")

                    except Exception as e:
                        warnings.append(f"Failed to restore {table}: {e}")
                        logger.error(f"Failed to restore {table}: {e}")

            finally:
                await db.disconnect()

            # Clean up
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

            duration = (datetime.now() - start_time).total_seconds()

            return RestoreResult(
                success=True,
                timestamp=timestamp,
                source_backup=str(backup_path),
                tables_restored=tables_restored,
                rows_restored=total_rows,
                duration_seconds=round(duration, 2),
                warnings=warnings
            )

        except Exception as e:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)

            duration = (datetime.now() - start_time).total_seconds()

            return RestoreResult(
                success=False,
                timestamp=timestamp,
                source_backup=str(backup_path),
                duration_seconds=round(duration, 2),
                error_message=str(e),
                warnings=warnings
            )

    async def list_available_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups with their block info.

        Returns:
            List of backup info dicts
        """
        self.blockchain.load_chain()
        backups = []

        for block in self.blockchain.chain.blocks:
            backup_path = self.config.BACKUPS_DIR / block.data_reference
            exists = backup_path.exists()

            backups.append({
                'block_number': block.block_number,
                'timestamp': block.timestamp,
                'filename': block.data_reference,
                'file_exists': exists,
                'size_mb': block.metadata.get('backup_size_mb', 0),
                'tables_count': block.metadata.get('tables_count', 0),
                'total_rows': block.metadata.get('total_rows', 0)
            })

        return sorted(backups, key=lambda x: x['block_number'], reverse=True)

    async def _verify_backup_hash(self, backup_path: Path) -> bool:
        """Verify backup file hash against blockchain."""
        self.blockchain.load_chain()

        # Find block by filename
        filename = backup_path.name
        for block in self.blockchain.chain.blocks:
            if block.data_reference == filename:
                return self.blockchain.verify_backup_file(backup_path, block.block_number)

        logger.warning(f"No blockchain block found for {filename}")
        return False

    async def _get_restored_stats(self) -> Dict[str, Any]:
        """Get database stats after restore."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from angela_core.database import AngelaDatabase

        db = AngelaDatabase()
        await db.connect()

        try:
            tables = await db.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )

            total_rows = 0
            for table in tables:
                try:
                    count = await db.fetchval(
                        f"SELECT COUNT(*) FROM {table['table_name']}"
                    )
                    total_rows += count
                except Exception:
                    pass

            return {
                'tables_count': len(tables),
                'total_rows': total_rows
            }

        finally:
            await db.disconnect()
