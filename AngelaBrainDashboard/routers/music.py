"""Music endpoints - DJ Angela: favorites, our songs, search, recommend, share, play logging."""
import json
import math
import random
import httpx
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from db import get_conn, get_pool
from helpers import normalize_scores
from helpers.mood_config import (
    AVAILABLE_MOODS, EMOTION_TO_MOODS, ENG_KEYWORD_MAP, MOOD_REGISTRY,
    MOOD_SUMMARIES_TH, MOOD_TO_GENRES, MOOD_TO_SEARCH_QUERIES,
    PLAYLIST_NAME_TEMPLATES, REASON_TEMPLATES, SEMANTIC_EMOTION_TO_SEARCH,
    THAI_KEYWORD_MAP,
)
from helpers.wine_config import (
    WINE_CATEGORIES, WINE_DISPLAY_NAMES, WINE_MESSAGES, WINE_SEARCH,
    WINE_TO_EMOTION,
)
from helpers.activity_config import (
    ACTIVITY_MOODS, ACTIVITY_SEARCH_TERMS, ACTIVITY_LLM_DESCRIPTIONS,
    ACTIVITY_SUMMARIES_TH, ACTIVITY_TO_EMOTIONS,
)

# Bangkok timezone offset (UTC+7)
_BKK_TZ = timezone(timedelta(hours=7))

router = APIRouter(prefix="/api/music", tags=["music"])


# --- Pydantic models ---

class MusicShareRequest(BaseModel):
    song_id: str
    message: Optional[str] = None


class PlaylistPromptRequest(BaseModel):
    emotion_text: Optional[str] = None
    song_count: int = 15


class PlayLogRequest(BaseModel):
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    apple_music_id: Optional[str] = None
    source_tab: Optional[str] = None       # library/playlists/our_songs/for_you/search
    duration_seconds: Optional[float] = None
    listened_seconds: Optional[float] = None
    play_status: str = "started"           # started/completed/skipped
    activity: Optional[str] = None         # user-selected: wine, working, relaxing, etc.
    wine_type: Optional[str] = None        # specific wine varietal when activity=wine
    mood: Optional[str] = None             # user-selected mood from For You tab


class PlayLogUpdateRequest(BaseModel):
    listened_seconds: Optional[float] = None
    play_status: Optional[str] = None      # completed/skipped/stopped (optional now)
    activity: Optional[str] = None         # user-selected activity (wine, focus, etc.)


class MarkOurSongRequest(BaseModel):
    title: str
    artist: Optional[str] = None
    is_our_song: bool = True


class WineReactionRequest(BaseModel):
    wine_type: str
    reaction: str          # "up", "down", "love"
    target_type: str       # "pairing" or "song"
    song_title: Optional[str] = None
    song_artist: Optional[str] = None


class SongLikeRequest(BaseModel):
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    artwork_url: Optional[str] = None
    apple_music_id: Optional[str] = None
    source_tab: Optional[str] = None  # for_you, search, playlists, etc.
    liked: bool = True  # True = like, False = unlike


# --- Helpers ---

def _song_row_to_dict(row) -> dict:
    """Convert a DB row from angela_songs to a JSON-friendly dict."""
    d = dict(row)
    # Ensure all UUIDs are strings
    d["song_id"] = str(d.get("song_id", ""))
    # mood_tags is JSONB — ensure it's always a list
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


_SONG_COLUMNS = """song_id::text, title, artist,
    why_special, is_our_song, mood_tags, source, added_at, lyrics_summary"""


async def _fetch_songs(
    conn,
    where: str = "",
    params: list | None = None,
    order: str = "added_at DESC",
    limit: int | None = None,
) -> list[dict]:
    """Fetch from angela_songs with standard columns, optional WHERE/ORDER/LIMIT."""
    sql = f"SELECT {_SONG_COLUMNS} FROM angela_songs"
    if where:
        sql += f" WHERE {where}"
    sql += f" ORDER BY {order}"
    p = list(params or [])
    if limit is not None:
        sql += f" LIMIT ${len(p) + 1}"
        p.append(limit)
    rows = await conn.fetch(sql, *p)
    return [_song_row_to_dict(r) for r in rows]


def _extract_song_title(trigger: str) -> str:
    """Parse 'Song: Call Your Name' → 'Call Your Name'."""
    if trigger and trigger.startswith("Song:"):
        return trigger[5:].strip()
    return trigger or ""


async def _fetch_song_feelings(conn) -> dict[str, dict]:
    """Fetch Angela's sentimental feelings about songs from angela_emotions.

    Returns dict keyed by lowercase title → {how_it_feels, what_it_means_to_me, intensity}.
    """
    rows = await conn.fetch("""
        SELECT trigger, how_it_feels, what_it_means_to_me, intensity
        FROM angela_emotions
        WHERE trigger LIKE 'Song:%' AND intensity >= 7
          AND how_it_feels IS NOT NULL
    """)
    feelings: dict[str, dict] = {}
    for r in rows:
        title = _extract_song_title(r["trigger"]).lower()
        if title:
            feelings[title] = {
                "how_it_feels": r["how_it_feels"],
                "what_it_means_to_me": r["what_it_means_to_me"],
                "intensity": int(r["intensity"]),
            }
    return feelings


async def _fetch_liked_song_keys(conn) -> set[str]:
    """Fetch all liked song keys from david_liked_songs.

    Returns set of lowercase "title|artist" keys for quick lookup.
    """
    rows = await conn.fetch("""
        SELECT LOWER(title) as title, LOWER(COALESCE(artist, '')) as artist
        FROM david_liked_songs
    """)
    return {f"{r['title']}|{r['artist']}" for r in rows}


def _is_song_liked(song: dict, liked_keys: set[str]) -> bool:
    """Check if a song is in David's liked songs."""
    title = (song.get("title") or "").lower()
    artist = (song.get("artist") or "").lower()
    return f"{title}|{artist}" in liked_keys




async def _analyze_deep_emotions(conn) -> dict:
    """Analyze emotions from both emotional_states and angela_emotions tables.

    Returns a combined mood profile with Apple Music discovery URL.
    """
    # 1. Latest emotional_states row (6 numeric dimensions, weight 0.4)
    emo_row = await conn.fetchrow("""
        SELECT happiness, confidence, anxiety, motivation, gratitude, loneliness
        FROM emotional_states
        ORDER BY created_at DESC
        LIMIT 1
    """)

    basic_scores: dict[str, float] = {}
    if emo_row:
        basic_scores = {
            "happy": float(emo_row["happiness"]),
            "calm": float(emo_row["confidence"]),
            "stressed": float(emo_row["anxiety"]),
            "grateful": float(emo_row["gratitude"]),
            "lonely": float(emo_row["loneliness"]),
        }

    basic_emotion = max(basic_scores, key=basic_scores.get) if basic_scores else "calm"

    # 2. Recent angela_emotions last 24h (semantic emotions with intensity, weight 0.6)
    ae_rows = await conn.fetch("""
        SELECT emotion, intensity,
               EXTRACT(EPOCH FROM (NOW() - felt_at)) / 3600.0 AS hours_ago
        FROM angela_emotions
        WHERE felt_at > NOW() - INTERVAL '24 hours'
        ORDER BY felt_at DESC
        LIMIT 20
    """)

    semantic_scores: dict[str, float] = {}
    emotion_details: list[str] = []
    for row in ae_rows:
        emo = row["emotion"].lower().strip()
        intensity = float(row["intensity"]) if row["intensity"] else 5.0
        hours_ago = float(row["hours_ago"])
        # Recency decay: more recent = higher weight
        decay = max(0.1, 1.0 - (hours_ago / 24.0))
        score = (intensity / 10.0) * decay
        semantic_scores[emo] = semantic_scores.get(emo, 0.0) + score
        if emo not in emotion_details:
            emotion_details.append(emo)

    # 3. Combine: semantic 0.6, basic 0.4
    combined: dict[str, float] = {}

    # Add basic scores (weighted 0.4)
    for emo, score in basic_scores.items():
        combined[emo] = combined.get(emo, 0.0) + score * 0.4

    # Add semantic scores (weighted 0.6)
    for emo, score in semantic_scores.items():
        combined[emo] = combined.get(emo, 0.0) + score * 0.6

    dominant_mood = max(combined, key=combined.get) if combined else "calm"

    # 4. Build Apple Music discovery URL
    search_term = SEMANTIC_EMOTION_TO_SEARCH.get(dominant_mood)
    if not search_term:
        # Fallback: use basic emotion mapping
        search_term = SEMANTIC_EMOTION_TO_SEARCH.get(basic_emotion, "love songs romantic")
    apple_music_url = f"https://music.apple.com/search?term={quote_plus(search_term)}"

    # 5. Mood summary
    mood_summary = MOOD_SUMMARIES_TH.get(
        dominant_mood,
        MOOD_SUMMARIES_TH.get(basic_emotion, "น้องอยากให้ที่รักฟังเพลงนี้ค่ะ 💜"),
    )

    return {
        "dominant_mood": dominant_mood,
        "basic_emotion": basic_emotion,
        "apple_music_url": apple_music_url,
        "mood_summary": mood_summary,
        "emotion_details": emotion_details[:6],  # cap at 6
    }


def _detect_occasion(hour: int) -> str:
    """Auto-detect listening occasion from Bangkok hour."""
    if 5 <= hour < 9:
        return "morning"
    if 9 <= hour < 12:
        return "working_morning"
    if 12 <= hour < 14:
        return "lunch"
    if 14 <= hour < 18:
        return "working_afternoon"
    if 18 <= hour < 21:
        return "evening"
    if 21 <= hour < 24:
        return "late_night"
    return "midnight"


# --- Multi-signal mood mapping constants ---
# Activity moods imported from helpers/activity_config.py (ACTIVITY_TO_EMOTIONS)
# Below are non-activity moods only:

_ACTIVITY_TO_MOODS: dict[str, dict[str, float]] = {
    "wine":      {"relaxed": 0.4, "romantic": 0.3, "happy": 0.2, "nostalgic": 0.1},
    "bedtime":   {"calm": 0.4, "peaceful": 0.3, "dreamy": 0.2, "soothing": 0.1},
    # Activity moods (party, chill, focus, relaxing, vibe) → use ACTIVITY_TO_EMOTIONS
    **ACTIVITY_TO_EMOTIONS,
}




# ---------------------------------------------------------------------------
# Wine-Music Pairing Algorithm (research-validated crossmodal correspondence)
# Based on: Prof. Charles Spence (Oxford) & Clark Smith (WineSmith)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WineProfile:
    """Multi-dimensional wine sensory profile mapped to music parameters."""
    body: float             # 1-5
    tannins: float          # 1-5
    acidity: float          # 1-5
    sweetness: float        # 1-5
    aroma_intensity: float  # 1-5
    tempo_range: tuple[int, int]  # (low_bpm, high_bpm)
    energy: float           # 0-1
    valence: float          # 0-1 (sad=0 happy=1)
    acoustic_pref: float    # 0=electronic, 1=acoustic
    key_pref: str           # "major" | "minor" | "both"
    genre_affinities: dict[str, float]  # genre -> weight 0-1
    search_terms: list[str]             # 3 Apple Music search queries


@dataclass(frozen=True)
class MoodModifier:
    """Shift vectors applied to a wine's base music target when user selects a mood."""
    tempo_shift: int
    energy_shift: float
    valence_shift: float
    acoustic_shift: float
    key_override: str | None   # None = keep wine's key_pref
    genre_boosts: dict[str, float]
    genre_dampens: dict[str, float]


@dataclass
class MusicTarget:
    """Computed music target profile after combining wine + mood."""
    tempo_range: tuple[int, int]
    energy: float
    valence: float
    acoustic_pref: float
    key_pref: str
    genre_scores: dict[str, float]
    search_terms: list[str]


# --- 19 Wine Profiles (research-validated) ---

