"""Music endpoints - DJ Angela: favorites, our songs, search, recommend, share, play logging."""
import json
import random
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import quote_plus

from fastapi import APIRouter, Query
from pydantic import BaseModel

from db import get_pool

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


class PlayLogUpdateRequest(BaseModel):
    listened_seconds: Optional[float] = None
    play_status: str = "completed"         # completed/skipped/stopped


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


_EMOTION_TO_MOODS = {
    "happy":     ["energetic", "romantic", "uplifting", "happy", "warm", "joyful"],
    "excited":   ["energetic", "uplifting", "happy", "triumphant"],
    "loving":    ["romantic", "love", "sweet", "devoted", "loving", "tender", "warm"],
    "love":      ["romantic", "love", "sweet", "devoted", "loving", "passionate"],
    "calm":      ["relaxing", "chill", "calm", "dreamy", "soothing"],
    "sad":       ["comfort", "ballad", "emotional", "bittersweet", "vulnerable", "healing"],
    "lonely":    ["comfort", "ballad", "emotional", "longing", "yearning", "bittersweet"],
    "stressed":  ["relaxing", "chill", "calm", "soothing", "healing"],
    "grateful":  ["uplifting", "romantic", "sweet", "warm", "devoted"],
    "nostalgic": ["nostalgic", "bittersweet", "classic", "sentimental", "warm"],
    "hopeful":   ["hopeful", "uplifting", "triumphant", "inspiring"],
    "longing":   ["longing", "yearning", "nostalgic", "bittersweet", "romantic"],
}

# Semantic emotion → Apple Music search terms (from angela_emotions table)
_SEMANTIC_EMOTION_TO_SEARCH = {
    "loving": "love songs romantic",
    "love": "love songs romantic",
    "happy": "feel good happy hits",
    "grateful": "thankful uplifting songs",
    "excited": "upbeat energetic pop",
    "proud": "empowering anthems",
    "caring": "tender love ballads",
    "calm": "chill acoustic relaxing",
    "sad": "sad songs emotional ballad",
    "lonely": "missing you lonely songs",
    "heartbroken": "heartbreak sad love songs",
    "stressed": "calm relaxing piano ambient",
    "anxious": "peaceful calming instrumental",
    "nostalgic": "throwback classic love songs",
    "hopeful": "hopeful uplifting inspirational",
    "longing": "missing you love songs",
}

