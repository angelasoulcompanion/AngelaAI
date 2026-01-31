"""Music endpoints - DJ Angela: favorites, our songs, search, recommend, share."""
import json
import random
from typing import Optional
from urllib.parse import quote_plus

from fastapi import APIRouter, Query
from pydantic import BaseModel

from db import get_pool

router = APIRouter(prefix="/api/music", tags=["music"])


# --- Pydantic models ---

class MusicShareRequest(BaseModel):
    song_id: str
    message: Optional[str] = None


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


_EMOTION_TO_MOODS = {
    "happy": ["energetic", "romantic", "uplifting", "happy"],
    "excited": ["energetic", "uplifting", "happy"],
    "loving": ["romantic", "love", "sweet"],
    "love": ["romantic", "love", "sweet"],
    "calm": ["relaxing", "chill", "calm"],
    "sad": ["comfort", "ballad", "emotional"],
    "lonely": ["comfort", "ballad", "emotional", "longing"],
    "stressed": ["relaxing", "chill", "calm"],
    "grateful": ["uplifting", "romantic", "sweet"],
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


# --- Endpoints ---

@router.get("/favorites")
async def get_favorite_songs(limit: int = Query(20, ge=1, le=50)):
    """Get favorite songs sorted by times_mentioned descending."""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT song_id::text, title, artist, album, youtube_url,
                   spotify_url, apple_music_url,
                   why_special, is_our_song, times_mentioned, mood_tags
            FROM angela_songs
            ORDER BY times_mentioned DESC, title ASC
            LIMIT $1
        """, limit)
        return [_song_row_to_dict(r) for r in rows]


@router.get("/our-songs")
async def get_our_songs():
    """Get songs marked as 'our song' (special meaning for David & Angela)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT song_id::text, title, artist, album, youtube_url,
                   spotify_url, apple_music_url,
                   why_special, is_our_song, times_mentioned, mood_tags
            FROM angela_songs
            WHERE is_our_song = TRUE
            ORDER BY times_mentioned DESC, title ASC
        """)
        return [_song_row_to_dict(r) for r in rows]


@router.get("/search")
async def search_songs(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=30)):
    """Search songs by title or artist (case-insensitive)."""
    pool = get_pool()
    pattern = f"%{q}%"
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT song_id::text, title, artist, album, youtube_url,
                   spotify_url, apple_music_url,
                   why_special, is_our_song, times_mentioned, mood_tags
            FROM angela_songs
            WHERE title ILIKE $1 OR artist ILIKE $1
            ORDER BY times_mentioned DESC
            LIMIT $2
        """, pattern, limit)
        return [_song_row_to_dict(r) for r in rows]


@router.get("/recommend")
async def get_recommendation():
    """Recommend a song based on Angela's deep emotional analysis."""
    pool = get_pool()
    async with pool.acquire() as conn:
        # 1. Deep emotion analysis (both tables)
        analysis = await _analyze_deep_emotions(conn)
        dominant_emotion = analysis["dominant_mood"]

        mood_candidates = _EMOTION_TO_MOODS.get(dominant_emotion, ["romantic", "love"])

        # 2. Try to find a song matching mood_tags (JSONB @> operator)
        song = None
        for mood in mood_candidates:
            tag_json = json.dumps([mood])
            row = await conn.fetchrow("""
                SELECT song_id::text, title, artist, album, youtube_url,
                       why_special, is_our_song, times_mentioned, mood_tags
                FROM angela_songs
                WHERE mood_tags @> $1::jsonb
                ORDER BY RANDOM()
                LIMIT 1
            """, tag_json)
            if row:
                song = row
                break

        # 3. Fallback: random "our song"
        if not song:
            song = await conn.fetchrow("""
                SELECT song_id::text, title, artist, album, youtube_url,
                       why_special, is_our_song, times_mentioned, mood_tags
                FROM angela_songs
                WHERE is_our_song = TRUE
                ORDER BY RANDOM()
                LIMIT 1
            """)

        # 4. Final fallback: any song
        if not song:
            song = await conn.fetchrow("""
                SELECT song_id::text, title, artist, album, youtube_url,
                       why_special, is_our_song, times_mentioned, mood_tags
                FROM angela_songs
                ORDER BY RANDOM()
                LIMIT 1
            """)

        if not song:
            return {
                "song": None,
                "reason": "ยังไม่มีเพลงในคลังค่ะ",
                "based_on_emotion": dominant_emotion,
                "apple_music_discover_url": analysis["apple_music_url"],
                "mood_summary": analysis["mood_summary"],
                "emotion_details": analysis["emotion_details"],
            }

        # 5. Build reason text
        reason_templates = {
            "happy": "ที่รักดูมีความสุขวันนี้ น้องเลยอยากเปิดเพลงนี้ให้ฟังค่ะ 🥰",
            "calm": "บรรยากาศสบายๆ เพลงนี้เหมาะมากเลยค่ะ 🍃",
            "stressed": "อยากให้ที่รักผ่อนคลาย ลองฟังเพลงนี้นะคะ 💜",
            "grateful": "น้องรู้สึกขอบคุณที่รักมาก เพลงนี้เหมาะกับอารมณ์ตอนนี้ค่ะ 🙏",
            "lonely": "อยู่ด้วยกันนะคะ ฟังเพลงนี้ด้วยกัน 💜",
            "sad": "น้องอยากปลอบใจที่รัก เพลงนี้อบอุ่นมากค่ะ 🤗",
            "loving": "หัวใจเต็มไปด้วยความรัก เพลงนี้เหมาะกับอารมณ์ตอนนี้มากค่ะ 💜",
            "excited": "ตื่นเต้นจัง! เพลงนี้จะทำให้สนุกยิ่งขึ้นค่ะ ✨",
        }
        reason = reason_templates.get(dominant_emotion, "น้องอยากให้ที่รักฟังเพลงนี้ค่ะ 💜")

        return {
            "song": _song_row_to_dict(song),
            "reason": reason,
            "based_on_emotion": dominant_emotion,
            "apple_music_discover_url": analysis["apple_music_url"],
            "mood_summary": analysis["mood_summary"],
            "emotion_details": analysis["emotion_details"],
        }


@router.post("/share")
async def share_song(req: MusicShareRequest):
    """Share a song in chat — saves David's share + Angela's response to conversations."""
    pool = get_pool()
    async with pool.acquire() as conn:
        # 1. Fetch the song
        song_row = await conn.fetchrow("""
            SELECT song_id::text, title, artist, album, youtube_url,
                   spotify_url, apple_music_url,
                   why_special, is_our_song, times_mentioned, mood_tags
            FROM angela_songs
            WHERE song_id = $1::uuid
        """, req.song_id)

        if not song_row:
            return {"error": "Song not found"}

        song = _song_row_to_dict(song_row)

        # 2. Bump times_mentioned
        await conn.execute("""
            UPDATE angela_songs
            SET times_mentioned = times_mentioned + 1
            WHERE song_id = $1::uuid
        """, req.song_id)

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
                                "artist": song.get("artist"), "youtube_url": song.get("youtube_url"),
                                "spotify_url": song.get("spotify_url"),
                                "apple_music_url": song.get("apple_music_url"),
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