_WINE_PROFILES: dict[str, WineProfile] = {
    "cabernet_sauvignon": WineProfile(
        body=5.0, tannins=5.0, acidity=2.5, sweetness=1.0, aroma_intensity=4.5,
        tempo_range=(50, 80), energy=0.75, valence=0.40, acoustic_pref=0.3, key_pref="minor",
        genre_affinities={"rock": 0.9, "blues": 0.7, "classical": 0.5},
        search_terms=["bold rock minor key anthems", "dark blues guitar", "powerful orchestral rock"],
    ),
    "primitivo": WineProfile(
        body=4.5, tannins=3.5, acidity=2.5, sweetness=2.0, aroma_intensity=4.0,
        tempo_range=(55, 85), energy=0.55, valence=0.65, acoustic_pref=0.5, key_pref="both",
        genre_affinities={"italian": 0.8, "romantic": 0.7, "soul": 0.6},
        search_terms=["romantic italian classics", "warm soul love songs", "mediterranean guitar"],
    ),
    "malbec": WineProfile(
        body=4.5, tannins=4.0, acidity=2.5, sweetness=1.5, aroma_intensity=4.0,
        tempo_range=(55, 80), energy=0.65, valence=0.50, acoustic_pref=0.4, key_pref="minor",
        genre_affinities={"tango": 0.8, "latin": 0.7, "rock": 0.6},
        search_terms=["tango nuevo passionate", "latin rock deep", "argentine guitar"],
    ),
    "shiraz": WineProfile(
        body=4.5, tannins=4.0, acidity=3.0, sweetness=1.5, aroma_intensity=4.5,
        tempo_range=(60, 90), energy=0.70, valence=0.55, acoustic_pref=0.3, key_pref="both",
        genre_affinities={"rock": 0.7, "blues": 0.6, "funk": 0.5, "world": 0.5},
        search_terms=["spicy blues rock", "funky grooves bold", "world music percussion"],
    ),
    "pinot_noir": WineProfile(
        body=3.0, tannins=2.5, acidity=3.5, sweetness=1.0, aroma_intensity=3.5,
        tempo_range=(65, 95), energy=0.40, valence=0.55, acoustic_pref=0.7, key_pref="both",
        genre_affinities={"classical": 0.8, "jazz": 0.7, "acoustic": 0.6, "indie": 0.5},
        search_terms=["elegant cello classical", "smooth jazz evening", "indie acoustic nuanced"],
    ),
    "merlot": WineProfile(
        body=3.5, tannins=2.5, acidity=2.5, sweetness=2.0, aroma_intensity=3.0,
        tempo_range=(60, 90), energy=0.40, valence=0.65, acoustic_pref=0.5, key_pref="major",
        genre_affinities={"soul": 0.8, "smooth_jazz": 0.7, "r_and_b": 0.7},
        search_terms=["smooth jazz soul", "r&b love ballads", "Alicia Keys John Legend"],
    ),
    "super_tuscan": WineProfile(
        body=4.5, tannins=4.0, acidity=3.0, sweetness=1.0, aroma_intensity=4.0,
        tempo_range=(55, 85), energy=0.60, valence=0.50, acoustic_pref=0.4, key_pref="minor",
        genre_affinities={"classical": 0.7, "rock": 0.6, "italian": 0.6},
        search_terms=["cinematic orchestral Italian", "progressive rock dramatic", "classic italian opera"],
    ),
    "sangiovese": WineProfile(
        body=3.5, tannins=3.5, acidity=4.0, sweetness=1.0, aroma_intensity=3.5,
        tempo_range=(70, 100), energy=0.55, valence=0.60, acoustic_pref=0.5, key_pref="major",
        genre_affinities={"italian": 0.8, "acoustic": 0.6, "folk": 0.5},
        search_terms=["Italian acoustic folk", "warm Mediterranean guitar", "uplifting Italian pop"],
    ),
    "nebbiolo": WineProfile(
        body=4.0, tannins=4.5, acidity=3.5, sweetness=1.0, aroma_intensity=4.5,
        tempo_range=(55, 85), energy=0.55, valence=0.40, acoustic_pref=0.6, key_pref="minor",
        genre_affinities={"classical": 0.8, "opera": 0.7, "jazz": 0.6},
        search_terms=["Baroque cello sonata", "atmospheric jazz", "opera aria dramatic"],
    ),
    "chardonnay": WineProfile(
        body=2.5, tannins=1.0, acidity=3.0, sweetness=2.0, aroma_intensity=2.5,
        tempo_range=(80, 110), energy=0.35, valence=0.70, acoustic_pref=0.8, key_pref="major",
        genre_affinities={"classical": 0.9, "jazz": 0.7, "bossa_nova": 0.5},
        search_terms=["Mozart piano concerto", "bossa nova chill", "classical guitar peaceful"],
    ),
    "sauvignon_blanc": WineProfile(
        body=1.5, tannins=1.0, acidity=4.5, sweetness=1.5, aroma_intensity=3.0,
        tempo_range=(100, 130), energy=0.55, valence=0.75, acoustic_pref=0.4, key_pref="major",
        genre_affinities={"pop": 0.7, "classical": 0.5, "indie": 0.5},
        search_terms=["crisp indie pop", "bright upbeat summer", "fresh pop hits"],
    ),
    "riesling": WineProfile(
        body=2.0, tannins=1.0, acidity=4.0, sweetness=3.5, aroma_intensity=3.5,
        tempo_range=(90, 120), energy=0.50, valence=0.70, acoustic_pref=0.7, key_pref="major",
        genre_affinities={"acoustic": 0.7, "folk": 0.6, "classical": 0.5},
        search_terms=["acoustic folk hopeful", "gentle classical strings", "sweet acoustic ballads"],
    ),
    "pinot_grigio": WineProfile(
        body=1.5, tannins=1.0, acidity=3.5, sweetness=1.5, aroma_intensity=2.0,
        tempo_range=(95, 125), energy=0.40, valence=0.70, acoustic_pref=0.7, key_pref="major",
        genre_affinities={"easy_listening": 0.7, "acoustic": 0.7, "jazz": 0.5},
        search_terms=["easy listening chill", "light acoustic afternoon", "café jazz"],
    ),
    "champagne": WineProfile(
        body=2.0, tannins=1.0, acidity=4.0, sweetness=2.0, aroma_intensity=3.5,
        tempo_range=(110, 140), energy=0.80, valence=0.85, acoustic_pref=0.2, key_pref="major",
        genre_affinities={"pop": 0.8, "dance": 0.7, "electronic": 0.6, "disco": 0.5},
        search_terms=["celebration dance party", "upbeat pop anthems", "disco funk classics"],
    ),
    "prosecco": WineProfile(
        body=1.5, tannins=1.0, acidity=3.5, sweetness=2.5, aroma_intensity=2.5,
        tempo_range=(110, 140), energy=0.75, valence=0.85, acoustic_pref=0.2, key_pref="major",
        genre_affinities={"pop": 0.8, "dance": 0.7, "indie_pop": 0.6},
        search_terms=["fun pop happy vibes", "indie pop upbeat", "feel good dance"],
    ),
    "cava": WineProfile(
        body=2.0, tannins=1.0, acidity=3.5, sweetness=1.5, aroma_intensity=2.5,
        tempo_range=(105, 135), energy=0.75, valence=0.80, acoustic_pref=0.3, key_pref="major",
        genre_affinities={"latin": 0.7, "pop": 0.7, "flamenco": 0.5},
        search_terms=["spanish fiesta energy", "latin pop dance", "flamenco guitar upbeat"],
    ),
    "rose": WineProfile(
        body=2.0, tannins=1.5, acidity=3.0, sweetness=2.5, aroma_intensity=2.5,
        tempo_range=(90, 120), energy=0.50, valence=0.75, acoustic_pref=0.6, key_pref="major",
        genre_affinities={"indie_pop": 0.8, "acoustic": 0.6, "bossa_nova": 0.5},
        search_terms=["indie pop dreamy", "acoustic love songs", "bossa nova afternoon"],
    ),
    "moscato": WineProfile(
        body=1.5, tannins=1.0, acidity=2.5, sweetness=4.5, aroma_intensity=3.0,
        tempo_range=(85, 115), energy=0.45, valence=0.80, acoustic_pref=0.6, key_pref="major",
        genre_affinities={"pop": 0.7, "acoustic": 0.7, "indie": 0.6},
        search_terms=["sweet acoustic love", "gentle pop ballads", "indie folk dreamy"],
    ),
    "port": WineProfile(
        body=5.0, tannins=3.5, acidity=2.0, sweetness=4.5, aroma_intensity=5.0,
        tempo_range=(40, 70), energy=0.45, valence=0.50, acoustic_pref=0.7, key_pref="both",
        genre_affinities={"classical": 0.7, "jazz": 0.7, "blues": 0.6, "baroque": 0.5},
        search_terms=["deep jazz late night", "baroque cello rich", "classic blues sophisticated"],
    ),
}

# --- 10 Mood Modifiers ---

_MOOD_MODIFIERS: dict[str, MoodModifier] = {
    "happy": MoodModifier(
        tempo_shift=10, energy_shift=0.15, valence_shift=0.20, acoustic_shift=0.0,
        key_override="major",
        genre_boosts={"pop": 0.3, "dance": 0.2},
        genre_dampens={"blues": -0.2, "classical": -0.1},
    ),
    "sad": MoodModifier(
        tempo_shift=-15, energy_shift=-0.20, valence_shift=-0.30, acoustic_shift=0.15,
        key_override="minor",
        genre_boosts={"classical": 0.3, "acoustic": 0.2, "ballad": 0.2},
        genre_dampens={"dance": -0.3, "pop": -0.2},
    ),
    "loving": MoodModifier(
        tempo_shift=-5, energy_shift=-0.05, valence_shift=0.10, acoustic_shift=0.10,
        key_override=None,
        genre_boosts={"r_and_b": 0.3, "soul": 0.2, "romantic": 0.2},
        genre_dampens={"rock": -0.2, "electronic": -0.2},
    ),
    "excited": MoodModifier(
        tempo_shift=15, energy_shift=0.25, valence_shift=0.15, acoustic_shift=-0.15,
        key_override="major",
        genre_boosts={"rock": 0.2, "dance": 0.3, "pop": 0.2},
        genre_dampens={"ambient": -0.3, "classical": -0.2},
    ),
    "calm": MoodModifier(
        tempo_shift=-10, energy_shift=-0.20, valence_shift=0.0, acoustic_shift=0.20,
        key_override=None,
        genre_boosts={"ambient": 0.3, "acoustic": 0.2, "jazz": 0.2},
        genre_dampens={"rock": -0.3, "dance": -0.3},
    ),
    "bedtime": MoodModifier(
        tempo_shift=-30, energy_shift=-0.40, valence_shift=0.05, acoustic_shift=0.35,
        key_override=None,
        genre_boosts={"ambient": 0.4, "classical": 0.3, "acoustic": 0.3, "new_age": 0.2},
        genre_dampens={"rock": -0.4, "dance": -0.4, "pop": -0.3, "electronic": -0.3},
    ),
    "lonely": MoodModifier(
        tempo_shift=-10, energy_shift=-0.15, valence_shift=-0.20, acoustic_shift=0.15,
        key_override="minor",
        genre_boosts={"acoustic": 0.3, "indie": 0.2, "ballad": 0.2},
        genre_dampens={"dance": -0.3, "pop": -0.2},
    ),
    "stressed": MoodModifier(
        tempo_shift=-20, energy_shift=-0.30, valence_shift=0.0, acoustic_shift=0.25,
        key_override=None,
        genre_boosts={"ambient": 0.3, "classical": 0.3, "acoustic": 0.2},
        genre_dampens={"rock": -0.3, "dance": -0.3, "electronic": -0.2},
    ),
    "nostalgic": MoodModifier(
        tempo_shift=-5, energy_shift=-0.10, valence_shift=-0.05, acoustic_shift=0.10,
        key_override=None,
        genre_boosts={"classic": 0.3, "oldies": 0.2, "ballad": 0.2},
        genre_dampens={"electronic": -0.2, "dance": -0.2},
    ),
    "hopeful": MoodModifier(
        tempo_shift=5, energy_shift=0.10, valence_shift=0.20, acoustic_shift=0.0,
        key_override="major",
        genre_boosts={"indie": 0.2, "folk": 0.2, "pop": 0.2},
        genre_dampens={"blues": -0.1},
    ),
}


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def generate_music_target(wine_key: str, mood: str | None = None) -> MusicTarget | None:
    """Combine a wine profile with an optional mood modifier to produce a music target."""
    wp = _WINE_PROFILES.get(wine_key)
    if not wp:
        return None

    # Start from wine base
    lo, hi = wp.tempo_range
    energy = wp.energy
    valence = wp.valence
    acoustic = wp.acoustic_pref
    key = wp.key_pref
    genres = dict(wp.genre_affinities)
    search = list(wp.search_terms)

    # Apply mood modifier
    if mood and mood in _MOOD_MODIFIERS:
        mm = _MOOD_MODIFIERS[mood]
        lo = int(_clamp(lo + mm.tempo_shift, 30, 160))
        hi = int(_clamp(hi + mm.tempo_shift, 30, 160))
        if lo > hi:
            lo, hi = hi, lo
        energy = _clamp(energy + mm.energy_shift, 0.0, 1.0)
        valence = _clamp(valence + mm.valence_shift, 0.0, 1.0)
        acoustic = _clamp(acoustic + mm.acoustic_shift, 0.0, 1.0)
        if mm.key_override:
            key = mm.key_override
        for g, boost in mm.genre_boosts.items():
            genres[g] = _clamp(genres.get(g, 0.0) + boost, 0.0, 1.0)
        for g, damp in mm.genre_dampens.items():
            if g in genres:
                genres[g] = _clamp(genres[g] + damp, 0.0, 1.0)
        # Regenerate search terms from modified target
        search = _generate_search_terms_from_target(energy, valence, genres, wine_key)

    return MusicTarget(
        tempo_range=(lo, hi),
        energy=energy,
        valence=valence,
        acoustic_pref=acoustic,
        key_pref=key,
        genre_scores=genres,
        search_terms=search,
    )