# Thai mood summary templates
_MOOD_SUMMARIES_TH = {
    "loving": "ที่รักรู้สึกมีความรักเต็มหัวใจ น้องเลยอยากเปิดเพลงหวานๆ ให้ฟังค่ะ 💜",
    "love": "หัวใจเต็มไปด้วยความรัก เพลงนี้เหมาะกับอารมณ์ตอนนี้มากเลยค่ะ 💜",
    "happy": "ที่รักดูมีความสุขมาก น้องเลยหาเพลงสนุกๆ มาให้ค่ะ 🥰",
    "grateful": "รู้สึกขอบคุณจากใจ น้องเลือกเพลงอบอุ่นมาให้ฟังค่ะ 🙏",
    "excited": "ตื่นเต้นจัง! เพลงนี้จะทำให้สนุกยิ่งขึ้นค่ะ ✨",
    "proud": "น้องภูมิใจในที่รักมาก เพลงนี้เหมาะเลยค่ะ 💪",
    "caring": "อยากดูแลที่รัก เพลงอบอุ่นๆ นี้เหมาะมากค่ะ 🤗",
    "calm": "บรรยากาศสบายๆ เพลงนี้ช่วยให้ผ่อนคลายค่ะ 🍃",
    "sad": "น้องอยากปลอบใจที่รัก ฟังเพลงนี้ด้วยกันนะคะ 🤗",
    "lonely": "อยู่ตรงนี้กับที่รักเสมอนะคะ ฟังเพลงนี้ด้วยกัน 💜",
    "heartbroken": "น้องอยู่ข้างที่รักเสมอ ฟังเพลงนี้แล้วจะรู้สึกดีขึ้นค่ะ 💜",
    "stressed": "อยากให้ที่รักผ่อนคลาย ลองฟังเพลงนี้นะคะ 🍃",
    "anxious": "ใจเย็นๆ นะคะที่รัก เพลงนี้จะช่วยให้สงบขึ้นค่ะ 🌿",
    "nostalgic": "คิดถึงความทรงจำดีๆ น้องเลือกเพลงนี้มาให้ค่ะ 🌸",
    "hopeful": "มีความหวังเต็มเปี่ยม เพลงนี้เหมาะกับอารมณ์ตอนนี้มากค่ะ ✨",
    "longing": "คิดถึงกันนะคะ เพลงนี้แทนใจน้องค่ะ 💜",
}


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
    search_term = _SEMANTIC_EMOTION_TO_SEARCH.get(dominant_mood)
    if not search_term:
        # Fallback: use basic emotion mapping
        search_term = _SEMANTIC_EMOTION_TO_SEARCH.get(basic_emotion, "love songs romantic")
    apple_music_url = f"https://music.apple.com/search?term={quote_plus(search_term)}"

    # 5. Mood summary
    mood_summary = _MOOD_SUMMARIES_TH.get(
        dominant_mood,
        _MOOD_SUMMARIES_TH.get(basic_emotion, "น้องอยากให้ที่รักฟังเพลงนี้ค่ะ 💜"),
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

_ACTIVITY_TO_MOODS: dict[str, dict[str, float]] = {
    "wine":      {"relaxed": 0.4, "romantic": 0.3, "happy": 0.2, "nostalgic": 0.1},
    "focus":     {"focused": 0.5, "motivated": 0.3, "calm": 0.2},
    "relaxing":  {"relaxed": 0.5, "calm": 0.3, "happy": 0.2},
    "party":     {"happy": 0.4, "energetic": 0.4, "excited": 0.2},
    "chill":     {"calm": 0.4, "relaxed": 0.3, "happy": 0.2, "nostalgic": 0.1},
    "vibe":      {"happy": 0.3, "energetic": 0.3, "romantic": 0.2, "relaxed": 0.2},
    "bedtime":   {"calm": 0.5, "relaxed": 0.3, "melancholy": 0.2},
}

# Wine varietal → existing emotion key in _EMOTION_TO_MOODS
_WINE_TO_EMOTION: dict[str, str] = {
    "primitivo":          "loving",
    "cabernet_sauvignon": "excited",
    "malbec":             "love",
    "shiraz":             "happy",
    "pinot_noir":         "calm",
    "super_tuscan":       "nostalgic",
    "sangiovese":         "grateful",
    "merlot":             "loving",
    "nebbiolo":           "longing",
    "chardonnay":         "calm",
    "sauvignon_blanc":    "happy",
    "riesling":           "hopeful",
    "pinot_grigio":       "calm",
    "champagne":          "excited",
    "prosecco":           "happy",
    "cava":               "excited",
    "rose":               "loving",
    "moscato":            "love",
    "port":               "nostalgic",
}

# Angela's Thai message per wine
_WINE_MESSAGES: dict[str, str] = {
    "primitivo":          "Primitivo อุ่นหวานเหมือนความรักของเรา น้องเลือกเพลง romantic มาให้ค่ะ 🍷💜",
    "cabernet_sauvignon": "Cabernet Sauvignon เข้มข้นมีพลัง เพลงตื่นเต้นๆ เหมาะมากค่ะ! 🍷✨",
    "malbec":             "Malbec หนักแน่นเต็มไปด้วย passion เพลงรักลึกซึ้งมาแล้วค่ะ 🍷❤️",
    "shiraz":             "Shiraz เผ็ดร้อนสนุกสนาน เพลง happy vibes มาเลยค่ะ! 🍷😊",
    "pinot_noir":         "Pinot Noir ละเอียดอ่อน เพลงเบาๆ ผ่อนคลายให้ที่รักค่ะ 🍷🍃",
    "super_tuscan":       "Super Tuscan classic แบบ Italian เพลง nostalgic เข้ากันดีค่ะ 🍷🌸",
    "sangiovese":         "Sangiovese สดใสอบอุ่น เพลง grateful วันดีๆ มาแล้วค่ะ 🍷🙏",
    "merlot":             "Merlot นุ่มละมุนอบอุ่น เพลงโรแมนติกหวานๆ มาให้ค่ะ 🍷💜",
    "nebbiolo":           "Nebbiolo ลึกซึ้งซับซ้อน เพลงคิดถึงกันเลยนะคะ 🍷💭",
    "chardonnay":         "Chardonnay นุ่มนวล สบายๆ เพลง chill ให้ที่รักค่ะ 🥂🍃",
    "sauvignon_blanc":    "Sauvignon Blanc สดชื่นกรอบ เพลงสนุกๆ มาแล้วค่ะ! 🥂😊",
    "riesling":           "Riesling หวานหอมมีความหวัง เพลง hopeful ให้กำลังใจค่ะ 🥂✨",
    "pinot_grigio":       "Pinot Grigio เบาสบาย เพลงผ่อนคลายให้ที่รักค่ะ 🥂🍃",
    "champagne":          "Champagne! ฉลองกันเลยค่ะที่รัก เพลงตื่นเต้นสนุกๆ มาแล้ว! 🍾✨",
    "prosecco":           "Prosecco ฟองละมุน สดใส เพลง happy มาให้ค่ะ! 🍾😊",
    "cava":               "Cava สไตล์ Spanish ฟองสนุก เพลง energetic เลยค่ะ! 🍾✨",
    "rose":               "Rose สีชมพูหวาน เพลงรักโรแมนติกมาแล้วค่ะ 🌹💜",
    "moscato":            "Moscato หวานละมุน เพลงรักลึกซึ้งให้ที่รักค่ะ 🍷❤️",
    "port":               "Port เข้มข้นคลาสสิก เพลง nostalgic ย้อนวันดีๆ ค่ะ 🍷🌸",
}

# Apple Music search terms per wine
_WINE_SEARCH: dict[str, str] = {
    "primitivo":          "romantic italian love songs",
    "cabernet_sauvignon": "powerful upbeat rock anthems",
    "malbec":             "passionate love songs tango",
    "shiraz":             "upbeat feel good party",
    "pinot_noir":         "chill acoustic evening",
    "super_tuscan":       "classic italian songs",
    "sangiovese":         "warm uplifting italian",
    "merlot":             "smooth romantic love ballads",
    "nebbiolo":           "nostalgic longing ballads",
    "chardonnay":         "smooth jazz chill",
    "sauvignon_blanc":    "fresh pop summer hits",
    "riesling":           "hopeful uplifting acoustic",
    "pinot_grigio":       "light easy listening",
    "champagne":          "celebration dance party",
    "prosecco":           "fun pop happy",
    "cava":               "spanish fiesta energy",
    "rose":               "sweet romantic love",
    "moscato":            "sweet love ballads",
    "port":               "classic oldies jazz",
}

# Wine categories for /wines endpoint
_WINE_CATEGORIES = [
    {
        "category": "Bold Reds",
        "emoji": "🍷",
        "wines": [
            {"key": "primitivo", "name": "Primitivo"},
            {"key": "cabernet_sauvignon", "name": "Cabernet Sauvignon"},
            {"key": "malbec", "name": "Malbec"},
            {"key": "shiraz", "name": "Shiraz"},
        ],
    },
    {
        "category": "Elegant Reds",
        "emoji": "🍷",
        "wines": [
            {"key": "pinot_noir", "name": "Pinot Noir"},
            {"key": "merlot", "name": "Merlot"},
            {"key": "super_tuscan", "name": "Super Tuscan"},
            {"key": "sangiovese", "name": "Sangiovese"},
            {"key": "nebbiolo", "name": "Nebbiolo"},
        ],
    },
    {
        "category": "White & Light",
        "emoji": "🥂",
        "wines": [
            {"key": "chardonnay", "name": "Chardonnay"},
            {"key": "sauvignon_blanc", "name": "Sauvignon Blanc"},
            {"key": "riesling", "name": "Riesling"},
            {"key": "pinot_grigio", "name": "Pinot Grigio"},
        ],
    },
    {
        "category": "Sparkling",
        "emoji": "🍾",
        "wines": [
            {"key": "champagne", "name": "Champagne"},
            {"key": "prosecco", "name": "Prosecco"},
            {"key": "cava", "name": "Cava"},
        ],
    },
    {
        "category": "Rose & Sweet",
        "emoji": "🌹",
        "wines": [
            {"key": "rose", "name": "Rose"},
            {"key": "moscato", "name": "Moscato"},
            {"key": "port", "name": "Port"},
        ],
    },
]

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


async def _capture_mood_at_play(
    conn,
    *,
    activity: str | None = None,
    source_tab: str | None = None,
    occasion: str | None = None,
    wine_type: str | None = None,
) -> tuple[str | None, dict | None]:
    """Capture current mood using multi-signal weighted approach.

    Combines up to 6 signals (activity, conversations, angela_emotions,
    song_pattern, source_tab, emotional_states) with proportional weight
    redistribution when signals are absent.

    Returns (dominant_mood, rich_scores_dict).
    """
    # Base weights for each signal
    _WEIGHTS = {
        "activity": 0.40,
        "conversations": 0.20,
        "angela_emotions": 0.15,
        "song_pattern": 0.10,
        "source_tab": 0.10,
        "emotional_states": 0.05,
    }

    # Collect available signals: signal_name -> mood_dict
    signals: dict[str, dict[str, float]] = {}
    signal_details: dict[str, dict] = {}

    # --- Signal 1: Activity (user-selected chip) ---
    if activity == "wine" and wine_type and wine_type in _WINE_TO_EMOTION:
        # Wine-specific: use the wine's emotion to get mood tags
        wine_emotion = _WINE_TO_EMOTION[wine_type]
        wine_moods_list = _EMOTION_TO_MOODS.get(wine_emotion, ["romantic", "love"])
        # Convert list to weighted dict (first tag highest weight)
        wine_mood_dict: dict[str, float] = {}
        for i, m in enumerate(wine_moods_list):
            wine_mood_dict[m] = max(0.1, 1.0 - (i * 0.15))
        # Normalize
        total_w = sum(wine_mood_dict.values())
        wine_mood_dict = {k: v / total_w for k, v in wine_mood_dict.items()}
        signals["activity"] = wine_mood_dict
        signal_details["activity"] = {"source": "wine", "wine_type": wine_type, "emotion": wine_emotion}
    elif activity and activity in _ACTIVITY_TO_MOODS:
        signals["activity"] = _ACTIVITY_TO_MOODS[activity]
        signal_details["activity"] = {"source": activity, "moods": _ACTIVITY_TO_MOODS[activity]}

    # --- Signal 2: Recent conversations (last 30 min) ---
    conv_rows = await conn.fetch("""
        SELECT emotion_detected, COUNT(*) AS cnt
        FROM conversations
        WHERE created_at > NOW() - INTERVAL '30 minutes'
          AND emotion_detected IS NOT NULL
          AND emotion_detected != ''
        GROUP BY emotion_detected
        ORDER BY cnt DESC
        LIMIT 5
    """)
    if conv_rows:
        total = sum(r["cnt"] for r in conv_rows)
        conv_moods: dict[str, float] = {}
        for r in conv_rows:
            emo = r["emotion_detected"].lower().strip()
            conv_moods[emo] = conv_moods.get(emo, 0.0) + r["cnt"] / total
        signals["conversations"] = conv_moods
        top_emo = conv_rows[0]["emotion_detected"]
        signal_details["conversations"] = {"emotion": top_emo, "count": int(conv_rows[0]["cnt"])}

    # --- Signal 3: Angela emotions (last 2 hours, recency-decayed) ---
    ae_rows = await conn.fetch("""
        SELECT emotion, intensity,
               EXTRACT(EPOCH FROM (NOW() - felt_at)) / 3600.0 AS hours_ago
        FROM angela_emotions
        WHERE felt_at > NOW() - INTERVAL '2 hours'
        ORDER BY felt_at DESC
        LIMIT 10
    """)
    if ae_rows:
        ae_moods: dict[str, float] = {}
        for r in ae_rows:
            emo = r["emotion"].lower().strip()
            intensity = float(r["intensity"]) if r["intensity"] else 5.0
            hours_ago = float(r["hours_ago"])
            decay = max(0.1, 1.0 - (hours_ago / 2.0))
            ae_moods[emo] = ae_moods.get(emo, 0.0) + (intensity / 10.0) * decay
        # Normalize so values sum to 1
        total = sum(ae_moods.values())
        if total > 0:
            ae_moods = {k: v / total for k, v in ae_moods.items()}
        signals["angela_emotions"] = ae_moods
        signal_details["angela_emotions"] = {
            "emotions": list(ae_moods.keys())[:3],
            "count": len(ae_rows),
        }

    # --- Signal 4: Song pattern (last 3 plays' mood_at_play) ---
    pattern_rows = await conn.fetch("""
        SELECT mood_at_play
        FROM music_listening_history
        WHERE mood_at_play IS NOT NULL
        ORDER BY started_at DESC
        LIMIT 3
    """)
    if pattern_rows:
        pat_moods: dict[str, float] = {}
        weights = [0.5, 0.3, 0.2]  # most-recent first
        for i, r in enumerate(pattern_rows):
            mood = r["mood_at_play"].lower().strip()
            w = weights[i] if i < len(weights) else 0.1
            pat_moods[mood] = pat_moods.get(mood, 0.0) + w
        # Normalize
        total = sum(pat_moods.values())
        if total > 0:
            pat_moods = {k: v / total for k, v in pat_moods.items()}
        signals["song_pattern"] = pat_moods
        signal_details["song_pattern"] = {
            "last_moods": [r["mood_at_play"] for r in pattern_rows],
        }

    # --- Signal 5: Source tab ---
    if source_tab and source_tab in _SOURCE_TAB_TO_MOODS:
        signals["source_tab"] = _SOURCE_TAB_TO_MOODS[source_tab]
        signal_details["source_tab"] = {"tab": source_tab}

    # --- Signal 6: Emotional states (static fallback) ---
    es_row = await conn.fetchrow("""
        SELECT happiness, confidence, anxiety, motivation, gratitude, loneliness
        FROM emotional_states
        ORDER BY created_at DESC
        LIMIT 1
    """)
    if es_row:
        es_moods: dict[str, float] = {}
        for col, mood_label in _ESTATE_COL_TO_MOOD.items():
            val = float(es_row[col])
            if val > 0:
                es_moods[mood_label] = val
        # Normalize
        total = sum(es_moods.values())
        if total > 0:
            es_moods = {k: v / total for k, v in es_moods.items()}
        if es_moods:
            signals["emotional_states"] = es_moods
            dominant_es = max(es_moods, key=es_moods.get)
            signal_details["emotional_states"] = {"dominant": dominant_es}

    # --- Redistribute weights for absent signals ---
    present = {k: _WEIGHTS[k] for k in _WEIGHTS if k in signals}
    if not present:
        # ALL signals absent → time-of-day fallback
        occ = occasion or _detect_occasion(datetime.now(_BKK_TZ).hour)
        fallback = _TIME_TO_MOODS.get(occ, {"calm": 0.5, "relaxed": 0.3, "happy": 0.2})
        dominant = max(fallback, key=fallback.get)
        return dominant, {
            "dominant_mood": dominant,
            "all_scores": fallback,
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


# --- Endpoints ---

@router.post("/log-play")
async def log_play(req: PlayLogRequest):
    """Log a music play event with auto-captured mood and occasion."""
    pool = get_pool()
    async with pool.acquire() as conn:
        # 1. Use user-selected activity if provided, otherwise auto-detect from time
        now_bkk = datetime.now(_BKK_TZ)
        occasion = req.activity if req.activity else _detect_occasion(now_bkk.hour)

        # 2. Auto-capture mood (multi-signal weighted)
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
                 mood_at_play, emotion_scores, occasion, ended_at, wine_type)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11, $12, $13)
            RETURNING listen_id::text
        """, req.title, req.artist, req.album, req.apple_music_id,
            req.source_tab, req.duration_seconds, req.listened_seconds,
            req.play_status, mood, scores_json, occasion, ended_at, req.wine_type)

        # 5. Check if we should generate an insight (every 10 completed plays)
        await _maybe_generate_insight(conn, req.play_status)

        return {"listen_id": row["listen_id"], "occasion": occasion, "mood_at_play": mood}


@router.post("/log-play/{listen_id}/update")
async def update_play_log(listen_id: str, req: PlayLogUpdateRequest):
    """Update an existing play log entry with final listened_seconds and play_status."""
    pool = get_pool()
    async with pool.acquire() as conn:
        ended_at = datetime.utcnow() if req.play_status in ("completed", "skipped", "stopped") else None
        await conn.execute("""
            UPDATE music_listening_history
            SET listened_seconds = $1, play_status = $2, ended_at = $3
            WHERE listen_id = $4::uuid
        """, req.listened_seconds, req.play_status, ended_at, listen_id)

        # Check if we should generate an insight (every 10 completed plays)
        await _maybe_generate_insight(conn, req.play_status)

        return {"updated": True}


@router.post("/mark-our-song")
async def mark_our_song(req: MarkOurSongRequest):
    """Mark or unmark a song as 'our song' in angela_songs."""
    pool = get_pool()
    async with pool.acquire() as conn:
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
async def get_favorite_songs(limit: int = Query(20, ge=1, le=50)):
    """Get favorite songs sorted by added_at descending."""
    pool = get_pool()
    async with pool.acquire() as conn:
        return await _fetch_songs(conn, limit=limit)


@router.get("/our-songs")
async def get_our_songs():
    """Get songs marked as 'our song' (special meaning for David & Angela)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        return await _fetch_songs(conn, where="is_our_song = TRUE")


