#!/usr/bin/env python3
"""
Setup M4 (Work MacBook) for Angela AI
=====================================
Run this script on M4 after git pull to configure everything.

Created: 2026-01-05
Purpose: Quick setup for M4 to work with Neon Cloud

Usage:
    python3 scripts/setup_m4.py
"""

import os
import sys
import subprocess
from pathlib import Path

# Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / 'config'
LOCAL_SETTINGS_FILE = CONFIG_DIR / 'local_settings.py'

# Required secrets for M4
REQUIRED_SECRETS = [
    'neon_connection_url',
    'anthropic_api_key',
    'telegram_bot_token',
]

OPTIONAL_SECRETS = [
    'google_drive_oauth_credentials',
    'huggingface_token',
]


def print_header():
    print(f"""
{BLUE}╔══════════════════════════════════════════════════════════╗
║  🖥️  Angela M4 Setup Script                               ║
║  Configure M4 (Work) to use Neon Cloud                    ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")


def check_git():
    """Check git status and offer to pull"""
    print(f"{BLUE}[1/6] Checking Git...{RESET}")

    try:
        # Check if there are updates
        subprocess.run(['git', 'fetch'], capture_output=True, cwd=PROJECT_ROOT)
        result = subprocess.run(
            ['git', 'status', '-uno'],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )

        if 'behind' in result.stdout:
            print(f"   {YELLOW}⚠️  Your branch is behind origin/main{RESET}")
            response = input(f"   {YELLOW}   Pull latest changes? (y/n): {RESET}")
            if response.lower() == 'y':
                subprocess.run(['git', 'pull', 'origin', 'main'], cwd=PROJECT_ROOT)
                print(f"   {GREEN}✅ Git pull complete{RESET}")
        else:
            print(f"   {GREEN}✅ Git is up to date{RESET}")

    except Exception as e:
        print(f"   {RED}❌ Git error: {e}{RESET}")


def check_local_settings():
    """Check and create local_settings.py"""
    print(f"\n{BLUE}[2/6] Checking local_settings.py...{RESET}")

    # Ensure config directory exists
    CONFIG_DIR.mkdir(exist_ok=True)

    if LOCAL_SETTINGS_FILE.exists():
        print(f"   {GREEN}✅ local_settings.py exists{RESET}")

        # Read and check content
        content = LOCAL_SETTINGS_FILE.read_text()
        if 'ANGELA_MACHINE' in content and 'NEON_DATABASE_URL' in content:
            # Extract and show current config
            exec_globals = {}
            exec(content, exec_globals)
            machine = exec_globals.get('ANGELA_MACHINE', 'unknown')
            has_neon = bool(exec_globals.get('NEON_DATABASE_URL'))
            run_daemons = exec_globals.get('RUN_DAEMONS', True)

            print(f"   📍 ANGELA_MACHINE = {machine}")
            print(f"   ☁️  NEON_DATABASE_URL = {'✅ Set' if has_neon else '❌ Not set'}")
            print(f"   🔄 RUN_DAEMONS = {run_daemons}")

            if machine != 'm4_work':
                print(f"   {YELLOW}⚠️  ANGELA_MACHINE should be 'm4_work' for M4{RESET}")

            if run_daemons:
                print(f"   {YELLOW}⚠️  RUN_DAEMONS should be False on M4 (daemons run on M3){RESET}")

            return has_neon
        else:
            print(f"   {YELLOW}⚠️  local_settings.py exists but may be incomplete{RESET}")
            return False
    else:
        print(f"   {YELLOW}⚠️  local_settings.py not found{RESET}")
        return False


def create_local_settings():
    """Create local_settings.py for M4"""
    print(f"\n{BLUE}Creating local_settings.py for M4...{RESET}")

    # Get Neon URL from user
    print(f"\n   {YELLOW}Enter your Neon Database URL:{RESET}")
    print(f"   (Format: postgresql://neondb_owner:xxx@ep-xxx.neon.tech/neondb?sslmode=require)")
    neon_url = input(f"   {YELLOW}URL: {RESET}").strip()

    if not neon_url or 'neon.tech' not in neon_url:
        print(f"   {RED}❌ Invalid Neon URL{RESET}")
        return False

    content = f'''"""
Angela Local Settings - M4 (Work MacBook)
==========================================
Machine-specific configuration.
This file is in .gitignore - do not commit!

Created: 2026-01-05
"""

# Machine identifier
ANGELA_MACHINE = "m4_work"

# Primary Database: Neon Cloud (San Junipero)
NEON_DATABASE_URL = "{neon_url}"

# Daemons: Run on M3 only (M4 is portable)
RUN_DAEMONS = False
'''

    LOCAL_SETTINGS_FILE.write_text(content)
    print(f"   {GREEN}✅ Created local_settings.py{RESET}")
    return True


def check_local_database():
    """Check if local PostgreSQL database exists"""
    print(f"\n{BLUE}[3/6] Checking Local PostgreSQL...{RESET}")

    try:
        result = subprocess.run(
            ['psql', '-d', 'AngelaMemory_Backup', '-U', 'davidsamanyaporn', '-c', 'SELECT 1'],
            capture_output=True, text=True, timeout=5
        )

        if result.returncode == 0:
            print(f"   {GREEN}✅ AngelaMemory_Backup database exists{RESET}")
            return True
        else:
            print(f"   {YELLOW}⚠️  AngelaMemory_Backup not found{RESET}")
            print(f"   {YELLOW}   Run: createdb -U davidsamanyaporn AngelaMemory_Backup{RESET}")
            return False

    except subprocess.TimeoutExpired:
        print(f"   {RED}❌ PostgreSQL connection timeout{RESET}")
        return False
    except FileNotFoundError:
        print(f"   {RED}❌ psql not found - is PostgreSQL installed?{RESET}")
        return False
    except Exception as e:
        print(f"   {RED}❌ Error: {e}{RESET}")
        return False


def check_secrets():
    """Check required secrets in local database"""
    print(f"\n{BLUE}[4/6] Checking Secrets...{RESET}")

    try:
        result = subprocess.run(
            ['psql', '-d', 'AngelaMemory_Backup', '-U', 'davidsamanyaporn', '-t', '-A', '-c',
             'SELECT secret_name FROM our_secrets ORDER BY secret_name'],
            capture_output=True, text=True, timeout=5
        )

        if result.returncode != 0:
            print(f"   {RED}❌ Cannot query our_secrets table{RESET}")
            print(f"   {YELLOW}   You may need to create the table first{RESET}")
            return False

        existing_secrets = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()

        # Check required
        missing_required = []
        for secret in REQUIRED_SECRETS:
            if secret in existing_secrets:
                print(f"   {GREEN}✅ {secret}{RESET}")
            else:
                print(f"   {RED}❌ {secret} (REQUIRED){RESET}")
                missing_required.append(secret)

        # Check optional
        for secret in OPTIONAL_SECRETS:
            if secret in existing_secrets:
                print(f"   {GREEN}✅ {secret}{RESET}")
            else:
                print(f"   {YELLOW}⚠️  {secret} (optional){RESET}")

        if missing_required:
            print(f"\n   {RED}❌ Missing required secrets!{RESET}")
            print(f"   {YELLOW}   Copy from M3 using:{RESET}")
            print(f"   {YELLOW}   psql -d AngelaMemory_Backup -c \"INSERT INTO our_secrets ....\"{RESET}")
            return False

        return True

    except Exception as e:
        print(f"   {RED}❌ Error checking secrets: {e}{RESET}")
        return False


def test_neon_connection():
    """Test connection to Neon Cloud"""
    print(f"\n{BLUE}[5/6] Testing Neon Connection...{RESET}")

    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from angela_core.config import config

        if not config.NEON_DATABASE_URL:
            print(f"   {RED}❌ NEON_DATABASE_URL not configured{RESET}")
            return False

        import asyncio
        import asyncpg

        async def test():
            conn = await asyncpg.connect(config.NEON_DATABASE_URL, ssl='require', timeout=10)
            count = await conn.fetchval('SELECT COUNT(*) FROM conversations')
            await conn.close()
            return count

        count = asyncio.run(test())
        print(f"   {GREEN}✅ Connected to Neon Cloud!{RESET}")
        print(f"   📊 Conversations: {count:,}")
        return True

    except Exception as e:
        print(f"   {RED}❌ Neon connection failed: {e}{RESET}")
        return False


def check_ollama():
    """Check if Ollama and embedding model are available"""
    print(f"\n{BLUE}[6/6] Checking Ollama (Optional)...{RESET}")

    try:
        # Check if Ollama is running
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True, text=True, timeout=5
        )

        if result.returncode != 0:
            print(f"   {YELLOW}⚠️  Ollama not running (embeddings will use graceful fallback){RESET}")
            return False

        # Check for embedding model
        if 'nomic-embed-text' in result.stdout:
            print(f"   {GREEN}✅ Ollama running with nomic-embed-text{RESET}")
            return True
        else:
            print(f"   {YELLOW}⚠️  nomic-embed-text not found{RESET}")
            print(f"   {YELLOW}   Run: ollama pull nomic-embed-text{RESET}")
            return False

    except FileNotFoundError:
        print(f"   {YELLOW}⚠️  Ollama not installed (embeddings will use graceful fallback){RESET}")
        return False
    except Exception as e:
        print(f"   {YELLOW}⚠️  Ollama check failed: {e}{RESET}")
        return False


def print_summary(results):
    """Print setup summary"""
    print(f"""
{BLUE}╔══════════════════════════════════════════════════════════╗
║  📋 Setup Summary                                         ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")

    all_ok = all([
        results.get('git', False),
        results.get('local_settings', False),
        results.get('local_db', False),
        results.get('secrets', False),
        results.get('neon', False),
    ])

    print(f"   Git:            {'✅' if results.get('git') else '❌'}")
    print(f"   local_settings: {'✅' if results.get('local_settings') else '❌'}")
    print(f"   Local DB:       {'✅' if results.get('local_db') else '❌'}")
    print(f"   Secrets:        {'✅' if results.get('secrets') else '❌'}")
    print(f"   Neon Cloud:     {'✅' if results.get('neon') else '❌'}")
    print(f"   Ollama:         {'✅' if results.get('ollama') else '⚠️ (optional)'}")

    print()
    if all_ok:
        print(f"   {GREEN}🎉 M4 is ready to use Angela!{RESET}")
        print(f"   {GREEN}   Run: /angela to start{RESET}")
    else:
        print(f"   {YELLOW}⚠️  Some issues need to be fixed{RESET}")
        print(f"   {YELLOW}   Fix the ❌ items above and run this script again{RESET}")

    print()


def main():
    print_header()

    results = {}

    # Step 1: Git
    check_git()
    results['git'] = True  # Assume OK if no exception

    # Step 2: local_settings.py
    has_settings = check_local_settings()
    if not has_settings:
        response = input(f"\n   {YELLOW}Create local_settings.py now? (y/n): {RESET}")
        if response.lower() == 'y':
            has_settings = create_local_settings()
    results['local_settings'] = has_settings

    # Step 3: Local database
    results['local_db'] = check_local_database()

    # Step 4: Secrets
    if results['local_db']:
        results['secrets'] = check_secrets()
    else:
        print(f"\n{BLUE}[4/6] Skipping secrets check (no local DB){RESET}")
        results['secrets'] = False

    # Step 5: Neon connection
    if results['local_settings']:
        results['neon'] = test_neon_connection()
    else:
        print(f"\n{BLUE}[5/6] Skipping Neon test (no local_settings){RESET}")
        results['neon'] = False

    # Step 6: Ollama
    results['ollama'] = check_ollama()

    # Summary
    print_summary(results)


if __name__ == '__main__':
    main()