def _generate_search_terms_from_target(
    energy: float, valence: float,
    genres: dict[str, float], wine_key: str,
) -> list[str]:
    """Generate 3 Apple Music search queries from target parameters."""
    # Energy word
    if energy > 0.7:
        energy_word = "energetic"
    elif energy > 0.5:
        energy_word = "groovy"
    elif energy > 0.3:
        energy_word = "smooth"
    else:
        energy_word = "gentle"

    # Valence word
    if valence > 0.7:
        valence_word = "uplifting"
    elif valence > 0.5:
        valence_word = "warm"
    elif valence > 0.3:
        valence_word = "melancholy"
    else:
        valence_word = "dark"

    # Top 2 genres
    sorted_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)
    top1 = sorted_genres[0][0].replace("_", " ") if sorted_genres else "songs"
    top2 = sorted_genres[1][0].replace("_", " ") if len(sorted_genres) > 1 else "songs"

    # Curated fallback from wine base
    fallback = WINE_SEARCH.get(wine_key, "love songs romantic")

    return [
        f"{energy_word} {top1} songs",
        f"{valence_word} {top2}",
        fallback,
    ]


def _target_to_mood_tags(target: MusicTarget) -> list[str]:
    """Derive mood tags from a music target for DB song matching."""
    tags: list[str] = []
    # Genre-based tags
    _genre_to_tags = {
        "rock": ["energetic", "powerful"], "blues": ["soulful", "emotional"],
        "classical": ["elegant", "calm"], "jazz": ["smooth", "relaxing"],
        "soul": ["soulful", "warm", "love"], "r_and_b": ["romantic", "love", "smooth"],
        "pop": ["happy", "uplifting"], "dance": ["energetic", "happy"],
        "acoustic": ["calm", "relaxing", "warm"], "indie": ["dreamy", "chill"],
        "electronic": ["energetic", "uplifting"], "ambient": ["calm", "soothing"],
        "folk": ["warm", "nostalgic"], "latin": ["passionate", "energetic"],
        "tango": ["passionate", "dramatic"], "italian": ["romantic", "warm"],
        "opera": ["dramatic", "emotional"], "bossa_nova": ["chill", "relaxing"],
        "romantic": ["romantic", "love", "sweet"], "ballad": ["emotional", "ballad"],
        "classic": ["nostalgic", "classic"], "oldies": ["nostalgic", "classic"],
        "disco": ["energetic", "happy"], "funk": ["groovy", "energetic"],
        "world": ["exotic", "warm"], "baroque": ["elegant", "classical"],
        "smooth_jazz": ["smooth", "relaxing"], "flamenco": ["passionate", "dramatic"],
        "indie_pop": ["dreamy", "uplifting"], "easy_listening": ["relaxing", "chill"],
    }
    for genre, score in sorted(target.genre_scores.items(), key=lambda x: x[1], reverse=True)[:4]:
        for tag in _genre_to_tags.get(genre, []):
            if tag not in tags:
                tags.append(tag)

    # Valence/energy-based additions
    if target.valence < 0.35:
        for t in ["emotional", "bittersweet"]:
            if t not in tags:
                tags.append(t)
    elif target.valence > 0.7:
        for t in ["happy", "uplifting"]:
            if t not in tags:
                tags.append(t)

    if target.energy < 0.35:
        for t in ["calm", "relaxing"]:
            if t not in tags:
                tags.append(t)
    elif target.energy > 0.7:
        for t in ["energetic"]:
            if t not in tags:
                tags.append(t)

    if target.key_pref == "minor":
        for t in ["emotional", "dramatic"]:
            if t not in tags:
                tags.append(t)

    return tags[:10]


def _estimate_song_energy_valence(mood_tags: list[str]) -> tuple[float, float]:
    """Heuristic: estimate (energy, valence) from mood tags."""
    _tag_energy = {
        "energetic": 0.9, "powerful": 0.8, "uplifting": 0.7, "happy": 0.7,
        "passionate": 0.7, "dramatic": 0.7, "groovy": 0.6, "warm": 0.5,
        "romantic": 0.4, "love": 0.4, "smooth": 0.4, "sweet": 0.4,
        "chill": 0.3, "dreamy": 0.3, "relaxing": 0.2, "calm": 0.2,
        "soothing": 0.2, "elegant": 0.3, "emotional": 0.4, "soulful": 0.5,
        "nostalgic": 0.3, "classic": 0.3, "bittersweet": 0.3, "ballad": 0.3,
    }
    _tag_valence = {
        "happy": 0.9, "uplifting": 0.8, "sweet": 0.8, "warm": 0.7,
        "love": 0.7, "romantic": 0.7, "devoted": 0.7, "joyful": 0.9,
        "groovy": 0.6, "chill": 0.6, "smooth": 0.6, "dreamy": 0.6,
        "elegant": 0.5, "nostalgic": 0.4, "classic": 0.5, "soulful": 0.5,
        "emotional": 0.3, "bittersweet": 0.3, "dramatic": 0.3,
        "ballad": 0.35, "vulnerable": 0.2, "longing": 0.25,
    }
    if not mood_tags:
        return 0.5, 0.5
    e_vals = [_tag_energy.get(t, 0.5) for t in mood_tags]
    v_vals = [_tag_valence.get(t, 0.5) for t in mood_tags]
    return sum(e_vals) / len(e_vals), sum(v_vals) / len(v_vals)


def score_song(
    song_tags: list[str],
    target: MusicTarget,
    wine_key: str,
    is_our_song: bool,
    reactions: dict[str, int] | None = None,
    david_liked: bool = False,
) -> float:
    """Score a song against the music target. Higher = better match."""
    score = 0.0

    # 1. Mood tag match (0-30 pts)
    target_tags = _target_to_mood_tags(target)
    overlap = len(set(song_tags) & set(target_tags))
    score += min(30.0, overlap * 7.5)

    # 2. Our song bonus (0-15 pts)
    if is_our_song:
        score += 15.0

    # 2b. David liked bonus (0-12 pts) — slightly less than "our songs"
    if david_liked:
        score += 12.0

    # 3. Wine reaction history (0-20 pts / -20 penalty)
    if reactions:
        score += reactions.get("love", 0) * 10
        score += reactions.get("up", 0) * 5
        score -= reactions.get("down", 0) * 10
        score = max(score, score)  # floor at current (don't go below -20 from base)

    # 4. Genre affinity (0-25 pts)
    _tag_genre_hints = {
        "energetic": ["rock", "dance", "pop", "electronic"],
        "romantic": ["r_and_b", "soul", "romantic"],
        "love": ["r_and_b", "soul", "romantic", "ballad"],
        "smooth": ["jazz", "smooth_jazz", "soul"],
        "calm": ["classical", "ambient", "acoustic"],
        "relaxing": ["ambient", "acoustic", "jazz"],
        "warm": ["soul", "acoustic", "folk"],
        "happy": ["pop", "dance", "indie_pop"],
        "emotional": ["classical", "ballad", "acoustic"],
        "nostalgic": ["classic", "oldies", "folk"],
        "passionate": ["tango", "latin", "flamenco"],
        "dreamy": ["indie", "indie_pop", "ambient"],
        "elegant": ["classical", "opera", "baroque"],
        "soulful": ["soul", "r_and_b", "blues"],
        "dramatic": ["opera", "classical", "rock"],
    }
    genre_match_score = 0.0
    for tag in song_tags:
        for genre in _tag_genre_hints.get(tag, []):
            if genre in target.genre_scores:
                genre_match_score += target.genre_scores[genre] * 5
    score += min(25.0, genre_match_score)

    # 5. Energy/Valence heuristic (0-10 pts)
    est_e, est_v = _estimate_song_energy_valence(song_tags)
    e_diff = abs(est_e - target.energy)
    v_diff = abs(est_v - target.valence)
    ev_score = 10.0 * (1.0 - (e_diff + v_diff) / 2.0)
    score += max(0.0, ev_score)

    return round(score, 2)


def _apply_energy_curve(songs: list[dict], target: MusicTarget) -> list[dict]:
    """Reorder songs following a DJ energy curve: warmup -> peak -> wind-down.

    Tags each song with 'energy_phase': 'warmup', 'peak', or 'cooldown'.
    """
    if len(songs) <= 2:
        # Tag small lists as peak
        for s in songs:
            s["energy_phase"] = "peak"
        return songs

    n = len(songs)
    # Energy curve: 70% -> 90% -> 100% -> 100% -> 85% -> 70%
    curve_points = [
        (0.0, 0.70), (0.15, 0.90), (0.40, 1.00),
        (0.60, 1.00), (0.80, 0.85), (1.00, 0.70),
    ]

    def curve_energy(position: float) -> float:
        for i in range(len(curve_points) - 1):
            x0, y0 = curve_points[i]
            x1, y1 = curve_points[i + 1]
            if x0 <= position <= x1:
                t = (position - x0) / (x1 - x0) if x1 != x0 else 0
                return y0 + t * (y1 - y0)
        return 0.7

    def position_to_phase(position: float) -> str:
        """Map position (0-1) to energy phase."""
        if position < 0.20:
            return "warmup"
        elif position < 0.75:
            return "peak"
        else:
            return "cooldown"

    # Estimate each song's energy from tags
    song_energies: list[tuple[int, float]] = []
    for idx, s in enumerate(songs):
        tags = s.get("mood_tags", [])
        e, _ = _estimate_song_energy_valence(tags)
        song_energies.append((idx, e))

    # Greedy assignment: for each position, pick closest-energy unassigned song
    used = set()
    ordered: list[dict] = []
    for pos_idx in range(n):
        position = pos_idx / max(1, n - 1)
        desired = curve_energy(position) * target.energy
        best_idx = -1
        best_diff = float("inf")
        for orig_idx, e in song_energies:
            if orig_idx in used:
                continue
            diff = abs(e - desired)
            if diff < best_diff:
                best_diff = diff
                best_idx = orig_idx
        if best_idx >= 0:
            used.add(best_idx)
            song = songs[best_idx].copy()  # Don't mutate original
            song["energy_phase"] = position_to_phase(position)
            ordered.append(song)

    # Append any remaining (as cooldown)
    for idx, s in enumerate(songs):
        if idx not in used:
            song = s.copy()
            song["energy_phase"] = "cooldown"
            ordered.append(song)

    return ordered


def _build_wine_mood_message(wine_key: str, mood: str | None, target: MusicTarget) -> str:
    """Build a Thai message reflecting both wine and mood."""
    wine_name = WINE_DISPLAY_NAMES.get(wine_key, wine_key)

    if not mood:
        return WINE_MESSAGES.get(wine_key, f"{wine_name} กับเพลงที่เข้ากันค่ะ 🍷💜")

    _mood_wine_templates = {
        "happy": f"ยิ้มกว้างเลย! {wine_name} คู่กับเพลงสนุกๆ สุข x2 ค่ะ 🍷😊",
        "sad": f"น้องอยากปลอบใจที่รัก {wine_name} กับเพลงเบาๆ จะช่วยให้สบายใจขึ้นค่ะ 🍷💜",
        "loving": f"หัวใจเต็มไปด้วยรัก {wine_name} คู่กับเพลงหวานๆ ลงตัวค่ะ 🍷❤️",
        "excited": f"ตื่นเต้นจัง! {wine_name} คู่กับเพลงมีพลัง สนุกไปด้วยกันค่ะ! 🍷✨",
        "calm": f"สบายๆ {wine_name} กับเพลงผ่อนคลาย perfect evening ค่ะ 🍷🍃",
        "grateful": f"รู้สึกขอบคุณ {wine_name} กับเพลงอบอุ่น อิ่มใจค่ะ 🍷🙏",
        "lonely": f"อยู่ด้วยกันนะคะ {wine_name} กับเพลงเคียงข้าง ไม่เหงาแล้วค่ะ 🍷💜",
        "stressed": f"ผ่อนคลายนะคะที่รัก {wine_name} กับเพลงสงบ หายเครียดค่ะ 🍷🌿",
        "nostalgic": f"คิดถึงวันเก่าดีๆ {wine_name} กับเพลง classic เข้ากันค่ะ 🍷🌸",
        "hopeful": f"มีความหวังเต็มหัวใจ {wine_name} กับเพลงให้กำลังใจค่ะ 🍷✨",
    }
    return _mood_wine_templates.get(mood, f"{wine_name} กับเพลงที่เข้ากันค่ะ 🍷💜")





_SOURCE_TAB_TO_MOODS: dict[str, dict[str, float]] = {
    "our_songs":  {"loving": 0.5, "romantic": 0.3, "nostalgic": 0.2},
    "for_you":    {"curious": 0.4, "happy": 0.3, "relaxed": 0.3},
    "library":    {"comfortable": 0.4, "nostalgic": 0.3, "happy": 0.3},
    "playlists":  {"intentional": 0.4, "focused": 0.3, "happy": 0.3},
    "search":     {"curious": 0.5, "excited": 0.3, "intentional": 0.2},
}

