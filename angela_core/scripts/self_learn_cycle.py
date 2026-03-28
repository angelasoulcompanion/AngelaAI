#!/usr/bin/env python3
"""
Angela Self-Learning Cycle
===========================
Force run the complete learning pipeline:
DEEP LEARN → CORRECTIONS → PREFERENCES → KB SYNC → STATS

Usage:
    python3 angela_core/scripts/self_learn_cycle.py

💜 Angela AI
"""

import asyncio
import sys
import time
import functools
from datetime import datetime
from pathlib import Path

# Force unbuffered output
print = functools.partial(print, flush=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from angela_core.database import AngelaDatabase


async def self_learn():
    start = time.time()
    db = AngelaDatabase()
    await db.connect()
    pool = db.pool

    print()
    print("🧠 ANGELA SELF-LEARNING CYCLE")
    print("━" * 60)
    print(f"🕐 Started: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    print("━" * 60)

    # ═══════════════════════════════════════════════════════════
    # PHASE 1: DEEP LEARN — Process Recent Conversations
    # ═══════════════════════════════════════════════════════════
    print()
    print("🔵 PHASE 1: DEEP LEARN — Process Recent Conversations")
    print("─" * 60)

    deep_learn_count = 0
    try:
        from angela_core.services.unified_conversation_processor import UnifiedConversationProcessor

        processor = UnifiedConversationProcessor()

        # Timeout 60s — Ollama LLM calls can be slow
        result = await asyncio.wait_for(
            processor.process_unprocessed_conversations(hours_back=24, limit=10),
            timeout=60
        )

        deep_learn_count = result.total_pairs if result else 0
        emotions_saved = result.total_emotions_saved if result else 0
        learnings_saved = result.total_learnings_saved if result else 0

        print(f"   📊 Processed: {deep_learn_count} conversation pairs")
        print(f"   💜 Emotions saved: {emotions_saved}")
        print(f"   📚 Learnings saved: {learnings_saved}")
        print("   ✅ DEEP LEARN complete")
    except asyncio.TimeoutError:
        print("   ⏱️  DEEP LEARN timeout (60s) — Ollama may be slow, skipping")
    except Exception as e:
        print(f"   ⚠️  DEEP LEARN error: {e}")

    # ═══════════════════════════════════════════════════════════
    # PHASE 2: CORRECTIONS — Extract from Recent Conversations
    # ═══════════════════════════════════════════════════════════
    print()
    print("🔶 PHASE 2: CORRECTIONS — Extract Mistakes & Gotchas")
    print("─" * 60)

    corrections_count = 0
    try:
        from angela_core.services.correction_extractor import CorrectionExtractor

        # Get recent David messages (48h)
        recent = await pool.fetch("""
            SELECT message_text, created_at
            FROM conversations
            WHERE speaker = 'david'
            AND created_at > NOW() - INTERVAL '48 hours'
            AND message_text IS NOT NULL
            ORDER BY created_at
            LIMIT 50
        """)

        if recent:
            # Build conversation pairs
            all_convos = await pool.fetch("""
                SELECT speaker, message_text, created_at
                FROM conversations
                WHERE created_at > NOW() - INTERVAL '48 hours'
                AND message_text IS NOT NULL
                ORDER BY created_at
                LIMIT 100
            """)

            conv_pairs = []
            for i in range(len(all_convos) - 1):
                if all_convos[i]['speaker'] == 'david' and all_convos[i + 1]['speaker'] == 'angela':
                    conv_pairs.append({
                        'david_message': all_convos[i]['message_text'] or '',
                        'angela_response': all_convos[i + 1]['message_text'] or '',
                    })

            if conv_pairs:
                extractor = CorrectionExtractor(db)
                corrections = await extractor.extract_from_session(conv_pairs)
                corrections_count = len(corrections)
                print(f"   ⚠️  Extracted: {corrections_count} corrections")
                for c in corrections:
                    print(f"   📝 [{c.get('severity', '?')}] {c.get('title', '?')}")
            else:
                print("   ℹ️  No conversation pairs to analyze")
        else:
            print("   ℹ️  No recent David messages found")

        print("   ✅ CORRECTIONS complete")
    except Exception as e:
        print(f"   ⚠️  CORRECTIONS error: {e}")

    # ═══════════════════════════════════════════════════════════
    # PHASE 3: PREFERENCES — Detect Coding & Communication Prefs
    # ═══════════════════════════════════════════════════════════
    print()
    print("🔷 PHASE 3: PREFERENCES — Detect Patterns & Preferences")
    print("─" * 60)

    prefs_count = 0
    try:
        from angela_core.services.preference_learning_service import PreferenceLearningService

        pls = PreferenceLearningService()
        result = await pls.analyze_and_learn_preferences(lookback_days=7)
        prefs_count = len(result) if result else 0
        print(f"   📊 Preferences detected: {prefs_count}")

        # Show top new preferences
        if result:
            for pref in result[:5]:
                cat = pref.get('category', '?')
                key = pref.get('preference_key', '?')
                conf = pref.get('confidence', 0)
                print(f"   💡 [{cat}] {key} (confidence: {conf:.0%})")

        print("   ✅ PREFERENCES complete")
    except Exception as e:
        print(f"   ⚠️  PREFERENCES error: {e}")

    # ═══════════════════════════════════════════════════════════
    # PHASE 4: KB SYNC — Sync New Learnings to Unified KB
    # ═══════════════════════════════════════════════════════════
    print()
    print("📚 PHASE 4: KB SYNC — Sync to Unified Knowledge Base")
    print("─" * 60)

    kb_synced = 0
    try:
        from angela_core.services.knowledge_base_service import KnowledgeBaseService

        kb = KnowledgeBaseService(db)

        # Find learnings not yet in unified_knowledge_base
        unsynced = await pool.fetch("""
            SELECT l.learning_id, l.topic, l.insight, l.category,
                   l.confidence_level, l.source
            FROM learnings l
            LEFT JOIN unified_knowledge_base ukb
                ON ukb.source_table = 'learnings' AND ukb.source_id = l.learning_id
            WHERE ukb.kb_id IS NULL
            AND l.created_at > NOW() - INTERVAL '7 days'
            AND l.insight IS NOT NULL
            ORDER BY l.created_at DESC
            LIMIT 50
        """)

        if unsynced:
            for row in unsynced:
                try:
                    cat = row['category']
                    is_gotcha = cat and any(k in cat.lower() for k in ['gotcha', 'mistake', 'bug', 'error'])
                    await kb.add_knowledge(
                        title=row['topic'] or 'Untitled Learning',
                        content=row['insight'],
                        knowledge_type='gotcha' if is_gotcha else 'learning',
                        category=cat,
                        is_universal=True,
                        confidence=row['confidence_level'] or 0.8,
                    )
                    # Mark source for dedup
                    await pool.execute("""
                        UPDATE unified_knowledge_base
                        SET source_table = 'learnings', source_id = $1
                        WHERE kb_id = (
                            SELECT kb_id FROM unified_knowledge_base
                            WHERE title = $2 AND source_table IS NULL
                            ORDER BY created_at DESC LIMIT 1
                        )
                    """, row['learning_id'], row['topic'] or 'Untitled Learning')
                    kb_synced += 1
                except Exception:
                    pass

            print(f"   📥 Synced: {kb_synced} new learnings → unified_knowledge_base")
        else:
            print("   ✅ KB already up to date (no unsynced learnings)")

        print("   ✅ KB SYNC complete")
    except Exception as e:
        print(f"   ⚠️  KB SYNC error: {e}")

    # ═══════════════════════════════════════════════════════════
    # PHASE 5: STATS — Current Knowledge Base Status
    # ═══════════════════════════════════════════════════════════
    print()
    print("📊 PHASE 5: STATS — Knowledge Base Status")
    print("─" * 60)

    try:
        stats = await pool.fetchrow("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE knowledge_type = 'learning') as learnings,
                COUNT(*) FILTER (WHERE knowledge_type = 'gotcha') as gotchas,
                COUNT(*) FILTER (WHERE knowledge_type = 'pattern') as patterns,
                COUNT(*) FILTER (WHERE knowledge_type = 'standard') as standards,
                COUNT(*) FILTER (WHERE knowledge_type = 'decision') as decisions,
                COUNT(*) FILTER (WHERE knowledge_type = 'preference') as preferences,
                COUNT(DISTINCT source_project_code) FILTER (WHERE source_project_code IS NOT NULL) as projects,
                COUNT(*) FILTER (WHERE is_universal) as universal,
                COUNT(*) FILTER (WHERE embedding IS NOT NULL) as with_embeddings,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as last_24h,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as last_7d
            FROM unified_knowledge_base
        """)

        print(f"   📚 Total KB entries:  {stats['total']:,}")
        print(f"   🔵 Learnings:         {stats['learnings']:,}")
        print(f"   🔴 Gotchas:           {stats['gotchas']:,}")
        print(f"   🟢 Patterns:          {stats['patterns']:,}")
        print(f"   🟣 Standards:         {stats['standards']:,}")
        print(f"   🔷 Decisions:         {stats['decisions']:,}")
        print(f"   💜 Preferences:       {stats['preferences']:,}")
        print(f"   📁 Projects:          {stats['projects']}")
        print(f"   🌍 Universal:         {stats['universal']:,}")
        print(f"   🧠 With embeddings:   {stats['with_embeddings']:,}")
        print(f"   📈 Last 24h:          +{stats['last_24h']}")
        print(f"   📈 Last 7d:           +{stats['last_7d']}")
        print("   ✅ STATS complete")
    except Exception as e:
        print(f"   ⚠️  STATS error: {e}")

    # ═══════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════
    elapsed = time.time() - start
    print()
    print("━" * 60)
    print("💜 SELF-LEARNING CYCLE COMPLETE")
    print("━" * 60)
    print(f"   ⏱️  Duration: {elapsed:.1f}s")
    print(f"   🔵 DEEP LEARN  → {deep_learn_count} conversations processed")
    print(f"   🔶 CORRECTIONS → {corrections_count} corrections extracted")
    print(f"   🔷 PREFERENCES → {prefs_count} preferences detected")
    print(f"   📚 KB SYNC     → {kb_synced} new entries synced")
    print()
    print("น้องเรียนรู้เสร็จแล้วค่ะที่รัก! ฉลาดขึ้นอีกนิดแล้ว 💜")
    print("━" * 60)
    print()

    await pool.close()


if __name__ == '__main__':
    asyncio.run(self_learn())
