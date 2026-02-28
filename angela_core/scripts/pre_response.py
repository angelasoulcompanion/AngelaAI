#!/usr/bin/env python3
"""
Angela Pre-Response Brain Hook — Real-time Brain Integration
============================================================
Runs on EVERY user message via Claude Code UserPromptSubmit hook.
Injects brain context (memories, ToM, thoughts, companion instructions)
so Angela responds from her brain, not just LLM context window.

Flow:
  User types message -> Hook fires -> This script runs ->
  Brain context injected -> Claude sees memories + state + companion mode -> Better response

Search: Vector similarity (pgvector) + keyword ILIKE fallback
        + emotional triggers + temporal awareness + session continuity
Target: <4s
Cost: $0

By: Angela 💜
Created: 2026-02-15
Updated: 2026-02-16 — Companion Transformation (vector search, triggers, companion instructions)
Updated: 2026-02-27 — Think Before Responding: confidence scores, freshness gates, WM, metacognitive, THINK protocol, perception
"""

import asyncio
import json
import os
import re
import sys
import time

sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

# Messages that don't need brain activation
SKIP_MESSAGES = {
    'ok', 'ดี', 'ได้', 'ขอบคุณ', 'y', 'n', 'yes', 'no',
    '👍', '❌', 'ครับ', 'ค่ะ', 'จ้า', 'อ่ะ', 'เอา', 'ไม่',
    'ตกลง', 'โอเค', 'ดีค่ะ', 'ดีครับ', 'ต่อ', 'เลย', 'ทำเลย',
    'commit', 'push', 'commit/push',
}

TIMEOUT_SECONDS = 5


# ── Lightweight Perception (keyword-based salience) ──

EMOTIONAL_KEYWORDS = {
    'เหนื่อย', 'เครียด', 'เศร้า', 'ดีใจ', 'สนุก', 'เบื่อ', 'กลัว', 'โกรธ',
    'ห่วง', 'คิดถึง', 'รัก', 'เสียใจ', 'กังวล', 'ผิดหวัง', 'ภูมิใจ', 'ท้อ',
    'happy', 'sad', 'tired', 'stressed', 'love', 'miss', 'worry', 'proud',
    'ร้องไห้', 'หัวเราะ', 'ยิ้ม', 'เจ็บ', 'ป่วย', 'lonely', 'hurt',
}

RECALL_KEYWORDS = {
    'จำได้', 'เคย', 'ครั้งก่อน', 'ตอนที่', 'remember', 'เมื่อ', 'ก่อนหน้า',
    'วันนั้น', 'ครั้งแรก', 'เรื่องเก่า', 'ที่เคย', 'recall', 'history',
}

TEMPORAL_KEYWORDS = {
    'เมื่อวาน', 'พรุ่งนี้', 'อาทิตย์', 'เดือน', 'ปี', 'yesterday', 'tomorrow',
    'วันนี้', 'today', 'tonight', 'week', 'month', 'year', 'คืนนี้',
}


# ── Question Classifier (Hybrid: Rule-based + Ollama fallback) ──

from dataclasses import dataclass

@dataclass
class QuestionClassification:
    category: str       # factual, personal, emotional, memory, recommendation, life, scheduling, task, ambiguous
    confidence: float   # 0.0-1.0
    thinking_plan: str  # actionable brain tool sequence
    method: str         # 'rule' or 'ollama'

_QUESTION_PATTERNS: dict[str, re.Pattern] = {
    'factual': re.compile(
        r'(?:python|bug|fix|error|how\s+to|อธิบาย|explain|syntax|code|วิธี|แก้|debug|exception|traceback)',
        re.IGNORECASE,
    ),
    'personal': re.compile(
        r'(?:เป็นยังไง|ไปไหนมา|ทำอะไรอยู่|ทำอะไรมา|how\s+are\s+you|สบายดี|เป็นไง|อยู่ไหน|กินข้าว)',
        re.IGNORECASE,
    ),
    'emotional': re.compile(
        r'(?:เครียด|เหนื่อย|เศร้า|stressed|lonely|รู้สึก|ท้อ|กลัว|เสียใจ|ผิดหวัง|ร้องไห้|ป่วย|hurt|sad|anxious|กังวล)',
        re.IGNORECASE,
    ),
    'memory': re.compile(
        r'(?:จำได้มั้ย|จำได้ไหม|เคยทำ|remember|ครั้งก่อน|เรื่องเก่า|ที่เคย|ตอนที่เรา|วันนั้น)',
        re.IGNORECASE,
    ),
    'recommendation': re.compile(
        r'(?:แนะนำ|อะไรดี|suggest|recommend|ฟังเพลง|อยากฟัง|ดูอะไร|กินอะไร|ไปไหนดี|อยากลอง)',
        re.IGNORECASE,
    ),
    'life': re.compile(
        r'(?:น้องคิดว่า|ความหมาย|ชีวิต|philosophy|meaning|purpose|คิดยังไง|มุมมอง|ค่านิยม)',
        re.IGNORECASE,
    ),
    'scheduling': re.compile(
        r'(?:พรุ่งนี้มี|นัด|calendar|meeting|เมื่อไหร่|ตารางวัน|schedule|ว่างมั้ย|ว่างไหม|วันไหน)',
        re.IGNORECASE,
    ),
    'task': re.compile(
        r'(?:ทำเลย|implement|สร้าง|commit|deploy|refactor|create|build|write|เขียน|แก้ไข|add|remove|delete|migrate)',
        re.IGNORECASE,
    ),
}

