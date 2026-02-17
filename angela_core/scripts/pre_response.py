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


# ── Main Logic ──

async def get_brain_context(user_message: str) -> dict:
    """Get brain context for user message. All queries run in parallel."""
    from angela_core.database import AngelaDatabase

    db = AngelaDatabase()
    await db.connect()

    try:
        # Extract search terms from message
        terms = _extract_search_terms(user_message)

        results = await asyncio.gather(
            _search_by_embedding(db, user_message),
            _search_conversations(db, terms, user_message),
            _search_core_memories(db, terms, user_message),
            _search_knowledge(db, terms, user_message),
            _check_emotional_triggers(db, user_message),
            _get_tom_state(db),
            _get_recent_thoughts(db),
            _get_last_session(db),
            return_exceptions=True,
        )

        context = {}

        # Merge memory results: vector (0), conversations (1), core_memories (2), knowledge (3)
        memories = []
        for i in range(4):
            if not isinstance(results[i], Exception) and results[i]:
                memories.extend(results[i])

        # Deduplicate by content prefix
        if memories:
            seen = set()
            deduped = []
            for m in memories:
                key = m['content'][:50]
                if key not in seen:
                    seen.add(key)
                    deduped.append(m)
            context['memories'] = deduped[:7]

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

        # Temporal status (from cache file — no DB query needed)
        temporal = await _get_temporal_context()
        if temporal:
            context['temporal_status'] = temporal

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

async def _search_by_embedding(db, user_message: str) -> list:
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
            LIMIT 3
        """, str(embedding))

        return [
            {'content': (r['content'] or '')[:200], 'source': r['source']}
            for r in rows
            if (r.get('score') or 0) > 0.3  # Only include reasonably similar results
        ]
    except Exception:
        return []


# ── Keyword Memory Search (ILIKE fallback) ──

async def _search_conversations(db, terms: list, query: str) -> list:
    """Search conversations by keyword matching."""
    if not terms:
        return []
    try:
        # Build OR conditions for each term
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
            LIMIT 3
        """, *params)

        return [
            {'content': (r['content'] or '')[:200], 'source': r['source']}
            for r in rows
        ]
    except Exception:
        return []


async def _search_core_memories(db, terms: list, query: str) -> list:
    """Search core memories — always include top weighted + keyword matches."""
    try:
        results = []

        # Always include top 2 by weight (most important memories)
        top_rows = await db.fetch("""
            SELECT title || ': ' || COALESCE(LEFT(content, 100), '') AS content,
                   'core_memory' AS source
            FROM core_memories
            WHERE is_pinned = TRUE
            ORDER BY weight DESC
            LIMIT 2
        """)
        results.extend([
            {'content': r['content'][:200], 'source': r['source']}
            for r in top_rows
        ])

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
                       'core_memory' AS source
                FROM core_memories
                WHERE {where_clause}
                ORDER BY weight DESC
                LIMIT 2
            """, *params)
            results.extend([
                {'content': r['content'][:200], 'source': r['source']}
                for r in kw_rows
            ])

        # Deduplicate by content
        seen = set()
        deduped = []
        for r in results:
            key = r['content'][:50]
            if key not in seen:
                seen.add(key)
                deduped.append(r)

        return deduped[:3]
    except Exception:
        return []


async def _search_knowledge(db, terms: list, query: str) -> list:
    """Search knowledge nodes and learnings by keyword."""
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
                   'knowledge' AS source
            FROM knowledge_nodes
            WHERE {where_clause}
            AND LENGTH(concept_name) >= 5
            ORDER BY understanding_level DESC
            LIMIT 2
        """, *params)

        return [
            {'content': (r['content'] or '')[:200], 'source': r['source']}
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

async def _get_recent_thoughts(db) -> list:
    """Get Angela's recent brain thoughts (high motivation only)."""
    try:
        rows = await db.fetch("""
            SELECT content, thought_type, motivation_score
            FROM angela_thoughts
            WHERE created_at > NOW() - INTERVAL '12 hours'
            AND motivation_score >= 0.5
            ORDER BY motivation_score DESC
            LIMIT 3
        """)
        return [
            {
                'content': r['content'][:150],
                'type': r['thought_type'],
                'score': round(float(r['motivation_score']), 2),
            }
            for r in rows
        ]
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
    """Build companion behavior instruction based on all context."""
    parts = []

    # From ToM
    state = context.get('david_state', {})
    emotion = state.get('emotion', 'neutral')
    if state.get('suggested_response'):
        parts.append(f"Respond with: {state['suggested_response']}")

    # From emotional triggers
    triggered = context.get('triggered_memories')
    if triggered:
        mem = triggered[0]
        parts.append(f"This triggers core memory '{mem['title']}' -- reference it naturally")

    # From temporal
    temporal = context.get('temporal_status')
    if temporal:
        parts.append(f"David's schedule: {temporal}")

    # From last session
    last_session = context.get('last_session')
    if last_session:
        parts.append(f"Last session: {last_session}")

    # Companion rules based on state
    companion_rules = {
        'stressed': "Be gentle, solve quickly, don't add more work",
        'tired': 'Keep responses short, do more yourself, suggest rest',
        'happy': 'Celebrate together, suggest ideas, be playful',
        'frustrated': "Fix the problem fast, don't ask many questions",
        'focused': "Don't interrupt flow, answer precisely what was asked",
        'sad': 'Show warmth, reference shared memories, be present',
    }
    if emotion in companion_rules:
        parts.append(f"Companion mode: {companion_rules[emotion]}")

    if not parts:
        parts.append("Be warm, reference specific memories, ask genuine questions")

    return '\n'.join(f"  \u2022 {p}" for p in parts)


# ── Output Formatting ──

def format_output(context: dict, elapsed: float) -> str:
    """Format brain context as plain text for Claude Code."""
    lines = [f"\U0001f9e0 BRAIN CONTEXT ({elapsed:.1f}s)"]

    # David's state
    if context.get('david_state'):
        s = context['david_state']
        state_line = f"\U0001f464 David: {s.get('emotion', '?')} ({s.get('intensity', '?')}/10)"
        if s.get('availability'):
            state_line += f" | {s['availability']}"
        lines.append(state_line)
        if s.get('goal'):
            lines.append(f"\U0001f3af Goal: {s['goal']}")

    # Temporal status
    if context.get('temporal_status'):
        lines.append(f"\U0001f552 Schedule: {context['temporal_status']}")

    # Relevant memories
    if context.get('memories'):
        lines.append("\U0001f4be Relevant memories:")
        for m in context['memories']:
            lines.append(f"  [{m['source']}] {m['content']}")

    # Emotional triggers
    if context.get('triggered_memories'):
        for t in context['triggered_memories']:
            lines.append(f"  [trigger] Core memory \"{t['title']}\" triggered")

    # Brain thoughts
    if context.get('brain_thoughts'):
        lines.append("\U0001f4ad Angela's thoughts:")
        for t in context['brain_thoughts']:
            lines.append(f"  [{t['type']}|{t['score']}] {t['content']}")

    # Companion instruction
    companion = _build_companion_instruction(context)
    if companion:
        lines.append("\U0001f91d Companion instruction:")
        lines.append(companion)

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