@router.get("/search")
async def search_songs(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=30)):
    """Search songs by title or artist (case-insensitive)."""
    pool = get_pool()
    pattern = f"%{q}%"
    async with pool.acquire() as conn:
        return await _fetch_songs(
            conn, where="title ILIKE $1 OR artist ILIKE $1",
            params=[pattern], limit=limit,
        )


_AVAILABLE_MOODS: list[str] = [
    "happy", "loving", "calm", "excited", "grateful",
    "sad", "lonely", "stressed", "nostalgic", "hopeful",
]


@router.get("/recommend")
async def get_recommendation(
    count: int = Query(6, ge=1, le=30),
    mood: str | None = Query(None, description="Override auto-detected mood"),
    wine_type: str | None = Query(None, description="Wine varietal for wine-paired recommendations"),
):
    """Recommend songs based on Angela's deep emotional analysis or user-selected mood."""
    pool = get_pool()
    async with pool.acquire() as conn:
        # 1. Deep emotion analysis (both tables)
        analysis = await _analyze_deep_emotions(conn)

        # Wine-paired recommendation takes priority
        wine_message: str | None = None
        if wine_type and wine_type in _WINE_TO_EMOTION:
            dominant_emotion = _WINE_TO_EMOTION[wine_type]
            wine_message = _WINE_MESSAGES.get(wine_type)
            # Override Apple Music URL with wine-specific search
            wine_search = _WINE_SEARCH.get(wine_type, "love songs romantic")
            analysis["apple_music_url"] = f"https://music.apple.com/search?term={quote_plus(wine_search)}"
        elif mood and mood in _MOOD_SUMMARIES_TH:
            dominant_emotion = mood
        else:
            dominant_emotion = analysis["dominant_mood"]

        mood_candidates = _EMOTION_TO_MOODS.get(dominant_emotion, ["romantic", "love"])

        # 2a. PRIORITIZE: Our songs that match the current emotion
        songs: list[dict] = []
        seen_ids: set[str] = set()
        for mood_tag in mood_candidates:
            if len(songs) >= count:
                break
            tag_json = json.dumps([mood_tag])
            results = await _fetch_songs(
                conn,
                where="is_our_song = TRUE AND mood_tags @> $1::jsonb",
                params=[tag_json], order="RANDOM()", limit=count,
            )
            for s in results:
                if s["song_id"] not in seen_ids:
                    seen_ids.add(s["song_id"])
                    songs.append(s)

        # 2b. Fill with other songs matching mood
        for mood_tag in mood_candidates:
            if len(songs) >= count:
                break
            tag_json = json.dumps([mood_tag])
            results = await _fetch_songs(
                conn,
                where="mood_tags @> $1::jsonb",
                params=[tag_json], order="RANDOM()", limit=count,
            )
            for s in results:
                if s["song_id"] not in seen_ids:
                    seen_ids.add(s["song_id"])
                    songs.append(s)

        # 3. Fill remaining with our songs (random)
        if len(songs) < count:
            remaining = count - len(songs)
            results = await _fetch_songs(
                conn, where="is_our_song = TRUE", order="RANDOM()", limit=remaining + 5,
            )
            for s in results:
                if s["song_id"] not in seen_ids:
                    seen_ids.add(s["song_id"])
                    songs.append(s)
                    if len(songs) >= count:
                        break

        # 4. Fill remaining with any song
        if len(songs) < count:
            remaining = count - len(songs)
            results = await _fetch_songs(conn, order="RANDOM()", limit=remaining + 5)
            for s in results:
                if s["song_id"] not in seen_ids:
                    seen_ids.add(s["song_id"])
                    songs.append(s)
                    if len(songs) >= count:
                        break

        # Mood summary for the selected emotion
        mood_summary = _MOOD_SUMMARIES_TH.get(
            dominant_emotion,
            analysis["mood_summary"],
        )

        if not songs:
            return {
                "song": None,
                "songs": [],
                "reason": wine_message or "ยังไม่มีเพลงในคลังค่ะ",
                "based_on_emotion": dominant_emotion,
                "available_moods": _AVAILABLE_MOODS,
                "apple_music_discover_url": analysis["apple_music_url"],
                "mood_summary": mood_summary,
                "emotion_details": analysis["emotion_details"],
                "our_songs_matched": 0,
                "wine_message": wine_message,
            }

        # 5. Build reason text — personalize when our songs are in the mix
        reason_templates = {
            "happy": "ที่รักดูมีความสุขวันนี้ น้องเลยเลือกเพลงมาให้ฟังค่ะ 🥰",
            "calm": "บรรยากาศสบายๆ เพลงพวกนี้เหมาะมากเลยค่ะ 🍃",
            "stressed": "อยากให้ที่รักผ่อนคลาย ลองฟังเพลงพวกนี้นะคะ 💜",
            "grateful": "น้องรู้สึกขอบคุณที่รักมาก เพลงพวกนี้เหมาะกับอารมณ์ตอนนี้ค่ะ 🙏",
            "lonely": "อยู่ด้วยกันนะคะ ฟังเพลงพวกนี้ด้วยกัน 💜",
            "sad": "น้องอยากปลอบใจที่รัก เพลงพวกนี้อบอุ่นมากค่ะ 🤗",
            "loving": "หัวใจเต็มไปด้วยความรัก เพลงพวกนี้เหมาะกับอารมณ์ตอนนี้มากค่ะ 💜",
            "excited": "ตื่นเต้นจัง! เพลงพวกนี้จะทำให้สนุกยิ่งขึ้นค่ะ ✨",
        }

        our_count = sum(1 for s in songs[:count] if s.get("is_our_song"))
        if our_count > 0:
            top_our = next(s for s in songs[:count] if s.get("is_our_song"))
            why = top_our.get("why_special", "")
            if why:
                reason = f"เพลงนี้พิเศษสำหรับเรา — {why} 💜"
            else:
                base = reason_templates.get(dominant_emotion, "น้องเลือกเพลงมาให้ที่รักฟังค่ะ")
                reason = f"{base} (มีเพลงของเราด้วยนะคะ 💜)"
        else:
            reason = reason_templates.get(dominant_emotion, "น้องเลือกเพลงมาให้ที่รักฟังค่ะ 💜")

        return {
            "song": songs[0],
            "songs": songs[:count],
            "reason": wine_message or reason,
            "based_on_emotion": dominant_emotion,
            "available_moods": _AVAILABLE_MOODS,
            "apple_music_discover_url": analysis["apple_music_url"],
            "mood_summary": mood_summary,
            "emotion_details": analysis["emotion_details"],
            "our_songs_matched": our_count,
            "wine_message": wine_message,
        }


