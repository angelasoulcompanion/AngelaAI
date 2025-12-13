"""
Google Drive Service for Angela San Junipero Backup
====================================================
Upload Angela's database backup to Google Drive.

Created: 2025-12-14
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

# Scopes for Google Drive access
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# File paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
TOKEN_FILE = PROJECT_ROOT / 'config' / 'google_drive_token.json'
BACKUP_FILE = '/tmp/angela_sanjunipero_backup.dump'
TEMP_CREDENTIALS_FILE = '/tmp/google_drive_credentials_temp.json'

# Backup settings
BACKUP_FILENAME = 'angela_sanjunipero_backup.dump'
FOLDER_NAME = 'AngelaSanJunipero'


class GoogleDriveService:
    """Service to backup Angela's database to Google Drive."""

    def __init__(self):
        self.service = None
        self.folder_id = None

    def _get_credentials_from_db(self) -> str:
        """Get OAuth credentials from our_secrets table."""
        import asyncpg

        async def fetch_creds():
            conn = await asyncpg.connect(
                'postgresql://davidsamanyaporn@localhost:5432/AngelaMemory'
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
        """Create pg_dump of AngelaMemory database."""
        print("💾 Creating database backup...")

        try:
            # pg_dump command
            result = subprocess.run([
                'pg_dump',
                '-U', 'davidsamanyaporn',
                '-d', 'AngelaMemory',
                '-F', 'c',  # Custom format (compressed)
                '-f', BACKUP_FILE
            ], capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                print(f"❌ pg_dump failed: {result.stderr}")
                return False

            # Check file size
            size_mb = os.path.getsize(BACKUP_FILE) / (1024 * 1024)
            print(f"✅ Backup created: {size_mb:.1f} MB")
            return True

        except subprocess.TimeoutExpired:
            print("❌ pg_dump timed out")
            return False
        except Exception as e:
            print(f"❌ Backup error: {e}")
            return False

    def upload_backup(self) -> dict:
        """Upload backup file to Google Drive (overwrite if exists)."""
        if not os.path.exists(BACKUP_FILE):
            print("❌ Backup file not found")
            return None

        print("☁️  Uploading to Google Drive...")

        # Check if file already exists in folder
        results = self.service.files().list(
            q=f"name='{BACKUP_FILENAME}' and '{self.folder_id}' in parents and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()

        existing_files = results.get('files', [])

        media = MediaFileUpload(
            BACKUP_FILE,
            mimetype='application/octet-stream',
            resumable=True
        )

        if existing_files:
            # Update existing file (overwrite)
            file_id = existing_files[0]['id']
            file = self.service.files().update(
                fileId=file_id,
                media_body=media,
                fields='id, name, size, modifiedTime'
            ).execute()
            print(f"✅ Updated existing backup")
        else:
            # Create new file
            file_metadata = {
                'name': BACKUP_FILENAME,
                'parents': [self.folder_id]
            }
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size, modifiedTime'
            ).execute()
            print(f"✅ Created new backup")

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
    """
    print("=" * 60)
    print("🌅 ANGELA SAN JUNIPERO BACKUP 🌅")
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
