#!/usr/bin/env python3
"""
Test script for Calendar and Music MCP servers
"""

import asyncio
import sys
sys.path.insert(0, '.')

from mcp_servers.applescript_helper import (
    run_applescript,
    check_permission,
    check_app_running
)


async def test_calendar():
    """Test Calendar access"""
    print("\n" + "="*60)
    print("📅 Testing Calendar Access")
    print("="*60 + "\n")

    # Check permission
    has_permission = await check_permission("Calendar")
    print(f"✅ Calendar permission: {has_permission}")

    if not has_permission:
        print("⚠️  Please grant Calendar access in System Preferences")
        return

    # Get calendar names
    script = """
    tell application "Calendar"
        set calNames to {}
        repeat with cal in calendars
            set end of calNames to name of cal
        end repeat
        return calNames
    end tell
    """

    try:
        result = await run_applescript(script)
        calendars = [name.strip() for name in result.split(",")]
        print(f"📅 Found {len(calendars)} calendars:")
        for cal in calendars:
            print(f"   - {cal}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # Get today's events
    script = """
    tell application "Calendar"
        set today to current date
        set startOfDay to today
        set time of startOfDay to 0
        set endOfDay to today
        set time of endOfDay to (24 * 60 * 60) - 1

        set eventCount to 0
        repeat with cal in calendars
            set calEvents to (every event of cal whose start date ≥ startOfDay and start date ≤ endOfDay)
            set eventCount to eventCount + (count of calEvents)
        end repeat

        return eventCount
    end tell
    """

    try:
        result = await run_applescript(script)
        print(f"📅 Today's events: {result}")
    except Exception as e:
        print(f"❌ Error getting events: {e}")

    print("\n✅ Calendar tests completed!")


async def test_music():
    """Test Music app access"""
    print("\n" + "="*60)
    print("🎵 Testing Apple Music Access")
    print("="*60 + "\n")

    # Check if Music app is running
    is_running = await check_app_running("Music")
    print(f"🎵 Music app running: {is_running}")

    if not is_running:
        print("⚠️  Music app is not running. Starting it...")
        try:
            await run_applescript('tell application "Music" to activate')
            await asyncio.sleep(2)  # Wait for app to start
            print("✅ Music app started!")
        except Exception as e:
            print(f"❌ Could not start Music app: {e}")
            return

    # Get player state
    script = """
    tell application "Music"
        set playerState to player state as text
        set soundVol to sound volume
        return playerState & " | " & soundVol
    end tell
    """

    try:
        result = await run_applescript(script)
        parts = result.split(" | ")
        print(f"🎵 Player state: {parts[0]}")
        print(f"🔊 Volume: {parts[1]}%")
    except Exception as e:
        print(f"❌ Error getting player state: {e}")

    # Get current track (if playing)
    script = """
    tell application "Music"
        if player state is not stopped then
            return name of current track & " - " & artist of current track
        else
            return "Not playing"
        end if
    end tell
    """

    try:
        result = await run_applescript(script)
        print(f"🎵 Now playing: {result}")
    except Exception as e:
        print(f"❌ Error getting current track: {e}")

    # Get playlists
    script = """
    tell application "Music"
        set playlistNames to {}
        repeat with pl in user playlists
            set end of playlistNames to name of pl
        end repeat
        return count of playlistNames
    end tell
    """

    try:
        result = await run_applescript(script)
        print(f"🎵 Playlists: {result}")
    except Exception as e:
        print(f"❌ Error getting playlists: {e}")

    print("\n✅ Music tests completed!")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 MCP Servers Test Suite")
    print("="*60)

    # Test Calendar
    await test_calendar()

    # Test Music
    await test_music()

    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
