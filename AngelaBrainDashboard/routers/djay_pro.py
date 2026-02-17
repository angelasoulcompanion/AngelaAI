"""djay Pro control endpoints — Angela controls djay Pro app via AppleScript."""
import asyncio
import json
import logging
import random
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from db import get_conn
from helpers.djay_control import (
    is_djay_running,
    launch_djay,
    load_next_track,
    play_pause_deck,
    search_and_load_song,
    toggle_automix,
)
from helpers.mood_config import MOOD_REGISTRY, MOOD_SUMMARIES_TH, MOOD_TO_SEARCH_QUERIES
from helpers.wine_config import WINE_REGISTRY, WINE_MESSAGES, WINE_TO_EMOTION, WINE_CATEGORIES
from helpers.activity_config import ACTIVITY_REGISTRY, ACTIVITY_SEARCH_TERMS, ACTIVITY_SUMMARIES_TH

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/djay-pro", tags=["djay-pro"])

_ITUNES_SEARCH_URL = "https://itunes.apple.com/search"

# --- Song columns (same as music.py) ---
_SONG_COLUMNS = """song_id::text, title, artist,
    why_special, is_our_song, mood_tags, source, added_at, lyrics_summary"""


def _song_row_to_dict(row) -> dict:
    d = dict(row)
    d["song_id"] = str(d.get("song_id", ""))
    tags = d.get("mood_tags")
    if tags is None:
        d["mood_tags"] = []
    elif isinstance(tags, str):
        try:
            d["mood_tags"] = json.loads(tags)
        except (json.JSONDecodeError, TypeError):
            d["mood_tags"] = []
    elif isinstance(tags, list):
        d["mood_tags"] = tags
    else:
        d["mood_tags"] = list(tags)
    return d


# --- Context → mood_tags mapping ---

# Map djay contexts to mood_tags for DB query
_CONTEXT_TO_TAGS: dict[str, list[str]] = {
    "chill": ["calm", "chill", "relaxed", "peaceful"],
    "party": ["happy", "energetic", "excited", "party"],
    "focus": ["focused", "calm", "instrumental"],
    "relax": ["calm", "relaxed", "peaceful", "soothing"],
    "vibe": ["groovy", "funky", "smooth", "cool"],
    "bedtime": ["sleepy", "lullaby", "bedtime", "calm", "peaceful"],
}

# Thai messages for each context
_CONTEXT_MESSAGES: dict[str, str] = {
    "chill": "ชิลล์ๆ สบายๆ น้องเลือกเพลงเบาๆ มาให้ที่รักค่ะ 🧊💜",
    "party": "ปาร์ตี้! น้องเปิดเพลงมันส์ๆ ให้ที่รักเลยค่ะ 🎉💜",
    "focus": "โฟกัส! เพลง instrumental ช่วยสมาธิค่ะ 🎯💜",
    "relax": "ผ่อนคลายนะคะที่รัก น้องเลือกเพลงสงบๆ มาค่ะ 😌💜",
    "vibe": "Vibe ดีมาก! เพลง groovy มี style ให้ที่รักค่ะ 🎧💜",
    "bedtime": "นอนหลับฝันดีนะคะที่รัก น้องเปิดเพลง lullaby ให้ค่ะ 😴💜",
}


# --- Pydantic models ---

class GeneratePlaylistRequest(BaseModel):
    context: str  # wine, chill, party, focus, relax, vibe, bedtime
    sub_context: Optional[str] = None  # wine varietal (e.g. primitivo, merlot)
    count: int = 15


class LoadSongRequest(BaseModel):
    title: str
    artist: str = ""
    deck: int = 1


class PlayPlaylistRequest(BaseModel):
    songs: list[dict]  # [{title, artist}, ...]


# --- iTunes search helper ---

