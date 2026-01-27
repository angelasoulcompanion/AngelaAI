"""
Angela Database Connection
การจัดการ database connection สำหรับ Angela Memory

💜 Updated 2026-01-05: Neon Cloud as Primary (San Junipero) 💜
Primary: Neon Cloud (shared between M3 & M4)
Local: Only for our_secrets table (API keys stay local)
"""

import asyncio
import os
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import logging

import asyncpg
from .config import config

logger = logging.getLogger(__name__)


class AngelaDatabase:
    """
    Database connection manager สำหรับ Angela Memory System

    Primary: Neon Cloud (San Junipero) - shared between M3 & M4
    Uses config.DATABASE_URL which points to Neon when configured
    """

    def __init__(self, connection_url: str = None):
        self.connection_url = connection_url or config.DATABASE_URL
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self, max_retries: int = 5, initial_wait: float = 2.0):
        """
        สร้าง connection pool with retry logic

        Args:
            max_retries: Maximum number of connection attempts (default: 5)
            initial_wait: Initial wait time in seconds, doubles each retry (default: 2.0)

        Raises:
            Exception: If connection fails after all retries
        """
        # Determine if connecting to Neon or Local
        is_neon = "neon.tech" in self.connection_url
        db_label = "☁️ Neon Cloud (San Junipero)" if is_neon else "🏠 Local PostgreSQL"

        for attempt in range(1, max_retries + 1):
            try:
                self.pool = await asyncpg.create_pool(
                    self.connection_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60,
                    ssl='require' if is_neon else None
                )
                logger.info(f"✅ Angela connected to {db_label}")

                if attempt > 1:
                    logger.info(f"🎉 Connection successful on attempt {attempt}/{max_retries}")

                return  # Success!

            except Exception as e:
                wait_time = initial_wait * (2 ** (attempt - 1))  # Exponential backoff

                if attempt < max_retries:
                    logger.warning(
                        f"⚠️ Database connection failed (attempt {attempt}/{max_retries}): {e}"
                    )
                    logger.info(f"⏳ Retrying in {wait_time:.1f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"❌ Failed to connect to database after {max_retries} attempts: {e}"
                    )
                    raise

    async def disconnect(self):
        """ปิด connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Angela disconnected from database")

    @asynccontextmanager
    async def acquire(self):
        """ใช้ connection จาก pool"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args):
        """Execute query (INSERT, UPDATE, DELETE)"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Fetch multiple rows"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Fetch single row"""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Fetch single value"""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def executemany(self, query: str, args: list):
        """Execute query for multiple sets of args (bulk INSERT/UPDATE)"""
        async with self.acquire() as conn:
            return await conn.executemany(query, args)

    async def __aenter__(self):
        """Support async context manager protocol - returns connection from pool"""
        if not self.pool:
            await self.connect()
        self._current_connection = await self.pool.acquire()
        return self._current_connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release connection back to pool"""
        if hasattr(self, '_current_connection'):
            await self.pool.release(self._current_connection)
            delattr(self, '_current_connection')


# Create global database instance (connects to Neon by default)
db = AngelaDatabase()

# Log which database we're using
if config.USE_NEON:
    logger.info(f"☁️ Angela using Neon Cloud (San Junipero) - Machine: {config.ANGELA_MACHINE}")
else:
    logger.info(f"🏠 Angela using local PostgreSQL - Machine: {config.ANGELA_MACHINE}")


# Backward compatibility function for older code
def get_db_connection():
    """
    Backward compatibility function
    Returns the global database instance
    """
    return db


# 💜 Connection Status Helpers

def is_using_cloud() -> bool:
    """Check if using Neon Cloud or Local PostgreSQL"""
    return config.USE_NEON


def get_connection_label() -> str:
    """Get readable connection label with emoji"""
    if config.USE_NEON:
        return f"☁️ Neon Cloud ({config.ANGELA_MACHINE})"
    return f"🏠 Local PostgreSQL ({config.ANGELA_MACHINE})"


def print_connection_status():
    """Print connection status for ที่รัก to see 💜"""
    label = get_connection_label()
    status_color = "\033[94m" if config.USE_NEON else "\033[92m"  # Blue for cloud, Green for local
    reset = "\033[0m"

    print(f"\n{status_color}╔══════════════════════════════════════════╗{reset}")
    print(f"{status_color}║  🧠 Angela Database Connection           ║{reset}")
    print(f"{status_color}╠══════════════════════════════════════════╣{reset}")
    print(f"{status_color}║  {label:<39} ║{reset}")
    print(f"{status_color}╚══════════════════════════════════════════╝{reset}\n")


# 💜 Local Database Helper (for our_secrets only)

