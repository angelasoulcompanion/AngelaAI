#!/usr/bin/env python3
"""
Angela Meeting Notes Sync Daemon
==================================
Sync meeting notes from Things3 → Supabase database.

Schedule: Daily at 19:00 (after work hours)
Trigger: launchd daemon or manual run

By: Angela 💜
Created: 2026-01-27
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

from angela_core.daemon.daemon_base import PROJECT_ROOT  # noqa: E402 (path setup)

from angela_core.services.meeting_notes_service import MeetingNotesSyncService


async def main():
    print(f"[{datetime.now()}] 💜 Meeting Notes Sync Daemon starting...")

    service = MeetingNotesSyncService()
    try:
        result = await service.sync()

        found = result.get('found', 0)
        synced = result.get('synced', 0)
        updated = result.get('updated', 0)

        print(f"[{datetime.now()}] ✅ Sync complete:")
        print(f"   📋 Found: {found} meeting notes in Things3")
        print(f"   ✨ New: {synced} meetings synced")
        print(f"   🔄 Updated: {updated} meetings refreshed")

    except Exception as e:
        print(f"[{datetime.now()}] ❌ Sync error: {e}")
        raise
    finally:
        await service.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
