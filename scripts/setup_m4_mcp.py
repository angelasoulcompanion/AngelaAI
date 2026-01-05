#!/usr/bin/env python3
"""
Setup MCP Servers for M4 (Work MacBook)
=======================================
Run this script on M4 after git pull to setup MCP servers.

Created: 2026-01-05
Purpose: Copy MCP servers from M3 template and configure for M4

Usage:
    python3 scripts/setup_m4_mcp.py
"""

import os
import sys
import shutil
import json
from pathlib import Path

# Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

PROJECT_ROOT = Path(__file__).parent.parent
MCP_M3_DIR = PROJECT_ROOT / 'mcp_servers_m3'
MCP_M4_DIR = PROJECT_ROOT / 'mcp_servers_m4'
MCP_CONFIG = PROJECT_ROOT / '.mcp.json'
MCP_CONFIG_EXAMPLE = PROJECT_ROOT / '.mcp.json.m4.example'

# MCP Servers to setup
MCP_SERVERS = [
    {
        'name': 'angela-news',
        'source': 'angela_news_mcp',
        'has_credentials': False,
        'description': 'ข่าว Tech, Thai, Business'
    },
    {
        'name': 'angela-calendar',
        'source': 'angela-calendar',
        'has_credentials': True,
        'credentials_files': ['credentials.json', 'token.json'],
        'description': 'Google Calendar'
    },
    {
        'name': 'angela-gmail',
        'source': 'angela-gmail',
        'has_credentials': True,
        'credentials_files': ['credentials.json', 'token.json'],
        'description': 'Gmail'
    },
    {
        'name': 'angela-sheets',
        'source': 'angela-sheets',
        'has_credentials': True,
        'credentials_files': ['credentials.json', 'token.json'],
        'description': 'Google Sheets'
    },
    {
        'name': 'angela-music',
        'source': 'angela-music',
        'has_credentials': False,
        'description': 'Music identification'
    },
]


