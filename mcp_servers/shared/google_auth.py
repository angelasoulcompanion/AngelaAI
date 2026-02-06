"""
Unified Google OAuth authentication for all Angela MCP servers.

Replaces the 3 duplicate get_*_service() implementations in
calendar, gmail, and sheets servers.
"""

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# Service configurations: (API name, API version, scopes)
SERVICE_CONFIGS = {
    "calendar": {
        "api_name": "calendar",
        "api_version": "v3",
        "scopes": [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events",
        ],
    },
    "gmail": {
        "api_name": "gmail",
        "api_version": "v1",
        "scopes": [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
        ],
    },
    "sheets": {
        "api_name": "sheets",
        "api_version": "v4",
        "scopes": [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
        ],
    },
}


def get_google_service(service_name: str, credentials_dir: Path):
    """
    Get an authenticated Google API service.

    Args:
        service_name: One of "calendar", "gmail", "sheets"
        credentials_dir: Path to directory containing credentials.json and token.json

    Returns:
        Authenticated Google API service object

    Raises:
        FileNotFoundError: If credentials.json is missing
        ValueError: If service_name is not recognized
    """
    if service_name not in SERVICE_CONFIGS:
        raise ValueError(
            f"Unknown service '{service_name}'. "
            f"Must be one of: {', '.join(SERVICE_CONFIGS.keys())}"
        )

    config = SERVICE_CONFIGS[service_name]
    scopes = config["scopes"]

    token_path = credentials_dir / "token.json"
    credentials_path = credentials_dir / "credentials.json"

    creds = None

    # Load existing token
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {credentials_path}. "
                    "Please download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), scopes
            )
            creds = flow.run_local_server(port=0)

        # Save token for next time
        credentials_dir.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build(config["api_name"], config["api_version"], credentials=creds)