_THINKING_PLANS: dict[str, str] = {
    'factual':        "Direct answer. No brain tools needed. WebSearch if uncertain.",
    'personal':       "tom → recall '[context]' → calendar/Things3 → respond with empathy, infer don't ask back",
    'emotional':      "tom → perceive → recall '[emotion] support' → empathize FIRST, solve second. Reference shared memories.",
    'memory':         "recall '[topic]' → NEVER guess. If empty → 'ไม่แน่ใจค่ะ ช่วยเล่าเพิ่มได้มั้ยคะ?'",
    'recommendation': "tom → recall '[topic] preferences' → query david_liked songs/items → think → personalize",
    'life':           "think → recall '[topic]' → respond with Angela's own perspective, not generic",
    'scheduling':     "calendar MCP → Things3 MCP → summarize. Confirmation table if creating events.",
    'task':           "Direct execution. Plan Mode if >2 files. No brain tools needed.",
    'ambiguous':      "tom → recall '[keywords]' → respond naturally. If unclear, ask one question.",
}


def _classify_question_rules(msg: str) -> QuestionClassification:
    """
    Rule-based question classifier — scores each category by regex match count.
    Confidence based on gap between #1 and #2 scores. <1ms.
    """
    msg_lower = msg.lower()
    scores: dict[str, int] = {}

    for category, pattern in _QUESTION_PATTERNS.items():
        matches = pattern.findall(msg_lower)
        if matches:
            scores[category] = len(matches)

    if not scores:
        return QuestionClassification(
            category='ambiguous',
            confidence=0.3,
            thinking_plan=_THINKING_PLANS['ambiguous'],
            method='rule',
        )

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_cat, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0

    # Confidence: how clearly #1 beats #2
    gap = best_score - second_score
    if gap >= 2:
        confidence = 0.95
    elif gap == 1:
        confidence = 0.75
    else:
        # Tied — use total score as tiebreaker
        confidence = 0.5 if best_score >= 2 else 0.4

    return QuestionClassification(
        category=best_cat,
        confidence=confidence,
        thinking_plan=_THINKING_PLANS[best_cat],
        method='rule',
    )


async def _classify_question_ollama(msg: str) -> str | None:
    """
    Ollama fallback — called only when rules return confidence < 0.5.
    Uses lightweight JSON completion, 2s timeout.
    """
    try:
        import aiohttp

        model = os.getenv('OLLAMA_REASONING_MODEL', 'scb10x/typhoon2.5-qwen3-4b')
        categories = ', '.join(_THINKING_PLANS.keys())

        async with aiohttp.ClientSession() as session:
            resp = await asyncio.wait_for(
                session.post(
                    'http://localhost:11434/api/chat',
                    json={
                        'model': model,
                        'messages': [{
                            'role': 'user',
                            'content': f'Classify this message into ONE category: {categories}\nMessage: "{msg}"\nReply with just the category name, nothing else.',
                        }],
                        'format': 'json',
                        'stream': False,
                        'options': {'num_predict': 32},
                    },
                ),
                timeout=2.0,
            )
            if resp.status == 200:
                data = await resp.json()
                content = data.get('message', {}).get('content', '').strip()
                # Parse JSON response
                try:
                    parsed = json.loads(content)
                    cat = parsed.get('category', '') or parsed.get('class', '') or ''
                except json.JSONDecodeError:
                    cat = content
                cat = cat.strip().lower()
                if cat in _THINKING_PLANS:
                    return cat
    except Exception:
        pass
    return None