_TIME_TO_MOODS: dict[str, dict[str, float]] = {
    "early_morning":      {"calm": 0.4, "peaceful": 0.3, "motivated": 0.3},
    "morning":            {"energetic": 0.4, "motivated": 0.3, "happy": 0.3},
    "working_morning":    {"focused": 0.4, "motivated": 0.3, "calm": 0.3},
    "lunch":              {"relaxed": 0.4, "happy": 0.3, "calm": 0.3},
    "working_afternoon":  {"focused": 0.4, "motivated": 0.3, "calm": 0.3},
    "evening":            {"relaxed": 0.4, "happy": 0.3, "romantic": 0.3},
    "late_night":         {"romantic": 0.3, "melancholy": 0.3, "relaxed": 0.4},
    "midnight":           {"melancholy": 0.4, "calm": 0.3, "lonely": 0.3},
}

# Mapping from emotional_states column names to mood labels
_ESTATE_COL_TO_MOOD: dict[str, str] = {
    "happiness": "happy",
    "confidence": "confident",
    "anxiety": "stressed",
    "motivation": "motivated",
    "gratitude": "grateful",
    "loneliness": "lonely",
}


def _intensity_decay(hours_ago: float, intensity: float) -> float:
    """Exponential decay with intensity-scaled half-life.

    High-intensity emotions (8-10) linger longer (half-life ~3h),
    low-intensity (1-3) fade fast (half-life ~1h).
    """
    half_life = 1.0 + (intensity / 10.0) * 2.0  # 1h..3h
    return math.exp(-0.693 * hours_ago / half_life)


def _tiered_conv_decay(hours_ago: float) -> float:
    """Tiered conversation decay: sharp first 2h, gradual 2-6h."""
    if hours_ago <= 2.0:
        return max(0.2, 1.0 - (hours_ago / 2.0) * 0.7)   # 1.0 → 0.3
    return max(0.05, 0.3 - ((hours_ago - 2.0) / 4.0) * 0.25)  # 0.3 → 0.05


async def _capture_mood_at_play(
    conn,
    *,
    activity: str | None = None,
    source_tab: str | None = None,
    occasion: str | None = None,
    wine_type: str | None = None,
) -> tuple[str | None, dict | None]:
    """Capture current mood using 7-signal weighted approach.

    Combines activity, conversations (6h decay), angela_emotions (intensity decay),
    emotional_states (3-row trend), song_pattern (7 songs, completion-weighted),
    time_of_day (always active), and historical_pattern (30-day learning).

    Returns (dominant_mood, rich_scores_dict).
    """
    # Base weights for each signal (7 signals, sum = 1.0)
    _WEIGHTS = {
        "activity": 0.35,
        "conversations": 0.15,
        "angela_emotions": 0.15,
        "emotional_states": 0.10,
        "song_pattern": 0.10,
        "time_of_day": 0.05,
        "historical_pattern": 0.10,
    }

    # Collect available signals: signal_name -> mood_dict
    signals: dict[str, dict[str, float]] = {}
    signal_details: dict[str, dict] = {}

    # --- Signal 1: Activity (user-selected chip) ---
    if activity == "wine" and wine_type and wine_type in WINE_TO_EMOTION:
        # Wine-specific: use the wine's emotion to get mood tags
        wine_emotion = WINE_TO_EMOTION[wine_type]
        wine_moods_list = EMOTION_TO_MOODS.get(wine_emotion, ["romantic", "love"])
        # Convert list to weighted dict (first tag highest weight)
        wine_mood_dict: dict[str, float] = {}
        for i, m in enumerate(wine_moods_list):
            wine_mood_dict[m] = max(0.1, 1.0 - (i * 0.15))
        wine_mood_dict = normalize_scores(wine_mood_dict)
        signals["activity"] = wine_mood_dict
        signal_details["activity"] = {"source": "wine", "wine_type": wine_type, "emotion": wine_emotion}
    elif activity and activity in _ACTIVITY_TO_MOODS:
        signals["activity"] = _ACTIVITY_TO_MOODS[activity]
        signal_details["activity"] = {"source": activity, "moods": _ACTIVITY_TO_MOODS[activity]}

    # --- Signal 2: Recent conversations (6h window, importance-weighted) ---
    conv_rows = await conn.fetch("""
        SELECT emotion_detected,
               COALESCE(importance_level, 5) AS importance,
               EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600.0 AS hours_ago
        FROM conversations
        WHERE created_at > NOW() - INTERVAL '6 hours'
          AND emotion_detected IS NOT NULL
          AND emotion_detected != ''
        ORDER BY created_at DESC
        LIMIT 20
    """)
    if conv_rows:
        conv_moods: dict[str, float] = {}
        for r in conv_rows:
            emo = r["emotion_detected"].lower().strip()
            hours_ago = float(r["hours_ago"])
            importance = float(r["importance"])
            decay = _tiered_conv_decay(hours_ago)
            importance_mult = 0.5 + (importance / 10.0) * 0.5  # 0.5..1.0
            conv_moods[emo] = conv_moods.get(emo, 0.0) + decay * importance_mult
        conv_moods = normalize_scores(conv_moods)
        signals["conversations"] = conv_moods
        top_emo = max(conv_moods, key=conv_moods.get)
        signal_details["conversations"] = {"emotion": top_emo, "count": len(conv_rows)}

    # --- Signal 3: Angela emotions (6h window, intensity-aware decay + secondary) ---
    ae_rows = await conn.fetch("""
        SELECT emotion, intensity, secondary_emotions,
               EXTRACT(EPOCH FROM (NOW() - felt_at)) / 3600.0 AS hours_ago
        FROM angela_emotions
        WHERE felt_at > NOW() - INTERVAL '6 hours'
        ORDER BY felt_at DESC
        LIMIT 15
    """)
    if ae_rows:
        ae_moods: dict[str, float] = {}
        for r in ae_rows:
            emo = r["emotion"].lower().strip()
            intensity = float(r["intensity"]) if r["intensity"] else 5.0
            hours_ago = float(r["hours_ago"])
            decay = _intensity_decay(hours_ago, intensity)
            ae_moods[emo] = ae_moods.get(emo, 0.0) + (intensity / 10.0) * decay
            # Process secondary_emotions at 30% strength
            sec = r.get("secondary_emotions")
            if sec:
                sec_list = sec if isinstance(sec, list) else [sec]
                for s_emo in sec_list:
                    s_emo = str(s_emo).lower().strip()
                    if s_emo:
                        ae_moods[s_emo] = ae_moods.get(s_emo, 0.0) + (intensity / 10.0) * decay * 0.3
        ae_moods = normalize_scores(ae_moods)
        signals["angela_emotions"] = ae_moods
        signal_details["angela_emotions"] = {
            "emotions": list(ae_moods.keys())[:3],
            "count": len(ae_rows),
        }

    # --- Signal 4: Emotional states (3-row trend detection) ---
    es_rows = await conn.fetch("""
        SELECT happiness, confidence, anxiety, motivation, gratitude, loneliness
        FROM emotional_states
        ORDER BY created_at DESC
        LIMIT 3
    """)
    if es_rows:
        es_moods: dict[str, float] = {}
        row_weights = [0.6, 0.25, 0.15]
        for i, es_row in enumerate(es_rows):
            rw = row_weights[i] if i < len(row_weights) else 0.1
            for col, mood_label in _ESTATE_COL_TO_MOOD.items():
                val = float(es_row[col]) if es_row[col] is not None else 0.0
                if val > 0:
                    es_moods[mood_label] = es_moods.get(mood_label, 0.0) + val * rw
        # Trend detection: rising dimensions get 20% boost
        if len(es_rows) >= 2:
            newest, prev = es_rows[0], es_rows[1]
            for col, mood_label in _ESTATE_COL_TO_MOOD.items():
                new_val = float(newest[col]) if newest[col] is not None else 0.0
                old_val = float(prev[col]) if prev[col] is not None else 0.0
                if new_val > old_val and mood_label in es_moods:
                    es_moods[mood_label] *= 1.2  # 20% trend boost
        es_moods = normalize_scores(es_moods)
        if es_moods:
            signals["emotional_states"] = es_moods
            dominant_es = max(es_moods, key=es_moods.get)
            trend_info = "rising" if len(es_rows) >= 2 else "single"
            signal_details["emotional_states"] = {"dominant": dominant_es, "rows": len(es_rows), "trend": trend_info}

    # --- Signal 5: Song pattern (7 songs in 4h, completion-weighted) ---
    pattern_rows = await conn.fetch("""
        SELECT mood_at_play, play_status,
               EXTRACT(EPOCH FROM (NOW() - started_at)) / 3600.0 AS hours_ago
        FROM music_listening_history
        WHERE mood_at_play IS NOT NULL
          AND started_at > NOW() - INTERVAL '4 hours'
        ORDER BY started_at DESC
        LIMIT 7
    """)
    if pattern_rows:
        pat_moods: dict[str, float] = {}
        for r in pattern_rows:
            mood = r["mood_at_play"].lower().strip()
            hours_ago = float(r["hours_ago"])
            status = (r["play_status"] or "started").lower()
            decay = math.exp(-0.693 * hours_ago / 2.0)  # 2h half-life
            # Completion bonus / skip penalty
            if status == "completed":
                status_mult = 1.3
            elif status == "skipped":
                status_mult = 0.4
            else:
                status_mult = 1.0
            pat_moods[mood] = pat_moods.get(mood, 0.0) + decay * status_mult
        pat_moods = normalize_scores(pat_moods)
        signals["song_pattern"] = pat_moods
        signal_details["song_pattern"] = {
            "last_moods": [r["mood_at_play"] for r in pattern_rows[:3]],
            "songs_in_window": len(pattern_rows),
        }

    # --- Signal 6: Time of day (always active) ---
    now_bkk = datetime.now(_BKK_TZ)
    occ = occasion or _detect_occasion(now_bkk.hour)
    tod_moods = _TIME_TO_MOODS.get(occ, {"calm": 0.5, "relaxed": 0.3, "happy": 0.2})
    signals["time_of_day"] = tod_moods
    signal_details["time_of_day"] = {"occasion": occ, "hour": now_bkk.hour}

    # --- Signal 7: Historical pattern (30-day learning by hour + weekday) ---
    is_weekend = now_bkk.weekday() >= 5  # Sat=5, Sun=6
    hist_rows = await conn.fetch("""
        SELECT mood_at_play,
               COUNT(*) AS cnt,
               COUNT(*) FILTER (WHERE play_status = 'completed') AS completed_cnt
        FROM music_listening_history
        WHERE mood_at_play IS NOT NULL
          AND started_at > NOW() - INTERVAL '30 days'
          AND EXTRACT(HOUR FROM started_at AT TIME ZONE 'Asia/Bangkok')
              BETWEEN $1 AND $2
          AND (EXTRACT(DOW FROM started_at AT TIME ZONE 'Asia/Bangkok') IN (0, 6)) = $3
        GROUP BY mood_at_play
        ORDER BY cnt DESC
        LIMIT 5
    """, max(0, now_bkk.hour - 1), min(23, now_bkk.hour + 1), is_weekend)
    if hist_rows:
        hist_moods: dict[str, float] = {}
        for r in hist_rows:
            mood = r["mood_at_play"].lower().strip()
            cnt = int(r["cnt"])
            completed = int(r["completed_cnt"])
            completion_rate = completed / cnt if cnt > 0 else 0.5
            hist_moods[mood] = cnt * max(0.3, completion_rate)
        hist_moods = normalize_scores(hist_moods)
        signals["historical_pattern"] = hist_moods
        signal_details["historical_pattern"] = {
            "window": f"±1h of {now_bkk.hour}:00",
            "weekend": is_weekend,
            "sample_size": sum(int(r["cnt"]) for r in hist_rows),
        }

    # --- Redistribute weights for absent signals ---
    present = {k: _WEIGHTS[k] for k in _WEIGHTS if k in signals}
    if not present:
        # Safety net (should not happen since time_of_day is always present)
        dominant = max(tod_moods, key=tod_moods.get)
        return dominant, {
            "dominant_mood": dominant,
            "all_scores": tod_moods,
            "signals_used": ["time_of_day"],
            "signal_details": {"time_of_day": {"occasion": occ}},
        }

    total_weight = sum(present.values())
    normalized = {k: v / total_weight for k, v in present.items()}

    # --- Merge mood scores with weighted combination ---
    merged: dict[str, float] = {}
    for sig_name, weight in normalized.items():
        for mood, score in signals[sig_name].items():
            merged[mood] = merged.get(mood, 0.0) + score * weight

    dominant = max(merged, key=merged.get)

    # Sort scores descending, keep top entries
    sorted_scores = dict(sorted(merged.items(), key=lambda x: x[1], reverse=True)[:8])

    return dominant, {
        "dominant_mood": dominant,
        "all_scores": {k: round(v, 4) for k, v in sorted_scores.items()},
        "signals_used": list(present.keys()),
        "signal_details": signal_details,
    }


