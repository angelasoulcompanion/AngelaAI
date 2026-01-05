#!/usr/bin/env python3
"""
Google OAuth Setup Script for Angela MCP Servers
=================================================
This script creates a unified OAuth token for both Gmail and Calendar APIs.

Usage:
1. Download credentials.json from Google Cloud Console
2. Place it in this directory or specify path
3. Run: python3 setup_google_oauth.py
4. Complete OAuth flow in browser
5. Token will be created for both Gmail and Calendar MCPs
"""

import json
import shutil
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Combined scopes for both Gmail and Calendar
SCOPES = [
    # Gmail scopes
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    # Calendar scopes
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
]

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
MCP_SERVERS = PROJECT_ROOT / "mcp_servers"

# Credential locations to check
CREDENTIALS_LOCATIONS = [
    SCRIPT_DIR / "credentials.json",
    PROJECT_ROOT / "credentials.json",
    Path.home() / "Downloads" / "credentials.json",
]

# Target directories for token
TOKEN_TARGETS = [
    MCP_SERVERS / "angela-gmail" / "credentials",
    MCP_SERVERS / "angela-calendar" / "credentials",
]


def find_credentials() -> Path | None:
    """Find credentials.json file."""
    for path in CREDENTIALS_LOCATIONS:
        if path.exists():
            return path
    return None


def main():
    print("=" * 60)
    print("Google OAuth Setup for Angela MCP Servers")
    print("=" * 60)
    print()

    # Find credentials.json
    credentials_path = find_credentials()

    if not credentials_path:
        print("credentials.json not found!")
        print()
        print("Please download it from Google Cloud Console:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Select your project (or create one)")
        print("3. Create OAuth 2.0 Client ID (Desktop app)")
        print("4. Download the credentials.json file")
        print("5. Place it in one of these locations:")
        for loc in CREDENTIALS_LOCATIONS:
            print(f"   - {loc}")
        print()
        print("Then run this script again.")
        return

    print(f"Found credentials at: {credentials_path}")
    print()

    # Check for existing valid token
    existing_token = None
    for target in TOKEN_TARGETS:
        token_path = target / "token.json"
        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
                if creds.valid:
                    existing_token = creds
                    print(f"Found valid token at: {token_path}")
                    break
                elif creds.expired and creds.refresh_token:
                    print(f"Found expired token at {token_path}, trying to refresh...")
                    creds.refresh(Request())
                    existing_token = creds
                    break
            except Exception as e:
                print(f"Could not use token at {token_path}: {e}")

    if existing_token and existing_token.valid:
        print("Existing token is valid!")
        creds = existing_token
    else:
        # Run OAuth flow
        print("Starting OAuth flow...")
        print("A browser window will open. Please log in with:")
        print("  angelasoulcompanion@gmail.com")
        print()

        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path), SCOPES
        )
        creds = flow.run_local_server(port=0)

        print()
        print("OAuth flow completed!")

    # Save token to all target directories
    print()
    print("Saving token to MCP server directories...")

    token_json = creds.to_json()

    for target in TOKEN_TARGETS:
        target.mkdir(parents=True, exist_ok=True)
        token_path = target / "token.json"
        with open(token_path, 'w') as f:
            f.write(token_json)
        print(f"  Saved: {token_path}")

        # Also copy credentials.json for future use
        creds_copy = target / "credentials.json"
        shutil.copy(credentials_path, creds_copy)
        print(f"  Copied credentials: {creds_copy}")

    print()
    print("=" * 60)
    print("Setup completed!")
    print("=" * 60)
    print()
    print("Token scopes:")
    for scope in SCOPES:
        print(f"  - {scope.split('/')[-1]}")
    print()
    print(f"Token expiry: {creds.expiry}")
    print()
    print("You can now restart Claude Code to use the MCP servers.")
    print("Run '/mcp' to check if angela-gmail and angela-calendar are connected.")


if __name__ == "__main__":
    main()