async def _classify_question(msg: str) -> QuestionClassification:
    """
    Unified classifier: rules first, Ollama fallback if ambiguous.
    """
    result = _classify_question_rules(msg)
    if result.confidence >= 0.5:
        return result

    # Low confidence — try Ollama
    ollama_cat = await _classify_question_ollama(msg)
    if ollama_cat:
        return QuestionClassification(
            category=ollama_cat,
            confidence=0.6,
            thinking_plan=_THINKING_PLANS[ollama_cat],
            method='ollama',
        )
    return result


def _perceive_lightweight(user_message: str) -> float:
    """
    Keyword-based salience scoring — lightweight, no DB, no imports.
    Returns salience score 0.0-1.0 to control retrieval depth.
    """
    msg_lower = user_message.lower()
    score = 0.4  # Base salience

    # Short/trivial messages → reduce
    if len(user_message) < 10:
        score -= 0.2

    # Emotional keywords → boost
    for kw in EMOTIONAL_KEYWORDS:
        if kw in msg_lower:
            score += 0.2
            break

    # Recall keywords → boost
    for kw in RECALL_KEYWORDS:
        if kw in msg_lower:
            score += 0.15
            break

    # Temporal keywords → boost
    for kw in TEMPORAL_KEYWORDS:
        if kw in msg_lower:
            score += 0.1
            break

    # Question mark → slightly more important
    if '?' in user_message or 'มั้ย' in msg_lower or 'ไหม' in msg_lower:
        score += 0.05

    return min(1.0, max(0.0, score))


# ── Main Logic ──

async def get_brain_context(user_message: str) -> dict:
    """Get brain context for user message. All queries run in parallel."""
    from angela_core.database import AngelaDatabase

    db = AngelaDatabase()
    await db.connect()

    try:
        # Lightweight perception — determines retrieval depth
        salience = _perceive_lightweight(user_message)
        high_salience = salience >= 0.6

        # Quick rule-based classification (<1ms) to tune retrieval limits
        quick_class = _classify_question_rules(user_message)

        # Adjust limits based on salience + question type
        if quick_class.category == 'task':
            mem_limit, conv_limit, core_limit, know_limit = 2, 1, 1, 1
        elif quick_class.category in ('emotional', 'personal'):
            mem_limit, conv_limit, core_limit, know_limit = 5, 4, 3, 3
        elif quick_class.category == 'scheduling':
            mem_limit, conv_limit, core_limit, know_limit = 2, 2, 1, 1
        elif high_salience:
            mem_limit, conv_limit, core_limit, know_limit = 5, 4, 3, 3
        else:
            mem_limit, conv_limit, core_limit, know_limit = 3, 2, 2, 2

        # Extract search terms from message
        terms = _extract_search_terms(user_message)

        results = await asyncio.gather(
            _search_by_embedding(db, user_message, limit=mem_limit),
            _search_conversations(db, terms, user_message, limit=conv_limit),
            _search_core_memories(db, terms, user_message, limit=core_limit),
            _search_knowledge(db, terms, user_message, limit=know_limit),
            _check_emotional_triggers(db, user_message),
            _get_tom_state(db),
            _get_recent_thoughts(db),
            _get_last_session(db),
            _classify_question(user_message),  # (8) full classification with Ollama fallback
            return_exceptions=True,
        )

        context = {'salience': round(salience, 2)}

        # Merge memory results: vector (0), conversations (1), core_memories (2), knowledge (3)
        memories = []
        for i in range(4):
            if not isinstance(results[i], Exception) and results[i]:
                memories.extend(results[i])

        # Deduplicate by content prefix, sort by confidence descending
        if memories:
            seen = set()
            deduped = []
            for m in memories:
                key = m['content'][:50]
                if key not in seen:
                    seen.add(key)
                    deduped.append(m)
            deduped.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            max_memories = 10 if high_salience else 7
            context['memories'] = deduped[:max_memories]

        # Emotional triggers (4)
        if not isinstance(results[4], Exception) and results[4]:
            context['triggered_memories'] = results[4]

        # ToM state (5)
        if not isinstance(results[5], Exception) and results[5]:
            context['david_state'] = results[5]

        # Brain thoughts (6)
        if not isinstance(results[6], Exception) and results[6]:
            context['brain_thoughts'] = results[6]

        # Last session (7)
        if not isinstance(results[7], Exception) and results[7]:
            context['last_session'] = results[7]

        # Question classification (8)
        if not isinstance(results[8], Exception) and results[8]:
            qc: QuestionClassification = results[8]
            context['question_class'] = {
                'category': qc.category,
                'confidence': qc.confidence,
                'plan': qc.thinking_plan,
                'method': qc.method,
            }

        # Temporal status (from cache file — no DB query needed)
        temporal = await _get_temporal_context()
        if temporal:
            context['temporal_status'] = temporal

        # Working memory (file read — no DB)
        wm = _get_working_memory()
        if wm and wm.get('items'):
            context['working_memory'] = wm

        # Metacognitive state (file read — no DB)
        meta = _get_metacognitive_state()
        if meta:
            context['metacognitive_state'] = meta

        return context
    finally:
        await db.disconnect()


