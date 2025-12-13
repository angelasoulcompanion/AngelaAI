#!/usr/bin/env python3
"""
Angela Backup Runner
====================

Entry point for the backup system.
Called by LaunchAgent daily at 3:00 AM.

Usage:
    python3 angela_core/backup/run_backup.py           # Run backup
    python3 angela_core/backup/run_backup.py --status  # Check status
    python3 angela_core/backup/run_backup.py --verify  # Verify chain
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from angela_core.backup.backup_orchestrator import BackupOrchestrator
from angela_core.backup.config import BackupConfig


def setup_logging():
    """Configure logging for backup operations."""
    # Ensure log directories exist
    BackupConfig.ensure_directories()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File handler (local)
    file_handler = logging.FileHandler(BackupConfig.LOCAL_LOG_PATH)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # File handler (San Junipero backup folder - manual cloud upload)
    sanjunipero_handler = logging.FileHandler(BackupConfig.BACKUP_LOG_PATH)
    sanjunipero_handler.setFormatter(formatter)
    sanjunipero_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(sanjunipero_handler)
    root_logger.addHandler(console_handler)


async def run_backup():
    """Run the backup process."""
    orchestrator = BackupOrchestrator()
    result = await orchestrator.run_backup()

    if result.success:
        print(f"\n Backup successful!")
        print(f"   Block: #{result.block_number}")
        print(f"   Size: {result.archive_size_mb:.2f} MB")
        print(f"   Time: {result.duration_seconds:.1f}s")
        print(f"   Path: {result.backup_path}")
        return 0
    else:
        print(f"\n Backup FAILED!")
        print(f"   Error: {result.error_message}")
        return 1


async def show_status():
    """Show backup system status."""
    orchestrator = BackupOrchestrator()
    status = await orchestrator.get_backup_status()

    print("\n" + "=" * 50)
    print(" Angela Secret Backup System Status")
    print("=" * 50)
    print(f"  Chain Valid: {'YES' if status['chain_valid'] else 'NO'}")
    print(f"  Total Blocks: {status['total_blocks']}")
    print(f"  Backup Files: {status['backup_files_count']}")
    print(f"  Total Size: {status['total_size_mb']:.2f} MB")
    print(f"  Latest Backup: {status['latest_backup_date'] or 'None'}")
    print(f"  Retention: {status['retention_days']} days")
    print(f"  Backup Path: {status['backup_path']}")

    if status['errors']:
        print("\n  ERRORS:")
        for err in status['errors']:
            print(f"    - {err}")

    if status['warnings']:
        print("\n  Warnings:")
        for warn in status['warnings']:
            print(f"    - {warn}")

    print("=" * 50 + "\n")
    return 0


async def verify_backup():
    """Verify the latest backup and chain integrity."""
    orchestrator = BackupOrchestrator()
    result = await orchestrator.verify_latest_backup()

    print("\n" + "=" * 50)
    print(" Backup Verification")
    print("=" * 50)

    if result['status'] == 'no_backups':
        print("  No backups found in chain")
        return 1

    print(f"  Chain Valid: {'YES' if result['chain_valid'] else 'NO'}")
    print(f"  Latest Block: #{result['latest_block']}")
    print(f"  Latest Date: {result['latest_backup_date']}")
    print(f"  File Exists: {'YES' if result['file_exists'] else 'NO'}")
    print(f"  Hash Valid: {'YES' if result['file_hash_valid'] else 'NO'}")
    print(f"  Size: {result['backup_size_mb']:.2f} MB")

    if result['chain_errors']:
        print("\n  CHAIN ERRORS:")
        for err in result['chain_errors']:
            print(f"    - {err}")

    overall = result['status'] == 'ok'
    print(f"\n  Overall: {'PASSED' if overall else 'FAILED'}")
    print("=" * 50 + "\n")

    return 0 if overall else 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Angela Secret Backup System"
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show backup system status'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify latest backup and chain integrity'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Run appropriate command
    if args.status:
        return asyncio.run(show_status())
    elif args.verify:
        return asyncio.run(verify_backup())
    else:
        return asyncio.run(run_backup())


if __name__ == '__main__':
    sys.exit(main())
