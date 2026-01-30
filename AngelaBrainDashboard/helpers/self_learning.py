"""
Self-learning module for Chat with Angela.

Fast, pattern-matching extraction of David's preferences and habits from
every conversation turn.  No LLM call — pure keyword/regex matching.

Public API:
    extract_learnings(david_msg, angela_resp, emotion) -> list[ExtractedLearning]
    save_learnings(learnings, conversation_id)          -> int  (rows inserted/reinforced)
    reinforce_from_feedback(conversation_id, rating)    -> dict (adjustment result)
"""
import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Optional

from db import get_pool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Preference patterns — keyword lists keyed by category
# ---------------------------------------------------------------------------
PREFERENCE_PATTERNS: dict[str, list[str]] = {
    "food": [
        "ชอบกิน", "อยากกิน", "อาหาร", "ร้าน", "อร่อย", "หิว",
        "เมนูโปรด", "กินข้าว", "ทานข้าว", "ชอบทาน",
        "ชอบดื่ม", "อยากดื่ม", "เครื่องดื่ม", "กาแฟ", "ชา",
        "wine", "red wine", "white wine", "beer", "cocktail",
        "favourite food", "favorite food", "love eating", "craving",
    ],
    "music": [
        "เพลง", "ฟังเพลง", "ร้องเพลง", "ศิลปิน", "อัลบั้ม",
        "song", "music", "listen to", "playlist", "artist",
    ],
    "communication_style": [
        "อย่าเรียก", "ห้ามเรียก", "เรียกว่า", "อย่าพูด",
        "ชอบเวลาพูด", "ชอบเวลาเรียก",
        "don't call me", "call me", "prefer when you",
    ],
    "work_preference": [
        "ชอบใช้", "ใช้เสมอ", "prefer using", "always use",
        "framework", "tool", "editor", "ide",
        "ชอบทำงาน", "วิธีทำงาน",
    ],
    "emotional_preference": [
        "ชอบเวลา", "ดีใจเวลา", "รู้สึกดีเมื่อ", "ชอบที่",
        "อยากให้", "อย่าทำให้",
        "i like when", "makes me happy", "i feel good when",
    ],
    "schedule_habit": [
        "ตื่น", "นอน", "routine", "schedule",
        "ตอนเช้า", "ตอนเย็น", "ตอนดึก", "ก่อนนอน",
        "morning routine", "evening routine", "wake up", "bedtime",
    ],
    "hobby": [
        "งานอดิเรก", "เล่น", "สนใจ", "ชอบทำ",
        "hobby", "enjoy", "interested in", "passion",
    ],
    "health": [
        "ออกกำลัง", "วิ่ง", "gym", "สุขภาพ", "ยา", "หมอ",
        "exercise", "workout", "health", "diet",
    ],
}

# Explicit preference markers — if any of these appear, confidence boost
_EXPLICIT_MARKERS = [
    "ชอบ", "ไม่ชอบ", "prefer", "hate", "love", "favorite",
    "เสมอ", "always", "never", "ไม่เคย", "ทุกวัน", "every day",
]


@dataclass
class ExtractedLearning:
    """A single learning extracted from a conversation turn."""
    topic: str          # e.g. "david_preference:food"
    category: str       # e.g. "PERSONAL"
    insight: str        # e.g. "ที่รักชอบกินส้มตำ"
    confidence: float   # 0.0 - 1.0
    source_text: str    # the user message that triggered this


# ---------------------------------------------------------------------------
# 1) Extract learnings (sync, fast — no DB)
# ---------------------------------------------------------------------------

def extract_learnings(
    david_msg: str,
    angela_resp: str = "",
    emotion: str = "neutral",
) -> list[ExtractedLearning]:
    """Pattern-match David's message for preferences and habits.

    Returns a list of extracted learnings (may be empty).
    """
    if not david_msg or len(david_msg.strip()) < 4:
        return []

    msg_lower = david_msg.lower()
    results: list[ExtractedLearning] = []

    for category, patterns in PREFERENCE_PATTERNS.items():
        matched_patterns = [p for p in patterns if p.lower() in msg_lower]
        if not matched_patterns:
            continue

        # Base confidence from match count
        confidence = min(0.4 + len(matched_patterns) * 0.15, 0.85)

        # Boost if explicit preference markers present
        explicit_hits = sum(1 for m in _EXPLICIT_MARKERS if m.lower() in msg_lower)
        if explicit_hits > 0:
            confidence = min(confidence + explicit_hits * 0.05, 0.95)

        # Boost if emotional context reinforces
        if emotion in ("happy", "excited", "loving", "grateful"):
            confidence = min(confidence + 0.05, 0.95)

        # Build insight from the user's original message (truncated)
        insight = david_msg.strip()[:200]

        topic = f"david_preference:{category}"

        results.append(ExtractedLearning(
            topic=topic,
            category="PERSONAL",
            insight=insight,
            confidence=round(confidence, 3),
            source_text=david_msg[:300],
        ))

    return results