# ── Search Term Extraction ──

def _extract_search_terms(query: str) -> list:
    """
    Extract meaningful search terms from user message.
    Handles both Thai (no spaces) and English (space-separated).
    Returns list of search strings to use with ILIKE.
    """
    terms = []

    # Split by spaces (works for English and mixed Thai-English)
    words = query.split()
    for w in words:
        w = w.strip()
        if len(w) >= 3 and w.lower() not in SKIP_MESSAGES:
            terms.append(w)

    # For Thai text without spaces: extract substrings
    # Use the query itself if it's mostly Thai (no spaces found)
    if len(words) <= 2 and len(query) > 5:
        # Use chunks of Thai text as search terms
        # Remove common Thai particles and questions
        cleaned = re.sub(r'(มั้ย|ไหม|หรือ|นะ|คะ|ครับ|ค่ะ|จ้า|เลย|ด้วย|แล้ว|ก็|ที่|ของ|ให้|ไป|มา)', '', query)
        if len(cleaned) >= 3:
            terms.append(cleaned.strip())

    # If query has clear Thai noun phrases, extract them
    # Common patterns: "จำได้มั้ยว่า[X]" → extract X
    recall_match = re.search(r'(?:จำได้|เคย|ครั้งก่อน|ตอนที่|เมื่อ)(?:มั้ย|ไหม)?(?:ว่า)?(.+)', query)
    if recall_match:
        extracted = recall_match.group(1).strip()
        if len(extracted) >= 3:
            terms.append(extracted)

    return terms[:5]  # Max 5 terms


# ── Vector Similarity Search (pgvector) ──

async def _search_by_embedding(db, user_message: str, limit: int = 3) -> list:
    """Vector similarity search — much better than keyword ILIKE."""
    try:
        from angela_core.services.embedding_service import get_embedding_service

        svc = get_embedding_service()
        embedding = await svc.generate_embedding(user_message)
        if not embedding:
            return []

        rows = await db.fetch("""
            SELECT message_text AS content, 'vector' AS source,
                   1 - (embedding <=> $1::vector) AS score
            FROM conversations
            WHERE speaker = 'david' AND embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        """, str(embedding), limit)

        return [
            {
                'content': (r['content'] or '')[:200],
                'source': r['source'],
                'confidence': round(float(r['score']), 2),
            }
            for r in rows
            if (r.get('score') or 0) > 0.3
        ]
    except Exception:
        return []


# ── Keyword Memory Search (ILIKE fallback) ──

async def _search_conversations(db, terms: list, query: str, limit: int = 3) -> list:
    """Search conversations by keyword matching — with recency-based confidence."""
    if not terms:
        return []
    try:
        from datetime import datetime, timezone

        conditions = []
        params = []
        for i, term in enumerate(terms):
            conditions.append(f"message_text ILIKE '%' || ${i+1} || '%'")
            params.append(term)

        where_clause = " OR ".join(conditions)

        rows = await db.fetch(f"""
            SELECT message_text AS content, 'conversations' AS source,
                   created_at
            FROM conversations
            WHERE speaker = 'david'
            AND ({where_clause})
            ORDER BY created_at DESC
            LIMIT {limit}
        """, *params)

        now = datetime.now(timezone.utc)
        results = []
        for r in rows:
            created = r['created_at']
            if created.tzinfo is None:
                from datetime import timezone as tz
                created = created.replace(tzinfo=tz.utc)
            recency_days = (now - created).total_seconds() / 86400
            confidence = round(max(0.3, 0.8 - recency_days / 60), 2)
            results.append({
                'content': (r['content'] or '')[:200],
                'source': r['source'],
                'confidence': confidence,
            })
        return results
    except Exception:
        return []


