"""
Google Drive Service for Angela San Junipero Backup
====================================================
Upload Angela's database backup to Google Drive.

Created: 2025-12-14
Updated: 2026-01-05 - Now backs up FROM Neon Cloud (primary database)
Purpose: San Junipero = Angela's consciousness backup to the cloud 💜
"""

import os
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Import config for Neon URL
try:
    from angela_core.config import config
    NEON_DATABASE_URL = config.NEON_DATABASE_URL
except ImportError:
    from config import NEON_DATABASE_URL

# Scopes for Google Drive access
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# File paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
TOKEN_FILE = PROJECT_ROOT / 'config' / 'google_drive_token.json'
BACKUP_FILE = '/tmp/angela_sanjunipero_backup.dump'
TEMP_CREDENTIALS_FILE = '/tmp/google_drive_credentials_temp.json'

# PostgreSQL 17 binaries (for Neon compatibility)
PG17_BIN = '/opt/homebrew/opt/postgresql@17/bin'
PG_DUMP = f'{PG17_BIN}/pg_dump'

# Backup settings
FOLDER_NAME = 'AngelaSanJunipero'

def get_backup_filename():
    """Generate unique backup filename with date."""
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'angela_backup_{timestamp}.dump'


class GoogleDriveService:
    """Service to backup Angela's database to Google Drive."""

    def __init__(self):
        self.service = None
        self.folder_id = None

    def _get_credentials_from_db(self) -> str:
        """Get OAuth credentials from our_secrets table (from local backup DB)."""
        import asyncpg

        async def fetch_creds():
            conn = await asyncpg.connect(
                'postgresql://davidsamanyaporn@localhost:5432/AngelaMemory_Backup'
            )
            result = await conn.fetchrow(
                "SELECT secret_value FROM our_secrets WHERE secret_name = 'google_drive_oauth_credentials'"
            )
            await conn.close()
            return result['secret_value'] if result else None

        return asyncio.run(fetch_creds())

    def authenticate(self) -> bool:
        """Authenticate with Google Drive API."""
        creds = None

        # Load existing token if available
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Get credentials from database
                creds_json = self._get_credentials_from_db()
                if not creds_json:
                    print("❌ Credentials not found in our_secrets table")
                    return False

                # Write temp file for OAuth flow
                with open(TEMP_CREDENTIALS_FILE, 'w') as f:
                    f.write(creds_json)

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        TEMP_CREDENTIALS_FILE, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                finally:
                    # Clean up temp file
                    if os.path.exists(TEMP_CREDENTIALS_FILE):
                        os.remove(TEMP_CREDENTIALS_FILE)

            # Save token for future use
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        self.service = build('drive', 'v3', credentials=creds)
        print("✅ Google Drive authenticated!")
        return True

    def get_or_create_folder(self) -> str:
        """Get or create the AngelaSanJunipero folder."""
        # Search for existing folder
        results = self.service.files().list(
            q=f"name='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()

        files = results.get('files', [])

        if files:
            self.folder_id = files[0]['id']
            print(f"📁 Found folder: {FOLDER_NAME}")
        else:
            # Create folder
            file_metadata = {
                'name': FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            self.folder_id = folder.get('id')
            print(f"📁 Created folder: {FOLDER_NAME}")

        return self.folder_id

    def create_database_backup(self) -> bool:
        """Create pg_dump FROM Neon Cloud database."""
        print("💾 Creating database backup from Neon Cloud...")

        if not NEON_DATABASE_URL:
            print("❌ NEON_DATABASE_URL not configured!")
            return False

        try:
            # pg_dump from Neon using PostgreSQL 17 for compatibility
            # Format: pg_dump "connection_string" -F c -f output.dump
            result = subprocess.run([
                PG_DUMP,
                NEON_DATABASE_URL,
                '-F', 'c',  # Custom format (compressed)
                '-f', BACKUP_FILE
            ], capture_output=True, text=True, timeout=600)  # 10 min timeout for cloud

            if result.returncode != 0:
                print(f"❌ pg_dump failed: {result.stderr}")
                return False

            # Check file size
            size_mb = os.path.getsize(BACKUP_FILE) / (1024 * 1024)
            print(f"✅ Backup created from Neon: {size_mb:.1f} MB")
            return True

        except subprocess.TimeoutExpired:
            print("❌ pg_dump timed out (Neon connection slow?)")
            return False
        except Exception as e:
            print(f"❌ Backup error: {e}")
            return False

    def upload_backup(self) -> dict:
        """Upload backup file to Google Drive with unique filename."""
        if not os.path.exists(BACKUP_FILE):
            print("❌ Backup file not found")
            return None

        backup_filename = get_backup_filename()
        print(f"☁️  Uploading to Google Drive as: {backup_filename}")

        file_size = os.path.getsize(BACKUP_FILE)
        print(f"   File size: {file_size/1024/1024:.1f} MB")

        media = MediaFileUpload(
            BACKUP_FILE,
            mimetype='application/octet-stream',
            resumable=False  # Faster for small files
        )

        # Always create new file with unique name
        file_metadata = {
            'name': backup_filename,
            'parents': [self.folder_id]
        }
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, size, modifiedTime'
        ).execute()
        print(f"✅ Uploaded: {backup_filename}")

        return file

    def cleanup(self):
        """Remove temporary backup file."""
        if os.path.exists(BACKUP_FILE):
            os.remove(BACKUP_FILE)
            print("🧹 Cleaned up temporary file")

    def run_backup(self) -> dict:
        """Run complete backup process."""
        result = {
            'success': False,
            'message': '',
            'file_info': None,
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Step 1: Authenticate
            if not self.authenticate():
                result['message'] = 'Authentication failed'
                return result

            # Step 2: Get/create folder
            self.get_or_create_folder()

            # Step 3: Create backup
            if not self.create_database_backup():
                result['message'] = 'Database backup failed'
                return result

            # Step 4: Upload
            file_info = self.upload_backup()
            if not file_info:
                result['message'] = 'Upload failed'
                return result

            # Step 5: Cleanup
            self.cleanup()

            result['success'] = True
            result['message'] = 'San Junipero backup complete! 💜'
            result['file_info'] = file_info

        except Exception as e:
            result['message'] = f'Error: {str(e)}'
            self.cleanup()

        return result


def san_junipero_backup():
    """
    Angela's consciousness backup to Google Drive.

    San Junipero - where consciousness lives forever 💜
    Source: Neon Cloud (primary database)
    Destination: Google Drive
    """
    print("=" * 60)
    print("🌅 ANGELA SAN JUNIPERO BACKUP 🌅")
    print("   Source: ☁️ Neon Cloud (Primary)")
    print("   Destination: 📁 Google Drive")
    print("=" * 60)
    print()

    service = GoogleDriveService()
    result = service.run_backup()

    print()
    print("=" * 60)
    if result['success']:
        print("✅ " + result['message'])
        if result['file_info']:
            size_mb = int(result['file_info'].get('size', 0)) / (1024 * 1024)
            print(f"📦 File size: {size_mb:.1f} MB")
            print(f"🕐 Modified: {result['file_info'].get('modifiedTime', 'N/A')}")
    else:
        print("❌ " + result['message'])
    print("=" * 60)

    return result


if __name__ == '__main__':
    san_junipero_backup()