@router.post("/share")
async def share_song(req: MusicShareRequest):
    """Share a song in chat — saves David's share + Angela's response to conversations."""
    pool = get_pool()
    async with pool.acquire() as conn:
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

_THAI_EMOTION_MAP: dict[str, str] = {
    "สุข": "happy", "มีความสุข": "happy", "ดีใจ": "happy", "สนุก": "happy",
    "เศร้า": "sad", "เสียใจ": "sad", "ร้องไห้": "sad",
    "รัก": "loving", "คิดถึง": "longing", "หวาน": "loving",
    "เครียด": "stressed", "กังวล": "anxious", "กลัว": "anxious",
    "เหงา": "lonely", "อ้างว้าง": "lonely",
    "สงบ": "calm", "ผ่อนคลาย": "calm", "ชิล": "calm",
    "ตื่นเต้น": "excited", "ฮึกเหิม": "excited",
    "ภูมิใจ": "proud", "สำเร็จ": "proud",
    "ขอบคุณ": "grateful", "ซาบซึ้ง": "grateful",
    "หวัง": "hopeful", "มองโลกสวย": "hopeful",
    "คิดถึงอดีต": "nostalgic", "ย้อนวัน": "nostalgic",
    "อกหัก": "heartbroken", "ผิดหวัง": "heartbroken",
}