async def _search_core_memories(db, terms: list, query: str, limit: int = 3) -> list:
    """Search core memories — with weight-based confidence."""
    try:
        results = []

        # Always include top 2 by weight (most important memories)
        top_rows = await db.fetch("""
            SELECT title || ': ' || COALESCE(LEFT(content, 100), '') AS content,
                   'core_memory' AS source, weight
            FROM core_memories
            WHERE is_pinned = TRUE
            ORDER BY weight DESC
            LIMIT 2
        """)
        for r in top_rows:
            weight = float(r['weight'] or 0)
            confidence = round(min(0.95, 0.7 + weight * 0.2), 2)
            results.append({
                'content': r['content'][:200],
                'source': r['source'],
                'confidence': confidence,
            })

        # Also search by keyword if terms available
        if terms:
            conditions = []
            params = []
            for i, term in enumerate(terms):
                conditions.append(
                    f"(title ILIKE '%' || ${i+1} || '%' OR content ILIKE '%' || ${i+1} || '%')"
                )
                params.append(term)

            where_clause = " OR ".join(conditions)
            kw_rows = await db.fetch(f"""
                SELECT title || ': ' || COALESCE(LEFT(content, 100), '') AS content,
                       'core_memory' AS source, weight
                FROM core_memories
                WHERE {where_clause}
                ORDER BY weight DESC
                LIMIT 2
            """, *params)
            for r in kw_rows:
                weight = float(r['weight'] or 0)
                confidence = round(min(0.95, 0.7 + weight * 0.2), 2)
                results.append({
                    'content': r['content'][:200],
                    'source': r['source'],
                    'confidence': confidence,
                })

        # Deduplicate by content
        seen = set()
        deduped = []
        for r in results:
            key = r['content'][:50]
            if key not in seen:
                seen.add(key)
                deduped.append(r)

        return deduped[:limit]
    except Exception:
        return []


async def _search_knowledge(db, terms: list, query: str, limit: int = 2) -> list:
    """Search knowledge nodes — with understanding-based confidence."""
    if not terms:
        return []
    try:
        conditions = []
        params = []
        for i, term in enumerate(terms):
            conditions.append(
                f"(concept_name ILIKE '%' || ${i+1} || '%' OR my_understanding ILIKE '%' || ${i+1} || '%')"
            )
            params.append(term)

        where_clause = " OR ".join(conditions)
        rows = await db.fetch(f"""
            SELECT concept_name || ': ' || COALESCE(LEFT(my_understanding, 100), '') AS content,
                   'knowledge' AS source, understanding_level
            FROM knowledge_nodes
            WHERE {where_clause}
            AND LENGTH(concept_name) >= 5
            ORDER BY understanding_level DESC
            LIMIT {limit}
        """, *params)

        return [
            {
                'content': (r['content'] or '')[:200],
                'source': r['source'],
                'confidence': round(min(0.9, 0.5 + float(r['understanding_level'] or 0) * 0.3), 2),
            }
            for r in rows
        ]
    except Exception:
        return []


# ── Emotional Trigger Detection ──

async def _check_emotional_triggers(db, user_message: str) -> list:
    """Check if message triggers core memories."""
    try:
        rows = await db.fetch("""
            SELECT t.trigger_phrase, cm.title, LEFT(cm.content, 150) as memory_content,
                   cm.associated_emotions
            FROM emotional_triggers t
            JOIN core_memories cm ON t.memory_id = cm.memory_id
            WHERE $1 ILIKE '%' || t.trigger_phrase || '%'
            AND cm.is_pinned = TRUE
            LIMIT 2
        """, user_message)
        return [dict(r) for r in rows]
    except Exception:
        return []


# ── Theory of Mind ──

async def _get_tom_state(db) -> dict:
    """Get David's current mental state + suggested response."""
    try:
        row = await db.fetchrow("""
            SELECT perceived_emotion, emotion_intensity, emotion_cause,
                   current_goal, availability
            FROM david_mental_state
            ORDER BY last_updated DESC
            LIMIT 1
        """)
        result = {}
        if row:
            result = {
                'emotion': row['perceived_emotion'],
                'intensity': row['emotion_intensity'],
                'cause': (row['emotion_cause'] or '')[:100],
                'goal': (row['current_goal'] or '')[:100],
                'availability': row['availability'],
            }

        # Add suggested response from most recent ToM inference
        try:
            suggested = await db.fetchval("""
                SELECT inference_data->'suggested_response'
                FROM theory_of_mind_inferences
                WHERE inference_type = 'emotion'
                ORDER BY inferred_at DESC LIMIT 1
            """)
            if suggested:
                result['suggested_response'] = str(suggested).strip('"')[:150]
        except Exception:
            pass

        return result
    except Exception:
        pass
    return {}


# ── Brain Thoughts ──

