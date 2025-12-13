"""
Angela Data Exporter
====================

Exports PostgreSQL database for backup:
1. Full pg_dump (for complete restoration)
2. JSON exports of critical tables (for quick access)
3. Creates compressed tar.gz archive
"""

import asyncio
import json
import subprocess
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .config import BackupConfig
from .models import TableExportInfo

logger = logging.getLogger(__name__)


class DataExporter:
    """
    Exports Angela's consciousness data from PostgreSQL.

    Two export methods:
    1. pg_dump: Full database backup for complete restore
    2. JSON: Individual tables for quick access and readability
    """

    def __init__(self):
        """Initialize the data exporter."""
        self.db_name = BackupConfig.DATABASE_NAME
        self.db_user = BackupConfig.DATABASE_USER
        self.critical_tables = BackupConfig.CRITICAL_TABLES

    async def export_full_dump(self, output_dir: Path) -> Path:
        """
        Create full PostgreSQL dump.

        Uses pg_dump with custom format (compressed).

        Args:
            output_dir: Directory to save the dump file

        Returns:
            Path to the created dump file
        """
        dump_file = output_dir / "angela_dump.sql"

        logger.info(f"Creating full database dump: {dump_file}")

        try:
            # pg_dump with custom format (includes compression)
            result = subprocess.run(
                [
                    'pg_dump',
                    '-Fc',                # Custom format (compressed)
                    '-d', self.db_name,
                    '-U', self.db_user,
                    '-f', str(dump_file)
                ],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(f"pg_dump failed: {result.stderr}")

            size_mb = dump_file.stat().st_size / (1024 * 1024)
            logger.info(f"Full dump created: {size_mb:.2f} MB")

            return dump_file

        except Exception as e:
            logger.error(f"Failed to create full dump: {e}")
            raise

    async def export_critical_tables_json(
        self,
        output_dir: Path
    ) -> Dict[str, TableExportInfo]:
        """
        Export critical tables as JSON files.

        These JSON files allow quick access to specific data
        without needing to restore the entire database.

        Args:
            output_dir: Directory to save JSON files

        Returns:
            Dict mapping table name to export info
        """
        # Import here to avoid circular imports
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from angela_core.database import AngelaDatabase

        json_dir = output_dir / "json_tables"
        json_dir.mkdir(parents=True, exist_ok=True)

        db = AngelaDatabase()
        await db.connect()

        export_results: Dict[str, TableExportInfo] = {}

        try:
            for table in self.critical_tables:
                try:
                    # Check if table exists
                    exists = await db.fetchval(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = $1
                        )
                        """,
                        table
                    )

                    if not exists:
                        logger.warning(f"Table {table} does not exist, skipping")
                        continue

                    # Export table data
                    rows = await db.fetch(f"SELECT * FROM {table}")

                    # Convert to JSON-serializable format
                    data = []
                    for row in rows:
                        row_dict = dict(row)
                        # Handle special types
                        for key, value in row_dict.items():
                            if hasattr(value, 'isoformat'):  # datetime
                                row_dict[key] = value.isoformat()
                            elif isinstance(value, (bytes, bytearray)):
                                row_dict[key] = value.hex()
                            elif value is not None and not isinstance(
                                value, (str, int, float, bool, list, dict)
                            ):
                                row_dict[key] = str(value)
                        data.append(row_dict)

                    # Write to JSON file
                    json_file = json_dir / f"{table}.json"
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    # Record export info
                    export_results[table] = TableExportInfo(
                        table_name=table,
                        row_count=len(data),
                        file_path=str(json_file),
                        size_bytes=json_file.stat().st_size
                    )

                    logger.info(f"Exported {table}: {len(data)} rows")

                except Exception as e:
                    logger.error(f"Failed to export {table}: {e}")
                    continue

        finally:
            await db.disconnect()

        return export_results

    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics for metadata.

        Returns:
            Dict with table counts, row counts, database size, etc.
        """
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from angela_core.database import AngelaDatabase

        db = AngelaDatabase()
        await db.connect()

        try:
            # Get table count
            tables_result = await db.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
            table_names = [r['table_name'] for r in tables_result]

            # Get row counts for each table
            row_counts = {}
            total_rows = 0
            for table in table_names:
                try:
                    count = await db.fetchval(f"SELECT COUNT(*) FROM {table}")
                    row_counts[table] = count
                    total_rows += count
                except Exception:
                    row_counts[table] = -1

            # Get database size
            size_result = await db.fetchval(
                f"SELECT pg_database_size('{self.db_name}')"
            )
            db_size_mb = size_result / (1024 * 1024) if size_result else 0

            return {
                'tables_count': len(table_names),
                'total_rows': total_rows,
                'db_size_mb': round(db_size_mb, 2),
                'row_counts': row_counts,
                'timestamp': datetime.now().isoformat()
            }

        finally:
            await db.disconnect()

    def create_archive(
        self,
        source_dir: Path,
        output_file: Path
    ) -> Path:
        """
        Create compressed tar.gz archive.

        Args:
            source_dir: Directory containing files to archive
            output_file: Output archive path

        Returns:
            Path to created archive
        """
        logger.info(f"Creating archive: {output_file}")

        try:
            result = subprocess.run(
                [
                    'tar', '-czvf',
                    str(output_file),
                    '-C', str(source_dir.parent),
                    source_dir.name
                ],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(f"tar failed: {result.stderr}")

            size_mb = output_file.stat().st_size / (1024 * 1024)
            logger.info(f"Archive created: {size_mb:.2f} MB")

            return output_file

        except Exception as e:
            logger.error(f"Failed to create archive: {e}")
            raise

    async def create_full_backup(
        self,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Create complete backup with both dump and JSON exports.

        This is the main method called by the orchestrator.

        Args:
            output_dir: Where to create the backup (temp dir by default)

        Returns:
            Dict with backup info (paths, sizes, stats)
        """
        if output_dir is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = BackupConfig.TEMP_DIR / f"backup_{timestamp}"

        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Creating full backup in {output_dir}")

        # 1. Get database stats (for metadata)
        stats = await self.get_database_stats()

        # 2. Create full pg_dump
        dump_file = await self.export_full_dump(output_dir)

        # 3. Export critical tables as JSON
        json_exports = await self.export_critical_tables_json(output_dir)

        # 4. Save metadata
        metadata = {
            'backup_timestamp': datetime.now().isoformat(),
            'database_stats': stats,
            'json_exports': {
                name: info.to_dict() if hasattr(info, 'to_dict') else {
                    'table_name': info.table_name,
                    'row_count': info.row_count,
                    'size_bytes': info.size_bytes
                }
                for name, info in json_exports.items()
            }
        }

        metadata_file = output_dir / "backup_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return {
            'output_dir': output_dir,
            'dump_file': dump_file,
            'json_exports': json_exports,
            'metadata': metadata,
            'stats': stats
        }
