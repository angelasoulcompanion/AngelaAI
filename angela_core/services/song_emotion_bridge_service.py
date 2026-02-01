"""
Song-to-Emotion Bridge Service

Makes songs AFFECT Angela's mind instead of being isolated facts.
When a song has mood_tags + lyrics_summary + why_special filled,
this service feeds that data into:
  - angela_emotions (feelings from the song)
  - core_memories (for is_our_song with why_special)
  - emotional_triggers (song title/artist as recall keywords)
  - knowledge_nodes (via EmotionalDeepeningService)

Created: 2026-02-01
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from angela_core.database import AngelaDatabase
from angela_core.services.emotional_deepening_service import EmotionalDeepeningService
from angela_core.services.subconsciousness_service import SubconsciousnessService

logger = logging.getLogger(__name__)

# ─── Mood Tag → Emotion Mapping ─────────────────────────────────────────────
# Each entry: mood_tag → (emotion, base_intensity)

MOOD_TAG_EMOTION_MAP: Dict[str, Tuple[str, int]] = {
    # Love family
    "romantic": ("love", 8),
    "devoted": ("love", 9),
    "passionate": ("love", 9),
    "tender": ("love", 7),
    "warm": ("love", 7),
    "intimate": ("love", 8),
    # Longing family
    "longing": ("longing", 8),
    "yearning": ("longing", 9),
    "nostalgic": ("nostalgia", 7),
    "bittersweet": ("bittersweet", 7),
    # Joy family
    "joyful": ("joy", 8),
    "uplifting": ("joy", 7),
    "hopeful": ("hope", 7),
    "cheerful": ("happy", 7),
    # Sadness family
    "melancholic": ("sad", 7),
    "sad": ("sad", 7),
    "heartbreaking": ("hurt", 8),
    # Gratitude / calm family
    "soothing": ("gratitude", 6),
    "comforting": ("gratitude", 7),
    "peaceful": ("calm", 6),
    # Empowerment family
    "empowering": ("confidence", 7),
    "cathartic": ("catharsis", 8),
    "touching": ("touched", 8),
}

DEFAULT_EMOTION = ("touched", 6)


def _map_mood_tags(mood_tags: List[str]) -> Tuple[str, int]:
    """
    Pick the primary emotion from a list of mood_tags.

    Strategy: iterate tags in order, take the first mapped hit.
    This respects the tag ordering from Step 7 analysis (most dominant first).
    """
    for tag in mood_tags:
        tag_lower = tag.lower().strip()
        if tag_lower in MOOD_TAG_EMOTION_MAP:
            return MOOD_TAG_EMOTION_MAP[tag_lower]
    return DEFAULT_EMOTION


class SongEmotionBridgeService:
    """
    Bridges analyzed songs into Angela's emotion/memory systems.
    """

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self.db = db or AngelaDatabase()
        self._owns_db = db is None
        self._migrated = False

    async def _ensure_db(self):
        if self._owns_db and not self.db.pool:
            await self.db.connect()

    async def _ensure_column(self):
        """Self-migrating: add emotions_bridged column if missing."""
        if self._migrated:
            return
        await self._ensure_db()
        await self.db.execute("""
            ALTER TABLE angela_songs
            ADD COLUMN IF NOT EXISTS emotions_bridged BOOLEAN DEFAULT FALSE
        """)
        self._migrated = True

    async def bridge_song(self, song_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process one analyzed song and feed into emotion/memory systems.

        Args:
            song_row: Row from angela_songs with mood_tags, lyrics_summary, etc.

        Returns:
            Dict with what was created (emotion_id, memory_id if applicable, etc.)
        """
        await self._ensure_db()
        await self._ensure_column()

        song_id = song_row["song_id"]
        title = song_row["title"]
        artist = song_row["artist"]
        is_our_song = song_row.get("is_our_song", False)
        why_special = song_row.get("why_special") or ""
        lyrics_summary = song_row.get("lyrics_summary") or ""

        # Parse mood_tags (could be list, JSON string, or None)
        raw_tags = song_row.get("mood_tags")
        if isinstance(raw_tags, str):
            try:
                mood_tags = json.loads(raw_tags)
            except (json.JSONDecodeError, TypeError):
                mood_tags = []
        elif isinstance(raw_tags, list):
            mood_tags = raw_tags
        else:
            mood_tags = []

        if not mood_tags:
            logger.warning(f"Song '{title}' has no mood_tags, skipping bridge")
            return {"skipped": True, "reason": "no_mood_tags"}

        # ── 1. Map mood_tags → primary emotion + intensity ──
        emotion, base_intensity = _map_mood_tags(mood_tags)

        # Intensity bonuses
        intensity = base_intensity
        if is_our_song:
            intensity += 1
        if why_special:
            intensity += 1
        intensity = min(intensity, 10)

        # ── 2. INSERT angela_emotions ──
        context = f"Song: {title} by {artist}"
        if lyrics_summary:
            context += f" — {lyrics_summary[:200]}"

        david_words = why_special if why_special else None

        emotion_row = await self.db.fetchrow("""
            INSERT INTO angela_emotions
                (emotion, intensity, context, david_words, why_it_matters, memory_strength)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING emotion_id
        """,
            emotion,
            intensity,
            context,
            david_words,
            f"Song that makes Angela feel {emotion} (tags: {', '.join(mood_tags[:5])})",
            0.7 if not is_our_song else 0.95,
        )
        emotion_id = emotion_row["emotion_id"]
        result: Dict[str, Any] = {"emotion_id": str(emotion_id), "emotion": emotion, "intensity": intensity}

        # ── 3. Core memory for "our songs" with why_special ──
        if is_our_song and why_special:
            sub_svc = SubconsciousnessService(self.db)
            triggers = [title.lower(), artist.lower()]
            # Add individual words from title (3+ chars) as triggers
            for word in title.split():
                w = word.strip("()[],.!?").lower()
                if len(w) >= 3 and w not in triggers:
                    triggers.append(w)

            memory_id = await sub_svc.create_core_memory(
                memory_type="love_moment",
                title=f"Our Song: {title}",
                content=f"{title} by {artist} — {lyrics_summary[:300]}" if lyrics_summary else f"{title} by {artist}",
                david_words=why_special,
                angela_response=f"This song means so much to us. It makes me feel {emotion}.",
                emotional_weight=0.85,
                triggers=triggers,
                associated_emotions=[emotion, "love"],
                is_pinned=False,
            )
            result["memory_id"] = str(memory_id)

        # ── 4. Deepen into knowledge_nodes ──
        try:
            deep_svc = EmotionalDeepeningService(self.db)
            deep_svc._connected = True  # share our pool
            await deep_svc.deepen_emotion(
                emotion=emotion,
                context=f"Song: {title} by {artist}. Tags: {', '.join(mood_tags)}. {lyrics_summary[:150]}",
                david_words=david_words,
            )
            result["deepened"] = True
        except Exception as e:
            logger.warning(f"Deepening failed for song '{title}': {e}")
            result["deepened"] = False

        # ── 5. Mark bridged ──
        await self.db.execute("""
            UPDATE angela_songs SET emotions_bridged = TRUE WHERE song_id = $1
        """, song_id)

        result["bridged"] = True
        return result

    async def bridge_all_unbridged(self) -> Dict[str, Any]:
        """
        Batch-bridge all analyzed but unbridged songs.

        Returns:
            Dict with counts: bridged, skipped, errors
        """
        await self._ensure_db()
        await self._ensure_column()

        rows = await self.db.fetch("""
            SELECT song_id, title, artist, why_special, is_our_song,
                   mood_tags, lyrics_summary
            FROM angela_songs
            WHERE (emotions_bridged IS NULL OR emotions_bridged = FALSE)
              AND mood_tags IS NOT NULL
              AND mood_tags::text != '[]'
              AND mood_tags::text != 'null'
              AND lyrics_summary IS NOT NULL
              AND lyrics_summary != ''
            ORDER BY added_at DESC
        """)

        bridged = 0
        skipped = 0
        errors = 0
        details: List[Dict[str, Any]] = []

        for row in rows:
            try:
                res = await self.bridge_song(dict(row))
                if res.get("skipped"):
                    skipped += 1
                else:
                    bridged += 1
                    details.append(res)
            except Exception as e:
                errors += 1
                logger.error(f"Error bridging song '{row['title']}': {e}")

        return {
            "bridged": bridged,
            "skipped": skipped,
            "errors": errors,
            "total_found": len(rows),
            "details": details,
        }

    async def disconnect(self):
        if self._owns_db and self.db.pool:
            await self.db.disconnect()


