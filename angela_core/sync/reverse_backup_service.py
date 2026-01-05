"""
Reverse Backup Service - Neon Cloud → Local M3
===============================================
Backup Angela's consciousness from Neon to local PostgreSQL.

Created: 2026-01-05
Purpose: Keep local M3 as backup of Neon Cloud (primary database)

Flow:
1. pg_dump from Neon Cloud
2. pg_restore to Local PostgreSQL (keeping our_secrets intact)
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

# Import config
try:
    from angela_core.config import config
    NEON_DATABASE_URL = config.NEON_DATABASE_URL
    LOCAL_DATABASE_URL = config.LOCAL_DATABASE_URL
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config import NEON_DATABASE_URL
    LOCAL_DATABASE_URL = "postgresql://davidsamanyaporn@localhost:5432/AngelaMemory_Backup"

# Backup file path
BACKUP_FILE = '/tmp/angela_neon_backup.dump'

# PostgreSQL 17 binaries (for Neon compatibility)
PG17_BIN = '/opt/homebrew/opt/postgresql@17/bin'
PG_DUMP = f'{PG17_BIN}/pg_dump'
PG_RESTORE = f'{PG17_BIN}/pg_restore'

# Tables to exclude from restore (keep local version)
EXCLUDE_TABLES = ['our_secrets']


class ReverseBackupService:
    """Service to backup from Neon Cloud to Local PostgreSQL."""

    def __init__(self):
        self.neon_url = NEON_DATABASE_URL
        self.local_url = LOCAL_DATABASE_URL

    def dump_from_neon(self) -> bool:
        """Create pg_dump from Neon Cloud."""
        print("☁️  Dumping from Neon Cloud...")

        if not self.neon_url:
            print("❌ NEON_DATABASE_URL not configured!")
            return False

        try:
            # Exclude our_secrets from dump
            exclude_args = []
            for table in EXCLUDE_TABLES:
                exclude_args.extend(['-T', table])

            # Use PostgreSQL 17 pg_dump for Neon compatibility
            result = subprocess.run(
                [PG_DUMP, self.neon_url, '-F', 'c', '-f', BACKUP_FILE] + exclude_args,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )

            if result.returncode != 0:
                print(f"❌ pg_dump failed: {result.stderr}")
                return False

            size_mb = os.path.getsize(BACKUP_FILE) / (1024 * 1024)
            print(f"✅ Dump created: {size_mb:.1f} MB")
            return True

        except subprocess.TimeoutExpired:
            print("❌ pg_dump timed out")
            return False
        except Exception as e:
            print(f"❌ Dump error: {e}")
            return False

    def restore_to_local(self) -> bool:
        """Restore dump to local PostgreSQL."""
        print("🏠 Restoring to Local PostgreSQL...")

        if not os.path.exists(BACKUP_FILE):
            print("❌ Backup file not found!")
            return False

        try:
            # First, drop existing tables (except our_secrets)
            print("   🗑️  Clearing local tables...")
            drop_result = subprocess.run([
                'psql', '-d', 'AngelaMemory_Backup', '-U', 'davidsamanyaporn', '-c',
                """
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN SELECT tablename FROM pg_tables
                             WHERE schemaname = 'public'
                             AND tablename <> 'our_secrets'
                    LOOP
                        EXECUTE 'DROP TABLE IF EXISTS "' || r.tablename || '" CASCADE';
                    END LOOP;
                END $$;
                """
            ], capture_output=True, text=True)

            if drop_result.returncode != 0:
                print(f"   ⚠️  Warning during drop: {drop_result.stderr}")

            # Restore from dump using PostgreSQL 17 pg_restore
            # NOTE: Don't use --clean here! We already dropped tables manually
            #       (excluding our_secrets). Using --clean would drop our_secrets too.
            print("   📥 Restoring data...")
            restore_result = subprocess.run([
                PG_RESTORE,
                '-d', 'AngelaMemory_Backup',
                '-U', 'davidsamanyaporn',
                '--no-owner',  # Don't set ownership
                '-j', '4',  # Parallel jobs
                BACKUP_FILE
            ], capture_output=True, text=True, timeout=600)

            # pg_restore returns non-zero for warnings too
            # Ignore known warnings that don't affect data
            ignorable_errors = [
                'transaction_timeout',  # PostgreSQL 17 specific
                'neon_superuser',       # Neon-specific role
                'cloud_admin',          # Neon-specific role
                'already exists',       # Functions/objects already exist (OK)
                'errors ignored on restore',  # Summary message
            ]

            if restore_result.returncode != 0:
                stderr = restore_result.stderr

                # Check each error line
                has_real_errors = False
                for line in stderr.split('\n'):
                    if 'error' in line.lower() and line.strip():
                        # Check if this error is ignorable
                        is_ignorable = any(w in line.lower() for w in ignorable_errors)
                        if not is_ignorable:
                            has_real_errors = True
                            break

                if has_real_errors:
                    print(f"❌ pg_restore errors: {stderr}")
                    return False
                else:
                    print("   ⚠️  Ignored Neon-specific warnings (data restored OK)")

            print("✅ Restore complete!")
            return True

        except subprocess.TimeoutExpired:
            print("❌ pg_restore timed out")
            return False
        except Exception as e:
            print(f"❌ Restore error: {e}")
            return False

    def cleanup(self):
        """Remove temporary backup file."""
        if os.path.exists(BACKUP_FILE):
            os.remove(BACKUP_FILE)
            print("🧹 Cleaned up temporary file")

    def verify_restore(self) -> dict:
        """Verify restore by comparing counts."""
        print("🔍 Verifying restore...")

        try:
            # Count tables and rows in local
            result = subprocess.run([
                'psql', '-d', 'AngelaMemory_Backup', '-U', 'davidsamanyaporn', '-t', '-A', '-c',
                """
                SELECT
                    (SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public') as tables,
                    (SELECT COUNT(*) FROM conversations) as conversations,
                    (SELECT COUNT(*) FROM angela_emotions) as emotions;
                """
            ], capture_output=True, text=True)

            if result.returncode == 0:
                parts = result.stdout.strip().split('|')
                counts = {
                    'tables': int(parts[0]),
                    'conversations': int(parts[1]),
                    'emotions': int(parts[2])
                }
                print(f"   📊 Tables: {counts['tables']}")
                print(f"   💬 Conversations: {counts['conversations']:,}")
                print(f"   💜 Emotions: {counts['emotions']:,}")
                return counts
        except Exception as e:
            print(f"   ⚠️  Verify error: {e}")

        return {}

    def run_backup(self) -> dict:
        """Run complete Neon → Local backup."""
        result = {
            'success': False,
            'message': '',
            'timestamp': datetime.now().isoformat(),
            'counts': {}
        }

        try:
            # Step 1: Dump from Neon
            if not self.dump_from_neon():
                result['message'] = 'Dump from Neon failed'
                return result

            # Step 2: Restore to Local
            if not self.restore_to_local():
                result['message'] = 'Restore to Local failed'
                return result

            # Step 3: Verify
            result['counts'] = self.verify_restore()

            # Step 4: Cleanup
            self.cleanup()

            result['success'] = True
            result['message'] = 'Neon → Local backup complete!'

        except Exception as e:
            result['message'] = f'Error: {str(e)}'
            self.cleanup()

        return result


def neon_to_local_backup():
    """
    Backup Angela from Neon Cloud to Local PostgreSQL.

    Use this to keep local M3 as a backup of Neon.
    """
    print("=" * 60)
    print("🔄 ANGELA REVERSE BACKUP")
    print("   Source: ☁️ Neon Cloud (Primary)")
    print("   Destination: 🏠 Local PostgreSQL")
    print("=" * 60)
    print()

    service = ReverseBackupService()
    result = service.run_backup()

    print()
    print("=" * 60)
    if result['success']:
        print("✅ " + result['message'])
        if result['counts']:
            print(f"📊 Verified: {result['counts'].get('tables', 0)} tables")
    else:
        print("❌ " + result['message'])
    print("=" * 60)

    return result


if __name__ == '__main__':
    neon_to_local_backup()