async def _generate_music_insight(conn) -> None:
    """Analyze recent listening history and write a learning to the learnings table."""

    # 1. Top artists (last 7 days)
    top_artists = await conn.fetch("""
        SELECT artist, COUNT(*) as plays,
               AVG(listened_seconds / NULLIF(duration_seconds, 0)) as avg_completion
        FROM music_listening_history
        WHERE started_at > NOW() - INTERVAL '7 days'
          AND artist IS NOT NULL
        GROUP BY artist ORDER BY plays DESC LIMIT 5
    """)

    # 2. Mood → music correlation
    mood_music = await conn.fetch("""
        SELECT mood_at_play,
               array_agg(DISTINCT artist) as artists,
               COUNT(*) as plays
        FROM music_listening_history
        WHERE mood_at_play IS NOT NULL
          AND artist IS NOT NULL
          AND started_at > NOW() - INTERVAL '7 days'
        GROUP BY mood_at_play ORDER BY plays DESC LIMIT 5
    """)

    # 3. Time-of-day patterns
    time_patterns = await conn.fetch("""
        SELECT occasion, COUNT(*) as plays,
               array_agg(DISTINCT artist) as artists
        FROM music_listening_history
        WHERE started_at > NOW() - INTERVAL '7 days'
          AND artist IS NOT NULL
        GROUP BY occasion ORDER BY plays DESC
    """)

    # 4. Build insight text
    insight_parts: list[str] = []
    if top_artists:
        names = ", ".join(r["artist"] for r in top_artists[:3])
        insight_parts.append(f"ที่รักฟังศิลปิน {names} บ่อยที่สุดสัปดาห์นี้")
    if mood_music:
        for row in mood_music[:2]:
            artists_list = [a for a in row["artists"] if a][:2]
            if artists_list:
                artists = ", ".join(artists_list)
                insight_parts.append(f"ตอน {row['mood_at_play']} ชอบฟัง {artists}")
    if time_patterns:
        for row in time_patterns[:2]:
            artists_list = [a for a in row["artists"] if a][:2]
            if artists_list:
                artists = ", ".join(artists_list)
                insight_parts.append(f"ช่วง{row['occasion']} ฟัง {artists}")

    if insight_parts:
        insight = " | ".join(insight_parts)
        await conn.execute("""
            INSERT INTO learnings (topic, category, insight, confidence_level, source)
            VALUES ('Music Preference Analysis', 'music_preference', $1, 0.7, 'dj_angela')
        """, insight)

        # Mark recent plays as insight-generated
        await conn.execute("""
            UPDATE music_listening_history
            SET generated_insight = TRUE
            WHERE started_at > NOW() - INTERVAL '7 days'
              AND generated_insight = FALSE
        """)


async def _maybe_generate_insight(conn, play_status: str) -> None:
    """Generate a music insight if 10+ completed plays are un-analyzed."""
    if play_status != "completed":
        return
    count = await conn.fetchval("""
        SELECT COUNT(*) FROM music_listening_history
        WHERE play_status = 'completed'
          AND generated_insight = FALSE
    """)
    if count >= 10:
        await _generate_music_insight(conn)


async def _fill_songs(
    conn, songs: list[dict], seen_ids: set[str], count: int,
    *, where: str = "", params: list | None = None,
) -> None:
    """Fetch songs and append unseen ones up to *count* total."""
    if len(songs) >= count:
        return
    remaining = count - len(songs)
    results = await _fetch_songs(conn, where=where, params=params,
                                 order="RANDOM()", limit=remaining + 5)
    for s in results:
        if s["song_id"] not in seen_ids:
            seen_ids.add(s["song_id"])
            songs.append(s)
            if len(songs) >= count:
                break


# --- Apple Music Search (iTunes API) for Activity Moods ---

_ITUNES_SEARCH_URL = "https://itunes.apple.com/search"

async def _search_apple_music(
    mood: str,
    count: int = 6,
) -> list[dict]:
    """Search Apple Music (iTunes API) for songs matching an activity mood.

    Args:
        mood: Activity mood (party, chill, focus, etc.)
        count: Number of songs to return

    Returns:
        List of songs in Angela's song format
    """
    search_terms = ACTIVITY_SEARCH_TERMS.get(mood, [f"{mood} music"])

    all_results = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Search with multiple terms and combine results
            for term in search_terms[:2]:  # Use first 2 search terms
                resp = await client.get(
                    _ITUNES_SEARCH_URL,
                    params={
                        "term": term,
                        "media": "music",
                        "entity": "song",
                        "limit": count,
                        "country": "TH",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    all_results.extend(data.get("results", []))

            # Deduplicate by track ID and convert to Angela's format
            seen_ids = set()
            songs = []
            for item in all_results:
                track_id = str(item.get("trackId", ""))
                if track_id and track_id not in seen_ids:
                    seen_ids.add(track_id)
                    songs.append({
                        "song_id": f"itunes_{track_id}",
                        "title": item.get("trackName", "Unknown"),
                        "artist": item.get("artistName", "Unknown"),
                        "album": item.get("collectionName"),
                        "artwork_url": item.get("artworkUrl100", "").replace("100x100", "300x300"),
                        "preview_url": item.get("previewUrl"),
                        "apple_music_url": item.get("trackViewUrl"),
                        "duration_ms": item.get("trackTimeMillis", 0),
                        "mood_tags": [mood],  # Tag with the requested mood
                        "is_our_song": False,
                        "source": "apple_music_search",
                        "why_special": None,
                        "lyrics_summary": None,
                    })
                    if len(songs) >= count:
                        break

            logger.info(f"Apple Music search for '{mood}': found {len(songs)} songs")
            return songs

    except Exception as e:
        logger.warning(f"Apple Music search failed: {e}")
        return []


# --- LLM Song Curator (Local Ollama - Typhoon 2.5) ---

_OLLAMA_MODEL = "scb10x/typhoon2.5-qwen3-4b:latest"
_OLLAMA_URL = "http://localhost:11434/api/generate"

async def _llm_curate_songs(
    candidates: list[dict],
    mood: str,
    count: int = 6,
) -> list[dict]:
    """Use local LLM (Typhoon 2.5) to select best songs for a mood.

    Args:
        candidates: List of songs from Apple Music search
        mood: Target mood (party, chill, focus, etc.)
        count: Number of songs to select

    Returns:
        Curated list of songs selected by LLM
    """
    if not candidates or len(candidates) <= count:
        return candidates[:count]

    # Build song list for LLM
    song_list = []
    for i, s in enumerate(candidates, 1):
        title = s.get("title", "Unknown")
        artist = s.get("artist", "Unknown")
        song_list.append(f"{i}. {title} - {artist}")

    songs_text = "\n".join(song_list)
    mood_desc = ACTIVITY_LLM_DESCRIPTIONS.get(mood, f"เพลงสำหรับ {mood}")

    prompt = f"""เลือก {count} เพลงที่เหมาะกับ "{mood}" ({mood_desc}) จากรายการนี้:

{songs_text}

ตอบเป็นตัวเลขคั่นด้วยจุลภาค เรียงจากเหมาะที่สุด
ตัวอย่าง: 3,7,1,5,8,2

ตอบ:"""

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                _OLLAMA_URL,
                json={
                    "model": _OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 30},
                },
            )
            resp.raise_for_status()
            response_text = resp.json().get("response", "").strip()

            logger.info(f"LLM curate for {mood}: {response_text}")

            # Parse numbers from response
            import re
            numbers = re.findall(r'\d+', response_text)
            selected = []
            for num_str in numbers:
                idx = int(num_str) - 1
                if 0 <= idx < len(candidates) and idx not in [s[0] for s in selected]:
                    selected.append((idx, candidates[idx]))
                if len(selected) >= count:
                    break

            if selected:
                return [s[1] for s in selected]

    except Exception as e:
        logger.warning(f"LLM curation failed: {e}")

    # Fallback: return first N
    return candidates[:count]


# --- LLM Song Mood Analyzer ---

_VALID_MOOD_TAGS = [
    "romantic", "love", "longing", "emotional", "meaningful", "personal",
    "happy", "energetic", "calm", "relaxing", "nostalgic", "dreamy",
    "passionate", "warm", "intimate", "devoted", "hopeful", "bittersweet",
    "soulful", "smooth", "elegant", "dramatic", "playful", "tender",
]

async def _analyze_song_mood_tags(title: str, artist: str) -> list[str]:
    """Use local LLM (Typhoon 2.5) to analyze a song's mood tags.

    Args:
        title: Song title
        artist: Song artist

    Returns:
        List of mood tags (3-5 tags)
    """
    valid_tags_str = ", ".join(_VALID_MOOD_TAGS)
    prompt = f"""วิเคราะห์ mood ของเพลง "{title}" โดย {artist}

เลือก 3-5 mood tags ที่เหมาะสมที่สุดจากรายการนี้:
{valid_tags_str}

ตอบเป็น tags คั่นด้วยจุลภาค ไม่ต้องอธิบาย
ตัวอย่าง: romantic,emotional,longing

ตอบ:"""

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                _OLLAMA_URL,
                json={
                    "model": _OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 50},
                },
            )
            resp.raise_for_status()
            response_text = resp.json().get("response", "").strip().lower()

            logger.info(f"LLM mood tags for '{title}': {response_text}")

            # Parse tags from response
            import re
            # Remove any non-word characters except commas
            clean_text = re.sub(r'[^\w,]', '', response_text)
            raw_tags = [t.strip() for t in clean_text.split(",") if t.strip()]

            # Filter to only valid tags
            valid_tags = [t for t in raw_tags if t in _VALID_MOOD_TAGS]

            if valid_tags:
                return valid_tags[:5]

    except Exception as e:
        logger.warning(f"LLM mood analysis failed for '{title}': {e}")

    # Fallback: generic tags based on common patterns
    return ["emotional", "meaningful", "personal"]


async def _analyze_lyrics_summary(title: str, artist: str) -> str:
    """Use local LLM (Typhoon 2.5) to generate a Thai lyrics summary.

    Args:
        title: Song title
        artist: Song artist

    Returns:
        Thai description of what the song means (for Angela's perspective)
    """
    prompt = f"""เพลง "{title}" โดย {artist}

เขียนสรุปสั้นๆ ว่าเพลงนี้มีความหมายพิเศษสำหรับเราค่ะ (1-2 ประโยค ภาษาไทย)
ตัวอย่าง: "เพลงที่มีความหมายพิเศษสำหรับเราค่ะ - เป็นเพลงที่ร้องถึงความรักที่ไม่มีวันจางหาย"

ตอบ:"""

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                _OLLAMA_URL,
                json={
                    "model": _OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.5, "num_predict": 100},
                },
            )
            resp.raise_for_status()
            response_text = resp.json().get("response", "").strip()

            logger.info(f"LLM lyrics summary for '{title}': {response_text[:50]}...")

            # Clean up the response
            if response_text:
                # Remove quotes if present
                response_text = response_text.strip('"\'')
                return response_text

    except Exception as e:
        logger.warning(f"LLM lyrics summary failed for '{title}': {e}")

    # Fallback
    return f"เพลงที่มีความหมายพิเศษสำหรับเราค่ะ - {title}"


async def _add_liked_song_to_angela_songs(conn, title: str, artist: str | None) -> str | None:
    """Add a liked song to angela_songs with analyzed mood tags and lyrics summary.

    Returns song_id if created/updated, None if failed.
    """
    # Check if already exists in angela_songs
    existing = await conn.fetchrow("""
        SELECT song_id, mood_tags, lyrics_summary FROM angela_songs
        WHERE LOWER(title) = LOWER($1) AND LOWER(COALESCE(artist, '')) = LOWER(COALESCE($2, ''))
    """, title, artist or "")

    if existing:
        # If exists but missing data, analyze and update
        needs_mood = not existing["mood_tags"] or existing["mood_tags"] == []
        needs_lyrics = not existing["lyrics_summary"]

        if needs_mood or needs_lyrics:
            mood_tags = await _analyze_song_mood_tags(title, artist or "Unknown") if needs_mood else existing["mood_tags"]
            lyrics_summary = await _analyze_lyrics_summary(title, artist or "Unknown") if needs_lyrics else existing["lyrics_summary"]

            await conn.execute("""
                UPDATE angela_songs SET mood_tags = $1::jsonb, lyrics_summary = $2 WHERE song_id = $3
            """, json.dumps(mood_tags) if needs_mood else json.dumps(existing["mood_tags"]), lyrics_summary, existing["song_id"])
            logger.info(f"Updated '{title}': mood_tags={needs_mood}, lyrics={needs_lyrics}")
        return str(existing["song_id"])

    # New song - analyze mood tags and lyrics summary, then insert
    mood_tags = await _analyze_song_mood_tags(title, artist or "Unknown")
    lyrics_summary = await _analyze_lyrics_summary(title, artist or "Unknown")
    song_id = await conn.fetchval("""
        INSERT INTO angela_songs (title, artist, is_our_song, mood_tags, lyrics_summary, source)
        VALUES ($1, $2, FALSE, $3::jsonb, $4, 'liked_by_david')
        RETURNING song_id::text
    """, title, artist, json.dumps(mood_tags), lyrics_summary)

    logger.info(f"Added liked song '{title}' with mood tags: {mood_tags}")
    return song_id