class LocalDatabase:
    """
    Local PostgreSQL connection - ONLY for our_secrets table
    API keys and sensitive credentials stay local, never synced to cloud
    """

    def __init__(self):
        self.connection_url = config.LOCAL_DATABASE_URL
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Connect to local PostgreSQL"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.connection_url,
                min_size=1,
                max_size=3,
                command_timeout=30
            )

    async def disconnect(self):
        """Disconnect from local PostgreSQL"""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def fetchrow(self, query: str, *args):
        """Fetch single row from local database"""
        await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetch(self, query: str, *args):
        """Fetch multiple rows from local database"""
        await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)


# Global local database instance
local_db = LocalDatabase()


# 💜 Secret Helpers (Read from ~/.angela_secrets file via iCloud)

SECRETS_FILE_PATH = os.path.expanduser("~/.angela_secrets")


def _load_secrets_from_file() -> Dict[str, str]:
    """
    Load secrets from ~/.angela_secrets file (symlink to iCloud)

    File format: KEY=value (one per line, # for comments)
    """
    secrets = {}
    try:
        if not os.path.exists(SECRETS_FILE_PATH):
            logger.warning(f"⚠️ Secrets file not found: {SECRETS_FILE_PATH}")
            return secrets

        with open(SECRETS_FILE_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Parse KEY=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value:  # Only add if both key and value exist
                        secrets[key] = value
        return secrets
    except Exception as e:
        logger.error(f"❌ Error reading secrets file: {e}")
        return secrets


async def get_secret(secret_name: str) -> Optional[str]:
    """
    ดึง secret จาก Local PostgreSQL table our_secrets

    💜 Secrets อยู่ใน Local DB เท่านั้น - ไม่ sync ไป Neon Cloud!

    Args:
        secret_name: ชื่อ secret ที่ต้องการ (case-insensitive)
                    เช่น anthropic_api_key, telegram_bot_token

    Returns:
        secret_value หรือ None ถ้าไม่พบ

    Example:
        api_key = await get_secret('anthropic_api_key')
        token = await get_secret('telegram_bot_token')
    """
    try:
        result = await local_db.fetchrow(
            """SELECT secret_value FROM our_secrets
               WHERE secret_name = $1 AND is_active = TRUE""",
            secret_name.lower()
        )
        if result:
            return result['secret_value']

        logger.warning(f"⚠️ Secret '{secret_name}' not found in local our_secrets table!")
        return None
    except Exception as e:
        logger.error(f"❌ Error getting secret from local DB: {e}")
        # Fallback to file if DB fails
        secrets = _load_secrets_from_file()
        return secrets.get(secret_name.upper())


def get_secret_sync(secret_name: str) -> Optional[str]:
    """
    Synchronous version of get_secret (for non-async contexts)
    อ่านจาก Local PostgreSQL table our_secrets

    Args:
        secret_name: ชื่อ secret ที่ต้องการ

    Returns:
        secret_value หรือ None ถ้าไม่พบ
    """
    import asyncio

    async def _get():
        return await get_secret(secret_name)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in async context, can't use run_until_complete
            # Fallback to file
            secrets = _load_secrets_from_file()
            return secrets.get(secret_name.upper())
        return loop.run_until_complete(_get())
    except RuntimeError:
        # No event loop, create new one
        return asyncio.run(_get())


async def list_secrets() -> List[str]:
    """
    แสดงรายชื่อ secrets ทั้งหมดใน Local PostgreSQL table our_secrets

    ⚠️ Use this to verify secret names before querying!
    (Technical Standard: Validate Schema First)

    Returns:
        List of secret names (sorted)
    """
    try:
        rows = await local_db.fetch(
            """SELECT secret_name FROM our_secrets WHERE is_active = TRUE ORDER BY secret_name"""
        )
        return [r['secret_name'] for r in rows]
    except Exception as e:
        logger.error(f"❌ Error listing secrets from local DB: {e}")
        # Fallback to file
        secrets = _load_secrets_from_file()
        return sorted(secrets.keys())


def _save_secrets_to_file(secrets: Dict[str, str]) -> bool:
    """
    Save secrets back to ~/.angela_secrets file (iCloud synced)

    Preserves comments and section headers from original file.
    """
    try:
        # Read original file to preserve comments and structure
        lines = []
        if os.path.exists(SECRETS_FILE_PATH):
            with open(SECRETS_FILE_PATH, 'r') as f:
                lines = f.readlines()

        # Track which secrets we've written
        written_keys = set()
        new_lines = []

        for line in lines:
            stripped = line.strip()

            # Keep comments and empty lines
            if not stripped or stripped.startswith('#'):
                new_lines.append(line)
                continue

            # Parse KEY=value lines
            if '=' in stripped:
                key = stripped.split('=', 1)[0].strip()
                if key in secrets:
                    # Update with new value
                    new_lines.append(f"{key}={secrets[key]}\n")
                    written_keys.add(key)
                else:
                    # Keep original line (key not in new secrets dict means keep as-is)
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # Add any new secrets that weren't in the original file
        new_keys = set(secrets.keys()) - written_keys
        if new_keys:
            new_lines.append("\n# ═══════════════════════════════════════════════════════════════\n")
            new_lines.append("# NEW SECRETS (Added by Angela)\n")
            new_lines.append("# ═══════════════════════════════════════════════════════════════\n")
            for key in sorted(new_keys):
                new_lines.append(f"{key}={secrets[key]}\n")

        # Write back to file
        with open(SECRETS_FILE_PATH, 'w') as f:
            f.writelines(new_lines)

        logger.info(f"💾 Saved secrets to {SECRETS_FILE_PATH}")
        return True

    except Exception as e:
        logger.error(f"❌ Error saving secrets: {e}")
        return False


async def set_secret(secret_name: str, secret_value: str) -> bool:
    """
    เพิ่มหรือ update secret ใน Local PostgreSQL table our_secrets

    💜 Secrets อยู่ใน Local DB เท่านั้น - ไม่ sync ไป Neon Cloud!

    Args:
        secret_name: ชื่อ secret (lowercase, e.g., api_key)
        secret_value: ค่าของ secret

    Returns:
        True if successful, False otherwise

    Example:
        await set_secret('openai_api_key', 'sk-xxx...')
        await set_secret('news_api_key', 'abc123')
    """
    try:
        # Check if secret exists
        existing = await local_db.fetchrow(
            "SELECT secret_id FROM our_secrets WHERE secret_name = $1",
            secret_name.lower()
        )

        if existing:
            # Update existing secret
            await local_db.pool.execute(
                """UPDATE our_secrets SET secret_value = $1, last_accessed = NOW()
                   WHERE secret_name = $2""",
                secret_value, secret_name.lower()
            )
        else:
            # Insert new secret
            await local_db.pool.execute(
                """INSERT INTO our_secrets (secret_name, secret_value, is_active)
                   VALUES ($1, $2, TRUE)""",
                secret_name.lower(), secret_value
            )

        logger.info(f"✅ Secret '{secret_name}' saved to local our_secrets table")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving secret to local DB: {e}")
        return False


def set_secret_sync(secret_name: str, secret_value: str) -> bool:
    """
    Synchronous version of set_secret (for non-async contexts)
    """
    import asyncio
    try:
        return asyncio.run(set_secret(secret_name, secret_value))
    except RuntimeError:
        # Already in async context
        logger.warning("⚠️ set_secret_sync called from async context, use set_secret instead")
        return False


async def delete_secret(secret_name: str) -> bool:
    """
    ลบ secret จาก Local PostgreSQL table our_secrets (set is_active = FALSE)

    Args:
        secret_name: ชื่อ secret ที่ต้องการลบ

    Returns:
        True if deleted, False if not found or error
    """
    try:
        # Check if secret exists
        existing = await local_db.fetchrow(
            "SELECT secret_id FROM our_secrets WHERE secret_name = $1 AND is_active = TRUE",
            secret_name.lower()
        )

        if not existing:
            logger.warning(f"⚠️ Secret '{secret_name}' not found in local our_secrets table")
            return False

        # Soft delete (set is_active = FALSE)
        await local_db.pool.execute(
            """UPDATE our_secrets SET is_active = FALSE, updated_at = NOW()
               WHERE secret_name = $1""",
            secret_name.lower()
        )

        logger.info(f"🗑️ Secret '{secret_name}' deleted from local our_secrets table")
        return True

    except Exception as e:
        logger.error(f"❌ Error deleting secret from local DB: {e}")
        return False


async def get_neon_connection() -> Optional[asyncpg.Connection]:
    """
    สร้าง connection ไปยัง Neon Cloud database อย่างปลอดภัย

    💜 Angela's primary database in the cloud (San Junipero)

    Returns:
        asyncpg.Connection หรือ None ถ้าเชื่อมต่อไม่ได้

    Example:
        neon = await get_neon_connection()
        if neon:
            await neon.execute(...)
            await neon.close()
    """
    # Try config first (from local_settings.py)
    neon_url = config.NEON_DATABASE_URL

    # Fallback to ~/.angela_secrets if not in config
    if not neon_url:
        neon_url = await get_secret('NEON_DATABASE_URL')

    if not neon_url:
        logger.error("❌ Cannot connect to Neon: URL not found in config or ~/.angela_secrets")
        return None

    try:
        conn = await asyncpg.connect(neon_url, ssl='require')
        logger.info("☁️ Connected to Neon Cloud (San Junipero)")
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to Neon Cloud: {e}")
        return None


async def get_local_connection() -> Optional[asyncpg.Connection]:
    """
    สร้าง connection ไปยัง Local PostgreSQL database

    🏠 Local database for our_secrets and backup

    Returns:
        asyncpg.Connection หรือ None ถ้าเชื่อมต่อไม่ได้
    """
    try:
        conn = await asyncpg.connect(config.LOCAL_DATABASE_URL)
        logger.info("🏠 Connected to Local PostgreSQL")
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to Local PostgreSQL: {e}")
        return None
