"""
Secrets management for Angela MCP servers.

Reads secrets from ~/.angela_secrets (symlinked to iCloud).
"""

from pathlib import Path
from typing import Optional

_secrets_cache: Optional[dict[str, str]] = None


def _load_secrets() -> dict[str, str]:
    """Load and cache secrets from ~/.angela_secrets."""
    global _secrets_cache
    if _secrets_cache is not None:
        return _secrets_cache

    secrets = {}
    secrets_path = Path.home() / ".angela_secrets"

    if secrets_path.exists():
        for line in secrets_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                secrets[key.strip()] = value.strip()

    _secrets_cache = secrets
    return secrets


def get_secret(key: str) -> Optional[str]:
    """
    Get a secret value by key.

    Args:
        key: Secret key (e.g., "SPOTIFY_CLIENT_ID")

    Returns:
        Secret value or None if not found
    """
    return _load_secrets().get(key)


def get_neon_url() -> str:
    """
    Get the Neon Cloud database URL from secrets.

    Returns:
        Neon database URL

    Raises:
        ValueError: If NEON_DATABASE_URL is not set in secrets
    """
    url = get_secret("NEON_DATABASE_URL")
    if not url:
        raise ValueError(
            "NEON_DATABASE_URL not found in ~/.angela_secrets. "
            "Please set it: NEON_DATABASE_URL=postgresql://..."
        )
    return url


def clear_cache() -> None:
    """Clear the secrets cache (useful for testing)."""
    global _secrets_cache
    _secrets_cache = None