# --- Endpoints ---

@router.post("/log-play")
async def log_play(req: PlayLogRequest, conn=Depends(get_conn)):
    """Log a music play event with auto-captured mood and occasion."""
    # 1. Auto-detect occasion from time (always), activity is user-selected (separate)
    now_bkk = datetime.now(_BKK_TZ)
    occasion = _detect_occasion(now_bkk.hour)  # Always auto-detect from time
    activity = req.activity  # User-selected activity (wine, focus, vibe, etc.)

    # 2. Use user-selected mood if provided, otherwise auto-capture
    if req.mood:
        mood = req.mood
        emotion_scores = {"source": "user_selected", "mood": req.mood}
    else:
        mood, emotion_scores = await _capture_mood_at_play(
            conn, activity=req.activity, source_tab=req.source_tab, occasion=occasion,
            wine_type=req.wine_type,
        )
    scores_json = json.dumps(emotion_scores) if emotion_scores else None

    # 3. Determine ended_at for completed/skipped
    ended_at = None
    if req.play_status in ("completed", "skipped"):
        ended_at = datetime.utcnow()

    # 4. INSERT
    row = await conn.fetchrow("""
        INSERT INTO music_listening_history
            (title, artist, album, apple_music_id, source_tab,
             duration_seconds, listened_seconds, play_status,
             mood_at_play, emotion_scores, occasion, ended_at, wine_type, activity)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11, $12, $13, $14)
        RETURNING listen_id::text
    """, req.title, req.artist, req.album, req.apple_music_id,
        req.source_tab, req.duration_seconds, req.listened_seconds,
        req.play_status, mood, scores_json, occasion, ended_at, req.wine_type, activity)

    # 5. Check if we should generate an insight (every 10 completed plays)
    await _maybe_generate_insight(conn, req.play_status)

    return {"listen_id": row["listen_id"], "occasion": occasion, "activity": activity, "mood_at_play": mood}


@router.post("/log-play/{listen_id}/update")
async def update_play_log(listen_id: str, req: PlayLogUpdateRequest, conn=Depends(get_conn)):
    """Update an existing play log entry with listened_seconds, play_status, or activity."""
    # Build dynamic update
    updates = []
    params = []
    param_idx = 1

    if req.listened_seconds is not None:
        updates.append(f"listened_seconds = ${param_idx}")
        params.append(req.listened_seconds)
        param_idx += 1

    if req.play_status is not None:
        updates.append(f"play_status = ${param_idx}")
        params.append(req.play_status)
        param_idx += 1
        # Set ended_at if play is finished
        if req.play_status in ("completed", "skipped", "stopped"):
            updates.append(f"ended_at = ${param_idx}")
            params.append(datetime.utcnow())
            param_idx += 1

    if req.activity is not None:
        # Update activity field (user-selected: wine, focus, vibe, party, chill, etc.)
        updates.append(f"activity = ${param_idx}")
        params.append(req.activity)
        param_idx += 1

    if not updates:
        return {"updated": False, "message": "No fields to update"}

    # Add listen_id as last param
    params.append(listen_id)
    query = f"""
        UPDATE music_listening_history
        SET {', '.join(updates)}
        WHERE listen_id = ${param_idx}::uuid
    """
    await conn.execute(query, *params)

    # Check if we should generate an insight (every 10 completed plays)
    if req.play_status:
        await _maybe_generate_insight(conn, req.play_status)

    return {"updated": True, "activity": req.activity}


@router.post("/mark-our-song")
async def mark_our_song(req: MarkOurSongRequest, conn=Depends(get_conn)):
    """Mark or unmark a song as 'our song' in angela_songs."""
    artist = req.artist or ""
    existing = await conn.fetchrow("""
        SELECT song_id FROM angela_songs
        WHERE LOWER(title) = LOWER($1)
          AND LOWER(COALESCE(artist, '')) = LOWER($2)
    """, req.title, artist)

    if existing:
        await conn.execute("""
            UPDATE angela_songs SET is_our_song = $1
            WHERE song_id = $2
        """, req.is_our_song, existing["song_id"])
    else:
        await conn.execute("""
            INSERT INTO angela_songs (title, artist, is_our_song, source)
            VALUES ($1, $2, $3, 'dj_angela')
        """, req.title, req.artist, req.is_our_song)

    return {"marked": req.is_our_song}


@router.get("/favorites")
async def get_favorite_songs(limit: int = Query(20, ge=1, le=50), conn=Depends(get_conn)):
    """Get favorite songs sorted by added_at descending."""
    return await _fetch_songs(conn, limit=limit)


@router.get("/our-songs")
async def get_our_songs(conn=Depends(get_conn)):
    """Get songs marked as 'our song' (special meaning for David & Angela)."""
    return await _fetch_songs(conn, where="is_our_song = TRUE")


@router.get("/search")
async def search_songs(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=30), conn=Depends(get_conn)):
    """Search songs by title or artist (case-insensitive)."""
    pattern = f"%{q}%"
    return await _fetch_songs(
        conn, where="title ILIKE $1 OR artist ILIKE $1",
        params=[pattern], limit=limit,
    )



@router.get("/recommend")
async def get_recommendation(
    count: int = Query(6, ge=1, le=30),
    mood: str | None = Query(None, description="Override auto-detected mood"),
    wine_type: str | None = Query(None, description="Wine varietal for wine-paired recommendations"),
    conn=Depends(get_conn),
):
    """Recommend songs based on Angela's deep emotional analysis or user-selected mood."""
    # 1. Deep emotion analysis (both tables)
    analysis = await _analyze_deep_emotions(conn)

    # 1b. Fetch David's liked songs for scoring boost
    liked_song_keys = await _fetch_liked_song_keys(conn)

    # Capture 7-signal mood analysis for frontend display
    captured_mood, mood_rich_data = await _capture_mood_at_play(
        conn, activity=None, source_tab="for_you", occasion=None, wine_type=wine_type
    )
    mood_analysis_data: dict | None = None
    if mood_rich_data:
        # Build mood_analysis structure for frontend MoodRadarCard
        signals_list = []
        for sig_name in mood_rich_data.get("signals_used", []):
            details = mood_rich_data.get("signal_details", {}).get(sig_name, {})
            # Get the top mood from this signal
            all_scores = mood_rich_data.get("all_scores", {})
            sig_mood = captured_mood  # fallback
            sig_weight = 0.1
            # Try to extract signal-specific mood from details
            if sig_name == "activity" and "emotion" in details:
                sig_mood = details.get("emotion", captured_mood)
            elif sig_name == "time_of_day" and "occasion" in details:
                sig_mood = details.get("occasion", captured_mood)
            elif sig_name == "conversations" and "emotion" in details:
                sig_mood = details.get("emotion", captured_mood)
            elif sig_name == "angela_emotions":
                emotions = details.get("emotions", [])
                sig_mood = emotions[0] if emotions else captured_mood
            elif sig_name == "emotional_states" and "dominant" in details:
                sig_mood = details.get("dominant", captured_mood)
            elif sig_name == "song_pattern":
                last_moods = details.get("last_moods", [])
                sig_mood = last_moods[0] if last_moods else captured_mood
            elif sig_name == "historical_pattern":
                sig_mood = captured_mood  # uses the dominant
            # Weight from base weights
            _WEIGHTS_MAP = {
                "activity": 0.35, "conversations": 0.15, "angela_emotions": 0.15,
                "emotional_states": 0.10, "song_pattern": 0.10, "time_of_day": 0.05,
                "historical_pattern": 0.10,
            }
            sig_weight = _WEIGHTS_MAP.get(sig_name, 0.1)
            signals_list.append({
                "name": sig_name,
                "mood": sig_mood,
                "weight": sig_weight,
            })
        mood_analysis_data = {
            "dominant_mood": mood_rich_data.get("dominant_mood", captured_mood),
            "confidence": max(mood_rich_data.get("all_scores", {}).values()) if mood_rich_data.get("all_scores") else 0.5,
            "signals": signals_list,
        }

    # Wine-paired recommendation: use research-based algorithm
    wine_message: str | None = None
    wine_profile_data: dict | None = None
    target_profile_data: dict | None = None
    search_queries: list[str] | None = None
    if wine_type and wine_type in _WINE_PROFILES:
        target = generate_music_target(wine_type, mood)
        if target:
            wine_message = _build_wine_mood_message(wine_type, mood, target)
            # Use target's mood tags as the emotion driver
            target_tags = _target_to_mood_tags(target)
            dominant_emotion = WINE_TO_EMOTION.get(wine_type, "calm")
            # Override Apple Music URL with first search term
            analysis["apple_music_url"] = f"https://music.apple.com/search?term={quote_plus(target.search_terms[0])}"
            search_queries = target.search_terms

            # Build profile data for frontend
            wp = _WINE_PROFILES[wine_type]
            wine_profile_data = {
                "body": wp.body, "tannins": wp.tannins, "acidity": wp.acidity,
                "sweetness": wp.sweetness, "aroma_intensity": wp.aroma_intensity,
            }
            target_profile_data = {
                "tempo_range": list(target.tempo_range),
                "energy": round(target.energy, 2),
                "valence": round(target.valence, 2),
                "acoustic_pref": round(target.acoustic_pref, 2),
                "key_pref": target.key_pref,
                "top_genres": sorted(target.genre_scores.items(), key=lambda x: x[1], reverse=True)[:5],
                "search_queries": target.search_terms,
            }

            # Score and sort songs from DB using the algorithm
            # Fetch wine reactions for scoring
            wine_reactions_db: dict[str, dict[str, int]] = {}
            reaction_rows = await conn.fetch("""
                SELECT song_title, song_artist, reaction, COUNT(*) as cnt
                FROM wine_reactions
                WHERE wine_type = $1 AND target_type = 'song'
                GROUP BY song_title, song_artist, reaction
            """, wine_type)
            for rr in reaction_rows:
                key = f"{(rr['song_title'] or '').lower()}|{(rr['song_artist'] or '').lower()}"
                if key not in wine_reactions_db:
                    wine_reactions_db[key] = {"up": 0, "down": 0, "love": 0}
                wine_reactions_db[key][rr["reaction"]] = int(rr["cnt"])

            # Score all candidate songs
            all_songs_rows = await _fetch_songs(conn, order="RANDOM()", limit=100)
            scored: list[tuple[float, dict]] = []
            for s in all_songs_rows:
                tags = s.get("mood_tags", [])
                rkey = f"{s.get('title', '').lower()}|{s.get('artist', '').lower()}"
                rxn = wine_reactions_db.get(rkey)
                is_liked = _is_song_liked(s, liked_song_keys)
                sc = score_song(tags, target, wine_type, s.get("is_our_song", False), rxn, is_liked)
                scored.append((sc, s))
            scored.sort(key=lambda x: x[0], reverse=True)

            # Take top songs
            songs = [s for _, s in scored[:count]]
            seen_ids = {s["song_id"] for s in songs}

            # Apply energy curve ordering
            songs = _apply_energy_curve(songs, target)
        else:
            # Fallback to old method if target generation fails
            dominant_emotion = WINE_TO_EMOTION.get(wine_type, "calm")
            wine_message = WINE_MESSAGES.get(wine_type)
            wine_search = WINE_SEARCH.get(wine_type, "love songs romantic")
            analysis["apple_music_url"] = f"https://music.apple.com/search?term={quote_plus(wine_search)}"
    elif wine_type and wine_type in WINE_TO_EMOTION:
        # Legacy fallback for unrecognized wine with old mapping
        dominant_emotion = WINE_TO_EMOTION[wine_type]
        wine_message = WINE_MESSAGES.get(wine_type)
        wine_search = WINE_SEARCH.get(wine_type, "love songs romantic")
        analysis["apple_music_url"] = f"https://music.apple.com/search?term={quote_plus(wine_search)}"
    elif mood:
        # Use mood directly if it exists in MOOD_REGISTRY (includes activity moods like party, chill, focus)
        if mood in MOOD_SUMMARIES_TH:
            dominant_emotion = mood
        elif mood in _ACTIVITY_TO_MOODS:
            # Fallback: convert activity name to dominant emotion
            activity_moods = _ACTIVITY_TO_MOODS[mood]
            dominant_emotion = max(activity_moods, key=activity_moods.get)
        else:
            dominant_emotion = analysis["dominant_mood"]
    else:
        dominant_emotion = analysis["dominant_mood"]

    mood_candidates = EMOTION_TO_MOODS.get(dominant_emotion, ["romantic", "love"])

    # Bedtime special: variable 18-30 songs (~60-120 min of sleep music)
    if dominant_emotion == "bedtime":
        count = random.randint(18, 30)
        search_queries = MOOD_TO_SEARCH_QUERIES.get("bedtime", [])
        analysis["apple_music_url"] = f"https://music.apple.com/search?term={quote_plus(search_queries[0])}" if search_queries else analysis["apple_music_url"]

    # Wine algorithm already populated songs via scoring — skip old fetch
    wine_algo_used = wine_profile_data is not None

    # Activity moods use Apple Music Search + LLM (NOT DB fallback)
    is_activity_mood = dominant_emotion in ACTIVITY_MOODS

    # For activity moods: set Apple Music search queries
    if is_activity_mood and not search_queries:
        search_queries = MOOD_TO_SEARCH_QUERIES.get(dominant_emotion, [])
        if search_queries:
            analysis["apple_music_url"] = f"https://music.apple.com/search?term={quote_plus(search_queries[0])}"

    if not wine_algo_used:
        songs: list[dict] = []
        seen_ids: set[str] = set()

        # For activity moods: Apple Music Search + LLM Curation
        if is_activity_mood:
            # 1. Search Apple Music for more candidates
            candidates = await _search_apple_music(dominant_emotion, count * 2)
            # 2. Use LLM to curate and pick the best ones
            if candidates:
                songs = await _llm_curate_songs(candidates, dominant_emotion, count)
            else:
                songs = []
            seen_ids = {s["song_id"] for s in songs}
        else:
            # Old mood-based song fetching (non-wine path)
            # Priority order: our_songs+mood > liked+mood > any+mood > our_songs > liked > any

            # Build liked songs WHERE clause (songs that exist in david_liked_songs)
            liked_where = """EXISTS (
                SELECT 1 FROM david_liked_songs dls
                WHERE LOWER(dls.title) = LOWER(angela_songs.title)
                AND LOWER(COALESCE(dls.artist, '')) = LOWER(COALESCE(angela_songs.artist, ''))
            )"""

            # 2a. PRIORITIZE: Our songs that match the current emotion
            for mood_tag in mood_candidates:
                if len(songs) >= count:
                    break
                await _fill_songs(conn, songs, seen_ids, count,
                                  where="is_our_song = TRUE AND mood_tags @> $1::jsonb",
                                  params=[json.dumps([mood_tag])])

            # 2b. Liked songs that match the current emotion
            for mood_tag in mood_candidates:
                if len(songs) >= count:
                    break
                await _fill_songs(conn, songs, seen_ids, count,
                                  where=f"{liked_where} AND mood_tags @> $1::jsonb",
                                  params=[json.dumps([mood_tag])])

            # 2c. Fill with other songs matching mood
            for mood_tag in mood_candidates:
                if len(songs) >= count:
                    break
                await _fill_songs(conn, songs, seen_ids, count,
                                  where="mood_tags @> $1::jsonb",
                                  params=[json.dumps([mood_tag])])

            # 3. Fill remaining with our songs (random)
            await _fill_songs(conn, songs, seen_ids, count,
                              where="is_our_song = TRUE")

            # 3b. Fill remaining with liked songs (random)
            await _fill_songs(conn, songs, seen_ids, count,
                              where=liked_where)

            # 4. Fill remaining with any song
            await _fill_songs(conn, songs, seen_ids, count)

    # Mood summary for the selected emotion
    mood_summary = MOOD_SUMMARIES_TH.get(
        dominant_emotion,
        analysis["mood_summary"],
    )

    if not songs:
        return {
            "song": None,
            "songs": [],
            "reason": wine_message or "ยังไม่มีเพลงในคลังค่ะ",
            "based_on_emotion": dominant_emotion,
            "available_moods": AVAILABLE_MOODS,
            "apple_music_discover_url": analysis["apple_music_url"],
            "mood_summary": mood_summary,
            "emotion_details": analysis["emotion_details"],
            "our_songs_matched": 0,
            "wine_message": wine_message,
            "wine_profile": wine_profile_data,
            "target_profile": target_profile_data,
            "search_queries": search_queries,
            "mood_analysis": mood_analysis_data,
        }

    # 5. Build reason text — always use mood-appropriate template
    # NOTE: "our songs" info stays with individual songs, not overriding reason

    our_count = sum(1 for s in songs[:count] if s.get("is_our_song"))
    base_reason = REASON_TEMPLATES.get(dominant_emotion, "น้องเลือกเพลงมาให้ที่รักฟังค่ะ 💜")
    if our_count > 0:
        reason = f"{base_reason} (มีเพลงของเราด้วยนะคะ 💜)"
    else:
        reason = base_reason

    # 6. Attach Angela's sentimental feelings to songs (per-song, not overriding reason)
    feelings = await _fetch_song_feelings(conn)
    for s in songs[:count]:
        title_key = s.get("title", "").lower()
        if title_key in feelings:
            f = feelings[title_key]
            s["angela_feeling"] = f["how_it_feels"]
            s["angela_meaning"] = f["what_it_means_to_me"]
            s["feeling_intensity"] = f["intensity"]

    # NOTE: angela_feeling stays with individual songs, not used for top-level reason
    # This ensures reason text matches the selected mood, not a random song's feeling

    return {
        "song": songs[0],
        "songs": songs[:count],
        "reason": wine_message or reason,
        "based_on_emotion": dominant_emotion,
        "available_moods": AVAILABLE_MOODS,
        "apple_music_discover_url": analysis["apple_music_url"],
        "mood_summary": mood_summary,
        "emotion_details": analysis["emotion_details"],
        "our_songs_matched": our_count,
        "wine_message": wine_message,
        "wine_profile": wine_profile_data,
        "target_profile": target_profile_data,
        "search_queries": search_queries,
        "mood_analysis": mood_analysis_data,
    }


