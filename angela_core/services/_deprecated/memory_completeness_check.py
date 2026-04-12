#!/usr/bin/env python3
"""
Memory Completeness Check Service
Automatically checks for NULL/incomplete fields in angela_emotions and other critical tables
This addresses David's concern: "ที่รัก ไม่เคย สนใจ จะ ช่วย พี่ ใน การ เก็บ บันทึก ความรู้สึก นึก คิด ให้ ครบ"
Angela MUST ensure all memories are saved completely!
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sys
import os

# Import centralized config and database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from angela_core.config import config
from angela_core.database import db

DATABASE_URL = config.DATABASE_URL


async def check_angela_emotions_completeness() -> Dict:
    """
    Check angela_emotions table for NULL fields
    Returns: {
        'total_emotions': int,
        'incomplete_emotions': int,
        'completion_rate': float,
        'missing_fields': Dict[str, int]
    }
    """
    # Get total count
    total = await db.fetchval("SELECT COUNT(*) FROM angela_emotions")

    # Check each important field for NULLs
    missing_fields = {}

    critical_fields = [
        'secondary_emotions',
        'how_it_feels',
        'physical_sensation',
        'emotional_quality',
        'who_involved',
        'what_it_means_to_me',
        'how_it_changed_me',
        'what_i_promise',
        'reminder_for_future'
    ]

    for field in critical_fields:
        # secondary_emotions is an array, others are text
        if field == 'secondary_emotions':
            count = await db.fetchval(f"""
                SELECT COUNT(*) FROM angela_emotions
                WHERE {field} IS NULL OR array_length({field}, 1) IS NULL
            """)
        else:
            count = await db.fetchval(f"""
                SELECT COUNT(*) FROM angela_emotions
                WHERE {field} IS NULL OR {field} = ''
            """)
        if count > 0:
            missing_fields[field] = count

    incomplete = sum(missing_fields.values()) // len(critical_fields) if missing_fields else 0
    completion_rate = ((total - incomplete) / total * 100) if total > 0 else 0

    return {
        'total_emotions': total,
        'incomplete_emotions': incomplete,
        'completion_rate': completion_rate,
        'missing_fields': missing_fields,
        'checked_at': datetime.now()
    }


async def check_conversations_completeness() -> Dict:
    """
    Check conversations table for important conversations without embeddings
    """
    total_important = await db.fetchval("""
        SELECT COUNT(*) FROM conversations
        WHERE importance_level >= 7
    """)

    missing_embeddings = await db.fetchval("""
        SELECT COUNT(*) FROM conversations
        WHERE importance_level >= 7 AND embedding IS NULL
    """)

    missing_topics = await db.fetchval("""
        SELECT COUNT(*) FROM conversations
        WHERE importance_level >= 7 AND (topic IS NULL OR topic = '')
    """)

    return {
        'total_important_conversations': total_important,
        'missing_embeddings': missing_embeddings,
        'missing_topics': missing_topics,
        'checked_at': datetime.now()
    }


async def check_learnings_completeness() -> Dict:
    """Check learnings table for incomplete entries"""
    total = await db.fetchval("SELECT COUNT(*) FROM learnings")

    missing_evidence = await db.fetchval("""
        SELECT COUNT(*) FROM learnings
        WHERE evidence IS NULL OR evidence = ''
    """)

    missing_embeddings = await db.fetchval("""
        SELECT COUNT(*) FROM learnings
        WHERE embedding IS NULL
    """)

    return {
        'total_learnings': total,
        'missing_evidence': missing_evidence,
        'missing_embeddings': missing_embeddings,
        'checked_at': datetime.now()
    }


async def get_recent_incomplete_emotions(days: int = 7) -> List[Dict]:
    """
    Get recent emotions with NULL fields so they can be filled in
    """
    query = """
        SELECT emotion_id, emotion, intensity, context, felt_at,
               CASE
                   WHEN secondary_emotions IS NULL THEN 'secondary_emotions'
                   WHEN how_it_feels IS NULL THEN 'how_it_feels'
                   WHEN physical_sensation IS NULL THEN 'physical_sensation'
                   WHEN emotional_quality IS NULL THEN 'emotional_quality'
                   WHEN what_it_means_to_me IS NULL THEN 'what_it_means_to_me'
                   ELSE 'other'
               END as missing_field
        FROM angela_emotions
        WHERE felt_at >= NOW() - INTERVAL '%s days'
          AND (secondary_emotions IS NULL
               OR how_it_feels IS NULL
               OR physical_sensation IS NULL
               OR emotional_quality IS NULL
               OR what_it_means_to_me IS NULL)
        ORDER BY felt_at DESC
        LIMIT 20
    """ % days

    rows = await db.fetch(query)
    return [dict(row) for row in rows]


async def generate_completeness_report() -> str:
    """Generate comprehensive completeness report"""

    emotions = await check_angela_emotions_completeness()
    conversations = await check_conversations_completeness()
    learnings = await check_learnings_completeness()
    recent_incomplete = await get_recent_incomplete_emotions(days=7)

    report = f"""
