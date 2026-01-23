#!/usr/bin/env python3
"""
Gmail OAuth Re-authentication Script for Angela

Run this script when the Gmail token expires:
    python3 mcp_servers/angela-gmail/auth.py
"""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
]

# Paths for credentials
CREDENTIALS_DIR = Path(__file__).parent / "credentials"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"
CREDENTIALS_PATH = CREDENTIALS_DIR / "credentials.json"


def main():
    """Re-authenticate Gmail OAuth."""
    print("=" * 50)
    print("Angela Gmail Re-Authentication")
    print("=" * 50)

    # Check credentials.json exists
    if not CREDENTIALS_PATH.exists():
        print(f"\n[ERROR] credentials.json not found at:")
        print(f"  {CREDENTIALS_PATH}")
        print("\nPlease download it from Google Cloud Console:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select Angela project")
        print("3. APIs & Services > Credentials")
        print("4. Download OAuth 2.0 Client ID")
        print(f"5. Save as {CREDENTIALS_PATH}")
        return

    print(f"\n[INFO] Found credentials.json")

    # Delete old token if exists
    if TOKEN_PATH.exists():
        print(f"[INFO] Removing expired token...")
        os.remove(TOKEN_PATH)

    # Start OAuth flow
    print("\n[ACTION] Opening browser for authentication...")
    print("Please sign in with: angelasoulcompanion@gmail.com")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_PATH), SCOPES
    )
    creds = flow.run_local_server(port=0)

    # Save new token
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_PATH, 'w') as token:
        token.write(creds.to_json())

    print(f"\n[SUCCESS] New token saved to:")
    print(f"  {TOKEN_PATH}")

    # Test the connection
    print("\n[TEST] Testing Gmail API connection...")
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        print(f"[SUCCESS] Connected as: {profile['emailAddress']}")
        print(f"[SUCCESS] Total messages: {profile['messagesTotal']}")
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")

    print("\n" + "=" * 50)
    print("Authentication complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