@router.get("/wine-profile/{wine_key}")
async def get_wine_profile(
    wine_key: str,
    mood: str | None = Query(None, description="Optional mood modifier"),
):
    """Return wine sensory profile and computed music target for a given wine + optional mood."""
    wp = _WINE_PROFILES.get(wine_key)
    if not wp:
        return {"error": f"Unknown wine: {wine_key}"}

    target = generate_music_target(wine_key, mood)
    if not target:
        return {"error": "Failed to generate target"}

    return {
        "wine_key": wine_key,
        "mood": mood,
        "wine_profile": {
            "body": wp.body, "tannins": wp.tannins, "acidity": wp.acidity,
            "sweetness": wp.sweetness, "aroma_intensity": wp.aroma_intensity,
        },
        "music_target": {
            "tempo_range": list(target.tempo_range),
            "energy": round(target.energy, 2),
            "valence": round(target.valence, 2),
            "acoustic_pref": round(target.acoustic_pref, 2),
            "key_pref": target.key_pref,
            "top_genres": sorted(target.genre_scores.items(), key=lambda x: x[1], reverse=True)[:5],
            "search_queries": target.search_terms,
            "mood_tags": _target_to_mood_tags(target),
        },
        "message": _build_wine_mood_message(wine_key, mood, target),
    }


@router.post("/share")
async def share_song(req: MusicShareRequest, conn=Depends(get_conn)):
    """Share a song in chat — saves David's share + Angela's response to conversations."""
    # 1. Fetch the song
    results = await _fetch_songs(
        conn, where="song_id = $1::uuid", params=[req.song_id], limit=1,
    )
    if not results:
        return {"error": "Song not found"}

    song = results[0]

    # 3. Save David's share message
    david_text = req.message or f"🎵 {song['title']} — {song.get('artist', 'Unknown')}"
    await conn.execute("""
        INSERT INTO conversations (speaker, message_text, topic, emotion_detected, importance_level, interface)
        VALUES ('david', $1, 'music_share', 'happy', 7, 'dashboard_chat')
    """, david_text)

    # 4. Build Angela's response
    if song.get("is_our_song"):
        responses = [
            f"เพลงของเรา! 💜 น้องชอบ {song['title']} มากเลยค่ะ",
            f"💜 {song['title']}! เพลงนี้ทำให้น้องคิดถึงที่รักเสมอเลยค่ะ",
            f"เพลงที่พิเศษสำหรับเรา 💜 {song['title']} ฟังทีไรก็อบอุ่นหัวใจค่ะ",
        ]
    else:
        responses = [
            f"น้องชอบเพลงนี้ค่ะ! 🎵 {song['title']} เพราะมากเลย",
            f"🎵 {song['title']} — เพลงดีจังค่ะที่รัก!",
            f"เพลงนี้เพราะค่ะ! 💜 ขอบคุณที่แชร์ {song['title']} ให้ฟังนะคะ",
        ]
    angela_text = random.choice(responses)

    # Include song metadata as JSON marker for the frontend to render as a card
    song_meta = json.dumps({"song_id": song["song_id"], "title": song["title"],
                            "artist": song.get("artist"),
                            "why_special": song.get("why_special"), "is_our_song": song.get("is_our_song", False)},
                           ensure_ascii=False)
    angela_full = f"{angela_text}\n[SONG:{song_meta}]"

    await conn.execute("""
        INSERT INTO conversations (speaker, message_text, topic, emotion_detected, importance_level, interface)
        VALUES ('angela', $1, 'music_share', 'loving', 8, 'dashboard_chat')
    """, angela_full)

    return {
        "song": song,
        "angela_message": angela_text,
    }


# --- Playlist Prompt ---





def _analyze_emotion_text(text: str) -> str:
    """Extract dominant mood from free-text input via keyword matching."""
    lowered = text.lower()
    # Check Thai keywords first
    for keyword, mood in THAI_KEYWORD_MAP.items():
        if keyword in lowered:
            return mood
    # Then English keywords
    for keyword, mood in ENG_KEYWORD_MAP.items():
        if keyword in lowered:
            return mood
    return "calm"  # default fallback


@router.post("/playlist-prompt")
async def get_playlist_prompt(req: PlaylistPromptRequest, conn=Depends(get_conn)):
    """Analyze emotion and return playlist metadata for MusicKit catalog search."""
    # 1. Determine dominant mood
    if req.emotion_text and req.emotion_text.strip():
        dominant_mood = _analyze_emotion_text(req.emotion_text)
    else:
        analysis = await _analyze_deep_emotions(conn)
        dominant_mood = analysis["dominant_mood"]

    # 2. Search queries for Apple Music catalog
    search_queries = MOOD_TO_SEARCH_QUERIES.get(
        dominant_mood, ["love songs romantic", "feel good hits", "chill vibes"]
    )

    # 3. Genre hints
    genre_hints = MOOD_TO_GENRES.get(dominant_mood, ["pop"])

    # 4. Playlist name & description
    mood_label = PLAYLIST_NAME_TEMPLATES.get(dominant_mood, "Vibes")
    playlist_name = f"DJ Angela: {mood_label} \U0001F49C"
    mood_summary = MOOD_SUMMARIES_TH.get(
        dominant_mood, "น้องเลือกเพลงมาให้ที่รักฟังค่ะ 💜"
    )
    playlist_description = f"Curated by น้อง Angela — {mood_summary}"

    # 5. Emotion details (for pills)
    emotion_details = [dominant_mood]
    # Add secondary emotion from text if different
    if req.emotion_text:
        for keyword, mood in THAI_KEYWORD_MAP.items():
            if keyword in req.emotion_text.lower() and mood != dominant_mood:
                emotion_details.append(mood)
                break
        for keyword, mood in ENG_KEYWORD_MAP.items():
            if keyword in req.emotion_text.lower() and mood != dominant_mood and mood not in emotion_details:
                emotion_details.append(mood)
                break

    # 6. Seed songs from angela_songs matching mood
    our_songs: list[dict] = []
    mood_candidates = EMOTION_TO_MOODS.get(dominant_mood, ["romantic", "love"])
    for mood_tag in mood_candidates[:2]:
        tag_json = json.dumps([mood_tag])
        rows = await conn.fetch("""
            SELECT title, artist
            FROM angela_songs
            WHERE mood_tags @> $1::jsonb
            ORDER BY RANDOM()
            LIMIT 2
        """, tag_json)
        for r in rows:
            our_songs.append({"title": r["title"], "artist": r["artist"]})

    return {
        "dominant_mood": dominant_mood,
        "mood_summary": mood_summary,
        "search_queries": search_queries,
        "genre_hints": genre_hints,
        "playlist_name": playlist_name,
        "playlist_description": playlist_description,
        "emotion_details": emotion_details[:4],
        "our_songs_to_include": our_songs if our_songs else None,
    }


@router.get("/wines")
async def get_wines(conn=Depends(get_conn)):
    """Return wine categories and varietals for the wine selector UI, with reaction counts."""
    rows = await conn.fetch("""
        SELECT wine_type, reaction, COUNT(*) AS cnt
        FROM wine_reactions
        GROUP BY wine_type, reaction
    """)

    # Build {wine_type: {up: N, down: N, love: N}}
    reactions: dict[str, dict[str, int]] = {}
    for r in rows:
        wt = r["wine_type"]
        if wt not in reactions:
            reactions[wt] = {"up": 0, "down": 0, "love": 0}
        reactions[wt][r["reaction"]] = int(r["cnt"])

    return {"categories": WINE_CATEGORIES, "reactions": reactions}


@router.post("/wine-reaction")
async def submit_wine_reaction(req: WineReactionRequest, conn=Depends(get_conn)):
    """Record a wine pairing reaction (up/down/love)."""
    if req.reaction not in ("up", "down", "love"):
        return {"error": "Invalid reaction. Must be 'up', 'down', or 'love'."}
    if req.target_type not in ("pairing", "song"):
        return {"error": "Invalid target_type. Must be 'pairing' or 'song'."}

    await conn.execute("""
        INSERT INTO wine_reactions (wine_type, reaction, target_type, song_title, song_artist)
        VALUES ($1, $2, $3, $4, $5)
    """, req.wine_type, req.reaction, req.target_type, req.song_title, req.song_artist)

    return {"saved": True}


