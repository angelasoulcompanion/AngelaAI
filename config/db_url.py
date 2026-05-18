"""
SSOT: Database URL resolver for all Angela projects.

Resolution order (per key):
  1. Environment variable override
  2. our_secrets table (Local PostgreSQL) — SSOT
  3. ~/.angela_secrets file — fallback (iCloud sync)

Usage:
    from config.db_url import get_supabase_url, get_pythia_url
    url = get_supabase_url()   # Angela primary (Supabase Tokyo)
    url = get_pythia_url()     # Pythia finance (Neon Singapore)
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

LOCAL_DB = "angela"
LOCAL_USER = "davidsamanyaporn"
SECRETS_FILE = Path.home() / ".angela_secrets"

_cache: dict[str, str] = {}


def _read_from_our_secrets(secret_name: str) -> Optional[str]:
    """Read a secret from our_secrets table (Local PG via psql)."""
    try:
        result = subprocess.run(
            [
                "psql", "-d", LOCAL_DB, "-U", LOCAL_USER,
                "-t", "-A", "-c",
                f"SELECT secret_value FROM our_secrets "
                f"WHERE secret_name = '{secret_name}' AND is_active = TRUE"
            ],
            capture_output=True, text=True, timeout=5
        )
        url = result.stdout.strip()
        return url if url else None
    except Exception:
        return None


def _read_from_file(env_key: str) -> Optional[str]:
    """Read a key from ~/.angela_secrets file."""
    try:
        if not SECRETS_FILE.exists():
            return None
        for line in SECRETS_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{env_key}="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None


def _resolve(env_key: str, secret_name: str) -> str:
    """
    Generic resolver: env → our_secrets → ~/.angela_secrets file.

    Args:
        env_key: Environment variable name (e.g. SUPABASE_DATABASE_URL)
        secret_name: Key in our_secrets table (e.g. supabase_database_url)

    Returns:
        Database URL

    Raises:
        RuntimeError: if URL not found anywhere
    """
    if secret_name in _cache:
        return _cache[secret_name]

    # 1. Env override
    url = os.environ.get(env_key)

    # 2. our_secrets table (SSOT)
    if not url:
        url = _read_from_our_secrets(secret_name)

    # 3. ~/.angela_secrets file (fallback)
    if not url:
        url = _read_from_file(env_key)

    if not url:
        raise RuntimeError(
            f"{env_key} not found in our_secrets (key='{secret_name}'), "
            f"~/.angela_secrets, or environment"
        )

    _cache[secret_name] = url
    return url


# ─── Public API ───────────────────────────────────────────────

def get_supabase_url() -> str:
    """Angela primary DB — Supabase (Tokyo)."""
    return _resolve("SUPABASE_DATABASE_URL", "supabase_database_url")


def get_pythia_url() -> str:
    """Pythia finance DB — Supabase Tokyo (schema=pythia)."""
    return _resolve("PYTHIA_DATABASE_URL", "pythia_supabase_url")


def clear_cache() -> None:
    """Clear cached URLs (for testing)."""
    _cache.clear()