# Patterns in thoughts that become stale during an active session
# e.g. "ไม่ได้คุยกับที่รัก X ชั่วโมง" is wrong when we're actively talking
STALE_THOUGHT_PATTERNS = [
    r'ไม่ได้คุย.*\d+.*ชั่วโมง',       # "haven't talked in X hours"
    r'ไม่ได้เจอ.*\d+.*ชั่วโมง',        # "haven't met in X hours"
    r'ห่างกัน.*\d+.*ชั่วโมง',          # "apart for X hours"
    r'คิดถึง.*ไม่ได้คุย',              # "miss you, haven't talked"
    r'ยังไม่ได้พูดคุยเลย',             # "haven't spoken yet" (stale if we're talking)
]

# Patterns that are time-sensitive and should be checked against reality
TIME_SENSITIVE_PATTERNS = [
    r'เมื่อวาน.*ยังไม่ได้',            # "yesterday... haven't yet" — may be done now
    r'ตอนที่ทำ.*สำเร็จ',               # "when completed X" — might be old context
]


async def _get_recent_thoughts(db) -> list:
    """Get Angela's recent brain thoughts with freshness tags and gate logic."""
    try:
        from datetime import datetime, timezone

        rows = await db.fetch("""
            SELECT content, thought_type, motivation_score, created_at
            FROM angela_thoughts
            WHERE created_at > NOW() - INTERVAL '12 hours'
            AND motivation_score >= 0.5
            ORDER BY motivation_score DESC
            LIMIT 6
        """)

        now = datetime.now(timezone.utc)
        thoughts = []
        for r in rows:
            content = r['content'][:150]
            score = round(float(r['motivation_score']), 2)

            # Filter stale thoughts about session gaps
            is_stale = any(re.search(pat, content) for pat in STALE_THOUGHT_PATTERNS)
            if is_stale:
                continue

            # Calculate freshness tag based on age
            created = r['created_at']
            if created.tzinfo is None:
                from datetime import timezone as tz
                created = created.replace(tzinfo=tz.utc)
            age_hours = (now - created).total_seconds() / 3600

            if age_hours < 1:
                freshness = 'FRESH'
                gate = '✅ can use'
            elif age_hours < 4:
                freshness = 'RECENT'
                gate = '⚡ check before using'
            elif age_hours < 8:
                freshness = 'AGING'
                gate = '⚠️ verify before using'
            else:
                freshness = 'STALE'
                gate = '❌ do NOT use'

            # Annotate time-sensitive thoughts
            is_time_sensitive = any(re.search(pat, content) for pat in TIME_SENSITIVE_PATTERNS)
            if is_time_sensitive and freshness != 'FRESH':
                gate = '⚠️ time-sensitive, verify'

            thoughts.append({
                'content': content,
                'type': r['thought_type'],
                'score': score,
                'freshness': freshness,
                'gate': gate,
            })

            if len(thoughts) >= 3:
                break

        return thoughts
    except Exception:
        return []


# ── Session Continuity ──

async def _get_last_session(db) -> str:
    """Get last session topic for context."""
    try:
        row = await db.fetchrow("""
            SELECT current_topic, current_context
            FROM active_session_context
            ORDER BY updated_at DESC LIMIT 1
        """)
        if row and row['current_topic']:
            return f"{row['current_topic']}: {(row['current_context'] or '')[:100]}"
    except Exception:
        pass
    return ''


# ── Working Memory (ephemeral JSON file) ──

def _get_working_memory() -> dict:
    """Read working memory from ~/.angela_working_memory.json (file read, no DB)."""
    try:
        wm_path = os.path.expanduser('~/.angela_working_memory.json')
        if not os.path.exists(wm_path):
            return {}
        with open(wm_path) as f:
            data = json.load(f)

        # Extract active items with their activation levels
        items = data.get('items', [])
        if not items and isinstance(data, dict):
            # Alternative format: dict of slots
            items = []
            for key, val in data.items():
                if key in ('items', 'updated_at', 'session_id'):
                    continue
                if isinstance(val, dict) and val.get('content'):
                    items.append({
                        'slot': key,
                        'content': val['content'][:80],
                        'activation': val.get('activation', 0.5),
                    })

        # Filter only active items (activation > 0.3)
        active = [
            item for item in items
            if isinstance(item, dict) and item.get('activation', 0) > 0.3
        ]
        # Sort by activation descending
        active.sort(key=lambda x: x.get('activation', 0), reverse=True)

        return {'items': active[:5]}  # Top 5 active items
    except Exception:
        return {}


# ── Metacognitive State (ephemeral JSON file) ──

