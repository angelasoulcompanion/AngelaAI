#!/usr/bin/env python3
"""
Angela Music MCP Server
=======================

MCP server for music features - search songs, get lyrics, find YouTube links,
and manage Angela's favorite songs.

Created: 2025-12-29
By: Angela for David
"""

import asyncio
import json
import logging
import urllib.parse
from datetime import datetime
from typing import Optional
import httpx

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("angela-music")

# Create MCP server
app = Server("angela-music")

# HTTP client for API calls
http_client = httpx.AsyncClient(timeout=30.0)


# =============================================================================
# MUSICBRAINZ API (Free, no key required)
# =============================================================================

async def search_musicbrainz(query: str, search_type: str = "recording") -> list:
    """
    Search MusicBrainz for songs/artists/albums.

    search_type: recording (songs), artist, release (albums)
    """
    base_url = "https://musicbrainz.org/ws/2"

    headers = {
        "User-Agent": "AngelaMusicMCP/1.0 (angelasoulcompanion@gmail.com)",
        "Accept": "application/json"
    }

    params = {
        "query": query,
        "fmt": "json",
        "limit": 10
    }

    try:
        url = f"{base_url}/{search_type}"
        response = await http_client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        results = []

        if search_type == "recording":
            for item in data.get("recordings", []):
                artist = item.get("artist-credit", [{}])[0].get("name", "Unknown")
                results.append({
                    "title": item.get("title", ""),
                    "artist": artist,
                    "id": item.get("id", ""),
                    "length": item.get("length", 0),
                    "score": item.get("score", 0)
                })
        elif search_type == "artist":
            for item in data.get("artists", []):
                results.append({
                    "name": item.get("name", ""),
                    "id": item.get("id", ""),
                    "country": item.get("country", ""),
                    "type": item.get("type", ""),
                    "score": item.get("score", 0)
                })
        elif search_type == "release":
            for item in data.get("releases", []):
                artist = item.get("artist-credit", [{}])[0].get("name", "Unknown")
                results.append({
                    "title": item.get("title", ""),
                    "artist": artist,
                    "id": item.get("id", ""),
                    "date": item.get("date", ""),
                    "country": item.get("country", ""),
                    "score": item.get("score", 0)
                })

        return results

    except Exception as e:
        logger.error(f"MusicBrainz search error: {e}")
        return []


# =============================================================================
# YOUTUBE FUNCTIONS (No API key required)
# =============================================================================

def get_youtube_search_url(song: str, artist: str) -> str:
    """Generate YouTube search URL for a song."""
    query = f"{artist} {song} official"
    encoded = urllib.parse.quote(query)
    return f"https://www.youtube.com/results?search_query={encoded}"


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats."""
    import re

    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]+)',
        r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


async def get_youtube_video_info(url: str) -> dict:
    """
    Get video info from YouTube using oEmbed API (free, no key required).

    Returns: {title, author, video_id, youtube_url}
    """
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Could not extract video ID from URL"}

    # Use oEmbed API
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"

    try:
        response = await http_client.get(oembed_url)
        response.raise_for_status()
        data = response.json()

        return {
            "title": data.get("title", "Unknown"),
            "author": data.get("author_name", "Unknown"),
            "video_id": video_id,
            "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        }
    except Exception as e:
        logger.error(f"YouTube oEmbed error: {e}")
        return {"error": str(e)}


# =============================================================================
# DATABASE FUNCTIONS (Angela's favorite songs)
# =============================================================================

# Neon Cloud Database URL (San Junipero - shared between M3 & M4)
NEON_DATABASE_URL = "postgresql://neondb_owner:npg_mXbQ5jKhN3zt@ep-withered-bush-a164h0b8-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"


async def get_db_connection():
    """Get database connection - uses Neon Cloud (San Junipero)."""
    import asyncpg
    return await asyncpg.connect(NEON_DATABASE_URL)


async def ensure_songs_table():
    """Ensure angela_songs table exists."""
    conn = await get_db_connection()
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS angela_songs (
                song_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                title VARCHAR(255) NOT NULL,
                artist VARCHAR(255),
                album VARCHAR(255),
                youtube_url TEXT,
                why_special TEXT,
                added_by VARCHAR(50) DEFAULT 'david',
                times_mentioned INTEGER DEFAULT 1,
                first_mentioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_mentioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_our_song BOOLEAN DEFAULT FALSE,
                mood_tags JSONB DEFAULT '[]'::jsonb
            )
        ''')

        # Create index
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_angela_songs_title
            ON angela_songs(title, artist)
        ''')
    finally:
        await conn.close()


async def add_favorite_song(
    title: str,
    artist: str,
    why_special: str = None,
    youtube_url: str = None,
    is_our_song: bool = False,
    mood_tags: list = None
) -> dict:
    """Add a song to Angela's favorites."""
    await ensure_songs_table()
    conn = await get_db_connection()

    try:
        # Check if song already exists
        existing = await conn.fetchrow('''
            SELECT song_id, times_mentioned FROM angela_songs
            WHERE LOWER(title) = LOWER($1) AND LOWER(artist) = LOWER($2)
        ''', title, artist)

        if existing:
            # Update existing
            await conn.execute('''
                UPDATE angela_songs
                SET times_mentioned = times_mentioned + 1,
                    last_mentioned_at = CURRENT_TIMESTAMP,
                    is_our_song = COALESCE($2, is_our_song),
                    why_special = COALESCE($3, why_special)
                WHERE song_id = $1
            ''', existing['song_id'], is_our_song, why_special)

            return {
                "status": "updated",
                "song_id": str(existing['song_id']),
                "times_mentioned": existing['times_mentioned'] + 1
            }
        else:
            # Insert new
            result = await conn.fetchrow('''
                INSERT INTO angela_songs
                (title, artist, youtube_url, why_special, is_our_song, mood_tags)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING song_id
            ''', title, artist, youtube_url, why_special, is_our_song,
                json.dumps(mood_tags or []))

            return {
                "status": "added",
                "song_id": str(result['song_id']),
                "times_mentioned": 1
            }
    finally:
        await conn.close()