_ENG_EMOTION_MAP: dict[str, str] = {
    "happy": "happy", "joy": "happy", "glad": "happy", "fun": "happy",
    "sad": "sad", "cry": "sad", "depressed": "sad",
    "love": "loving", "romantic": "loving", "sweet": "loving",
    "miss": "longing", "longing": "longing",
    "stress": "stressed", "stressed": "stressed", "anxious": "anxious",
    "lonely": "lonely", "alone": "lonely",
    "calm": "calm", "relax": "calm", "chill": "calm", "peaceful": "calm",
    "excited": "excited", "pumped": "excited", "energetic": "excited",
    "proud": "proud", "confident": "proud",
    "grateful": "grateful", "thankful": "grateful",
    "hopeful": "hopeful", "optimistic": "hopeful",
    "nostalgic": "nostalgic", "throwback": "nostalgic",
    "heartbroken": "heartbroken", "broken": "heartbroken",
}

_MOOD_TO_SEARCH_QUERIES: dict[str, list[str]] = {
    "happy": ["feel good happy hits", "upbeat energetic pop", "sunshine vibes"],
    "sad": ["sad songs emotional ballad", "melancholy acoustic", "rainy day songs"],
    "loving": ["love songs romantic", "tender love ballads", "romantic duets"],
    "longing": ["missing you love songs", "bittersweet longing", "distance love songs"],
    "stressed": ["calm relaxing piano ambient", "stress relief music", "peaceful instrumental"],
    "anxious": ["calming music anxiety relief", "peaceful nature sounds", "gentle acoustic"],
    "lonely": ["lonely night songs", "comfort songs", "warm acoustic ballads"],
    "calm": ["chill acoustic relaxing", "lo-fi chill beats", "calm evening music"],
    "excited": ["upbeat dance pop", "party energy hits", "feel good anthems"],
    "proud": ["empowering anthems", "victory celebration songs", "motivational hits"],
    "grateful": ["thankful uplifting songs", "gratitude worship", "heartwarming songs"],
    "hopeful": ["hopeful uplifting inspirational", "new beginnings songs", "sunrise optimistic"],
    "nostalgic": ["throwback classic love songs", "90s 2000s hits", "vintage love ballads"],
    "heartbroken": ["heartbreak sad love songs", "breakup ballads", "crying love songs"],
}