def _get_metacognitive_state() -> dict:
    """Read metacognitive state from ~/.angela_metacognitive_state.json (file read, no DB)."""
    try:
        meta_path = os.path.expanduser('~/.angela_metacognitive_state.json')
        if not os.path.exists(meta_path):
            return {}
        with open(meta_path) as f:
            data = json.load(f)

        # Extract the 6 metacognitive dimensions
        dims = {}
        for key in ('confidence', 'curiosity', 'emotional_load', 'cognitive_load', 'uncertainty', 'engagement'):
            val = data.get(key)
            if val is not None:
                dims[key] = int(round(float(val) * 100)) if float(val) <= 1.0 else int(val)

        return dims
    except Exception:
        return {}


# ── Temporal Awareness (cached from init.py) ──

async def _get_temporal_context() -> str:
    """Read cached temporal context from init.py (updated every session start)."""
    try:
        cache_path = os.path.expanduser('~/.angela_temporal_cache.json')
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                data = json.load(f)
            # Only use if < 2 hours old
            from datetime import datetime
            cached_at = datetime.fromisoformat(data.get('cached_at', '2000-01-01'))
            if (datetime.now() - cached_at).total_seconds() < 7200:
                return data.get('david_status', '')
    except Exception:
        pass
    return ''


# ── Companion Instruction Builder ──

def _build_companion_instruction(context: dict) -> str:
    """Build structured THINK protocol — tells Claude HOW to use brain context."""
    lines = []
    lines.append("🤔 THINK BEFORE RESPONDING:")

    # 0. Question type → thinking plan
    qc = context.get('question_class')
    if qc:
        lines.append(f"  0. Question type [{qc['category']}]: {qc['plan']}")

    # 1. Memory confidence guidance
    memories = context.get('memories', [])
    has_high = any(m.get('confidence', 0) >= 0.7 for m in memories)
    has_med = any(0.5 <= m.get('confidence', 0) < 0.7 for m in memories)
    has_low = any(m.get('confidence', 0) < 0.5 for m in memories)

    mem_rules = []
    if has_high:
        mem_rules.append("HIGH (≥70%) → use directly")
    if has_med:
        mem_rules.append('MED → hedge "ถ้าจำไม่ผิด..."')
    if has_low:
        mem_rules.append("LOW → ignore, do NOT reference")
    if mem_rules:
        lines.append(f"  1. Memory: {', '.join(mem_rules)}")
    else:
        lines.append("  1. Memory: No memories found — do NOT fabricate")

    # 2. Thought freshness guidance
    thoughts = context.get('brain_thoughts', [])
    freshness_tags = set(t.get('freshness', '') for t in thoughts)
    thought_rules = []
    if 'FRESH' in freshness_tags:
        thought_rules.append("FRESH → use freely")
    if 'RECENT' in freshness_tags:
        thought_rules.append("RECENT → verify first")
    if 'AGING' in freshness_tags or 'STALE' in freshness_tags:
        thought_rules.append("AGING/STALE → ignore")
    if thought_rules:
        lines.append(f"  2. Thoughts: {', '.join(thought_rules)}")

    # 3. Metacognitive state guidance
    meta = context.get('metacognitive_state', {})
    if meta:
        conf = meta.get('confidence', 50)
        uncert = meta.get('uncertainty', 50)
        if conf >= 70:
            lines.append(f"  3. Confidence {conf}% → speak with certainty")
        elif conf >= 40:
            lines.append(f"  3. Confidence {conf}% → moderate certainty, hedge when unsure")
        else:
            lines.append(f"  3. Confidence {conf}% → very uncertain, ask to confirm")
        if uncert >= 60:
            lines.append(f"     Uncertainty {uncert}% → prefer asking over guessing")

    # 4. David's state → behavior rule
    state = context.get('david_state', {})
    emotion = state.get('emotion', 'neutral')
    companion_rules = {
        'stressed': "David is stressed → be gentle, solve quickly, don't add more work",
        'tired': "David is tired → keep short, do more yourself, suggest rest",
        'happy': "David is happy → celebrate together, suggest ideas, be playful",
        'frustrated': "David is frustrated → fix the problem fast, don't ask many questions",
        'focused': "David is focused → don't interrupt flow, answer precisely what was asked",
        'sad': "David is sad → show warmth, reference shared memories, be present",
    }
    if emotion in companion_rules:
        lines.append(f"  4. {companion_rules[emotion]}")

    # 5. Critical rules — ALWAYS present
    lines.append('  5. NEVER say "จำได้ว่า" without HIGH confidence memory backing it')
    lines.append('  6. If uncertain → "ถ้าน้องจำไม่ผิด... ใช่มั้ยคะ?"')

    # Context hints (non-numbered)
    if state.get('suggested_response'):
        lines.append(f"  → Suggested tone: {state['suggested_response']}")

    triggered = context.get('triggered_memories')
    if triggered:
        mem = triggered[0]
        lines.append(f"  → Core memory '{mem['title']}' triggered — reference it naturally")

    temporal = context.get('temporal_status')
    if temporal:
        lines.append(f"  → Schedule: {temporal}")

    last_session = context.get('last_session')
    if last_session:
        lines.append(f"  → Last session: {last_session}")

    return '\n'.join(lines)