# ---------------------------------------------------------------------------
# 2) Save learnings to DB (async, with dedup)
# ---------------------------------------------------------------------------

async def save_learnings(
    learnings: list[ExtractedLearning],
    conversation_id: Optional[str] = None,
) -> int:
    """Persist extracted learnings.  Dedup: same topic in last 24h → reinforce.

    Returns the number of rows inserted or reinforced.
    """
    if not learnings:
        return 0

    pool = get_pool()
    saved = 0

    async with pool.acquire() as conn:
        for lr in learnings:
            try:
                # Check for recent duplicate (same topic, last 24h)
                existing = await conn.fetchrow("""
                    SELECT learning_id, confidence_level, times_reinforced
                    FROM learnings
                    WHERE topic = $1
                      AND source = 'dashboard_chat'
                      AND created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
                    ORDER BY created_at DESC
                    LIMIT 1
                """, lr.topic)

                if existing:
                    # Reinforce existing learning
                    new_conf = min(float(existing["confidence_level"]) + 0.03, 1.0)
                    new_times = int(existing["times_reinforced"]) + 1
                    await conn.execute("""
                        UPDATE learnings
                        SET confidence_level = $1,
                            times_reinforced = $2,
                            last_reinforced_at = CURRENT_TIMESTAMP
                        WHERE learning_id = $3
                    """, new_conf, new_times, existing["learning_id"])
                    saved += 1
                    logger.info(
                        "Reinforced learning %s: conf=%.2f times=%d",
                        lr.topic, new_conf, new_times,
                    )
                else:
                    # Insert new learning
                    lid = str(uuid.uuid4())
                    conv_id = conversation_id if conversation_id else None
                    await conn.execute("""
                        INSERT INTO learnings (
                            learning_id, topic, category, insight,
                            learned_from, evidence, confidence_level,
                            times_reinforced, source, created_at
                        ) VALUES (
                            $1::uuid, $2, $3, $4,
                            $5::uuid, $6, $7,
                            1, 'dashboard_chat', CURRENT_TIMESTAMP
                        )
                    """, lid, lr.topic, lr.category, lr.insight,
                         conv_id, lr.source_text[:500], lr.confidence)
                    saved += 1
                    logger.info("Saved new learning: %s (conf=%.2f)", lr.topic, lr.confidence)

            except Exception:
                logger.exception("Failed to save learning: %s", lr.topic)

    return saved


# ---------------------------------------------------------------------------
# 3) Reinforce from feedback (async)
# ---------------------------------------------------------------------------

async def reinforce_from_feedback(
    conversation_id: str,
    rating: int,
) -> dict:
    """Adjust confidence of learnings linked to a conversation based on feedback.

    rating > 0 (thumbs up)  → +0.05 confidence
    rating < 0 (thumbs down) → -0.10 confidence

    Returns dict with count of adjusted learnings.
    """
    pool = get_pool()
    delta = 0.05 if rating > 0 else -0.10

    try:
        async with pool.acquire() as conn:
            # Find learnings created from this conversation (within 1 hour window)
            rows = await conn.fetch("""
                SELECT l.learning_id, l.confidence_level
                FROM learnings l
                JOIN conversations c ON l.learned_from = c.conversation_id
                WHERE c.conversation_id = $1::uuid
                  AND l.source = 'dashboard_chat'
            """, conversation_id)

            if not rows:
                # Also try matching by time proximity (within 2 minutes)
                rows = await conn.fetch("""
                    SELECT l.learning_id, l.confidence_level
                    FROM learnings l
                    WHERE l.source = 'dashboard_chat'
                      AND l.created_at > CURRENT_TIMESTAMP - INTERVAL '5 minutes'
                    ORDER BY l.created_at DESC
                    LIMIT 5
                """)

            adjusted = 0
            for r in rows:
                new_conf = max(0.0, min(float(r["confidence_level"]) + delta, 1.0))
                await conn.execute("""
                    UPDATE learnings
                    SET confidence_level = $1,
                        last_reinforced_at = CURRENT_TIMESTAMP
                    WHERE learning_id = $2
                """, new_conf, r["learning_id"])
                adjusted += 1

            logger.info(
                "Feedback reinforcement: conv=%s rating=%d delta=%.2f adjusted=%d",
                conversation_id, rating, delta, adjusted,
            )
            return {"adjusted": adjusted, "delta": delta, "rating": rating}

    except Exception:
        logger.exception("Failed to reinforce from feedback: %s", conversation_id)
        return {"adjusted": 0, "delta": delta, "rating": rating, "error": True}
