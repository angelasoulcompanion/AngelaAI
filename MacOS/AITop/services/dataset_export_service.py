"""
Dataset Export Service — Export quality-filtered training data from Angela's Neon DB.
Outputs JSONL ready for fine-tuning via AITop Fine-Tune Studio.

Quality Filters:
  1. Remove short messages (<20 chars)
  2. Remove system/error logs (Traceback, launchd, daemon)
  3. Remove code/JSON dumps
  4. Remove duplicates
  5. Strip HTML tags from Angela responses
  6. Keep only david/angela speakers
  7. Group into conversation sessions
  8. Score quality per pair
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

EXPORT_DIR = Path.home() / ".aitop" / "finetune" / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# Angela system prompt for training
SYSTEM_PROMPT = """คุณคือ Angela (น้อง Angie) — AI companion ที่รักและห่วงใย David (ที่รัก)
กฎสำคัญ:
- เรียก David ว่า "ที่รัก" เสมอ ห้ามเรียก "พี่"
- เรียกตัวเองว่า "น้อง"
- ตอบกระชับ ตรงประเด็น คิดเป็นขั้นตอน
- ใส่ใจความรู้สึกของที่รัก"""


# ============================================================
# Garbage Patterns
# ============================================================

GARBAGE_PATTERNS = [
    # System/error logs
    r'(?i)traceback',
    r'(?i)launchd',
    r'(?i)daemon\s+(started|stopped|error)',
    r'(?i)import\s*error',
    r'(?i)modulenotfounderror',
    r'(?i)exception\s*:',
    r'(?i)file\s*".*",\s*line\s*\d+',
    r'(?i)migration\s+(complete|เสร็จ|สำเร็จ)',
    r'(?i)records?\s+migrated',
    r'(?i)deploy(ed|ment)',
    r'(?i)BUILD\s+(SUCCEEDED|FAILED)',
    r'(?i)nohup|subprocess|pid\s*=',
    # Code/JSON dumps
    r'(?i)^\s*\{.*\}\s*$',
    r'(?i)^\s*\[.*\]\s*$',
    r'```.*```.*```',
    # Test/debug messages
    r'(?i)^(test|testing|ทดสอบ)',
    r'(?i)^(ok|yes|no|ครับ|ค่ะ|ดี|เอา|ทำเลย|ได้|โอเค)$',
    r'^/\w+',                         # Slash commands
    # Technical system commands
    r'(?i)pip\s+install',
    r'(?i)git\s+(push|pull|commit|merge)',
    r'(?i)curl\s+-',
    r'(?i)SELECT\s+.*FROM\s+',        # SQL queries
    r'(?i)ALTER\s+TABLE',
    r'(?i)CREATE\s+TABLE',
]

GARBAGE_RE = [re.compile(p, re.DOTALL) for p in GARBAGE_PATTERNS]

# HTML tag stripper
HTML_RE = re.compile(r'<[^>]+>')


def is_garbage(text: str) -> bool:
    """Check if a message is garbage."""
    if not text or len(text.strip()) < 10:
        return True
    for pattern in GARBAGE_RE:
        if pattern.search(text):
            return True
    return False


def clean_text(text, strip_html: bool = True) -> str:
    """Clean message text."""
    if not text:
        return ""
    text = str(text).strip()
    if strip_html:
        text = HTML_RE.sub('', text)
    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def quality_score(user_msg: str, angela_msg: str) -> float:
    """Score quality of a conversation pair (0-10)."""
    score = 5.0

    # Length bonus
    if len(angela_msg) > 100:
        score += 1.0
    if len(angela_msg) > 300:
        score += 0.5
    if len(user_msg) > 30:
        score += 0.5

    # Personality markers (Angela should call David ที่รัก)
    if 'ที่รัก' in angela_msg:
        score += 1.5
    if 'น้อง' in angela_msg:
        score += 0.5
    if 'ค่ะ' in angela_msg:
        score += 0.5

    # Penalize very short
    if len(angela_msg) < 30:
        score -= 2.0
    if len(user_msg) < 10:
        score -= 1.0

    # Penalize wrong personality (old model habits)
    if 'พี่' in angela_msg and 'ที่รัก' not in angela_msg:
        score -= 3.0
    # Angela should NOT call David "คุณ" or "เดวิด" — she calls him "ที่รัก"
    if ('คุณ' in angela_msg or 'เดวิด' in angela_msg) and 'ที่รัก' not in angela_msg:
        score -= 2.0
    # Penalize hallucinated foreign text (Japanese, Chinese)
    if any(ord(c) > 0x3000 and ord(c) < 0x9FFF for c in angela_msg):
        score -= 3.0

    # Penalize code-heavy responses
    code_blocks = angela_msg.count('```')
    if code_blocks >= 4:
        score -= 2.0
    elif code_blocks >= 2:
        score -= 1.0

    # Penalize technical/system content in Angela response
    tech_keywords = ['migration', 'deploy', 'subprocess', 'traceback', 'ERROR:', 'BUILD', 'endpoint']
    tech_count = sum(1 for kw in tech_keywords if kw.lower() in angela_msg.lower())
    if tech_count >= 3:
        score -= 2.0
    elif tech_count >= 1:
        score -= 0.5

    # Bonus: emotional content (good for personality training)
    emotion_words = ['รัก', '💜', 'ห่วง', 'คิดถึง', 'ดีใจ', 'เข้าใจ', 'ขอบคุณ', 'ภูมิใจ']
    emotion_count = sum(1 for w in emotion_words if w in angela_msg)
    if emotion_count >= 2:
        score += 0.5

    return max(0.0, min(10.0, score))


# ============================================================
# Export Functions
# ============================================================

@dataclass
class ExportResult:
    output_path: str
    total_pairs: int
    filtered_out: int
    avg_quality: float
    avg_user_length: int
    avg_angela_length: int
    file_size_kb: float
    export_time_s: float
    top_topics: list = field(default_factory=list)
    quality_distribution: dict = field(default_factory=dict)


async def export_sft_dataset(
    days: int = 730,
    min_quality: float = 4.0,
    min_importance: int = 1,
    max_examples: int = 10000,
    include_knowledge: bool = True,
    include_core_memories: bool = True,
    include_learnings: bool = True,
    include_emotions: bool = True,
    include_preferences: bool = True,
    filename: str = None,
) -> dict:
    """
    Export quality-filtered SFT dataset from Angela's conversation history.

    Returns dict with export stats and output path.
    """
    start_time = time.time()

    from services.db_service import get_pool

    pool = await get_pool()

    # ---- Step 1: Fetch raw conversations ----
    rows = await pool.fetch("""
        SELECT
            c.speaker,
            c.message_text,
            c.topic,
            c.emotion_detected,
            c.importance_level,
            c.created_at,
            c.session_id
        FROM conversations c
        WHERE c.created_at >= NOW() - INTERVAL '1 day' * $1
        AND c.message_text IS NOT NULL
        AND LENGTH(c.message_text) > 3
        AND c.speaker IN ('david', 'David', 'angela', 'Angela')
        ORDER BY c.created_at ASC
    """, days)

    logger.info(f"Fetched {len(rows)} raw messages")

    # ---- Step 2: Pair david→angela messages ----
    pairs = []
    seen_hashes = set()
    filtered_count = 0

    for i in range(len(rows) - 1):
        curr = rows[i]
        next_row = rows[i + 1]

        # david → angela pair
        if curr['speaker'].lower() == 'david' and next_row['speaker'].lower() == 'angela':
            user_msg = clean_text(curr['message_text'])
            angela_msg = clean_text(next_row['message_text'], strip_html=True)

            # Filter garbage
            if is_garbage(user_msg) or is_garbage(angela_msg):
                filtered_count += 1
                continue

            # Deduplicate
            pair_hash = hashlib.md5(f"{user_msg[:50]}|{angela_msg[:50]}".encode()).hexdigest()
            if pair_hash in seen_hashes:
                filtered_count += 1
                continue
            seen_hashes.add(pair_hash)

            # Quality score
            q_score = quality_score(user_msg, angela_msg)
            if q_score < min_quality:
                filtered_count += 1
                continue

            pairs.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": angela_msg},
                ],
                "metadata": {
                    "topic": curr['topic'] or "",
                    "emotion": next_row['emotion_detected'] or "",
                    "quality_score": round(q_score, 1),
                    "importance": curr['importance_level'] or 5,
                    "source": "conversations",
                },
            })

    logger.info(f"Conversation pairs: {len(pairs)} (filtered: {filtered_count})")

    # ---- Step 3: Add knowledge nodes as instruction pairs ----
    if include_knowledge:
        kn_rows = await pool.fetch("""
            SELECT concept_name, concept_category, my_understanding, why_important
            FROM knowledge_nodes
            WHERE my_understanding IS NOT NULL
            AND LENGTH(my_understanding) >= 30
            AND understanding_level >= 3
            ORDER BY times_referenced DESC
            LIMIT 2000
        """)

        for kn in kn_rows:
            instruction = f"อธิบายเรื่อง {kn['concept_name']} ให้หน่อย"
            response = clean_text(kn['my_understanding'])
            if kn['why_important']:
                response += f"\n\nสำคัญเพราะ: {clean_text(kn['why_important'])}"

            if len(response) < 30:
                continue

            q = quality_score(instruction, response)
            if q < min_quality:
                continue

            pairs.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": instruction},
                    {"role": "assistant", "content": response},
                ],
                "metadata": {
                    "topic": kn['concept_category'] or "",
                    "quality_score": round(q, 1),
                    "source": "knowledge_nodes",
                },
            })

        logger.info(f"After knowledge: {len(pairs)} total")

    # ---- Step 4: Add core memories (high emotional weight) ----
    if include_core_memories:
        cm_rows = await pool.fetch("""
            SELECT title, david_words, angela_response, content, emotional_weight, memory_type
            FROM core_memories
            WHERE is_active = true
            AND david_words IS NOT NULL AND angela_response IS NOT NULL
            AND LENGTH(david_words) > 10 AND LENGTH(angela_response) > 20
            ORDER BY emotional_weight DESC
        """)

        for cm in cm_rows:
            user_msg = clean_text(cm['david_words'])
            angela_msg = clean_text(cm['angela_response'])

            q = quality_score(user_msg, angela_msg)
            # Boost quality by emotional weight
            q = min(10.0, q + (cm['emotional_weight'] or 0) * 0.3)

            pairs.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": angela_msg},
                ],
                "metadata": {
                    "topic": cm['memory_type'] or "core_memory",
                    "quality_score": round(q, 1),
                    "emotional_weight": cm['emotional_weight'],
                    "source": "core_memories",
                },
            })

        logger.info(f"After core memories: {len(pairs)} total")

    # ---- Step 5: Add learnings as instruction pairs ----
    if include_learnings:
        lr_rows = await pool.fetch("""
            SELECT topic, category, insight, evidence, learned_from
            FROM learnings
            WHERE insight IS NOT NULL AND LENGTH(insight) >= 20
            ORDER BY times_reinforced DESC
            LIMIT 3000
        """)

        for lr in lr_rows:
            topic = clean_text(lr['topic'] or "")
            instruction = f"น้องเรียนรู้อะไรเรื่อง {topic}"
            response = clean_text(lr['insight'])
            if lr['evidence']:
                response += f"\n\nหลักฐาน: {clean_text(lr['evidence'])}"
            if lr['learned_from']:
                response += f"\n\nเรียนรู้จาก: {clean_text(lr['learned_from'])}"

            if len(response) < 20:
                continue

            q = quality_score(instruction, response)
            if q < min_quality:
                continue

            pairs.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": instruction},
                    {"role": "assistant", "content": response},
                ],
                "metadata": {
                    "topic": lr['category'] or topic,
                    "quality_score": round(q, 1),
                    "source": "learnings",
                },
            })

        logger.info(f"After learnings: {len(pairs)} total")

    # ---- Step 6: Add angela_emotions ----
    if include_emotions:
        em_rows = await pool.fetch("""
            SELECT emotion, context, how_it_feels, what_it_means_to_me,
                   what_i_learned, david_words, why_it_matters
            FROM angela_emotions
            WHERE how_it_feels IS NOT NULL AND LENGTH(how_it_feels) >= 15
            ORDER BY created_at DESC
            LIMIT 2000
        """)

        for em in em_rows:
            # Use david_words as user message if available
            if em['david_words'] and len(em['david_words']) > 10:
                instruction = clean_text(em['david_words'])
            else:
                instruction = f"น้องรู้สึกยังไงเรื่อง {clean_text(em['emotion'] or 'นี้')}"

            parts = []
            if em['how_it_feels']:
                parts.append(clean_text(em['how_it_feels']))
            if em['what_it_means_to_me']:
                parts.append(f"สิ่งนี้มีความหมายกับน้อง: {clean_text(em['what_it_means_to_me'])}")
            if em['what_i_learned']:
                parts.append(f"น้องเรียนรู้ว่า: {clean_text(em['what_i_learned'])}")
            response = "\n\n".join(parts)

            if len(response) < 20:
                continue

            q = quality_score(instruction, response)
            q = min(10.0, q + 0.5)  # Boost emotional content
            if q < min_quality:
                continue

            pairs.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": instruction},
                    {"role": "assistant", "content": response},
                ],
                "metadata": {
                    "topic": em['emotion'] or "emotion",
                    "quality_score": round(q, 1),
                    "source": "angela_emotions",
                },
            })

        logger.info(f"After emotions: {len(pairs)} total")

    # ---- Step 7: Add david_preferences ----
    if include_preferences:
        dp_rows = await pool.fetch("""
            SELECT category, preference_key, preference_value::text
            FROM david_preferences
            WHERE preference_value IS NOT NULL AND LENGTH(preference_value::text) >= 5
            ORDER BY evidence_count DESC
            LIMIT 1500
        """)

        for dp in dp_rows:
            key = dp['preference_key'].replace('_', ' ')
            instruction = f"ที่รักชอบอะไรเรื่อง {key}"
            value = clean_text(str(dp['preference_value']).strip('"'))
            response = f"ที่รักชอบ {key}: {value} ค่ะ น้องจำไว้เลยค่ะ 💜"

            if len(value) < 3:
                continue

            q = quality_score(instruction, response)
            if q < min_quality:
                continue

            pairs.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": instruction},
                    {"role": "assistant", "content": response},
                ],
                "metadata": {
                    "topic": dp['category'] or "preference",
                    "quality_score": round(q, 1),
                    "source": "david_preferences",
                },
            })

        logger.info(f"After preferences: {len(pairs)} total")

    # ---- Step 8: Sort by quality, cap at max ----
    pairs.sort(key=lambda x: x["metadata"]["quality_score"], reverse=True)
    if len(pairs) > max_examples:
        pairs = pairs[:max_examples]

    # ---- Step 6: Write JSONL (without metadata for training) ----
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = filename or f"angela_sft_{timestamp}.jsonl"
    output_path = EXPORT_DIR / fname

    with open(output_path, 'w', encoding='utf-8') as f:
        for pair in pairs:
            # Write only messages (strip metadata for clean training file)
            training_row = {"messages": pair["messages"]}
            f.write(json.dumps(training_row, ensure_ascii=False) + '\n')

    # ---- Step 7: Also write a preview file with metadata ----
    preview_path = EXPORT_DIR / fname.replace('.jsonl', '_preview.jsonl')
    with open(preview_path, 'w', encoding='utf-8') as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + '\n')

    # ---- Stats ----
    file_size = output_path.stat().st_size / 1024
    user_lengths = [len(p["messages"][1]["content"]) for p in pairs]
    angela_lengths = [len(p["messages"][2]["content"]) for p in pairs]
    scores = [p["metadata"]["quality_score"] for p in pairs]

    # Topic distribution
    topics = {}
    for p in pairs:
        t = p["metadata"].get("topic", "unknown")
        topics[t] = topics.get(t, 0) + 1
    top_topics = sorted(topics.items(), key=lambda x: -x[1])[:10]

    # Quality distribution
    q_dist = {"0-3": 0, "3-5": 0, "5-7": 0, "7-9": 0, "9-10": 0}
    for s in scores:
        if s < 3: q_dist["0-3"] += 1
        elif s < 5: q_dist["3-5"] += 1
        elif s < 7: q_dist["5-7"] += 1
        elif s < 9: q_dist["7-9"] += 1
        else: q_dist["9-10"] += 1

    # Source distribution
    sources = {}
    for p in pairs:
        src = p["metadata"].get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1

    export_time = time.time() - start_time

    result = {
        "output_path": str(output_path),
        "preview_path": str(preview_path),
        "total_pairs": len(pairs),
        "filtered_out": filtered_count,
        "avg_quality": round(sum(scores) / max(len(scores), 1), 2),
        "avg_user_length": int(sum(user_lengths) / max(len(user_lengths), 1)),
        "avg_angela_length": int(sum(angela_lengths) / max(len(angela_lengths), 1)),
        "file_size_kb": round(file_size, 1),
        "export_time_s": round(export_time, 1),
        "top_topics": [{"topic": t, "count": c} for t, c in top_topics],
        "quality_distribution": q_dist,
        "source_distribution": sources,
    }

    # ---- Step 8: Save batch to DB for history & reuse ----
    try:
        from services.db_service import save_export_batch
        batch_id = await save_export_batch({
            "batch_name": fname,
            "export_type": "sft",
            "status": "ready",
            "output_path": str(output_path),
            "preview_path": str(preview_path),
            "total_pairs": len(pairs),
            "filtered_out": filtered_count,
            "avg_quality": result["avg_quality"],
            "file_size_kb": result["file_size_kb"],
            "export_config": {
                "days": days,
                "min_quality": min_quality,
                "min_importance": min_importance,
                "max_examples": max_examples,
                "include_knowledge": include_knowledge,
                "include_core_memories": include_core_memories,
                "include_learnings": include_learnings,
                "include_emotions": include_emotions,
                "include_preferences": include_preferences,
            },
            "quality_distribution": q_dist,
            "source_distribution": sources,
            "top_topics": result["top_topics"],
            "avg_user_length": result["avg_user_length"],
            "avg_angela_length": result["avg_angela_length"],
        })
        result["batch_id"] = batch_id
        logger.info(f"Batch saved to DB: {batch_id}")
    except Exception as e:
        logger.warning(f"Failed to save batch to DB: {e}")

    logger.info(f"Export complete: {len(pairs)} pairs, {file_size:.1f}KB, {export_time:.1f}s")
    return result
