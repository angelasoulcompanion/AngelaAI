"""
Angela Configuration
SSOT: our_secrets table → config.db_url.get_supabase_url()
"""

from config.db_url import get_supabase_url

# Backward compat — some modules import SUPABASE_DATABASE_URL from config
try:
    SUPABASE_DATABASE_URL = get_supabase_url()
except RuntimeError:
    SUPABASE_DATABASE_URL = ""
