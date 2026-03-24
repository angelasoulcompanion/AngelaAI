"""
Secrets management for Angela MCP servers.

DB URL: delegates to config.db_url (SSOT: our_secrets table)
Other secrets: reads from ~/.angela_secrets (symlinked to iCloud)
"""

import sys
from pathlib import Path
from typing import Optional

# Add AngelaAI root to sys.path for config imports
_angela_root = str(Path(__file__).resolve().parents[2])
if _angela_root not in sys.path:
    sys.path.insert(0, _angela_root)

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


def get_supabase_url() -> str:
    """
    Get the Supabase database URL — delegates to config.db_url (SSOT).

    Resolution: env → our_secrets table → ~/.angela_secrets file
    """
    from config.db_url import get_supabase_url as _resolve
    return _resolve()


def clear_cache() -> None:
    """Clear the secrets cache (useful for testing)."""
    global _secrets_cache
    _secrets_cache = None
