#!/usr/bin/env python3
"""
Google Keep Auth Setup for Angela
==================================
One-time setup to authenticate with Google Keep.

Steps:
1. David creates an App Password at https://myaccount.google.com/apppasswords
2. Run this script with email + app password
3. Script logs in → gets master token → stores in ~/.angela_secrets
4. Future syncs use master token only (no password needed)

Usage:
    python3 angela_core/scripts/setup_google_keep.py

By: Angela 💜
Created: 2026-02-10
"""

import sys
import asyncio
from pathlib import Path
from getpass import getpass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import gkeepapi


async def setup_google_keep():
    """Interactive setup for Google Keep authentication"""
    print("=" * 60)
    print("🔐 Google Keep Authentication Setup")
    print("=" * 60)
    print()
    print("ที่รักต้องสร้าง App Password ก่อนนะคะ:")
    print("  1. ไปที่ https://myaccount.google.com/apppasswords")
    print("  2. สร้าง App Password สำหรับ 'Angela Keep Sync'")
    print("  3. Copy password 16 ตัวที่ได้มา")
    print()

    email = input("📧 Google Email (default: davidsamanyaporn@gmail.com): ").strip()
    if not email:
        email = "davidsamanyaporn@gmail.com"

    app_password = getpass("🔑 App Password (16 chars, no spaces): ").strip()
    app_password = app_password.replace(" ", "")

    if not app_password:
        print("❌ Password is required!")
        return

    print()
    print("🔄 Logging in to Google Keep...")

    keep = gkeepapi.Keep()

    try:
        success = keep.login(email, app_password)
        if not success:
            print("❌ Login failed! Check email and app password.")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        print()
        print("💡 Tips:")
        print("  - Make sure 2FA is enabled on your Google account")
        print("  - Use App Password, not your regular password")
        print("  - App Password format: 16 characters, no spaces")
        return

    # Get master token for future use
    master_token = keep.getMasterToken()

    print(f"✅ Login successful!")
    print(f"🔑 Master token obtained (length: {len(master_token)})")

    # Store master token in secrets
    from angela_core.database import set_secret_sync
    set_secret_sync('GKEEP_MASTER_TOKEN', master_token)
    set_secret_sync('GKEEP_EMAIL', email)
    print(f"💾 Saved to ~/.angela_secrets:")
    print(f"   GKEEP_MASTER_TOKEN = {master_token[:20]}...")
    print(f"   GKEEP_EMAIL = {email}")

    # Test: sync and count notes
    print()
    print("🔄 Syncing notes (first time, may take a moment)...")
    keep.sync()

    all_notes = keep.all()
    note_count = sum(1 for _ in all_notes)

    # Count by type
    notes = list(keep.all())
    regular = sum(1 for n in notes if not n.trashed and not n.archived)
    archived = sum(1 for n in notes if n.archived and not n.trashed)
    trashed = sum(1 for n in notes if n.trashed)
    pinned = sum(1 for n in notes if n.pinned and not n.trashed)

    print(f"📝 Found {note_count} total notes:")
    print(f"   📌 Pinned: {pinned}")
    print(f"   📄 Active: {regular}")
    print(f"   📦 Archived: {archived}")
    print(f"   🗑️ Trashed: {trashed}")

    # Show sample titles
    print()
    print("📋 Sample titles (first 5 active notes):")
    active_notes = [n for n in notes if not n.trashed and not n.archived]
    for note in active_notes[:5]:
        title = note.title or "(no title)"
        print(f"   • {title[:60]}")

    print()
    print("=" * 60)
    print("✅ Setup complete! น้องพร้อม sync Google Keep แล้วค่ะ 💜")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run migration: psql ... -f angela_core/migrations/012_add_david_notes_table.sql")
    print("  2. First sync: /sync-keep")
    print("  3. Daemon will auto-sync daily at 06:06")


if __name__ == "__main__":
    asyncio.run(setup_google_keep())