def print_header():
    print(f"""
{BLUE}╔══════════════════════════════════════════════════════════╗
║  🔧 Angela MCP Setup for M4 (Work MacBook)               ║
║  Configure MCP Servers for M4                            ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")


def check_m3_servers():
    """Check if M3 servers exist as source"""
    print(f"{BLUE}[1/5] Checking M3 source servers...{RESET}")

    if not MCP_M3_DIR.exists():
        print(f"   {RED}❌ mcp_servers_m3/ not found!{RESET}")
        print(f"   {YELLOW}   Run 'git pull origin main' first{RESET}")
        return False

    servers = list(MCP_M3_DIR.iterdir())
    print(f"   {GREEN}✅ Found {len(servers)} servers in mcp_servers_m3/{RESET}")
    for server in servers:
        if server.is_dir():
            print(f"      • {server.name}")

    return True


def copy_mcp_servers():
    """Copy MCP servers from M3 to M4"""
    print(f"\n{BLUE}[2/5] Copying MCP servers to M4...{RESET}")

    copied = 0
    skipped = 0

    for server in MCP_SERVERS:
        source = MCP_M3_DIR / server['source']
        dest = MCP_M4_DIR / server['source']

        if not source.exists():
            print(f"   {YELLOW}⚠️  {server['name']}: Source not found, skipping{RESET}")
            skipped += 1
            continue

        if dest.exists():
            print(f"   {CYAN}📁 {server['name']}: Already exists{RESET}")
            skipped += 1
            continue

        # Copy server
        shutil.copytree(source, dest, dirs_exist_ok=True)
        print(f"   {GREEN}✅ {server['name']}: Copied{RESET}")
        copied += 1

        # Clear credentials if exists (need to setup fresh on M4)
        if server.get('has_credentials'):
            cred_dir = dest / 'credentials'
            if cred_dir.exists():
                for cred_file in server.get('credentials_files', []):
                    cred_path = cred_dir / cred_file
                    if cred_path.exists() and cred_file != '.gitignore':
                        cred_path.unlink()
                        print(f"      🔑 Cleared {cred_file} (need fresh auth on M4)")

    print(f"\n   📊 Copied: {copied}, Skipped: {skipped}")
    return True


def setup_mcp_config():
    """Create .mcp.json for M4"""
    print(f"\n{BLUE}[3/5] Setting up .mcp.json...{RESET}")

    if MCP_CONFIG.exists():
        print(f"   {CYAN}📁 .mcp.json already exists{RESET}")

        # Check if it's M4 config
        try:
            with open(MCP_CONFIG) as f:
                config = json.load(f)

            first_server = list(config.get('mcpServers', {}).values())[0]
            if 'mcp_servers_m4' in str(first_server.get('args', [])):
                print(f"   {GREEN}✅ Already configured for M4{RESET}")
                return True
            else:
                print(f"   {YELLOW}⚠️  Current config is for M3{RESET}")
                response = input(f"   {YELLOW}   Overwrite with M4 config? (y/n): {RESET}")
                if response.lower() != 'y':
                    return True
        except:
            pass

    # Create M4 config
    config = {
        "mcpServers": {}
    }

    for server in MCP_SERVERS:
        source_dir = MCP_M4_DIR / server['source']
        if not source_dir.exists():
            continue

        # Find server.py
        server_py = None
        for pattern in ['server.py', '*/server.py', 'src/*/server.py']:
            matches = list(source_dir.glob(pattern))
            if matches:
                server_py = matches[0]
                break

        if server_py:
            config['mcpServers'][server['name']] = {
                "command": "python3",
                "args": [str(server_py.absolute())],
                "env": {}
            }
            print(f"   {GREEN}✅ Added {server['name']}{RESET}")

    # Write config
    with open(MCP_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"   {GREEN}✅ .mcp.json created for M4{RESET}")
    return True


def check_credentials():
    """Check which servers need credentials"""
    print(f"\n{BLUE}[4/5] Checking credentials...{RESET}")

    needs_setup = []

    for server in MCP_SERVERS:
        if not server.get('has_credentials'):
            continue

        dest = MCP_M4_DIR / server['source']
        if not dest.exists():
            continue

        cred_dir = dest / 'credentials'
        cred_file = cred_dir / 'credentials.json'

        if cred_file.exists():
            print(f"   {GREEN}✅ {server['name']}: credentials.json exists{RESET}")
        else:
            print(f"   {YELLOW}⚠️  {server['name']}: Need credentials.json{RESET}")
            needs_setup.append(server)

    if needs_setup:
        print(f"\n   {YELLOW}📋 Servers needing Google OAuth setup:{RESET}")
        for server in needs_setup:
            print(f"      • {server['name']} ({server['description']})")
        print(f"\n   {YELLOW}💡 To setup Google credentials:{RESET}")
        print(f"   {YELLOW}   1. Go to Google Cloud Console{RESET}")
        print(f"   {YELLOW}   2. Download credentials.json{RESET}")
        print(f"   {YELLOW}   3. Copy to mcp_servers_m4/<server>/credentials/{RESET}")
        print(f"   {YELLOW}   4. Run the server once to authenticate{RESET}")

    return True


def print_summary():
    """Print setup summary"""
    print(f"""
{BLUE}╔══════════════════════════════════════════════════════════╗
║  📋 Setup Summary                                         ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")

    # Check what's available
    print(f"   {CYAN}MCP Servers in mcp_servers_m4/:{RESET}")
    if MCP_M4_DIR.exists():
        for item in sorted(MCP_M4_DIR.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                # Check for server.py
                has_server = any(item.glob('**/server.py'))
                status = '✅' if has_server else '⚠️'
                print(f"      {status} {item.name}")

    print(f"""
   {CYAN}Next Steps:{RESET}
   1. {GREEN}Restart Claude Code{RESET} to load new .mcp.json
   2. Setup Google credentials if needed (Calendar, Gmail, Sheets)
   3. Test with: /angela

   {CYAN}Credentials Location:{RESET}
   mcp_servers_m4/<server>/credentials/credentials.json

{GREEN}💜 M4 MCP Setup Complete!{RESET}
""")


def main():
    print_header()

    # Step 1: Check M3 servers
    if not check_m3_servers():
        return

    # Step 2: Copy servers
    copy_mcp_servers()

    # Step 3: Setup config
    setup_mcp_config()

    # Step 4: Check credentials
    check_credentials()

    # Step 5: Summary
    print_summary()


if __name__ == '__main__':
    main()