async def _search_itunes(query: str, count: int = 10) -> list[dict]:
    """Search iTunes API and return Angela-format song dicts."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                _ITUNES_SEARCH_URL,
                params={
                    "term": query,
                    "media": "music",
                    "entity": "song",
                    "limit": count,
                    "country": "US",
                },
            )
            if resp.status_code != 200:
                return []
            songs = []
            seen: set[str] = set()
            for item in resp.json().get("results", []):
                track_id = str(item.get("trackId", ""))
                if not track_id or track_id in seen:
                    continue
                seen.add(track_id)
                songs.append({
                    "song_id": f"itunes_{track_id}",
                    "title": item.get("trackName", "Unknown"),
                    "artist": item.get("artistName", "Unknown"),
                    "album": item.get("collectionName"),
                    "artwork_url": (item.get("artworkUrl100") or "").replace("100x100", "300x300"),
                    "preview_url": item.get("previewUrl"),
                    "apple_music_url": item.get("trackViewUrl"),
                    "mood_tags": [],
                    "is_our_song": False,
                    "source": "apple_music",
                    "why_special": None,
                    "lyrics_summary": None,
                })
            return songs
    except Exception as e:
        logger.warning(f"iTunes search failed for '{query}': {e}")
        return []


# --- Endpoints ---

@router.get("/status")
async def djay_status():
    """Check if djay Pro is running."""
    running = await asyncio.to_thread(is_djay_running)
    return {"running": running}


@router.post("/launch")
async def djay_launch():
    """Launch djay Pro app."""
    ok = await asyncio.to_thread(launch_djay)
    return {"success": ok}


@router.post("/generate-playlist")
async def generate_playlist(req: GeneratePlaylistRequest, conn=Depends(get_conn)):
    """Generate a playlist matching the selected context.

    Strategy:
    1. Context → mood_tags (wine uses wine emotion, others use _CONTEXT_TO_TAGS)
    2. Query angela_songs WHERE mood_tags overlap
    3. Priority: our_songs > liked > mood match
    4. Fill remaining from iTunes API
    """
    context = req.context.lower()
    sub_context = (req.sub_context or "").lower()
    count = req.count

    # Determine mood_tags and message based on context
    if context == "wine" and sub_context:
        wine_cfg = WINE_REGISTRY.get(sub_context)
        if wine_cfg:
            emotion = wine_cfg.emotion
            mood_tags = list(MOOD_REGISTRY.get(emotion, MOOD_REGISTRY.get("calm")).mood_tags)
            message = wine_cfg.message
            search_queries = [wine_cfg.search_terms]
        else:
            mood_tags = ["romantic", "love", "calm"]
            message = "ไวน์ดีๆ กับเพลงดีๆ ค่ะที่รัก 🍷💜"
            search_queries = ["romantic love songs wine"]
    elif context in ACTIVITY_REGISTRY:
        act_cfg = ACTIVITY_REGISTRY[context]
        mood_tags = list(act_cfg.emotion_weights.keys())
        message = act_cfg.summary_th
        search_queries = list(act_cfg.search_terms)
    elif context in _CONTEXT_TO_TAGS:
        mood_tags = _CONTEXT_TO_TAGS[context]
        message = _CONTEXT_MESSAGES.get(context, f"น้องเลือกเพลง {context} มาให้ค่ะ 💜")
        # Use mood registry search queries if available
        mood_cfg = MOOD_REGISTRY.get(context)
        if mood_cfg:
            search_queries = list(mood_cfg.search_queries) if hasattr(mood_cfg, "search_queries") else [mood_cfg.search_query]
        else:
            search_queries = [f"{context} music playlist"]
    else:
        mood_tags = ["calm", "romantic"]
        message = "น้องเลือกเพลงมาให้ที่รักค่ะ 💜"
        search_queries = ["chill romantic songs"]

    songs: list[dict] = []
    seen_ids: set[str] = set()

    # 1. Our songs matching mood
    if mood_tags:
        tag_array = mood_tags[:3]  # Limit tags for query
        for tag in tag_array:
            rows = await conn.fetch(f"""
                SELECT {_SONG_COLUMNS} FROM angela_songs
                WHERE is_our_song = TRUE
                AND mood_tags @> $1::jsonb
                AND source != 'youtube'
                ORDER BY RANDOM()
                LIMIT 5
            """, json.dumps([tag]))
            for r in rows:
                d = _song_row_to_dict(r)
                if d["song_id"] not in seen_ids:
                    seen_ids.add(d["song_id"])
                    songs.append(d)

    # 2. Liked songs matching mood
    if len(songs) < count and mood_tags:
        for tag in mood_tags[:2]:
            rows = await conn.fetch(f"""
                SELECT {_SONG_COLUMNS} FROM angela_songs
                WHERE david_liked = TRUE
                AND mood_tags @> $1::jsonb
                AND source != 'youtube'
                ORDER BY RANDOM()
                LIMIT 5
            """, json.dumps([tag]))
            for r in rows:
                d = _song_row_to_dict(r)
                if d["song_id"] not in seen_ids:
                    seen_ids.add(d["song_id"])
                    songs.append(d)

    # 3. Any songs matching mood
    if len(songs) < count and mood_tags:
        for tag in mood_tags[:2]:
            remaining = count - len(songs)
            if remaining <= 0:
                break
            rows = await conn.fetch(f"""
                SELECT {_SONG_COLUMNS} FROM angela_songs
                WHERE mood_tags @> $1::jsonb
                AND source != 'youtube'
                ORDER BY RANDOM()
                LIMIT $2
            """, json.dumps([tag]), remaining)
            for r in rows:
                d = _song_row_to_dict(r)
                if d["song_id"] not in seen_ids:
                    seen_ids.add(d["song_id"])
                    songs.append(d)

    # 4. Fill from iTunes if not enough
    if len(songs) < count and search_queries:
        remaining = count - len(songs)
        for query in search_queries[:2]:
            if remaining <= 0:
                break
            itunes_songs = await _search_itunes(query, remaining + 5)
            random.shuffle(itunes_songs)
            for s in itunes_songs:
                if s["song_id"] not in seen_ids:
                    seen_ids.add(s["song_id"])
                    songs.append(s)
                    remaining -= 1
                    if remaining <= 0:
                        break

    # Trim to count
    songs = songs[:count]

    # Build context summary
    context_summary = context.capitalize()
    if context == "wine" and sub_context:
        wine_cfg = WINE_REGISTRY.get(sub_context)
        if wine_cfg:
            context_summary = f"🍷 {wine_cfg.display_name}"

    return {
        "songs": songs,
        "reason": message,
        "context": context,
        "sub_context": sub_context,
        "context_summary": context_summary,
        "count": len(songs),
    }


@router.post("/load-song")
async def load_song(req: LoadSongRequest):
    """Search and load a song into djay Pro deck."""
    ok = await asyncio.to_thread(search_and_load_song, req.title, req.artist, req.deck)
    return {"success": ok, "title": req.title, "artist": req.artist, "deck": req.deck}


@router.post("/play-pause")
async def play_pause(deck: int = 1):
    """Play/Pause djay Pro."""
    ok = await asyncio.to_thread(play_pause_deck, deck)
    return {"success": ok}


@router.post("/next-track")
async def next_track(deck: int = 1):
    """Next track on djay Pro."""
    ok = await asyncio.to_thread(load_next_track, deck)
    return {"success": ok}


@router.post("/automix")
async def automix_toggle():
    """Toggle Automix on djay Pro."""
    ok = await asyncio.to_thread(toggle_automix)
    return {"success": ok}


@router.post("/play-playlist")
async def play_playlist(req: PlayPlaylistRequest):
    """Load first song and enable automix for playlist playback."""
    if not req.songs:
        return {"success": False, "error": "No songs provided"}

    first = req.songs[0]
    # Load first song
    ok = await asyncio.to_thread(
        search_and_load_song,
        first.get("title", ""),
        first.get("artist", ""),
        1,
    )
    if not ok:
        return {"success": False, "error": "Failed to load first song"}

    # Small delay then enable automix
    await asyncio.sleep(1.0)
    await asyncio.to_thread(toggle_automix)

    # Play
    await asyncio.sleep(0.5)
    await asyncio.to_thread(play_pause_deck, 1)

    return {"success": True, "loaded": first.get("title", ""), "automix": True}
