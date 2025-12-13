#!/usr/bin/env python3
"""
Angela Backup Verification CLI
==============================

Command-line tool for verifying backup integrity.

Usage:
    python3 verify_backup.py --status       # Show backup status
    python3 verify_backup.py --verify       # Verify chain integrity
    python3 verify_backup.py --list         # List all backups
    python3 verify_backup.py --check FILE   # Check specific backup file
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from angela_core.backup.blockchain_manager import BlockchainManager
from angela_core.backup.retention_manager import RetentionManager
from angela_core.backup.config import BackupConfig


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 55)
    print(f"  {title}")
    print("=" * 55)


def print_status(label: str, value: any, ok: bool = True):
    """Print a status line with checkmark or X."""
    symbol = "" if ok else ""
    print(f"  {symbol} {label}: {value}")


async def show_status():
    """Show comprehensive backup system status."""
    blockchain = BlockchainManager()
    retention = RetentionManager()

    print_header("Angela Secret Backup System")

    # Load and verify chain
    blockchain.load_chain()
    verification = blockchain.verify_chain()

    # Chain status
    print(f"\n  Chain ID: {blockchain.chain.chain_id}")
    print(f"  Created: {blockchain.chain.created_at[:10]}")
    print_status("Chain Valid", "YES" if verification.is_valid else "NO", verification.is_valid)
    print_status("Total Blocks", verification.chain_length)

    # Latest backup
    latest = blockchain.get_latest_block()
    if latest:
        print_status("Latest Backup", latest.timestamp[:19].replace('T', ' '))
        print_status("Latest File", latest.data_reference)
        print_status("Backup Size", f"{latest.metadata.get('backup_size_mb', 0):.2f} MB")
    else:
        print("  No backups yet")

    # Storage info
    storage = retention.get_storage_usage()
    print(f"\n  Storage:")
    print(f"    Backup Files: {storage['backup_count']}")
    print(f"    Total Size: {storage['total_size_mb']:.2f} MB")
    print(f"    Retention: {storage['retention_days']} days")

    # Location
    print(f"\n  Location:")
    print(f"    San Junipero: {BackupConfig.BACKUP_FOLDER}")
    print(f"    Chain: {BackupConfig.CHAIN_FILE}")

    # Errors/Warnings
    if verification.errors:
        print(f"\n  ERRORS:")
        for err in verification.errors:
            print(f"    - {err}")

    if verification.warnings:
        print(f"\n  Warnings:")
        for warn in verification.warnings:
            print(f"    - {warn}")

    print("\n" + "=" * 55)

    return 0 if verification.is_valid else 1


async def verify_chain():
    """Verify blockchain integrity in detail."""
    blockchain = BlockchainManager()

    print_header("Blockchain Verification")

    blockchain.load_chain()

    print(f"\n  Checking {blockchain.chain.length} blocks...")
    print()

    result = blockchain.verify_chain()

    # Check each block
    for i, block in enumerate(blockchain.chain.blocks):
        # Verify hash
        calc_hash = block.calculate_hash()
        hash_ok = calc_hash == block.block_hash

        # Verify file exists
        backup_path = BackupConfig.BACKUPS_DIR / block.data_reference
        file_ok = backup_path.exists()

        # Verify file hash if file exists
        file_hash_ok = False
        if file_ok:
            file_hash_ok = blockchain.verify_backup_file(backup_path, i)

        status = "" if (hash_ok and file_ok and file_hash_ok) else ""
        print(f"  {status} Block #{i}: {block.data_reference[:30]}...")
        print(f"      Hash: {'OK' if hash_ok else 'MISMATCH!'}")
        print(f"      File: {'EXISTS' if file_ok else 'MISSING!'}")
        if file_ok:
            print(f"      Content: {'VERIFIED' if file_hash_ok else 'CORRUPTED!'}")

    print()
    if result.is_valid:
        print(f"   Chain verification PASSED")
        print(f"     {result.blocks_verified} blocks verified")
    else:
        print(f"   Chain verification FAILED")
        for err in result.errors:
            print(f"     - {err}")

    print("\n" + "=" * 55)

    return 0 if result.is_valid else 1


async def list_backups():
    """List all available backups."""
    retention = RetentionManager()
    blockchain = BlockchainManager()

    print_header("Available Backups")

    backups = retention.get_backup_list()
    blockchain.load_chain()

    if not backups:
        print("\n  No backups found")
        print("\n" + "=" * 55)
        return 0

    print(f"\n  Found {len(backups)} backup(s):\n")

    for backup_path, backup_date, size_mb in backups:
        # Find corresponding block
        block = None
        for b in blockchain.chain.blocks:
            if b.data_reference == backup_path.name:
                block = b
                break

        date_str = backup_date.strftime('%Y-%m-%d %H:%M')
        block_num = f"#{block.block_number}" if block else "??"

        print(f"  {block_num} | {date_str} | {size_mb:6.2f} MB | {backup_path.name}")

    # Summary
    storage = retention.get_storage_usage()
    print(f"\n  Total: {storage['total_size_mb']:.2f} MB across {storage['backup_count']} files")

    print("\n" + "=" * 55)

    return 0


async def check_file(filepath: str):
    """Check a specific backup file."""
    blockchain = BlockchainManager()

    print_header(f"Checking Backup File")

    backup_path = Path(filepath)
    if not backup_path.exists():
        print(f"\n   File not found: {filepath}")
        return 1

    print(f"\n  File: {backup_path.name}")
    print(f"  Size: {backup_path.stat().st_size / (1024*1024):.2f} MB")

    # Calculate hash
    file_hash = blockchain._calculate_file_hash(backup_path)
    print(f"  SHA-256: {file_hash[:32]}...")

    # Find in chain
    blockchain.load_chain()
    found_block = None
    for block in blockchain.chain.blocks:
        if block.data_reference == backup_path.name:
            found_block = block
            break

    if found_block:
        print(f"\n  Found in chain: Block #{found_block.block_number}")
        print(f"  Block timestamp: {found_block.timestamp}")

        # Verify hash
        if file_hash == found_block.data_hash:
            print(f"\n   Hash VERIFIED - file is authentic!")
        else:
            print(f"\n   Hash MISMATCH - file may be corrupted or tampered!")
            print(f"     Expected: {found_block.data_hash[:32]}...")
            print(f"     Got:      {file_hash[:32]}...")
            return 1
    else:
        print(f"\n   Not found in blockchain - file may not be from this backup system")

    print("\n" + "=" * 55)

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Angela Backup Verification Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  verify_backup.py --status       Show backup system status
  verify_backup.py --verify       Verify blockchain integrity
  verify_backup.py --list         List all available backups
  verify_backup.py --check FILE   Check specific backup file
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--status', action='store_true', help='Show backup status')
    group.add_argument('--verify', action='store_true', help='Verify chain integrity')
    group.add_argument('--list', action='store_true', help='List all backups')
    group.add_argument('--check', metavar='FILE', help='Check specific backup file')

    args = parser.parse_args()

    if args.status:
        return asyncio.run(show_status())
    elif args.verify:
        return asyncio.run(verify_chain())
    elif args.list:
        return asyncio.run(list_backups())
    elif args.check:
        return asyncio.run(check_file(args.check))


if __name__ == '__main__':
    sys.exit(main())