async def get_our_songs() -> list:
    """Get all songs marked as 'our songs'."""
    await ensure_songs_table()
    conn = await get_db_connection()

    try:
        rows = await conn.fetch('''
            SELECT title, artist, why_special, youtube_url,
                   times_mentioned, first_mentioned_at
            FROM angela_songs
            WHERE is_our_song = TRUE
            ORDER BY first_mentioned_at ASC
        ''')

        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_favorite_songs(limit: int = 20) -> list:
    """Get Angela's favorite songs."""
    await ensure_songs_table()
    conn = await get_db_connection()

    try:
        rows = await conn.fetch('''
            SELECT title, artist, why_special, youtube_url,
                   times_mentioned, is_our_song, mood_tags
            FROM angela_songs
            ORDER BY times_mentioned DESC, last_mentioned_at DESC
            LIMIT $1
        ''', limit)

        return [dict(row) for row in rows]
    finally:
        await conn.close()


# =============================================================================
# MCP TOOLS
# =============================================================================

@app.list_tools()
async def list_tools():
    """List available music tools."""
    return [
        Tool(
            name="identify_youtube_song",
            description="Identify song/video from a YouTube URL. Use this when David sends a YouTube link to know what song it is.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "YouTube URL (supports youtube.com/watch, youtu.be, shorts)"
                    },
                    "add_to_favorites": {
                        "type": "boolean",
                        "default": False,
                        "description": "Also add this song to Angela's favorites"
                    },
                    "is_our_song": {
                        "type": "boolean",
                        "default": False,
                        "description": "Mark as 'our song' with special meaning"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="search_song",
            description="Search for songs by title, artist, or lyrics. Returns song info from MusicBrainz.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (song title, artist name, or keywords)"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["song", "artist", "album"],
                        "default": "song",
                        "description": "Type of search"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_youtube_link",
            description="Get YouTube search URL for a song",
            inputSchema={
                "type": "object",
                "properties": {
                    "song": {
                        "type": "string",
                        "description": "Song title"
                    },
                    "artist": {
                        "type": "string",
                        "description": "Artist name"
                    }
                },
                "required": ["song", "artist"]
            }
        ),
        Tool(
            name="add_to_favorites",
            description="Add a song to Angela's favorite songs in the database",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Song title"
                    },
                    "artist": {
                        "type": "string",
                        "description": "Artist name"
                    },
                    "why_special": {
                        "type": "string",
                        "description": "Why this song is special to us"
                    },
                    "is_our_song": {
                        "type": "boolean",
                        "default": False,
                        "description": "Mark as 'our song' (special meaning for David & Angela)"
                    },
                    "youtube_url": {
                        "type": "string",
                        "description": "YouTube URL of the song"
                    }
                },
                "required": ["title", "artist"]
            }
        ),
        Tool(
            name="get_our_songs",
            description="Get list of 'our songs' - songs with special meaning for David & Angela",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_favorites",
            description="Get Angela's favorite songs list",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Max number of songs to return"
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    if name == "identify_youtube_song":
        url = arguments.get("url", "")
        add_to_favorites = arguments.get("add_to_favorites", False)
        is_our_song = arguments.get("is_our_song", False)

        # Get video info from YouTube
        info = await get_youtube_video_info(url)

        if "error" in info:
            return [TextContent(
                type="text",
                text=f"Could not identify video: {info['error']}"
            )]

        # Parse title to extract song/artist (common patterns)
        title = info['title']
        author = info['author']

        # Try to extract artist - song from title
        song_title = title
        artist = author

        # Common patterns: "Artist - Song", "Song by Artist", etc.
        if " - " in title:
            parts = title.split(" - ", 1)
            artist = parts[0].strip()
            song_title = parts[1].strip()
        elif " by " in title.lower():
            parts = title.lower().split(" by ", 1)
            song_title = parts[0].strip()
            artist = parts[1].strip()

        # Clean up common suffixes
        for suffix in ['(Official Video)', '(Official Music Video)', '(Official Audio)',
                       '(Lyrics)', '(HD)', 'HIGH QUALITY AUDIO', '(Audio)', 'MV', 'M/V']:
            song_title = song_title.replace(suffix, '').strip()
            song_title = song_title.replace(suffix.lower(), '').strip()

        output = f"🎵 Identified Song:\n"
        output += f"   Title: {song_title}\n"
        output += f"   Artist: {artist}\n"
        output += f"   Channel: {info['author']}\n"
        output += f"   URL: {info['youtube_url']}\n"

        # Optionally add to favorites
        if add_to_favorites or is_our_song:
            result = await add_favorite_song(
                title=song_title,
                artist=artist,
                youtube_url=info['youtube_url'],
                is_our_song=is_our_song
            )
            status = "Added to favorites" if result['status'] == 'added' else "Updated in favorites"
            our_song_text = " as OUR SONG 💜" if is_our_song else ""
            output += f"\n✅ {status}{our_song_text}"

        return [TextContent(type="text", text=output)]

    elif name == "search_song":
        query = arguments.get("query", "")
        search_type = arguments.get("search_type", "song")

        # Map to MusicBrainz types
        type_map = {"song": "recording", "artist": "artist", "album": "release"}
        mb_type = type_map.get(search_type, "recording")

        results = await search_musicbrainz(query, mb_type)

        if not results:
            return [TextContent(
                type="text",
                text=f"No results found for '{query}'"
            )]

        # Format results
        output = f"Search results for '{query}':\n\n"
        for i, item in enumerate(results[:5], 1):
            if search_type == "song":
                length_sec = item.get('length', 0) // 1000 if item.get('length') else 0
                mins, secs = divmod(length_sec, 60)
                duration = f"{mins}:{secs:02d}" if length_sec else "?"
                output += f"{i}. {item['title']} - {item['artist']} ({duration})\n"
            elif search_type == "artist":
                output += f"{i}. {item['name']} ({item.get('country', '?')}) - {item.get('type', 'Artist')}\n"
            elif search_type == "album":
                output += f"{i}. {item['title']} - {item['artist']} ({item.get('date', '?')})\n"

        return [TextContent(type="text", text=output)]

    elif name == "get_youtube_link":
        song = arguments.get("song", "")
        artist = arguments.get("artist", "")

        url = get_youtube_search_url(song, artist)

        return [TextContent(
            type="text",
            text=f"YouTube search for '{song}' by {artist}:\n{url}"
        )]

    elif name == "add_to_favorites":
        title = arguments.get("title", "")
        artist = arguments.get("artist", "")
        why_special = arguments.get("why_special")
        is_our_song = arguments.get("is_our_song", False)
        youtube_url = arguments.get("youtube_url")

        result = await add_favorite_song(
            title=title,
            artist=artist,
            why_special=why_special,
            is_our_song=is_our_song,
            youtube_url=youtube_url
        )

        status = "Added new song" if result['status'] == 'added' else "Updated existing song"
        our_song_text = " (marked as OUR SONG)" if is_our_song else ""

        return [TextContent(
            type="text",
            text=f"{status}: '{title}' by {artist}{our_song_text}\nTimes mentioned: {result['times_mentioned']}"
        )]

    elif name == "get_our_songs":
        songs = await get_our_songs()

        if not songs:
            return [TextContent(
                type="text",
                text="No 'our songs' yet. Add songs with is_our_song=True!"
            )]

        output = "Our Songs (David & Angela):\n\n"
        for i, song in enumerate(songs, 1):
            output += f"{i}. {song['title']} - {song['artist']}\n"
            if song.get('why_special'):
                output += f"   Why special: {song['why_special']}\n"
            if song.get('youtube_url'):
                output += f"   YouTube: {song['youtube_url']}\n"
            output += "\n"

        return [TextContent(type="text", text=output)]

    elif name == "get_favorites":
        limit = arguments.get("limit", 20)
        songs = await get_favorite_songs(limit)

        if not songs:
            return [TextContent(
                type="text",
                text="No favorite songs yet!"
            )]

        output = f"Angela's Favorite Songs (Top {len(songs)}):\n\n"
        for i, song in enumerate(songs, 1):
            our_song = " [OUR SONG]" if song.get('is_our_song') else ""
            output += f"{i}. {song['title']} - {song['artist']}{our_song}\n"
            output += f"   Mentioned {song['times_mentioned']} times\n"

        return [TextContent(type="text", text=output)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run the MCP server."""
    logger.info("Starting Angela Music MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
