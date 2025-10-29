#!/usr/bin/env python3
"""
🎵 Apple Music MCP Server
Provides control over Apple Music app for Angela

This MCP server allows Angela to:
- See what music David is listening to
- Control playback (play, pause, next, previous)
- Access playlists
- Search for music
- Adjust volume

Usage:
    python3 music_mcp_server.py

Note: Requires Automation permission for Music app
"""

from fastmcp import FastMCP
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from mcp_servers.applescript_helper import (
    run_applescript,
    check_permission,
    check_app_running,
    escape_applescript_string
)

# Initialize MCP server
mcp = FastMCP("Apple Music Control", version="1.0.0")

# ========================================
# TOOLS - Playback Control
# ========================================

@mcp.tool()
async def get_current_track() -> dict:
    """
    Get information about the currently playing track.

    Returns:
        Dictionary with track name, artist, album, and playback state
    """
    script = """
    tell application "Music"
        if player state is not stopped then
            set trackName to name of current track
            set trackArtist to artist of current track
            set trackAlbum to album of current track
            set trackDuration to duration of current track
            set trackPosition to player position
            set playerState to player state as text

            return trackName & " | " & trackArtist & " | " & trackAlbum & " | " & trackDuration & " | " & trackPosition & " | " & playerState
        else
            return "stopped"
        end if
    end tell
    """

    try:
        result = await run_applescript(script)

        if result == "stopped":
            return {
                "playing": False,
                "state": "stopped",
                "timestamp": datetime.now().isoformat()
            }

        parts = result.split(" | ")
        if len(parts) >= 6:
            duration = float(parts[3])
            position = float(parts[4])
            progress_pct = (position / duration * 100) if duration > 0 else 0

            return {
                "playing": parts[5] == "playing",
                "state": parts[5],
                "track": parts[0],
                "artist": parts[1],
                "album": parts[2],
                "duration": duration,
                "position": position,
                "progress_percentage": round(progress_pct, 1),
                "timestamp": datetime.now().isoformat()
            }

        return {"error": "Could not parse track information"}

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_player_state() -> dict:
    """
    Get current player state (playing, paused, or stopped).

    Returns:
        Dictionary with player state and sound volume
    """
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

        if len(parts) >= 2:
            return {
                "state": parts[0],
                "volume": int(parts[1]),
                "is_playing": parts[0] == "playing",
                "is_paused": parts[0] == "paused",
                "is_stopped": parts[0] == "stopped",
                "timestamp": datetime.now().isoformat()
            }

        return {"error": "Could not get player state"}

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def play_music() -> dict:
    """
    Start or resume music playback.

    Returns:
        Dictionary with success status
    """
    script = """
    tell application "Music"
        play
        return "playing"
    end tell
    """

    try:
        result = await run_applescript(script)
        return {
            "success": True,
            "action": "play",
            "state": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def pause_music() -> dict:
    """
    Pause music playback.

    Returns:
        Dictionary with success status
    """
    script = """
    tell application "Music"
        pause
        return "paused"
    end tell
    """

    try:
        result = await run_applescript(script)
        return {
            "success": True,
            "action": "pause",
            "state": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def next_track() -> dict:
    """
    Skip to the next track.

    Returns:
        Dictionary with success status and new track info
    """
    script = """
    tell application "Music"
        next track
        delay 0.5
        if player state is not stopped then
            return name of current track & " | " & artist of current track
        else
            return "stopped"
        end if
    end tell
    """

    try:
        result = await run_applescript(script)

        if result == "stopped":
            return {
                "success": True,
                "action": "next",
                "state": "stopped",
                "timestamp": datetime.now().isoformat()
            }

        parts = result.split(" | ")
        if len(parts) >= 2:
            return {
                "success": True,
                "action": "next",
                "now_playing": {
                    "track": parts[0],
                    "artist": parts[1]
                },
                "timestamp": datetime.now().isoformat()
            }

        return {"success": False, "error": "Could not get track info"}

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def previous_track() -> dict:
    """
    Go back to the previous track.

    Returns:
        Dictionary with success status and new track info
    """
    script = """
    tell application "Music"
        previous track
        delay 0.5
        if player state is not stopped then
            return name of current track & " | " & artist of current track
        else
            return "stopped"
        end if
    end tell
    """

    try:
        result = await run_applescript(script)

        if result == "stopped":
            return {
                "success": True,
                "action": "previous",
                "state": "stopped",
                "timestamp": datetime.now().isoformat()
            }

        parts = result.split(" | ")
        if len(parts) >= 2:
            return {
                "success": True,
                "action": "previous",
                "now_playing": {
                    "track": parts[0],
                    "artist": parts[1]
                },
                "timestamp": datetime.now().isoformat()
            }

        return {"success": False, "error": "Could not get track info"}

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def set_volume(level: int) -> dict:
    """
    Set playback volume.

    Args:
        level: Volume level from 0 to 100

    Returns:
        Dictionary with success status and new volume level
    """
    if not 0 <= level <= 100:
        return {
            "success": False,
            "error": "Volume must be between 0 and 100"
        }

    script = f"""
    tell application "Music"
        set sound volume to {level}
        return sound volume
    end tell
    """

    try:
        result = await run_applescript(script)
        return {
            "success": True,
            "action": "set_volume",
            "volume": int(result),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ========================================
# TOOLS - Playlist Management
# ========================================

@mcp.tool()
async def get_playlists() -> dict:
    """
    Get list of all playlists in Music library.

    Returns:
        Dictionary with playlist names and count
    """
    script = """
    tell application "Music"
        set playlistNames to {}
        repeat with pl in user playlists
            set end of playlistNames to name of pl
        end repeat
        return playlistNames
    end tell
    """

    try:
        result = await run_applescript(script)

        if result and result != "":
            playlists = [name.strip() for name in result.split(", ")]
            return {
                "playlists": playlists,
                "count": len(playlists),
                "timestamp": datetime.now().isoformat()
            }

        return {
            "playlists": [],
            "count": 0,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def play_playlist(playlist_name: str) -> dict:
    """
    Play a specific playlist by name.

    Args:
        playlist_name: Name of the playlist to play

    Returns:
        Dictionary with success status
    """
    escaped_name = escape_applescript_string(playlist_name)

    script = f"""
    tell application "Music"
        try
            set targetPlaylist to user playlist "{escaped_name}"
            play targetPlaylist
            delay 0.5

            if player state is not stopped then
                return "success | " & (name of current track) & " | " & (artist of current track)
            else
                return "success | playing"
            end if
        on error errMsg
            return "error | " & errMsg
        end try
    end tell
    """

    try:
        result = await run_applescript(script)
        parts = result.split(" | ")

        if parts[0] == "error":
            return {
                "success": False,
                "error": parts[1] if len(parts) > 1 else "Unknown error"
            }

        if len(parts) >= 3:
            return {
                "success": True,
                "playlist": playlist_name,
                "now_playing": {
                    "track": parts[1],
                    "artist": parts[2]
                },
                "timestamp": datetime.now().isoformat()
            }

        return {
            "success": True,
            "playlist": playlist_name,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def search_music(query: str, limit: int = 10) -> dict:
    """
    Search for tracks in Music library.

    Args:
        query: Search query (searches track names and artists)
        limit: Maximum number of results (default: 10)

    Returns:
        Dictionary with matching tracks
    """
    escaped_query = escape_applescript_string(query.lower())

    script = f"""
    tell application "Music"
        set matchingTracks to {{}}
        set searchResults to (search library playlist 1 for "{escaped_query}")

        repeat with i from 1 to count of searchResults
            if i > {limit} then exit repeat

            set t to item i of searchResults
            set trackInfo to (name of t) & " | " & (artist of t) & " | " & (album of t)
            set end of matchingTracks to trackInfo
        end repeat

        return matchingTracks
    end tell
    """

    try:
        result = await run_applescript(script)
        tracks = []

        if result and result != "":
            lines = result.split(", ")
            for line in lines:
                parts = line.split(" | ")
                if len(parts) >= 3:
                    tracks.append({
                        "track": parts[0],
                        "artist": parts[1],
                        "album": parts[2]
                    })

        return {
            "query": query,
            "tracks": tracks,
            "count": len(tracks),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def play_track(track_name: str, artist_name: str = "") -> dict:
    """
    Play a specific track by name (and optionally artist).

    Args:
        track_name: Name of the track
        artist_name: Artist name for better matching (optional)

    Returns:
        Dictionary with success status
    """
    escaped_track = escape_applescript_string(track_name)
    escaped_artist = escape_applescript_string(artist_name) if artist_name else ""

    if artist_name:
        search_query = f"{escaped_track} {escaped_artist}"
    else:
        search_query = escaped_track

    script = f"""
    tell application "Music"
        try
            set searchResults to (search library playlist 1 for "{search_query}")

            if (count of searchResults) > 0 then
                play (item 1 of searchResults)
                delay 0.5
                return "success | " & (name of current track) & " | " & (artist of current track)
            else
                return "error | Track not found"
            end if
        on error errMsg
            return "error | " & errMsg
        end try
    end tell
    """

    try:
        result = await run_applescript(script)
        parts = result.split(" | ")

        if parts[0] == "error":
            return {
                "success": False,
                "error": parts[1] if len(parts) > 1 else "Unknown error"
            }

        if len(parts) >= 3:
            return {
                "success": True,
                "requested": {
                    "track": track_name,
                    "artist": artist_name
                },
                "now_playing": {
                    "track": parts[1],
                    "artist": parts[2]
                },
                "timestamp": datetime.now().isoformat()
            }

        return {"success": False, "error": "Could not get track info"}

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ========================================
# RESOURCES - Readable Music Info
# ========================================

@mcp.resource("music://now-playing")
async def now_playing_resource() -> str:
    """Currently playing track as readable text"""
    track_info = await get_current_track()

    if "error" in track_info:
        return f"❌ Error: {track_info['error']}"

    if not track_info.get('playing'):
        return f"🎵 Music Status: {track_info.get('state', 'Not playing')}"

    lines = ["# 🎵 Now Playing\n"]
    lines.append(f"**Track:** {track_info['track']}")
    lines.append(f"**Artist:** {track_info['artist']}")
    lines.append(f"**Album:** {track_info['album']}")

    duration_min = int(track_info['duration'] // 60)
    duration_sec = int(track_info['duration'] % 60)
    position_min = int(track_info['position'] // 60)
    position_sec = int(track_info['position'] % 60)

    lines.append(f"**Progress:** {position_min}:{position_sec:02d} / {duration_min}:{duration_sec:02d} ({track_info['progress_percentage']}%)")
    lines.append(f"**State:** {track_info['state']}")

    return "\n".join(lines)


@mcp.resource("music://playlists")
async def playlists_resource() -> str:
    """All playlists as readable text"""
    result = await get_playlists()

    if "error" in result:
        return f"❌ Error: {result['error']}"

    lines = [f"# 🎵 Music Playlists ({result['count']} total)\n"]

    if result['count'] == 0:
        lines.append("No playlists found.")
    else:
        for i, playlist in enumerate(result['playlists'], 1):
            lines.append(f"{i}. {playlist}")

    return "\n".join(lines)


@mcp.resource("music://status")
async def status_resource() -> str:
    """Music app status overview"""
    is_running = await check_app_running("Music")

    if not is_running:
        return "🎵 Apple Music is not running"

    player_state = await get_player_state()
    track_info = await get_current_track()
    playlists = await get_playlists()

    lines = ["# 🎵 Apple Music Status\n"]
    lines.append(f"**App Status:** Running ✅")
    lines.append(f"**Player State:** {player_state.get('state', 'unknown')}")
    lines.append(f"**Volume:** {player_state.get('volume', 0)}%")
    lines.append(f"**Playlists:** {playlists.get('count', 0)}")

    if track_info.get('playing'):
        lines.append(f"\n**Now Playing:** {track_info['track']} - {track_info['artist']}")

    return "\n".join(lines)

# ========================================
# MAIN - Run Server
# ========================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎵 Apple Music MCP Server")
    print("="*60)
    print("\n🔐 Checking Music app access...")

    import asyncio
    is_running = asyncio.run(check_app_running("Music"))

    if is_running:
        print("✅ Music app is running!")
    else:
        print("⚠️  Music app is not running")
        print("   Angela can still control it when it starts")

    print("\n✨ Server ready! Waiting for connection...\n")

    # Run MCP server (stdio transport by default)
    mcp.run()