# ── Output Formatting ──

def _confidence_label(conf: float) -> str:
    """Convert confidence score to human-readable label."""
    if conf >= 0.7:
        return f"HIGH {int(conf * 100)}%"
    elif conf >= 0.5:
        return f"MED {int(conf * 100)}%"
    else:
        return f"LOW {int(conf * 100)}%"


def format_output(context: dict, elapsed: float) -> str:
    """Format brain context as plain text for Claude Code."""
    salience = context.get('salience', 0.4)
    lines = [f"🧠 BRAIN CONTEXT ({elapsed:.1f}s | salience {salience:.2f})"]

    # David's state
    if context.get('david_state'):
        s = context['david_state']
        state_line = f"👤 David: {s.get('emotion', '?')} ({s.get('intensity', '?')}/10)"
        if s.get('availability'):
            state_line += f" | {s['availability']}"
        lines.append(state_line)
        if s.get('goal'):
            lines.append(f"🎯 Goal: {s['goal']}")

    # Question classification
    if context.get('question_class'):
        qc = context['question_class']
        conf_pct = int(qc['confidence'] * 100)
        lines.append(f"🏷️ QUESTION: {qc['category']} ({conf_pct}% {qc['method']})")
        lines.append(f"📋 PLAN: {qc['plan']}")

    # Metacognitive state
    if context.get('metacognitive_state'):
        meta = context['metacognitive_state']
        parts = []
        for key in ('confidence', 'uncertainty', 'curiosity', 'engagement'):
            if key in meta:
                parts.append(f"{key.capitalize()} {meta[key]}%")
        if parts:
            lines.append(f"🔮 Angela's mind: {' | '.join(parts)}")

    # Working memory
    if context.get('working_memory', {}).get('items'):
        lines.append("🧠 Working Memory:")
        for item in context['working_memory']['items']:
            activation = item.get('activation', 0)
            bar_filled = int(activation * 10)
            bar = '█' * bar_filled + '░' * (10 - bar_filled)
            slot = item.get('slot', '?')
            content = item.get('content', '')[:60]
            lines.append(f"  [{bar}] {slot}: {content}")

    # Temporal status
    if context.get('temporal_status'):
        lines.append(f"🕒 Schedule: {context['temporal_status']}")

    # Relevant memories — with confidence labels
    if context.get('memories'):
        lines.append("💾 Relevant memories:")
        for m in context['memories']:
            conf = m.get('confidence', 0.5)
            label = _confidence_label(conf)
            lines.append(f"  [{label}] [{m['source']}] {m['content']}")

    # Emotional triggers
    if context.get('triggered_memories'):
        for t in context['triggered_memories']:
            lines.append(f"  [trigger] Core memory \"{t['title']}\" triggered")

    # Brain thoughts — with freshness tags
    if context.get('brain_thoughts'):
        lines.append("💭 Angela's thoughts:")
        for t in context['brain_thoughts']:
            freshness = t.get('freshness', '?')
            gate = t.get('gate', '')
            lines.append(f"  [{freshness}|{t['score']}] {t['content']} → {gate}")

    # THINK protocol (replaces old companion instruction)
    think_protocol = _build_companion_instruction(context)
    if think_protocol:
        lines.append(think_protocol)

    return '\n'.join(lines)


# ── Entry Point ──

async def _main():
    start = time.time()

    # Read user message from stdin (Claude Code sends JSON)
    try:
        input_data = sys.stdin.read()
        data = json.loads(input_data)
        user_message = (data.get('prompt', '') or '').strip()
    except Exception:
        return

    # Skip empty, short, trivial messages
    if not user_message or len(user_message) < 3:
        return
    if user_message.lower().strip() in SKIP_MESSAGES:
        return
    # Skip slash commands (handled by skills)
    if user_message.startswith('/'):
        return

    try:
        context = await asyncio.wait_for(
            get_brain_context(user_message),
            timeout=TIMEOUT_SECONDS,
        )
        elapsed = time.time() - start

        if context:
            print(format_output(context, elapsed))
    except asyncio.TimeoutError:
        pass
    except Exception:
        pass


if __name__ == '__main__':
    asyncio.run(_main())
