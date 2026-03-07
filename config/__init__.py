"""
Angela Configuration
Loads Neon database URL from local_settings.py (gitignored)
"""

import os

try:
    from config.local_settings import NEON_DATABASE_URL
except ImportError:
    NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL", "")
