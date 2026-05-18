#!/usr/bin/env python3
"""
Unified Google OAuth Re-authentication Script for Angela MCP servers.

Replaces 3 duplicate auth.py scripts (gmail, calendar, sheets).

Usage:
    python3 mcp_servers/shared/reauth.py gmail
    python3 mcp_servers/shared/reauth.py calendar
    python3 mcp_servers/shared/reauth.py sheets
    python3 mcp_servers/shared/reauth.py gmail --test  # test only, don't re-auth
    python3 mcp_servers/shared/reauth.py gmail --user david  # different user prefix

The --user flag determines which directory the credentials live under
(default: angela → mcp_servers/angela-<service>/credentials/). For
example `--user david` reads/writes mcp_servers/david-<service>/credentials/.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from google_auth import SERVICE_CONFIGS

MCP_SERVERS_DIR = Path(__file__).parent.parent


USER_EMAILS = {
    "angela": "angelasoulcompanion@gmail.com",
    "david": "davidsamanyaporn@gmail.com",
}


def get_credentials_dir(service_name: str, user: str = "angela") -> Path:
    """Get the credentials directory for a service / user pair."""
    return MCP_SERVERS_DIR / f"{user}-{service_name}" / "credentials"


def reauth(service_name: str, user: str = "angela") -> Credentials:
    """Re-authenticate OAuth for a specific Google service + user."""
    config = SERVICE_CONFIGS[service_name]
    creds_dir = get_credentials_dir(service_name, user)
    token_path = creds_dir / "token.json"
    credentials_path = creds_dir / "credentials.json"
    user_email = USER_EMAILS.get(user, f"<{user}>@…")

    print("=" * 50)
    print(f"{user.title()} {service_name.title()} Re-Authentication")
    print(f"  Sign in as: {user_email}")
    print("=" * 50)

    if not credentials_path.exists():
        print(f"\n[ERROR] credentials.json not found at:")
        print(f"  {credentials_path}")
        print("\nPlease download it from Google Cloud Console:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select Angela project")
        print("3. APIs & Services > Credentials")
        print("4. Download OAuth 2.0 Client ID")
        print(f"5. Save as {credentials_path}")
        sys.exit(1)

    print(f"\n[INFO] Found credentials.json")

    if token_path.exists():
        print(f"[INFO] Removing expired token...")
        os.remove(token_path)

    print("\n[ACTION] Opening browser for authentication...")
    print(f"Please sign in with: {user_email}")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path), config["scopes"]
    )
    creds = flow.run_local_server(port=0)

    creds_dir.mkdir(parents=True, exist_ok=True)
    with open(token_path, 'w') as token:
        token.write(creds.to_json())

    print(f"\n[SUCCESS] New token saved to:")
    print(f"  {token_path}")

    return creds


def test_connection(service_name: str, creds: Credentials = None, user: str = "angela"):
    """Test the API connection for a specific service."""
    config = SERVICE_CONFIGS[service_name]

    if creds is None:
        creds_dir = get_credentials_dir(service_name, user)
        token_path = creds_dir / "token.json"
        if not token_path.exists():
            print(f"[ERROR] No token found. Run reauth first.")
            sys.exit(1)
        creds = Credentials.from_authorized_user_file(
            str(token_path), config["scopes"]
        )

    print(f"\n[TEST] Testing {service_name.title()} API connection...")
    service = build(config["api_name"], config["api_version"], credentials=creds)

    if service_name == "gmail":
        profile = service.users().getProfile(userId='me').execute()
        print(f"[SUCCESS] Connected as: {profile['emailAddress']}")
        print(f"[SUCCESS] Total messages: {profile['messagesTotal']}")

    elif service_name == "calendar":
        calendar = service.calendars().get(calendarId='primary').execute()
        print(f"[SUCCESS] Connected to calendar: {calendar['summary']}")
        now = datetime.now().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=now, maxResults=5,
            singleEvents=True, orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        print(f"[SUCCESS] Found {len(events)} upcoming events")
        for event in events[:3]:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"  - {event['summary']} ({start})")

    elif service_name == "sheets":
        spreadsheet = service.spreadsheets().create(
            body={'properties': {'title': 'Angela Auth Test (delete me)'}}
        ).execute()
        print(f"[SUCCESS] Connected! Created test sheet: {spreadsheet['spreadsheetId']}")
        print(f"[INFO] You can delete the test sheet from Google Drive")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in SERVICE_CONFIGS:
        print(f"Usage: {sys.argv[0]} <service> [--test] [--user <prefix>]")
        print(f"  Services: {', '.join(SERVICE_CONFIGS.keys())}")
        print(f"  Users:    {', '.join(USER_EMAILS.keys())} (default: angela)")
        print(f"  --test:   Test connection only (no re-auth)")
        sys.exit(1)

    service_name = sys.argv[1]
    test_only = "--test" in sys.argv
    user = "angela"
    if "--user" in sys.argv:
        idx = sys.argv.index("--user")
        if idx + 1 < len(sys.argv):
            user = sys.argv[idx + 1]

    if test_only:
        test_connection(service_name, user=user)
    else:
        creds = reauth(service_name, user=user)
        test_connection(service_name, creds, user=user)

    print("\n" + "=" * 50)
    print("Done!")
    print("=" * 50)


if __name__ == "__main__":
    main()