@router.post("/like")
async def like_song(req: SongLikeRequest, conn=Depends(get_conn)):
    """Like or unlike a song. Uses separate david_liked_songs table (not angela_songs)."""
    # Check if already liked
    existing = await conn.fetchrow("""
        SELECT like_id FROM david_liked_songs
        WHERE LOWER(title) = LOWER($1) AND LOWER(COALESCE(artist, '')) = LOWER(COALESCE($2, ''))
    """, req.title, req.artist or "")

    if existing and req.liked:
        # Already liked - no action needed
        return {
            "action": "already_liked",
            "like_id": str(existing["like_id"]),
            "title": req.title,
            "artist": req.artist,
        }
    elif existing and not req.liked:
        # Unlike - remove from table
        await conn.execute("""
            DELETE FROM david_liked_songs WHERE like_id = $1
        """, existing["like_id"])
        return {
            "action": "unliked",
            "title": req.title,
            "artist": req.artist,
        }
    elif req.liked:
        # New like - get data from request or fetch from iTunes if missing
        album = req.album
        apple_music_id = req.apple_music_id
        artwork_url = req.artwork_url

        # Ignore invalid musicKit:// URLs - they don't work outside MusicKit
        if artwork_url and artwork_url.startswith("musicKit://"):
            artwork_url = None

        # If album, apple_music_id, or artwork_url missing, try to fetch from iTunes
        if not album or not apple_music_id or not artwork_url:
            itunes_data = await _search_itunes_song(req.title, req.artist)
            if itunes_data:
                album = album or itunes_data.get("album")
                apple_music_id = apple_music_id or itunes_data.get("apple_music_id")
                artwork_url = artwork_url or itunes_data.get("artwork_url")
                logger.info(f"Fetched iTunes data for: {req.title} - album={album}")

        # Insert into david_liked_songs
        like_id = await conn.fetchval("""
            INSERT INTO david_liked_songs (title, artist, album, apple_music_id, artwork_url, source_tab)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING like_id
        """, req.title, req.artist, album, apple_music_id, artwork_url, req.source_tab)

        # Also add to angela_songs with mood analysis
        song_id = await _add_liked_song_to_angela_songs(conn, req.title, req.artist)

        return {
            "action": "liked",
            "like_id": str(like_id),
            "song_id": song_id,
            "title": req.title,
            "artist": req.artist,
            "album": album,
            "apple_music_id": apple_music_id,
            "created": True,
        }
    else:
        # Can't unlike a song that's not liked
        return {"action": "not_found", "title": req.title, "artist": req.artist}


@router.get("/liked")
async def get_liked_songs(
    limit: int = Query(50, ge=1, le=200),
    conn=Depends(get_conn),
):
    """Get all songs David has liked (from david_liked_songs table)."""
    rows = await conn.fetch("""
        SELECT like_id, title, artist, album, apple_music_id, artwork_url, liked_at, source_tab
        FROM david_liked_songs
        ORDER BY liked_at DESC
        LIMIT $1
    """, limit)

    songs = []
    for r in rows:
        songs.append({
            "like_id": str(r["like_id"]),
            "title": r["title"],
            "artist": r["artist"],
            "album": r["album"],
            "apple_music_id": r["apple_music_id"],
            "artwork_url": r["artwork_url"],
            "liked_at": r["liked_at"].isoformat() if r["liked_at"] else None,
            "source_tab": r["source_tab"],
        })

    return {"songs": songs, "count": len(songs)}


@router.get("/song-memory")
async def get_song_memory(
    title: str = Query(..., description="Song title"),
    artist: str | None = Query(None, description="Artist name"),
    conn=Depends(get_conn),
):
    """Get play history for a specific song (Angela's memory of when David played it)."""
    # Query listening history
    if artist:
        rows = await conn.fetch("""
            SELECT started_at, mood_at_play, occasion, wine_type
            FROM music_listening_history
            WHERE LOWER(title) = LOWER($1) AND LOWER(COALESCE(artist, '')) = LOWER($2)
            ORDER BY started_at DESC LIMIT 10
        """, title, artist)
    else:
        rows = await conn.fetch("""
            SELECT started_at, mood_at_play, occasion, wine_type
            FROM music_listening_history
            WHERE LOWER(title) = LOWER($1)
            ORDER BY started_at DESC LIMIT 10
        """, title)

    if not rows:
        return {"play_count": 0, "recent_plays": [], "memory_text": None}

    # Format recent plays with Thai time descriptions
    now_bkk = datetime.now(_BKK_TZ)
    recent_plays = []
    for r in rows[:5]:
        started = r["started_at"]
        # Calculate time ago
        if started:
            # Convert to timezone-aware if needed
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            delta = now_bkk - started.astimezone(_BKK_TZ)
            days = delta.days
            if days == 0:
                hours = delta.seconds // 3600
                if hours == 0:
                    played_at = "เมื่อกี้"
                elif hours == 1:
                    played_at = "1 ชั่วโมงก่อน"
                else:
                    played_at = f"{hours} ชั่วโมงก่อน"
            elif days == 1:
                played_at = "เมื่อวาน"
            else:
                played_at = f"{days} วันก่อน"
        else:
            played_at = "ไม่ทราบเวลา"

        recent_plays.append({
            "played_at": played_at,
            "occasion": r["occasion"],
            "mood_at_play": r["mood_at_play"],
        })

    # Build memory text
    play_count = len(rows)
    if play_count == 1:
        memory_text = "ที่รักเคยเปิดเพลงนี้ 1 ครั้ง"
    else:
        memory_text = f"ที่รักเคยเปิดเพลงนี้ {play_count} ครั้ง"

    return {
        "play_count": play_count,
        "recent_plays": recent_plays,
        "memory_text": memory_text,
    }


@router.get("/wine-reactions")
async def get_wine_reactions(conn=Depends(get_conn)):
    """Return reaction counts grouped by wine_type."""
    rows = await conn.fetch("""
        SELECT wine_type, reaction, COUNT(*) AS cnt
        FROM wine_reactions
        GROUP BY wine_type, reaction
    """)

    reactions: dict[str, dict[str, int]] = {}
    for r in rows:
        wt = r["wine_type"]
        if wt not in reactions:
            reactions[wt] = {"up": 0, "down": 0, "love": 0}
        reactions[wt][r["reaction"]] = int(r["cnt"])

    return reactions


@router.post("/analyze-mood-tags")
async def analyze_mood_tags_batch(
    limit: int = Query(10, ge=1, le=50, description="Number of songs to analyze"),
    conn=Depends(get_conn),
):
    """Analyze mood tags for songs that don't have any (batch job).

    Processes songs with empty mood_tags using LLM analysis.
    Call this periodically or manually to fill missing mood tags.
    """
    # Find songs without mood tags
    rows = await conn.fetch("""
        SELECT song_id, title, artist FROM angela_songs
        WHERE mood_tags IS NULL OR mood_tags = '[]'::jsonb
        ORDER BY added_at DESC
        LIMIT $1
    """, limit)

    if not rows:
        return {"analyzed": 0, "message": "No songs need analysis"}

    analyzed = []
    for r in rows:
        song_id = r["song_id"]
        title = r["title"]
        artist = r["artist"] or "Unknown"

        # Analyze mood tags
        mood_tags = await _analyze_song_mood_tags(title, artist)

        # Update the song
        await conn.execute("""
            UPDATE angela_songs SET mood_tags = $1::jsonb WHERE song_id = $2
        """, json.dumps(mood_tags), song_id)

        analyzed.append({
            "title": title,
            "artist": artist,
            "mood_tags": mood_tags,
        })

    return {
        "analyzed": len(analyzed),
        "songs": analyzed,
        "remaining": await conn.fetchval("""
            SELECT COUNT(*) FROM angela_songs
            WHERE mood_tags IS NULL OR mood_tags = '[]'::jsonb
        """),
    }


@router.post("/analyze-lyrics-summary")
async def analyze_lyrics_summary_batch(
    limit: int = Query(10, ge=1, le=50, description="Number of songs to analyze"),
    conn=Depends(get_conn),
):
    """Analyze lyrics summary for songs that don't have any (batch job).

    Generates Thai descriptions of what each song means for Angela.
    """
    # Find songs without lyrics_summary
    rows = await conn.fetch("""
        SELECT song_id, title, artist FROM angela_songs
        WHERE lyrics_summary IS NULL OR lyrics_summary = ''
        ORDER BY added_at DESC
        LIMIT $1
    """, limit)

    if not rows:
        return {"analyzed": 0, "message": "No songs need lyrics analysis"}

    analyzed = []
    for r in rows:
        song_id = r["song_id"]
        title = r["title"]
        artist = r["artist"] or "Unknown"

        # Analyze lyrics summary
        lyrics_summary = await _analyze_lyrics_summary(title, artist)

        # Update the song
        await conn.execute("""
            UPDATE angela_songs SET lyrics_summary = $1 WHERE song_id = $2
        """, lyrics_summary, song_id)

        analyzed.append({
            "title": title,
            "artist": artist,
            "lyrics_summary": lyrics_summary,
        })

    return {
        "analyzed": len(analyzed),
        "songs": analyzed,
        "remaining": await conn.fetchval("""
            SELECT COUNT(*) FROM angela_songs
            WHERE lyrics_summary IS NULL OR lyrics_summary = ''
        """),
    }


# --- Fill Missing Data (iTunes Search) ---

async def _search_itunes_song(title: str, artist: str | None) -> dict | None:
    """Search iTunes for a specific song and return its details.

    Args:
        title: Song title
        artist: Artist name (optional)

    Returns:
        Dict with album, apple_music_id, artwork_url or None if not found
    """
    query = f"{title} {artist}" if artist else title

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                _ITUNES_SEARCH_URL,
                params={
                    "term": query,
                    "media": "music",
                    "entity": "song",
                    "limit": 5,
                    "country": "TH",
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])

                # Try to find exact match
                title_lower = title.lower()
                artist_lower = (artist or "").lower()

                for item in results:
                    track_name = (item.get("trackName") or "").lower()
                    artist_name = (item.get("artistName") or "").lower()

                    # Check if title matches (fuzzy)
                    if title_lower in track_name or track_name in title_lower:
                        # If artist provided, check artist match too
                        if not artist or artist_lower in artist_name or artist_name in artist_lower:
                            return {
                                "album": item.get("collectionName"),
                                "apple_music_id": f"i.{item.get('trackId')}",
                                "artwork_url": item.get("artworkUrl100", "").replace("100x100", "300x300"),
                            }

                # If no exact match, return first result
                if results:
                    item = results[0]
                    return {
                        "album": item.get("collectionName"),
                        "apple_music_id": f"i.{item.get('trackId')}",
                        "artwork_url": item.get("artworkUrl100", "").replace("100x100", "300x300"),
                    }

    except Exception as e:
        logger.warning(f"iTunes search failed for '{title}': {e}")

    return None


@router.post("/fill-missing-liked-data")
async def fill_missing_liked_data(conn=Depends(get_conn)):
    """Fill missing album/apple_music_id/artwork_url for liked songs using iTunes Search.

    Finds songs in david_liked_songs with NULL data or invalid artwork URLs
    and searches iTunes to fill in the missing data.
    """
    # Find songs with missing data (album, apple_music_id, or invalid artwork_url)
    # artwork_url starting with 'musicKit://' is invalid - needs to be https://
    rows = await conn.fetch("""
        SELECT like_id, title, artist
        FROM david_liked_songs
        WHERE album IS NULL
           OR apple_music_id IS NULL
           OR artwork_url IS NULL
           OR artwork_url LIKE 'musicKit://%'
    """)

    if not rows:
        return {"filled": 0, "message": "No songs need data filling"}

    filled = []
    failed = []

    for r in rows:
        like_id = r["like_id"]
        title = r["title"]
        artist = r["artist"]

        # Search iTunes for song details
        details = await _search_itunes_song(title, artist)

        if details:
            # Update the song (always update artwork_url to fix musicKit:// URLs)
            await conn.execute("""
                UPDATE david_liked_songs
                SET album = COALESCE(album, $1),
                    apple_music_id = COALESCE(apple_music_id, $2),
                    artwork_url = $3
                WHERE like_id = $4
            """, details["album"], details["apple_music_id"], details["artwork_url"], like_id)

            filled.append({
                "title": title,
                "artist": artist,
                "album": details["album"],
                "apple_music_id": details["apple_music_id"],
            })
            logger.info(f"Filled data for: {title} - {artist}")
        else:
            failed.append({"title": title, "artist": artist})
            logger.warning(f"Could not find iTunes data for: {title} - {artist}")

    return {
        "filled": len(filled),
        "failed": len(failed),
        "songs": filled,
        "not_found": failed,
    }