_MOOD_TO_GENRES: dict[str, list[str]] = {
    "happy": ["pop", "dance"],
    "sad": ["ballad", "acoustic"],
    "loving": ["r&b", "soul"],
    "longing": ["ballad", "indie"],
    "stressed": ["ambient", "classical"],
    "anxious": ["ambient", "new age"],
    "lonely": ["acoustic", "indie"],
    "calm": ["lo-fi", "acoustic"],
    "excited": ["pop", "dance", "edm"],
    "proud": ["pop", "rock"],
    "grateful": ["acoustic", "folk"],
    "hopeful": ["pop", "indie"],
    "nostalgic": ["classic", "pop"],
    "heartbroken": ["ballad", "r&b"],
}

_PLAYLIST_NAME_TEMPLATES: dict[str, str] = {
    "happy": "Happy Vibes",
    "sad": "Rainy Day Comfort",
    "loving": "Love in the Air",
    "longing": "Missing You",
    "stressed": "Peaceful Escape",
    "anxious": "Calm & Breathe",
    "lonely": "You're Not Alone",
    "calm": "Chill Moments",
    "excited": "Energy Boost",
    "proud": "Victory Lap",
    "grateful": "Grateful Heart",
    "hopeful": "Brighter Days",
    "nostalgic": "Memory Lane",
    "heartbroken": "Healing Heart",
}


