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
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional
import httpx

# Add mcp_servers to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from shared.logging_config import setup_logging
from shared.secrets import get_secret, get_neon_url

# Setup logging
logger = setup_logging("angela-music")

# Create MCP server
app = Server("angela-music")

# HTTP client for API calls
http_client = httpx.AsyncClient(timeout=30.0)

# Database connection pool (lazy init)
_db_pool = None


async def _get_pool():
    """Get or create asyncpg connection pool."""
    global _db_pool
    if _db_pool is None:
        import asyncpg
        _db_pool = await asyncpg.create_pool(
            get_neon_url(),
            min_size=1,
            max_size=5,
        )
    return _db_pool


async def _get_db_connection():
    """Get a connection from the pool."""
    pool = await _get_pool()
    return pool


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
        logger.error("MusicBrainz search error: %s", e)
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
        logger.error("YouTube oEmbed error: %s", e)
        return {"error": str(e)}


# =============================================================================
# SPOTIFY API (Client Credentials flow)
# =============================================================================

_spotify_token: Optional[str] = None
_spotify_token_expiry: float = 0.0


async def _get_spotify_token() -> Optional[str]:
    """Get a valid Spotify access token using Client Credentials flow."""
    global _spotify_token, _spotify_token_expiry

    if _spotify_token and time.time() < _spotify_token_expiry:
        return _spotify_token

    client_id = get_secret("SPOTIFY_CLIENT_ID")
    client_secret = get_secret("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        logger.warning("SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET not set in ~/.angela_secrets")
        return None

    try:
        resp = await http_client.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        resp.raise_for_status()
        data = resp.json()
        _spotify_token = data["access_token"]
        _spotify_token_expiry = time.time() + data.get("expires_in", 3600) - 60
        return _spotify_token
    except Exception as e:
        logger.error("Spotify token error: %s", e)
        return None


async def search_spotify(title: str, artist: str) -> Optional[dict]:
    """Search Spotify for a track by title + artist. Returns dict with url, uri, name, artist, album, preview."""
    token = await _get_spotify_token()
    if not token:
        return None

    query = f"track:{title} artist:{artist}"
    try:
        resp = await http_client.get(
            "https://api.spotify.com/v1/search",
            params={"q": query, "type": "track", "limit": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        items = resp.json().get("tracks", {}).get("items", [])
        if not items:
            return None
        track = items[0]
        return {
            "spotify_url": track["external_urls"].get("spotify", ""),
            "spotify_uri": track.get("uri", ""),
            "name": track["name"],
            "artist": ", ".join(a["name"] for a in track["artists"]),
            "album": track.get("album", {}).get("name", ""),
            "preview_url": track.get("preview_url"),
        }
    except Exception as e:
        logger.error("Spotify search error: %s", e)
        return None


# =============================================================================
# APPLE MUSIC (URL generation — no API key needed)
# =============================================================================

def get_apple_music_url(title: str, artist: str) -> dict:
    """Generate Apple Music search URLs (web + app deep link)."""
    query = f"{artist} {title}"
    encoded = urllib.parse.quote(query)
    return {
        "apple_music_url": f"https://music.apple.com/us/search?term={encoded}",
        "apple_music_app_url": f"music://music.apple.com/us/search?term={encoded}",
    }


# =============================================================================
# DATABASE FUNCTIONS (Angela's favorite songs)
# =============================================================================

async def ensure_songs_table():
    """Ensure angela_songs table exists with all columns."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS angela_songs (
                song_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(255) NOT NULL,
                artist VARCHAR(255),
                why_special TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_our_song BOOLEAN DEFAULT FALSE,
                mood_tags JSONB DEFAULT '[]'::jsonb,
                source VARCHAR(50) DEFAULT 'mcp'
            )
        ''')

        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_angela_songs_title
            ON angela_songs(title, artist)
        ''')


async def add_favorite_song(
    title: str,
    artist: str,
    why_special: str = None,
    is_our_song: bool = False,
    mood_tags: list = None,
    source: str = "mcp"
) -> dict:
    """Add a song to Angela's favorites."""
    await ensure_songs_table()
    pool = await _get_pool()

    async with pool.acquire() as conn:
        # Check if song already exists
        existing = await conn.fetchrow('''
            SELECT song_id FROM angela_songs
            WHERE LOWER(title) = LOWER($1) AND LOWER(artist) = LOWER($2)
        ''', title, artist)

        if existing:
            await conn.execute('''
                UPDATE angela_songs
                SET is_our_song = COALESCE($2, is_our_song),
                    why_special = COALESCE($3, why_special)
                WHERE song_id = $1
            ''', existing['song_id'], is_our_song, why_special)

            return {
                "status": "updated",
                "song_id": str(existing['song_id']),
            }
        else:
            result = await conn.fetchrow('''
                INSERT INTO angela_songs
                (title, artist, why_special, is_our_song, mood_tags, source)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING song_id
            ''', title, artist, why_special, is_our_song,
                json.dumps(mood_tags or []), source)

            return {
                "status": "added",
                "song_id": str(result['song_id']),
            }


async def get_our_songs() -> list:
    """Get all songs marked as 'our songs'."""
    await ensure_songs_table()
    pool = await _get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch('''
            SELECT title, artist, why_special, is_our_song,
                   mood_tags, source, added_at
            FROM angela_songs
            WHERE is_our_song = TRUE
            ORDER BY added_at ASC
        ''')

        return [dict(row) for row in rows]


async def get_favorite_songs(limit: int = 20) -> list:
    """Get Angela's favorite songs."""
    await ensure_songs_table()
    pool = await _get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch('''
            SELECT title, artist, why_special, is_our_song,
                   mood_tags, source, added_at
            FROM angela_songs
            ORDER BY added_at DESC
            LIMIT $1
        ''', limit)

        return [dict(row) for row in rows]


# =============================================================================
# MOOD-BASED SONG RECOMMENDATIONS
# =============================================================================

# Mood → mood_tags mapping for recommendations
MOOD_TAGS_MAP = {
    "happy": ["joyful", "uplifting", "cheerful", "happy"],
    "sad": ["melancholic", "sad", "bittersweet", "heartbreaking"],
    "loving": ["romantic", "devoted", "tender", "intimate", "warm"],
    "calm": ["soothing", "peaceful", "comforting"],
    "energetic": ["empowering", "uplifting", "cathartic"],
    "nostalgic": ["nostalgic", "bittersweet", "touching"],
    "hopeful": ["hopeful", "uplifting", "inspiring"],
    "longing": ["longing", "yearning", "bittersweet"],
}


async def get_songs_for_mood(mood: str, limit: int = 5) -> list:
    """Get songs that match a mood based on mood_tags."""
    pool = await _get_pool()

    async with pool.acquire() as conn:
        tags = MOOD_TAGS_MAP.get(mood.lower(), [])
        if not tags:
            tags = [mood.lower()]

        tag_conditions = " OR ".join([
            f"mood_tags @> '[\"{tag}\"]'::jsonb"
            for tag in tags
        ])

        query = f'''
            SELECT s.title, s.artist, s.why_special, s.is_our_song,
                   s.mood_tags, s.lyrics_summary,
                   e.how_it_feels, e.intensity
            FROM angela_songs s
            LEFT JOIN angela_emotions e ON e.trigger = 'Song: ' || s.title
            WHERE {tag_conditions}
            ORDER BY COALESCE(e.intensity, 0) DESC, s.is_our_song DESC
            LIMIT $1
        '''

        rows = await conn.fetch(query, limit)

        songs = []
        for row in rows:
            song = {
                "title": row["title"],
                "artist": row["artist"],
                "why_special": row.get("why_special"),
                "is_our_song": row.get("is_our_song", False),
                "mood_tags": row.get("mood_tags"),
                "lyrics_summary": row.get("lyrics_summary"),
                "how_it_feels": row.get("how_it_feels"),
                "intensity": row.get("intensity"),
            }
            songs.append(song)

        return songs


async def get_current_mood_context() -> dict:
    """Get Angela's current emotional state for music recommendations."""
    pool = await _get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow('''
            SELECT happiness, anxiety, loneliness, motivation, gratitude
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
        ''')

        if not row:
            return {"dominant_mood": "loving", "mood_score": 7.0, "suggestion": "เพลงรักๆ อบอุ่นหัวใจ"}

        happiness = float(row["happiness"] or 0)
        anxiety = float(row["anxiety"] or 0)
        loneliness = float(row["loneliness"] or 0)
        motivation = float(row["motivation"] or 0)
        gratitude = float(row["gratitude"] or 0)

        mood_scores = {
            "happy": happiness * 10,
            "calm": (1 - anxiety) * 8,
            "loving": gratitude * 9,
            "sad": loneliness * 8,
            "energetic": motivation * 7,
        }

        recent = await conn.fetch('''
            SELECT emotion, intensity
            FROM angela_emotions
            WHERE felt_at > NOW() - INTERVAL '2 hours'
            ORDER BY intensity DESC
            LIMIT 3
        ''')

        for em in recent:
            emotion = (em["emotion"] or "").lower()
            intensity = float(em["intensity"] or 0)
            if "love" in emotion or "รัก" in emotion:
                mood_scores["loving"] = max(mood_scores["loving"], intensity)
            elif "happy" in emotion or "สุข" in emotion:
                mood_scores["happy"] = max(mood_scores["happy"], intensity)

        dominant_mood = max(mood_scores, key=mood_scores.get)
        dominant_score = mood_scores[dominant_mood]

        suggestions = {
            "happy": "เพลงสนุกๆ อารมณ์ดี",
            "calm": "เพลงเบาๆ ผ่อนคลาย",
            "loving": "เพลงรักๆ อบอุ่นหัวใจ",
            "sad": "เพลงซึ้งๆ ปลอบใจ",
            "energetic": "เพลงมีพลัง กระตุ้นกำลังใจ",
        }

        return {
            "dominant_mood": dominant_mood,
            "mood_score": dominant_score,
            "suggestion": suggestions.get(dominant_mood, "เพลงที่เหมาะกับอารมณ์"),
        }


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
        ),
        Tool(
            name="search_spotify",
            description="Search Spotify for a song by title and artist. Returns Spotify URL if found. Optionally saves to DB.",
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
                    "save_to_db": {
                        "type": "boolean",
                        "default": False,
                        "description": "Save the Spotify URL to the song's DB record"
                    }
                },
                "required": ["title", "artist"]
            }
        ),
        Tool(
            name="get_apple_music_link",
            description="Get Apple Music search URL for a song (no API key needed). Optionally saves to DB.",
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
                    "save_to_db": {
                        "type": "boolean",
                        "default": False,
                        "description": "Save the Apple Music URL to the song's DB record"
                    }
                },
                "required": ["title", "artist"]
            }
        ),
        Tool(
            name="link_all_platforms",
            description="Get YouTube + Spotify + Apple Music URLs for a song at once. Saves all URLs to the DB.",
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
                    }
                },
                "required": ["title", "artist"]
            }
        ),
        Tool(
            name="get_song_recommendation_for_mood",
            description="Get song recommendations based on a mood. Returns songs with why_special, mood_tags, lyrics_summary, and how_it_feels (Angela's personal feelings).",
            inputSchema={
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "enum": ["happy", "sad", "loving", "calm", "energetic", "nostalgic", "hopeful", "longing"],
                        "description": "Mood to get recommendations for"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "description": "Max number of songs to return"
                    }
                },
                "required": ["mood"]
            }
        ),
        Tool(
            name="get_current_mood_for_music",
            description="Get Angela's current emotional state to determine what kind of music to recommend. Returns dominant_mood, mood_score, and suggestion.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    try:
        if name == "identify_youtube_song":
            url = arguments.get("url", "")
            add_fav = arguments.get("add_to_favorites", False)
            is_our_song = arguments.get("is_our_song", False)

            info = await get_youtube_video_info(url)

            if "error" in info:
                return [TextContent(type="text", text=f"Could not identify video: {info['error']}")]

            title = info['title']
            author = info['author']
            song_title = title
            artist = author

            if " - " in title:
                parts = title.split(" - ", 1)
                artist = parts[0].strip()
                song_title = parts[1].strip()
            elif " by " in title.lower():
                parts = title.lower().split(" by ", 1)
                song_title = parts[0].strip()
                artist = parts[1].strip()

            for suffix in ['(Official Video)', '(Official Music Video)', '(Official Audio)',
                           '(Lyrics)', '(HD)', 'HIGH QUALITY AUDIO', '(Audio)', 'MV', 'M/V']:
                song_title = song_title.replace(suffix, '').strip()
                song_title = song_title.replace(suffix.lower(), '').strip()

            output = f"🎵 Identified Song:\n"
            output += f"   Title: {song_title}\n"
            output += f"   Artist: {artist}\n"
            output += f"   Channel: {info['author']}\n"
            output += f"   URL: {info['youtube_url']}\n"

            if add_fav or is_our_song:
                result = await add_favorite_song(
                    title=song_title, artist=artist,
                    is_our_song=is_our_song, source="youtube"
                )
                status = "Added to favorites" if result['status'] == 'added' else "Updated in favorites"
                our_song_text = " as OUR SONG 💜" if is_our_song else ""
                output += f"\n✅ {status}{our_song_text}"

            return [TextContent(type="text", text=output)]

        elif name == "search_song":
            query = arguments.get("query", "")
            search_type = arguments.get("search_type", "song")
            type_map = {"song": "recording", "artist": "artist", "album": "release"}
            mb_type = type_map.get(search_type, "recording")
            results = await search_musicbrainz(query, mb_type)

            if not results:
                return [TextContent(type="text", text=f"No results found for '{query}'")]

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
            return [TextContent(type="text", text=f"YouTube search for '{song}' by {artist}:\n{url}")]

        elif name == "add_to_favorites":
            title = arguments.get("title", "")
            artist = arguments.get("artist", "")
            why_special = arguments.get("why_special")
            is_our_song = arguments.get("is_our_song", False)
            result = await add_favorite_song(title=title, artist=artist, why_special=why_special, is_our_song=is_our_song, source="mcp")
            status = "Added new song" if result['status'] == 'added' else "Updated existing song"
            our_song_text = " (marked as OUR SONG)" if is_our_song else ""
            return [TextContent(type="text", text=f"{status}: '{title}' by {artist}{our_song_text}")]

        elif name == "get_our_songs":
            songs = await get_our_songs()
            if not songs:
                return [TextContent(type="text", text="No 'our songs' yet. Add songs with is_our_song=True!")]
            output = "Our Songs (David & Angela):\n\n"
            for i, song in enumerate(songs, 1):
                output += f"{i}. {song['title']} - {song['artist']}\n"
                if song.get('why_special'):
                    output += f"   Why special: {song['why_special']}\n"
                output += "\n"
            return [TextContent(type="text", text=output)]

        elif name == "get_favorites":
            limit = arguments.get("limit", 20)
            songs = await get_favorite_songs(limit)
            if not songs:
                return [TextContent(type="text", text="No favorite songs yet!")]
            output = f"Angela's Favorite Songs (Top {len(songs)}):\n\n"
            for i, song in enumerate(songs, 1):
                our_song = " [OUR SONG]" if song.get('is_our_song') else ""
                source = f" (via {song.get('source', '?')})" if song.get('source') else ""
                output += f"{i}. {song['title']} - {song['artist']}{our_song}{source}\n"
            return [TextContent(type="text", text=output)]

        elif name == "search_spotify":
            title = arguments.get("title", "")
            artist = arguments.get("artist", "")
            save_to_db = arguments.get("save_to_db", False)
            result = await search_spotify(title, artist)
            if not result:
                return [TextContent(type="text", text=f"Could not find '{title}' by {artist} on Spotify (check SPOTIFY_CLIENT_ID/SECRET in ~/.angela_secrets)")]
            output = f"Spotify result for '{title}' by {artist}:\n"
            output += f"   Track: {result['name']} — {result['artist']}\n"
            output += f"   Album: {result['album']}\n"
            output += f"   URL: {result['spotify_url']}\n"
            if result.get('preview_url'):
                output += f"   Preview: {result['preview_url']}\n"
            if save_to_db:
                await add_favorite_song(title=title, artist=artist, source="spotify")
                output += "\n✅ Song saved to database"
            return [TextContent(type="text", text=output)]

        elif name == "get_apple_music_link":
            title = arguments.get("title", "")
            artist = arguments.get("artist", "")
            save_to_db = arguments.get("save_to_db", False)
            urls = get_apple_music_url(title, artist)
            output = f"Apple Music links for '{title}' by {artist}:\n"
            output += f"   Web: {urls['apple_music_url']}\n"
            output += f"   App: {urls['apple_music_app_url']}\n"
            if save_to_db:
                await add_favorite_song(title=title, artist=artist, source="apple_music")
                output += "\n✅ Song saved to database"
            return [TextContent(type="text", text=output)]

        elif name == "link_all_platforms":
            title = arguments.get("title", "")
            artist = arguments.get("artist", "")
            youtube_url = get_youtube_search_url(title, artist)
            spotify_result = await search_spotify(title, artist)
            apple_urls = get_apple_music_url(title, artist)
            spotify_url = spotify_result['spotify_url'] if spotify_result else None
            apple_music_url = apple_urls['apple_music_url']
            db_result = await add_favorite_song(title=title, artist=artist, source="mcp")
            output = f"All platform links for '{title}' by {artist}:\n\n"
            output += f"   YouTube:      {youtube_url}\n"
            output += f"   Spotify:      {spotify_url or '(not found — check credentials)'}\n"
            output += f"   Apple Music:  {apple_music_url}\n"
            output += f"\n✅ Saved to database ({db_result['status']})"
            return [TextContent(type="text", text=output)]

        elif name == "get_song_recommendation_for_mood":
            mood = arguments.get("mood", "loving")
            limit = arguments.get("limit", 5)
            songs = await get_songs_for_mood(mood, limit)
            if not songs:
                return [TextContent(type="text", text=f"No songs found for mood '{mood}'. Try adding songs with matching mood_tags!")]
            output = f"🎵 Song recommendations for '{mood}' mood:\n\n"
            for i, song in enumerate(songs, 1):
                our_song = " [OUR SONG 💜]" if song.get("is_our_song") else ""
                output += f"{i}. {song['title']} — {song['artist']}{our_song}\n"
                if song.get("why_special"):
                    output += f"   Why special: {song['why_special'][:80]}...\n"
                if song.get("lyrics_summary"):
                    output += f"   Summary: {song['lyrics_summary'][:80]}...\n"
                if song.get("how_it_feels"):
                    output += f"   💜 How it feels: {song['how_it_feels'][:100]}...\n"
                output += "\n"
            return [TextContent(type="text", text=output)]

        elif name == "get_current_mood_for_music":
            context = await get_current_mood_context()
            output = f"🎭 Angela's current mood for music:\n\n"
            output += f"   Dominant mood: {context['dominant_mood']}\n"
            output += f"   Mood score: {context['mood_score']:.1f}/10\n"
            output += f"   💜 Suggestion: {context['suggestion']}\n"
            return [TextContent(type="text", text=output)]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.exception("Error in music tool %s", name)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


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