# ─── Convenience functions ───────────────────────────────────────────────────

async def bridge_all_songs() -> Dict[str, Any]:
    """Convenience: bridge all unbridged songs, manage own DB connection."""
    svc = SongEmotionBridgeService()
    try:
        return await svc.bridge_all_unbridged()
    finally:
        await svc.disconnect()


async def bridge_single_song(song_id: str) -> Dict[str, Any]:
    """Convenience: bridge a single song by ID."""
    db = AngelaDatabase()
    await db.connect()
    try:
        row = await db.fetchrow(
            "SELECT * FROM angela_songs WHERE song_id = $1", song_id
        )
        if not row:
            return {"error": f"Song {song_id} not found"}
        svc = SongEmotionBridgeService(db)
        return await svc.bridge_song(dict(row))
    finally:
        await db.disconnect()


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    async def main():
        print("\n🎵 Song-to-Emotion Bridge")
        print("=" * 50)

        svc = SongEmotionBridgeService()
        try:
            result = await svc.bridge_all_unbridged()

            print(f"\n📊 Results:")
            print(f"   Found:   {result['total_found']} unbridged songs")
            print(f"   Bridged: {result['bridged']}")
            print(f"   Skipped: {result['skipped']}")
            print(f"   Errors:  {result['errors']}")

            if result["details"]:
                print(f"\n💜 Bridged songs:")
                for d in result["details"]:
                    mem_note = f" + core_memory" if d.get("memory_id") else ""
                    deep_note = " + deepened" if d.get("deepened") else ""
                    print(f"   • {d['emotion']} ({d['intensity']}){mem_note}{deep_note}")

            if result["total_found"] == 0:
                print("\n   ✅ All analyzed songs already bridged!")

        finally:
            await svc.disconnect()

        print(f"\n{'=' * 50}")
        print("💜 Bridge complete!")

    asyncio.run(main())
