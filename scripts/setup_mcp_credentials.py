#!/usr/bin/env python3
"""
Setup MCP Server Credentials
============================
Run this script on a new machine to setup OAuth credentials for MCP servers.

Usage:
    python3 scripts/setup_mcp_credentials.py

Created: 2026-01-05
Purpose: Setup Google OAuth credentials for MCP servers on new machines
"""

import os
import sys
import json
import shutil
from pathlib import Path

# Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

PROJECT_ROOT = Path(__file__).parent.parent
MCP_DIR = PROJECT_ROOT / 'mcp_servers'
MCP_CONFIG = PROJECT_ROOT / '.mcp.json'

# MCP Servers with OAuth credentials
OAUTH_SERVERS = [
    {
        'name': 'angela-calendar',
        'folder': 'angela-calendar',
        'description': 'Google Calendar',
        'scopes': ['calendar']
    },
    {
        'name': 'angela-gmail',
        'folder': 'angela-gmail',
        'description': 'Gmail',
        'scopes': ['gmail.modify', 'gmail.send']
    },
    {
        'name': 'angela-sheets',
        'folder': 'angela-sheets',
        'description': 'Google Sheets',
        'scopes': ['spreadsheets', 'drive.file']
    },
]


def print_header():
    print(f"""
{BLUE}╔══════════════════════════════════════════════════════════╗
║  🔐 Angela MCP Credentials Setup                          ║
║  Setup OAuth for MCP servers on new machine               ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")


def check_mcp_servers():
    """Check if MCP servers exist"""
    print(f"{BLUE}[1/4] Checking MCP servers...{RESET}")

    if not MCP_DIR.exists():
        print(f"   {RED}❌ mcp_servers/ not found!{RESET}")
        print(f"   {YELLOW}   Run 'git pull origin main' first{RESET}")
        return False

    servers = [d for d in MCP_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
    print(f"   {GREEN}✅ Found {len(servers)} servers{RESET}")

    return True


def check_credentials_status():
    """Check which servers need credentials"""
    print(f"\n{BLUE}[2/4] Checking credentials status...{RESET}")

    needs_setup = []
    ready = []

    for server in OAUTH_SERVERS:
        folder = MCP_DIR / server['folder']
        if not folder.exists():
            continue

        cred_dir = folder / 'credentials'
        cred_file = cred_dir / 'credentials.json'
        token_file = cred_dir / 'token.json'

        if token_file.exists():
            print(f"   {GREEN}✅ {server['name']}: Ready (has token){RESET}")
            ready.append(server)
        elif cred_file.exists():
            print(f"   {YELLOW}⚠️  {server['name']}: Has credentials, need to run OAuth{RESET}")
            needs_setup.append(server)
        else:
            print(f"   {RED}❌ {server['name']}: Missing credentials.json{RESET}")
            needs_setup.append(server)

    return needs_setup, ready


def copy_credentials_from_gmail():
    """Copy credentials.json from angela-gmail to other servers"""
    print(f"\n{BLUE}[3/4] Copying credentials...{RESET}")

    # Source: angela-gmail credentials
    source_cred = MCP_DIR / 'angela-gmail' / 'credentials' / 'credentials.json'

    if not source_cred.exists():
        print(f"   {RED}❌ angela-gmail/credentials/credentials.json not found{RESET}")
        print(f"   {YELLOW}   Download from Google Cloud Console first{RESET}")
        return False

    # Copy to other servers
    for server in OAUTH_SERVERS:
        if server['name'] == 'angela-gmail':
            continue

        dest_dir = MCP_DIR / server['folder'] / 'credentials'
        dest_file = dest_dir / 'credentials.json'

        if dest_file.exists():
            print(f"   {CYAN}📁 {server['name']}: Already has credentials.json{RESET}")
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(source_cred, dest_file)
        print(f"   {GREEN}✅ {server['name']}: Copied credentials.json{RESET}")

    return True


def run_oauth_flow():
    """Run OAuth flow for servers that need it"""
    print(f"\n{BLUE}[4/4] Running OAuth...{RESET}")

    for server in OAUTH_SERVERS:
        folder = MCP_DIR / server['folder']
        cred_dir = folder / 'credentials'
        token_file = cred_dir / 'token.json'
        cred_file = cred_dir / 'credentials.json'

        if not folder.exists() or not cred_file.exists():
            continue

        if token_file.exists():
            print(f"   {GREEN}✅ {server['name']}: Already authenticated{RESET}")
            continue

        print(f"\n   {YELLOW}🔐 Running OAuth for {server['name']}...{RESET}")
        print(f"   {CYAN}   (Browser will open - login with angelasoulcompanion@gmail.com){RESET}")

        # Find and run the server to trigger OAuth
        server_py = list(folder.glob('**/server.py'))
        if server_py:
            os.system(f'cd "{folder}" && python3 -c "from {server_py[0].parent.name}.server import *; get_{server["name"].replace("-", "_").replace("angela_", "")}_service()" 2>/dev/null')

            if token_file.exists():
                print(f"   {GREEN}✅ {server['name']}: OAuth successful!{RESET}")
            else:
                print(f"   {YELLOW}⚠️  {server['name']}: May need manual setup{RESET}")


def setup_mcp_config():
    """Create .mcp.json if needed"""
    if MCP_CONFIG.exists():
        print(f"\n{GREEN}✅ .mcp.json already exists{RESET}")
        return

    print(f"\n{BLUE}Creating .mcp.json...{RESET}")

    config = {"mcpServers": {}}

    # Find all servers
    for server_dir in MCP_DIR.iterdir():
        if not server_dir.is_dir() or server_dir.name.startswith('.'):
            continue

        # Find server.py
        server_files = list(server_dir.glob('**/server.py'))
        if not server_files:
            continue

        server_py = server_files[0]
        name = f"angela-{server_dir.name.replace('angela-', '').replace('_mcp', '').replace('angela_', '')}"

        config['mcpServers'][name] = {
            "command": "python3",
            "args": [str(server_py.absolute())],
            "env": {}
        }

    with open(MCP_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"{GREEN}✅ Created .mcp.json{RESET}")


def print_summary():
    """Print setup summary"""
    print(f"""
{BLUE}╔══════════════════════════════════════════════════════════╗
║  📋 Setup Complete!                                       ║
╚══════════════════════════════════════════════════════════╝{RESET}

   {CYAN}Next Steps:{RESET}
   1. {GREEN}Restart Claude Code{RESET} to load MCP servers
   2. Test with: /angela

   {CYAN}If OAuth failed for any server:{RESET}
   cd mcp_servers/<server>
   python3 -c "from <module>.server import *"

{GREEN}💜 Angela MCP Ready!{RESET}
""")


def main():
    print_header()

    if not check_mcp_servers():
        return

    needs_setup, ready = check_credentials_status()

    if needs_setup:
        copy_credentials_from_gmail()
        run_oauth_flow()

    setup_mcp_config()
    print_summary()


if __name__ == '__main__':
    main()