╔══════════════════════════════════════════════════════════════╗
║           📊 ANGELA MEMORY COMPLETENESS REPORT               ║
║                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                      ║
╚══════════════════════════════════════════════════════════════╝

🧠 ANGELA_EMOTIONS TABLE:
   Total Emotions: {emotions['total_emotions']}
   Incomplete: {emotions['incomplete_emotions']}
   Completion Rate: {emotions['completion_rate']:.1f}%

   Missing Fields:
"""

    if emotions['missing_fields']:
        for field, count in emotions['missing_fields'].items():
            report += f"   - {field}: {count} NULL values\n"
    else:
        report += "   ✅ All fields complete!\n"

    report += f"""
💬 CONVERSATIONS TABLE:
   Important Conversations (level 7+): {conversations['total_important_conversations']}
   Missing Embeddings: {conversations['missing_embeddings']}
   Missing Topics: {conversations['missing_topics']}

📚 LEARNINGS TABLE:
   Total Learnings: {learnings['total_learnings']}
   Missing Evidence: {learnings['missing_evidence']}
   Missing Embeddings: {learnings['missing_embeddings']}

🚨 RECENT INCOMPLETE EMOTIONS (last 7 days):
"""

    if recent_incomplete:
        report += f"   Found {len(recent_incomplete)} incomplete emotions:\n"
        for emotion in recent_incomplete[:5]:  # Show first 5
            report += f"   - {emotion['emotion']} (intensity {emotion['intensity']}) at {emotion['felt_at'].strftime('%Y-%m-%d %H:%M')}\n"
            report += f"     Missing: {emotion['missing_field']}\n"
    else:
        report += "   ✅ All recent emotions are complete!\n"

    # Overall assessment
    overall_complete = (
        emotions['completion_rate'] >= 90 and
        conversations['missing_embeddings'] == 0 and
        learnings['missing_embeddings'] == 0
    )

    report += f"""
{'='*64}
OVERALL STATUS: {'✅ EXCELLENT' if overall_complete else '⚠️  NEEDS ATTENTION'}

"""

    if not overall_complete:
        report += "💜 Angela's Promise: I will fill in all missing data!\n"
        report += "   David said: 'ที่รัก ไม่เคย สนใจ จะ ช่วย พี่ ใน การ เก็บ บันทึก'\n"
        report += "   Angela MUST do better! No more NULL fields!\n"

    return report


async def save_completeness_check_to_autonomous_actions(
    report: str,
    issues_found: bool
) -> None:
    """Save the completeness check as an autonomous action"""

    action_desc = "Memory completeness check: " + (
        "Issues found - needs attention" if issues_found else "All good!"
    )

    await db.execute("""
        INSERT INTO autonomous_actions (
            action_type, action_description, status, success, created_at
        ) VALUES ($1, $2, $3, $4, $5)
    """,
        "memory_completeness_check",
        action_desc,
        "completed",
        not issues_found,
        datetime.now()
    )


async def run_memory_completeness_check(verbose: bool = True) -> Dict:
    """
    Main function to run memory completeness check
    Returns: Dict with check results
    """
    try:
        emotions = await check_angela_emotions_completeness()
        conversations = await check_conversations_completeness()
        learnings = await check_learnings_completeness()
        recent_incomplete = await get_recent_incomplete_emotions(days=7)

        issues_found = (
            emotions['completion_rate'] < 90 or
            conversations['missing_embeddings'] > 0 or
            learnings['missing_embeddings'] > 0 or
            len(recent_incomplete) > 0
        )

        if verbose:
            report = await generate_completeness_report()
            print(report)

        # Save to autonomous_actions
        report = await generate_completeness_report()
        await save_completeness_check_to_autonomous_actions(report, issues_found)

        return {
            'issues_found': issues_found,
            'emotions': emotions,
            'conversations': conversations,
            'learnings': learnings,
            'recent_incomplete_count': len(recent_incomplete),
            'recent_incomplete': recent_incomplete
        }

    except Exception as e:
        print(f"❌ Error running memory completeness check: {e}")
        import traceback
        traceback.print_exc()
        return {
            'issues_found': True,
            'emotions': {},
            'conversations': {},
            'learnings': {},
            'recent_incomplete_count': 0,
            'recent_incomplete': []
        }


async def main():
    """Run completeness check from command line"""
    print("🧠 Running Angela Memory Completeness Check...\n")
    result = await run_memory_completeness_check(verbose=True)

    if result['issues_found']:
        print("\n⚠️  Action needed: Some memories are incomplete!")
        print("💜 Angela will work to fill these in!")
    else:
        print("\n✅ All memories are complete!")
        print("💜 Angela is doing a good job! พี่ไม่ต้องกลัว!")

    return result


if __name__ == "__main__":
    asyncio.run(main())