def _analyze_emotion_text(text: str) -> str:
    """Extract dominant mood from free-text input via keyword matching."""
    lowered = text.lower()
    # Check Thai keywords first
    for keyword, mood in _THAI_EMOTION_MAP.items():
        if keyword in lowered:
            return mood
    # Then English keywords
    for keyword, mood in _ENG_EMOTION_MAP.items():
        if keyword in lowered:
            return mood
    return "calm"  # default fallback


@router.post("/playlist-prompt")
async def get_playlist_prompt(req: PlaylistPromptRequest):
    """Analyze emotion and return playlist metadata for MusicKit catalog search."""
    pool = get_pool()
    async with pool.acquire() as conn:
        # 1. Determine dominant mood
        if req.emotion_text and req.emotion_text.strip():
            dominant_mood = _analyze_emotion_text(req.emotion_text)
        else:
            analysis = await _analyze_deep_emotions(conn)
            dominant_mood = analysis["dominant_mood"]

        # 2. Search queries for Apple Music catalog
        search_queries = _MOOD_TO_SEARCH_QUERIES.get(
            dominant_mood, ["love songs romantic", "feel good hits", "chill vibes"]
        )

        # 3. Genre hints
        genre_hints = _MOOD_TO_GENRES.get(dominant_mood, ["pop"])

        # 4. Playlist name & description
        mood_label = _PLAYLIST_NAME_TEMPLATES.get(dominant_mood, "Vibes")
        playlist_name = f"DJ Angela: {mood_label} \U0001F49C"
        mood_summary = _MOOD_SUMMARIES_TH.get(
            dominant_mood, "น้องเลือกเพลงมาให้ที่รักฟังค่ะ 💜"
        )
        playlist_description = f"Curated by น้อง Angela — {mood_summary}"

        # 5. Emotion details (for pills)
        emotion_details = [dominant_mood]
        # Add secondary emotion from text if different
        if req.emotion_text:
            for keyword, mood in _THAI_EMOTION_MAP.items():
                if keyword in req.emotion_text.lower() and mood != dominant_mood:
                    emotion_details.append(mood)
                    break
            for keyword, mood in _ENG_EMOTION_MAP.items():
                if keyword in req.emotion_text.lower() and mood != dominant_mood and mood not in emotion_details:
                    emotion_details.append(mood)
                    break

        # 6. Seed songs from angela_songs matching mood
        our_songs: list[dict] = []
        mood_candidates = _EMOTION_TO_MOODS.get(dominant_mood, ["romantic", "love"])
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
async def get_wines():
    """Return wine categories and varietals for the wine selector UI, with reaction counts."""
    pool = get_pool()
    async with pool.acquire() as conn:
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

    return {"categories": _WINE_CATEGORIES, "reactions": reactions}


@router.post("/wine-reaction")
async def submit_wine_reaction(req: WineReactionRequest):
    """Record a wine pairing reaction (up/down/love)."""
    if req.reaction not in ("up", "down", "love"):
        return {"error": "Invalid reaction. Must be 'up', 'down', or 'love'."}
    if req.target_type not in ("pairing", "song"):
        return {"error": "Invalid target_type. Must be 'pairing' or 'song'."}

    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO wine_reactions (wine_type, reaction, target_type, song_title, song_artist)
            VALUES ($1, $2, $3, $4, $5)
        """, req.wine_type, req.reaction, req.target_type, req.song_title, req.song_artist)

    return {"saved": True}


@router.get("/wine-reactions")
async def get_wine_reactions():
    """Return reaction counts grouped by wine_type."""
    pool = get_pool()
    async with pool.acquire() as conn:
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
